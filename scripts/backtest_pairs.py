#!/usr/bin/env python
"""Pairs strategy report -> docs/PAIRS.md. Both modes, costs on, plus a walk-forward on entry/exit thresholds."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from alpha_forge.backtest import Backtester, COST_PRESETS
from alpha_forge.backtest.metrics import performance_summary
from alpha_forge.backtest.walk_forward import plateau, plateau_stats, run_grid, walk_forward
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.strategies import PairsTrading

START = "2015-01-01"
prices = load_prices(UNIVERSES["nifty50"], start=START)
bench = close_matrix(load_prices(UNIVERSES["india_benchmark"], start=START)).iloc[:, 0]
cost = COST_PRESETS["india_delivery"]
bt = Backtester(cost)

rows, curves = [], {}
for mode in ("neutral", "long_only"):
    for cost_name in ("india_delivery", "zero"):
        res = Backtester(COST_PRESETS[cost_name]).run(PairsTrading(mode=mode), prices, benchmark=bench)
        s = res.summary
        rows.append({"mode": mode, "costs": cost_name, "CAGR %": s["cagr_pct"], "Sharpe": s["sharpe"], "MaxDD %": s["max_drawdown_pct"],
                     "ann vol %": s["ann_vol_pct"], "turnover/yr": s["avg_annual_turnover"], "cost drag % total": s["total_cost_drag_pct"],
                     "bench CAGR %": s["benchmark_cagr_pct"], "bench MaxDD %": s["benchmark_max_dd_pct"]})
        if cost_name == "india_delivery":
            curves[mode] = res
        print(f"{mode:10s} {cost_name:15s} CAGR {s['cagr_pct']:7.2f}  Sharpe {s['sharpe']:5.2f}  MaxDD {s['max_drawdown_pct']:7.2f}  turnover/yr {s['avg_annual_turnover']}", flush=True)
full = pd.DataFrame(rows)

print("walk-forward on thresholds (long_only)...", flush=True)
grid = {"mode": ["long_only"], "entry": [1.5, 2.0, 2.5], "exit": [0.25, 0.5, 1.0], "max_hold": [20, 40]}
runs = run_grid(PairsTrading, prices, grid, cost, verbose=False)
wf, oos = walk_forward(runs)
pl = plateau(runs)
bench_sharpe = performance_summary(bench.pct_change().reindex(runs.returns.index).fillna(0))["sharpe"]
st = plateau_stats(pl, benchmark_score=bench_sharpe)
oos_s = performance_summary(oos)
bench_oos = performance_summary(bench.pct_change().reindex(oos.index).fillna(0))

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
Path("docs/img").mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(10, 5))
for mode, res in curves.items():
    (res.equity / res.equity.iloc[0]).plot(ax=ax, label=f"pairs {mode} (costs on)")
(1 + bench.pct_change().reindex(curves["neutral"].equity.index).fillna(0)).cumprod().plot(ax=ax, label="Nifty 50", color="black", alpha=.6)
ax.set_yscale("log"); ax.grid(alpha=.3); ax.legend(); ax.set_title("Sector pairs on Nifty 50")
fig.tight_layout(); fig.savefig("docs/img/pairs_nifty50.png", dpi=120)

wf_show = wf.copy(); wf_show["chosen"] = wf_show["chosen"].astype(str)
md = [f"# Pairs trading on Nifty 50 ({date.today()})", "",
      "Sector-constrained pairs, formation 252d re-run every 6 months, z-score window 60d, enter |z|>2, exit |z|<0.5, stop |z|>4, max hold 40d, 8 pairs. Costs: india_delivery per side on every leg.", "",
      "## Full period, default parameters", "", full.round(2).to_markdown(index=False), "",
      "![pairs](img/pairs_nifty50.png)", "",
      f"## Walk-forward on thresholds (long_only mode), OOS {oos.index[0].date()} to {oos.index[-1].date()}", "",
      f"OOS CAGR **{oos_s['cagr_pct']}%**, Sharpe **{oos_s['sharpe']}**, MaxDD **{oos_s['max_drawdown_pct']}%** | Nifty same period: CAGR {bench_oos['cagr_pct']}%, Sharpe {bench_oos['sharpe']}, MaxDD {bench_oos['max_drawdown_pct']}%", "",
      wf_show.to_markdown(index=False), "", "Plateau: " + ", ".join(f"{k}={v}" for k, v in st.items()), "",
      "## What this means", "",
      "* `neutral` is the true stat-arb book. Its return is what you get **before** the cost of borrowing/shorting, which in India means stock futures (lot size Rs 5-10 lakh each) and in the US a margin account. It cannot be run with Rs 50k. It is here so we know the size of the prize before we ever pay for that infrastructure.",
      "* `long_only` is runnable today. It is a relative-value rotation, not an arbitrage: it carries full market beta.",
      "* Judge both by Sharpe and drawdown vs. the trend book, not by CAGR alone. Turnover and cost drag tell you why stat-arb is a game for people paying 1 bp, not 19."]
Path("docs/PAIRS.md").write_text("\n".join(md))
print("wrote docs/PAIRS.md")
