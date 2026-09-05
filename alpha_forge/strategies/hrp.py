"""Trend filter + skfolio Hierarchical Risk Parity sizing.

Same entry rule as TrendFollowing (close > SMA(slow) and SMA(fast) > SMA(slow)),
but instead of sizing by 1/vol we hand the eligible assets to skfolio's HRP,
which clusters by correlation and allocates risk across clusters. On a book of
correlated ETFs/stocks this should spread risk better than inverse-vol, which
happily piles into five things that all move together.

Requires skfolio (Python 3.10+). Import is lazy so the rest of the package
works on the 3.9 environment.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


class TrendHRP(Strategy):
    name = "trend_hrp"

    @classmethod
    def default_params(cls):
        return {"fast": 50, "slow": 200, "lookback": 252, "max_weight": 0.25, "rebalance": "M", "model": "hrp"}

    def _allocator(self):
        from skfolio.optimization import HierarchicalRiskParity, RiskBudgeting, MeanRisk, InverseVolatility
        from skfolio.moments import LedoitWolf
        from skfolio.prior import EmpiricalPrior
        from skfolio import RiskMeasure
        p = self.params
        prior = EmpiricalPrior(covariance_estimator=LedoitWolf())
        if p["model"] == "hrp":
            return HierarchicalRiskParity(risk_measure=RiskMeasure.VARIANCE, prior_estimator=prior)
        if p["model"] == "riskparity":
            return RiskBudgeting(risk_measure=RiskMeasure.VARIANCE, prior_estimator=prior)  # cap applied after fit
        if p["model"] == "minvar":
            return MeanRisk(risk_measure=RiskMeasure.VARIANCE, prior_estimator=prior)  # cap applied after fit
        if p["model"] == "invvol":
            return InverseVolatility(prior_estimator=prior)
        raise ValueError(p["model"])

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        closes = close_matrix(prices)
        rets = closes.pct_change()
        fast = closes.rolling(p["fast"]).mean()
        slow = closes.rolling(p["slow"]).mean()
        signal = (closes > slow) & (fast > slow)
        periods = closes.index.to_period(p["rebalance"])
        is_reb = pd.Series(periods != np.roll(periods, -1), index=closes.index)
        is_reb.iloc[-1] = True
        weights = pd.DataFrame(np.nan, index=closes.index, columns=closes.columns)
        alloc = self._allocator()
        for i, ts in enumerate(closes.index):
            if not is_reb.iloc[i] or i < p["lookback"]:
                continue
            eligible = [c for c in closes.columns if signal.iloc[i][c]]
            row = pd.Series(0.0, index=closes.columns)
            if len(eligible) == 1:
                row[eligible[0]] = min(1.0, p["max_weight"])
            elif len(eligible) > 1:
                X = rets.iloc[i - p["lookback"] + 1:i + 1][eligible].dropna(axis=1, how="any")
                X = X.loc[:, X.std() > 0]  # a flat/ffilled series would give NaN correlations
                if X.shape[1] == 2 or (X.shape[1] >= 2 and p["model"] == "hrp" and X.shape[1] < 3):
                    # hierarchical clustering needs >= 3 assets; fall back to inverse-vol
                    iv = 1.0 / X.std()
                    w = iv / iv.sum()
                    row[w.index] = w.clip(upper=p["max_weight"]).values
                elif X.shape[1] >= 3 and len(X) > 60:
                    try:
                        alloc.fit(X)
                        w = pd.Series(alloc.weights_, index=X.columns).clip(lower=0)
                    except Exception as e:  # solver hiccup -> inverse-vol for this month, never crash a live run
                        print(f"[trend_hrp] {ts.date()} {p['model']} fit failed ({type(e).__name__}); inverse-vol fallback")
                        iv = 1.0 / X.std()
                        w = iv
                    w = w / w.sum() if w.sum() > 0 else w
                    # cap, then renormalise the excess into cash (no leverage, never breach cap)
                    w = w.clip(upper=p["max_weight"])
                    row[w.index] = w.values
            weights.iloc[i] = row.values
        return weights.ffill().fillna(0.0)
