"""Short-term mean reversion (Connors RSI(2) family).

Buy a liquid stock/ETF when it is in an uptrend (close > SMA200) but has had a
sharp 2-day pullback (RSI(2) < oversold). Exit when RSI(2) > exit level or after
max_hold days. Holds few positions, high turnover -> the strategy that costs kill
first; that's exactly why it is here as a teaching case.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


def rsi(close: pd.DataFrame, n: int) -> pd.DataFrame:
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


class RSIMeanReversion(Strategy):
    name = "meanrev"

    @classmethod
    def default_params(cls):
        return {"rsi_n": 2, "oversold": 10, "exit": 70, "trend_sma": 200, "max_hold": 5, "max_positions": 5}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        closes = close_matrix(prices)
        r = rsi(closes, p["rsi_n"])
        uptrend = closes > closes.rolling(p["trend_sma"]).mean()
        entry = (r < p["oversold"]) & uptrend
        exit_ = r > p["exit"]
        held = pd.DataFrame(False, index=closes.index, columns=closes.columns)
        age = pd.DataFrame(0, index=closes.index, columns=closes.columns)
        prev = pd.Series(False, index=closes.columns)
        prev_age = pd.Series(0, index=closes.columns)
        for i in range(len(closes)):
            e = entry.iloc[i].fillna(False)
            x = exit_.iloc[i].fillna(False)
            keep = prev & ~x & (prev_age < p["max_hold"])
            new = e & ~prev
            # cap number of new entries so we never exceed max_positions
            room = p["max_positions"] - int(keep.sum())
            if new.sum() > room:
                cand = r.iloc[i][new].sort_values()  # most oversold first
                new[:] = False
                new[cand.index[:max(room, 0)]] = True
            cur = keep | new
            cur_age = (prev_age + 1).where(keep, 0)
            held.iloc[i] = cur.values
            age.iloc[i] = cur_age.values
            prev, prev_age = cur, cur_age
        n = held.sum(axis=1).replace(0, np.nan)
        return held.astype(float).div(n, axis=0).fillna(0.0)
