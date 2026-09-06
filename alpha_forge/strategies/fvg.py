"""Fair Value Gap (FVG) strategy — the one ICT/SMC concept that is a hard, testable rule.

A bullish FVG is a 3-candle pattern where candle[i-2].high < candle[i].low: price
jumped, leaving an unfilled gap that often acts as support on a pullback. Rule:
when a bullish FVG exists AND the name is in an uptrend (close > SMA200), hold it;
exit when price closes below the gap (invalidation) or trend breaks. Long-only,
equal-weight across active names. This lets us judge the concept the same way we
judged everything else: costs on, out of sample.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from alpha_forge.data.loader import close_matrix
from .base import Strategy


class FVGStrategy(Strategy):
    name = "fvg"

    @classmethod
    def default_params(cls):
        return {"trend_sma": 200, "max_hold": 20, "min_gap_pct": 0.3}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        closes = close_matrix(prices)
        active = pd.DataFrame(False, index=closes.index, columns=closes.columns)
        for sym, df in prices.items():
            if sym not in closes.columns:
                continue
            d = df.copy()
            d.index = pd.to_datetime(d.index)
            if getattr(d.index, "tz", None) is not None:
                d.index = d.index.tz_localize(None)
            d = d.reindex(closes.index)
            high2 = d["High"].shift(2)
            low0 = d["Low"]
            gap = (low0 - high2) / high2 * 100
            bull_fvg = gap > p["min_gap_pct"]            # gap up leaving a void
            sma = d["Close"].rolling(p["trend_sma"]).mean()
            uptrend = d["Close"] > sma
            gap_bottom = high2                            # the gap's lower edge = invalidation level
            held = False
            hold_age = 0
            level = np.nan
            col = []
            for i in range(len(d)):
                c = d["Close"].iloc[i]
                if held:
                    if pd.isna(c) or c < level or hold_age >= p["max_hold"] or not bool(uptrend.iloc[i]):
                        held = False
                    else:
                        hold_age += 1
                if not held and bool(bull_fvg.iloc[i]) and bool(uptrend.iloc[i]):
                    held = True; hold_age = 0; level = float(gap_bottom.iloc[i])
                col.append(held)
            active[sym] = col
        n = active.sum(axis=1).replace(0, np.nan)
        return active.astype(float).div(n, axis=0).fillna(0.0)
