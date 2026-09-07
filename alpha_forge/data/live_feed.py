"""Live end-of-day close from AngelOne, to fix the Yahoo lag.

At 16:00 IST Yahoo hasn't posted today's NSE daily bar yet, so a daily run would
rebalance on yesterday's data. This pulls today's close (LTP after market close ≈
close) from AngelOne and appends it as today's bar, so signals and fills are current.
Falls back silently per-symbol if a quote fails.
"""
from __future__ import annotations

import time
from typing import Dict, Iterable

import pandas as pd


def angelone_ltps(tickers: Iterable[str], pause: float = 0.2) -> Dict[str, float]:
    from alpha_forge.brokers.angelone_broker import AngelOneBroker
    b = AngelOneBroker(live=False)
    out: Dict[str, float] = {}
    for t in tickers:
        try:
            out[t] = b.last_price(t)
        except Exception:
            pass
        time.sleep(pause)
    return out


def append_today_close(prices: Dict[str, pd.DataFrame], ltps: Dict[str, float]) -> int:
    """Append a today bar (O=H=L=C=LTP) to any series whose last bar predates today.
    Returns how many symbols were updated. Close-based strategies only use Close."""
    today = pd.Timestamp.today().normalize()
    updated = 0
    for t, px in ltps.items():
        if t not in prices or px is None:
            continue
        df = prices[t]
        last = pd.Timestamp(df.index[-1]).normalize()
        if last < today:
            vol = float(df["Volume"].iloc[-1]) if "Volume" in df else 0.0
            prices[t].loc[today] = {"Open": px, "High": px, "Low": px, "Close": px, "Volume": vol}
            updated += 1
    return updated
