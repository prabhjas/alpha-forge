#!/usr/bin/env python
"""Run every strategy x universe x cost preset and write docs/RESULTS.md.
This is the honest scoreboard. Costs ON. Benchmark shown next to each."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from alpha_forge.backtest import Backtester, COST_PRESETS
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.strategies import REGISTRY

START = "2015-01-01"
GRID = [
    ("nifty50", "india_delivery", "india_benchmark"),
    ("india_etf", "india_delivery", "india_benchmark"),
    ("us_core", "us_alpaca", "us_benchmark"),
]

rows = []
for universe, costs, bench_key in GRID:
    prices = load_prices(UNIVERSES[universe], start=START)
    bench = close_matrix(load_prices(UNIVERSES[bench_key], start=START)).iloc[:, 0]
    for sname, cls in REGISTRY.items():
        for cost_name in (costs, "zero"):
            res = Backtester(COST_PRESETS[cost_name]).run(cls(), prices, benchmark=bench)
            s = res.summary
            rows.append({
                "universe": universe, "strategy": sname, "costs": cost_name,
                "CAGR %": s["cagr_pct"], "Sharpe": s["sharpe"], "MaxDD %": s["max_drawdown_pct"],
                "Calmar": s["calmar"], "Turnover/yr": s["avg_annual_turnover"], "Cost drag % (total)": s["total_cost_drag_pct"],
                "Bench CAGR %": s["benchmark_cagr_pct"], "Bench MaxDD %": s["benchmark_max_dd_pct"],
                "Best mo %": s["best_month_pct"], "Worst mo %": s["worst_month_pct"], "Years": s["years"],
            })
            print(f"{universe:10s} {sname:9s} {cost_name:15s} CAGR {s['cagr_pct']:6.2f}%  Sharpe {s['sharpe']:5.2f}  MaxDD {s['max_drawdown_pct']:6.2f}%")

df = pd.DataFrame(rows)
md = [f"# Backtest scoreboard (generated {date.today()})", "",
      f"Period start {START}. Daily bars from Yahoo Finance, adjusted closes. Long-only, no leverage.",
      "Costs charged per side (see alpha_forge/backtest/costs.py). 'zero' rows exist only to show cost impact.", "",
      df.to_markdown(index=False), "",
      "## How to read this", "",
      "* Beat the benchmark CAGR **and** have a shallower MaxDD, or the strategy has no reason to exist.",
      "* Turnover/yr x cost per side = the tax you pay for activity. High-turnover ideas die here.",
      "* Best month tells you what a lucky month looks like. Nobody's best month is +300% (i.e. 10%/day).",
      "* These are in-sample with default parameters. Walk-forward validation is Phase 1 work before any live money.",
      "* **Survivorship bias**: universes are today's index members, i.e. the companies that won. That inflates every",
      "  number here, buy-and-hold most of all. Phase 1 replaces this with point-in-time constituents from the exchange."]
Path("docs").mkdir(exist_ok=True)
Path("docs/RESULTS.md").write_text("\n".join(md))
print("\nwrote docs/RESULTS.md")
