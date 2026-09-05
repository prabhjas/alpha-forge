"""Cross-sectional momentum (Jegadeesh & Titman 1993; works on NSE too - see
'Momentum in Indian equities', multiple academic papers).

Each month: rank universe by 12-month return skipping the most recent month,
buy the top N equal-weighted. Optional regime filter: go to cash when the
benchmark is below its 200-day moving average (cuts the 2008/2020-style crashes).
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


class CrossSectionalMomentum(Strategy):
    name = "momentum"

    @classmethod
    def default_params(cls):
        return {"lookback": 252, "skip": 21, "top_n": 8, "rebalance": "M", "regime_filter": True, "regime_sma": 200}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        closes = close_matrix(prices)
        mom = closes.shift(p["skip"]) / closes.shift(p["lookback"]) - 1.0
        # Rebalance on last trading day of each period
        periods = closes.index.to_period(p["rebalance"])
        is_reb = pd.Series(periods != np.roll(periods, -1), index=closes.index)
        is_reb.iloc[-1] = True
        weights = pd.DataFrame(0.0, index=closes.index, columns=closes.columns)
        ranks = mom.rank(axis=1, ascending=False)
        sel = (ranks <= p["top_n"]) & mom.notna()
        w_reb = sel.div(sel.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        weights[is_reb.values] = w_reb[is_reb.values]
        weights = weights.where(is_reb, other=np.nan).ffill().fillna(0.0)
        if p["regime_filter"]:
            eq_index = closes.mean(axis=1)  # proxy for the universe index
            regime = (eq_index > eq_index.rolling(p["regime_sma"]).mean()).astype(float)
            weights = weights.mul(regime, axis=0)
        return weights
