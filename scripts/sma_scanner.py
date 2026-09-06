#!/usr/bin/env python
"""Nifty SMA crossover scanner — READ-ONLY signal tool.

This is the tool from the tutorial screenshots: scan a universe, compute two
SMAs, flag bullish (fast crosses above slow) and bearish crossovers, rank by
how recently the crossover happened. It PLACES NO ORDERS. It prints a watchlist.

Runs Monday with zero broker keys (uses Yahoo data via our loader). When you
later add a Kite paid plan, swap the loader for kite.historical_data() and the
rest is unchanged.

  python scripts/sma_scanner.py --universe nifty50 --fast 6 --slow 30
  python scripts/sma_scanner.py --universe india_etf --fast 20 --slow 50 --max-age 5
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices

console = Console()


def scan(closes: pd.DataFrame, fast: int, slow: int) -> pd.DataFrame:
    rows = []
    for sym in closes.columns:
        px = closes[sym].dropna()
        if len(px) < slow + 5:
            continue
        sf, ss = px.rolling(fast).mean(), px.rolling(slow).mean()
        diff = (sf - ss).dropna()
        sign = np.sign(diff)
        crosses = sign.diff().fillna(0)
        up = crosses[crosses > 0].index
        dn = crosses[crosses < 0].index
        last_up = up[-1] if len(up) else None
        last_dn = dn[-1] if len(dn) else None
        if last_up is None and last_dn is None:
            continue
        if last_up is not None and (last_dn is None or last_up > last_dn):
            signal, when = "BULLISH", last_up
        else:
            signal, when = "BEARISH", last_dn
        age = int((px.index[-1] - when).days)
        last = float(px.iloc[-1])
        sep = float((sf.iloc[-1] - ss.iloc[-1]) / ss.iloc[-1] * 100)  # % separation, a whipsaw filter
        above200 = last > px.rolling(200).mean().iloc[-1] if len(px) >= 200 else np.nan
        rows.append({"symbol": sym, "signal": signal, "age_days": age, "cross_date": when.date(),
                     "last": round(last, 2), "sma_sep_%": round(sep, 2),
                     "above_200dma": bool(above200) if not pd.isna(above200) else None})
    df = pd.DataFrame(rows)
    return df.sort_values(["age_days", "signal"]).reset_index(drop=True) if len(df) else df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="nifty50", choices=list(UNIVERSES))
    ap.add_argument("--fast", type=int, default=6)
    ap.add_argument("--slow", type=int, default=30)
    ap.add_argument("--max-age", type=int, default=10, help="only show crossovers within N days")
    ap.add_argument("--min-sep", type=float, default=0.0, help="min %% SMA separation to filter whipsaws")
    a = ap.parse_args()

    prices = load_prices(UNIVERSES[a.universe], start="2023-01-01", use_cache=False)
    closes = close_matrix(prices)
    df = scan(closes, a.fast, a.slow)
    if len(df):
        df = df[(df.age_days <= a.max_age) & (df["sma_sep_%"].abs() >= a.min_sep)]

    t = Table(title=f"SMA {a.fast}/{a.slow} crossovers — {a.universe} — as of {closes.index[-1].date()}  (READ-ONLY, no orders)")
    for c in ["symbol", "signal", "age_days", "cross_date", "last", "sma_sep_%", "above_200dma"]:
        t.add_column(c, justify="right" if c in ("age_days", "last", "sma_sep_%") else "left")
    for _, r in df.iterrows():
        style = "green" if r.signal == "BULLISH" else "red"
        t.add_row(r.symbol, f"[{style}]{r.signal}[/{style}]", str(r.age_days), str(r.cross_date),
                  str(r["last"]), str(r["sma_sep_%"]), str(r.above_200dma))
    console.print(t)
    console.print(f"\n[bold]{len(df)}[/bold] fresh signals. Bullish crossovers that are ALSO above the 200-day average "
                  "are the ones our trend engine would actually consider. The rest are noise or counter-trend.")
    console.print("[dim]This tool screens. It does not decide or trade. Decisions go through the backtested engine + risk manager.[/dim]")
    Path("data_cache").mkdir(exist_ok=True)
    df.to_csv(f"data_cache/scan_{a.universe}_{date.today()}.csv", index=False)


if __name__ == "__main__":
    main()
