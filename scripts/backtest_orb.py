#!/usr/bin/env python
"""Intraday Opening Range Breakout (ORB) sanity check on 5-minute bars.

Rule: after the first `range_minutes` of the session, go long if price breaks the
range high (stop = range low, target = risk x rr, exit at close otherwise).
Long-only, one trade per symbol per day. Charges india_intraday / us costs.

Yahoo only gives ~60 days of 5m bars, so this is a SMELL TEST, not proof.
Real intraday research needs broker historical data (Kite paid / SmartAPI).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from alpha_forge.backtest import COST_PRESETS
from alpha_forge.backtest.metrics import performance_summary
from alpha_forge.data.loader import UNIVERSES, load_intraday


def orb_day(day: pd.DataFrame, range_bars: int, rr: float, cost_rt: float):
    if len(day) <= range_bars + 1:
        return None
    rng = day.iloc[:range_bars]
    hi, lo = rng["High"].max(), rng["Low"].min()
    risk = hi - lo
    if risk <= 0:
        return None
    rest = day.iloc[range_bars:]
    breakout = rest[rest["High"] > hi]
    if breakout.empty:
        return None
    entry_i = breakout.index[0]
    entry = hi
    after = rest.loc[entry_i:]
    stop, target = lo, hi + rr * risk
    for ts, bar in after.iterrows():
        if bar["Low"] <= stop:
            exit_px = stop; break
        if bar["High"] >= target:
            exit_px = target; break
    else:
        exit_px = after["Close"].iloc[-1]
    return (exit_px / entry - 1.0) - cost_rt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="nifty50", choices=list(UNIVERSES))
    ap.add_argument("--range-minutes", type=int, default=15)
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--costs", default="india_intraday", choices=list(COST_PRESETS))
    a = ap.parse_args()
    cost_rt = 2 * COST_PRESETS[a.costs].per_side
    range_bars = max(1, a.range_minutes // 5)
    data = load_intraday(UNIVERSES[a.universe][:12], days=55, interval="5m")
    trades = []
    for sym, df in data.items():
        df = df.copy(); df.index = pd.to_datetime(df.index)
        for d, day in df.groupby(df.index.date):
            r = orb_day(day, range_bars, a.rr, cost_rt)
            if r is not None:
                trades.append({"date": pd.Timestamp(d), "symbol": sym, "ret": r})
    t = pd.DataFrame(trades)
    if t.empty:
        print("no trades"); return
    daily = t.groupby("date")["ret"].mean()  # equal capital across that day's trades
    print(f"trades: {len(t)}  win rate: {(t.ret>0).mean():.1%}  avg trade: {t.ret.mean()*100:.3f}%  "
          f"median: {t.ret.median()*100:.3f}%  profit factor: {t.ret[t.ret>0].sum()/max(1e-9,-t.ret[t.ret<0].sum()):.2f}")
    print(f"days: {len(daily)}  avg daily (1 slot/day): {daily.mean()*100:.3f}%  best day: {daily.max()*100:.2f}%  worst day: {daily.min()*100:.2f}%")
    print("Reminder: your target was +10%/day. Best day above is what a real intraday edge looks like.")


if __name__ == "__main__":
    main()
