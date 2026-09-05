#!/usr/bin/env python
"""Walk-forward + parameter-plateau report for every strategy x universe -> docs/WALK_FORWARD.md

  python scripts/walk_forward_report.py            # all
  python scripts/walk_forward_report.py --only trend --universe india_etf
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from alpha_forge.backtest import COST_PRESETS
from alpha_forge.backtest.metrics import performance_summary
from alpha_forge.backtest.walk_forward import plateau, plateau_stats, run_grid, walk_forward
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.strategies import REGISTRY

START = "2015-01-01"
UNIVERSE_COSTS = {"nifty50": ("india_delivery", "india_benchmark"), "india_etf": ("india_delivery", "india_benchmark"), "us_core": ("us_alpaca", "us_benchmark")}

GRIDS = {
    "momentum": dict(grid={"lookback": [126, 189, 252], "skip": [0, 21], "top_n": [5, 8, 12], "regime_filter": [True, False]},
                     heat=("lookback", "top_n")),
    "trend": dict(grid={"fast": [20, 50, 100], "slow": [100, 150, 200, 250], "max_weight": [0.2, 0.25, 0.34]},
                  valid=lambda p: p["fast"] < p["slow"], heat=("fast", "slow")),
    "meanrev": dict(grid={"oversold": [5, 10, 15], "exit": [60, 70, 80], "max_hold": [3, 5, 7]}, heat=("oversold", "max_hold")),
}


def heatmap(pl: pd.DataFrame, x: str, y: str, title: str, path: Path):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    piv = pl.pivot_table(index=y, columns=x, values="sharpe", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(piv.values, cmap="RdYlGn", aspect="auto", vmin=min(0, np.nanmin(piv.values)), vmax=np.nanmax(piv.values))
    ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns); ax.set_xlabel(x)
    ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index); ax.set_ylabel(y)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title(title, fontsize=10); fig.colorbar(im, ax=ax, label="Sharpe (mean over other params)")
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


def oos_chart(curves: dict, bench: pd.Series, title: str, path: Path):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, r in curves.items():
        (1 + r).cumprod().plot(ax=ax, label=f"{name} (walk-forward OOS)")
    b = bench.pct_change().reindex(next(iter(curves.values())).index).fillna(0)
    (1 + b).cumprod().plot(ax=ax, label="benchmark", color="black", alpha=.6)
    ax.set_yscale("log"); ax.grid(alpha=.3); ax.legend(); ax.set_title(title)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(GRIDS))
    ap.add_argument("--universe", choices=list(UNIVERSE_COSTS))
    ap.add_argument("--train-years", type=int, default=3)
    ap.add_argument("--test-years", type=int, default=1)
    a = ap.parse_args()

    Path("reports").mkdir(exist_ok=True); Path("docs/img").mkdir(parents=True, exist_ok=True)
    md = [f"# Walk-forward & parameter-plateau report ({date.today()})", "",
          f"Train {a.train_years}y / test {a.test_years}y rolling, parameters chosen on train Sharpe only, scored on the following test year. "
          "Costs on. Data from {START}. Survivorship bias applies to the stock universes (today's members).".replace("{START}", START), ""]
    summary_rows = []
    for uni, (cost_name, bench_key) in UNIVERSE_COSTS.items():
        if a.universe and uni != a.universe:
            continue
        prices = load_prices(UNIVERSES[uni], start=START)
        bench = close_matrix(load_prices(UNIVERSES[bench_key], start=START)).iloc[:, 0]
        bench_r = bench.pct_change().dropna()
        cost = COST_PRESETS[cost_name]
        md += [f"## Universe `{uni}` (costs: {cost_name})", ""]
        curves = {}
        for sname, spec in GRIDS.items():
            if a.only and sname != a.only:
                continue
            print(f"== {uni} / {sname}", flush=True)
            runs = run_grid(REGISTRY[sname], prices, spec["grid"], cost, valid=spec.get("valid", lambda p: True))
            wf, oos = walk_forward(runs, a.train_years, a.test_years)
            pl = plateau(runs)
            bench_sharpe = performance_summary(bench_r.reindex(runs.returns.index).fillna(0)).get("sharpe", np.nan)
            st = plateau_stats(pl, benchmark_score=bench_sharpe)
            oos_s = performance_summary(oos)
            bench_oos = performance_summary(bench_r.reindex(oos.index).fillna(0))
            curves[sname] = oos
            hp = Path("docs/img") / f"plateau_{sname}_{uni}.png"
            heatmap(pl, *spec["heat"], f"{sname} on {uni}: Sharpe plateau", hp)
            pl.to_csv(Path("reports") / f"plateau_{sname}_{uni}.csv", index=False)
            summary_rows.append({"universe": uni, "strategy": sname, "OOS CAGR %": oos_s.get("cagr_pct"), "OOS Sharpe": oos_s.get("sharpe"),
                                 "OOS MaxDD %": oos_s.get("max_drawdown_pct"), "Bench CAGR % (same period)": bench_oos.get("cagr_pct"),
                                 "Bench Sharpe": bench_oos.get("sharpe"), "Bench MaxDD %": bench_oos.get("max_drawdown_pct"),
                                 "grid median Sharpe": st["median_sharpe"], "% grid > bench": st["pct_grid_above_benchmark"],
                                 "half/half rank corr": st["half_to_half_rank_corr"], "default rank": f"{st[f'default_rank_of_{len(pl)}']}/{len(pl)}"})
            wf_show = wf.copy(); wf_show["chosen"] = wf_show["chosen"].astype(str)
            md += [f"### {sname}", "",
                   f"Walk-forward OOS ({oos.index[0].date()} to {oos.index[-1].date()}): CAGR **{oos_s.get('cagr_pct')}%**, Sharpe **{oos_s.get('sharpe')}**, "
                   f"MaxDD **{oos_s.get('max_drawdown_pct')}%**  |  benchmark same period: CAGR {bench_oos.get('cagr_pct')}%, Sharpe {bench_oos.get('sharpe')}, MaxDD {bench_oos.get('max_drawdown_pct')}%", "",
                   wf_show.to_markdown(index=False), "",
                   "Plateau: " + ", ".join(f"{k}={v}" for k, v in st.items()), "",
                   f"![plateau]({hp.relative_to('docs').as_posix()})", "",
                   "Top 5 parameter sets (full period):", "", pl.head(5).round(2).to_markdown(index=False), ""]
        if curves:
            cp = Path("docs/img") / f"walk_forward_oos_{uni}.png"
            oos_chart(curves, bench, f"Walk-forward out-of-sample equity, {uni}", cp)
            md += [f"![oos]({cp.relative_to('docs').as_posix()})", ""]
    md.insert(3, pd.DataFrame(summary_rows).to_markdown(index=False))
    md.insert(4, "")
    md += ["## How to read this", "",
           "* **OOS Sharpe** is the only number that matters. It was never optimised.",
           "* **% grid > bench** and **grid median Sharpe**: how much of the parameter space beats the benchmark. Broad hill = robust; single spike = curve-fit.",
           "* **half/half rank corr**: Spearman correlation of parameter rankings between the first and second half of history. Near 0 means parameter choice is noise.",
           "* **default rank**: where our shipped default parameters sit in the grid. If it's #1 out of 36, be suspicious of how they were chosen."]
    Path("docs/WALK_FORWARD.md").write_text("\n".join(md))
    print(pd.DataFrame(summary_rows).to_string())
    print("wrote docs/WALK_FORWARD.md")


if __name__ == "__main__":
    main()
