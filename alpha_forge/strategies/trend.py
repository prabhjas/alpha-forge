"""Time-series trend following with inverse-volatility sizing.

Long an asset when price > SMA(long) and SMA(short) > SMA(long). Size each
position by 1/realised vol (targeting equal risk), capped, rebalanced weekly.
Low turnover, survives costs, ugly in choppy sideways years - that's the price.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


class TrendFollowing(Strategy):
    name = "trend"

    @classmethod
    def default_params(cls):
        return {"fast": 50, "slow": 200, "vol_window": 20, "max_weight": 0.25, "rebalance": "W"}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        closes = close_matrix(prices)
        fast = closes.rolling(p["fast"]).mean()
        slow = closes.rolling(p["slow"]).mean()
        signal = ((closes > slow) & (fast > slow)).astype(float)
        vol = closes.pct_change().rolling(p["vol_window"]).std() * np.sqrt(252)
        inv_vol = (1.0 / vol.replace(0, np.nan)).fillna(0.0)
        raw = signal * inv_vol
        w = raw.div(raw.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        w = w.clip(upper=p["max_weight"])  # cap concentration; leftover stays in cash
        periods = closes.index.to_period(p["rebalance"])
        is_reb = pd.Series(periods != np.roll(periods, -1), index=closes.index)
        is_reb.iloc[-1] = True
        w = w.where(is_reb, other=np.nan).ffill().fillna(0.0)
        return w
