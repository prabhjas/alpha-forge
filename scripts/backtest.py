#!/usr/bin/env python
"""Backtest one strategy on one universe.

  python scripts/backtest.py --strategy momentum --universe nifty50 --costs india_delivery
  python scripts/backtest.py --strategy trend --universe us_core --costs us_alpaca --param max_weight=0.2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rich.console import Console
from rich.table import Table

from alpha_forge.backtest import Backtester, COST_PRESETS
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.strategies import REGISTRY

console = Console()


def parse_params(items):
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        for cast in (int, float):
            try:
                v = cast(v); break
            except ValueError:
                continue
        if v in ("true", "false"):
            v = v == "true"
        out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True, choices=list(REGISTRY))
    ap.add_argument("--universe", required=True, choices=list(UNIVERSES))
    ap.add_argument("--costs", default="india_delivery", choices=list(COST_PRESETS))
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--capital", type=float, default=100_000)
    ap.add_argument("--param", action="append", help="key=value, repeatable")
    ap.add_argument("--save", action="store_true", help="save equity curve CSV + PNG to reports/")
    a = ap.parse_args()

    prices = load_prices(UNIVERSES[a.universe], start=a.start, end=a.end)
    bench_key = "india_benchmark" if a.universe.startswith(("nifty", "india")) else "us_benchmark"
    bench = load_prices(UNIVERSES[bench_key], start=a.start, end=a.end)
    bench_close = close_matrix(bench).iloc[:, 0]

    strat = REGISTRY[a.strategy](**parse_params(a.param))
    bt = Backtester(COST_PRESETS[a.costs], initial_capital=a.capital)
    res = bt.run(strat, prices, benchmark=bench_close)

    t = Table(title=f"{strat.describe()}  |  {a.universe}  |  costs={a.costs}")
    t.add_column("metric"); t.add_column("value", justify="right")
    for k, v in res.summary.items():
        t.add_row(k, str(v))
    console.print(t)
    console.print(f"Final equity from {a.capital:,.0f}: [bold]{res.equity.iloc[-1]:,.0f}[/bold]  ({res.equity.index[0].date()} -> {res.equity.index[-1].date()})")

    if a.save:
        out = Path("reports"); out.mkdir(exist_ok=True)
        stem = f"{a.strategy}_{a.universe}_{a.costs}"
        res.to_frame().to_csv(out / f"{stem}.csv")
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 5))
            (res.equity / a.capital).plot(ax=ax, label=strat.describe())
            (1 + res.benchmark_returns).cumprod().plot(ax=ax, label="benchmark")
            ax.set_yscale("log"); ax.legend(); ax.set_title(stem); ax.grid(alpha=.3)
            fig.tight_layout(); fig.savefig(out / f"{stem}.png", dpi=120)
            console.print(f"saved reports/{stem}.csv and .png")
        except Exception as e:  # matplotlib optional
            console.print(f"plot skipped: {e}")


if __name__ == "__main__":
    main()
