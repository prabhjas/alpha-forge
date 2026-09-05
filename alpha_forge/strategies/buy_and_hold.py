from __future__ import annotations

from typing import Dict

import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


class BuyAndHold(Strategy):
    """Equal-weight buy and hold, rebalanced monthly. The bar every active strategy must beat."""

    name = "buyhold"

    @classmethod
    def default_params(cls):
        return {"rebalance": "M"}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        closes = close_matrix(prices)
        valid = closes.notna()
        w = valid.div(valid.sum(axis=1), axis=0).fillna(0.0)
        # hold weights constant between month-ends (let them drift -> low turnover)
        month_end = w.index.to_period(self.params["rebalance"]) != w.index.to_period(self.params["rebalance"]).shift(-1)
        w_reb = w.where(pd.Series(month_end, index=w.index), other=None).ffill().fillna(0.0)
        return w_reb
