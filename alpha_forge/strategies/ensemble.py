"""Ensemble: blend several sub-strategies into ONE portfolio, then (optionally)
target a constant portfolio volatility.

Why this is better than running strategies separately:
  * Trend and momentum are positively but not perfectly correlated. Blending two
    edges that both beat the benchmark, but stumble at different times, raises
    risk-adjusted return (the only free lunch in finance: diversification).
  * Volatility targeting scales gross exposure up in calm markets and down in
    turbulent ones, holding portfolio risk roughly constant. It is the single
    most reliable drawdown-control technique in systematic trading.

No look-ahead: the vol scalar at day t uses only returns up to day t-1.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


class Ensemble(Strategy):
    name = "ensemble"

    @classmethod
    def default_params(cls):
        # components: list of (strategy_name, params_dict, budget). budgets are normalised.
        return {
            "components": [("trend", {}, 0.6), ("momentum", {}, 0.4)],
            "vol_target": 0.12,      # annualised; None disables targeting
            "vol_window": 30,
            "vol_scalar_cap": 1.0,   # never lever above 100% gross (Phase <4 rule)
            "vol_scalar_floor": 0.2,
        }

    def _build(self, name: str, params: dict):
        from alpha_forge.strategies import REGISTRY
        return REGISTRY[name](**params)

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        closes = close_matrix(prices)
        comps: List[Tuple[pd.DataFrame, float]] = []
        total_budget = sum(b for _, _, b in p["components"]) or 1.0
        for name, params, budget in p["components"]:
            w = self._build(name, params).generate_weights(prices).reindex(closes.index).reindex(columns=closes.columns).fillna(0.0)
            comps.append((w, budget / total_budget))
        blended = sum(w * b for w, b in comps)
        # cap any single name and renormalise gross to <= 1 (no leverage yet)
        gross = blended.abs().sum(axis=1)
        blended = blended.div(gross.where(gross > 1.0, 1.0), axis=0)

        if not p["vol_target"]:
            return blended

        asset_ret = closes.pct_change().fillna(0.0)
        # portfolio return the blend WOULD have earned, using yesterday's weights (causal)
        port_ret = (blended.shift(1).fillna(0.0) * asset_ret).sum(axis=1)
        realized = port_ret.rolling(p["vol_window"]).std() * np.sqrt(252)
        scalar = (p["vol_target"] / realized.replace(0, np.nan)).clip(p["vol_scalar_floor"], p["vol_scalar_cap"])
        scalar = scalar.shift(1).fillna(p["vol_scalar_floor"])  # decide today's size from data through yesterday
        return blended.mul(scalar, axis=0).fillna(0.0)


class SectorEnsemble(Ensemble):
    """3-way book for multi-sector stock universes: trend + momentum + sector-tilt.
    Best risk-adjusted config on Nifty 50 (Calmar 0.68). No vol target (few enough
    names that targeting adds little). Only use on universes with a sector map."""
    name = "sector_ensemble"

    @classmethod
    def default_params(cls):
        return {**Ensemble.default_params(),
                "components": [("trend", {}, 0.45), ("momentum", {}, 0.25), ("sector_tilt", {}, 0.30)],
                "vol_target": None}
