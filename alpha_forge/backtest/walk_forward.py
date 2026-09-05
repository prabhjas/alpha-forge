"""Walk-forward validation and parameter-plateau analysis.

Every strategy here is causal (rolling windows only), so a strategy's daily
return series computed over the full history is identical to what it would
have produced live. That lets us backtest each parameter set ONCE and then
slice the same series into train/test folds, instead of re-running per fold.

Walk-forward: for each fold, pick the parameter set with the best train-window
score, then record what THAT set did in the following test window. Stitching
the test windows together gives a fully out-of-sample equity curve.

Plateau: the score of every parameter set over the full period plus a
first-half vs second-half rank correlation. A real edge is a broad hill;
curve-fitting is a lone spike.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .costs import CostModel
from .engine import Backtester
from .metrics import performance_summary


def expand_grid(grid: Dict[str, Iterable]) -> List[Dict]:
    keys = list(grid)
    return [dict(zip(keys, vals)) for vals in itertools.product(*[list(grid[k]) for k in keys])]


def _score(r: pd.Series, by: str) -> float:
    s = performance_summary(r)
    return float(s.get(by, np.nan)) if s else np.nan


@dataclass
class GridRuns:
    params: List[Dict]
    returns: pd.DataFrame       # columns = param index, rows = dates, values = net daily return
    default_idx: Optional[int]


def run_grid(strategy_cls, prices, grid: Dict[str, Iterable], cost: CostModel,
             valid=lambda p: True, verbose: bool = True) -> GridRuns:
    bt = Backtester(cost)
    params = [p for p in expand_grid(grid) if valid(p)]
    cols = {}
    defaults = strategy_cls.default_params()
    default_idx = None
    for i, p in enumerate(params):
        res = bt.run(strategy_cls(**p), prices)
        cols[i] = res.daily_returns
        if all(defaults.get(k) == v for k, v in p.items()):
            default_idx = i
        if verbose and i % 10 == 0:
            print(f"    grid {i+1}/{len(params)}", flush=True)
    return GridRuns(params, pd.DataFrame(cols).fillna(0.0), default_idx)


def folds(index: pd.DatetimeIndex, train_years: int, test_years: int) -> List[Tuple]:
    years = sorted(set(index.year))
    out = []
    for i in range(0, len(years) - train_years, test_years):
        tr = (pd.Timestamp(f"{years[i]}-01-01"), pd.Timestamp(f"{years[i+train_years-1]}-12-31"))
        te_y0 = years[i + train_years]
        te_y1 = min(years[-1], te_y0 + test_years - 1)
        te = (pd.Timestamp(f"{te_y0}-01-01"), pd.Timestamp(f"{te_y1}-12-31"))
        out.append((tr, te))
    return out


def walk_forward(runs: GridRuns, train_years: int = 3, test_years: int = 1, select_by: str = "sharpe"):
    R = runs.returns
    rows = []
    oos = []
    for (tr0, tr1), (te0, te1) in folds(R.index, train_years, test_years):
        train = R.loc[tr0:tr1]
        test = R.loc[te0:te1]
        if len(train) < 200 or len(test) < 40:
            continue
        scores = train.apply(lambda c: _score(c, select_by))
        best = int(scores.idxmax())
        te_s = performance_summary(test[best])
        rows.append({
            "train": f"{tr0.year}-{tr1.year}", "test": f"{te0.year}" if te0.year == te1.year else f"{te0.year}-{te1.year}",
            "chosen": runs.params[best], "train_sharpe": round(float(scores.max()), 2),
            "test_sharpe": te_s.get("sharpe"), "test_cagr_pct": te_s.get("cagr_pct"), "test_maxdd_pct": te_s.get("max_drawdown_pct"),
            "default_test_sharpe": performance_summary(test[runs.default_idx]).get("sharpe") if runs.default_idx is not None else None,
        })
        oos.append(test[best])
    oos_series = pd.concat(oos).sort_index() if oos else pd.Series(dtype=float)
    return pd.DataFrame(rows), oos_series


def plateau(runs: GridRuns, by: str = "sharpe") -> pd.DataFrame:
    R = runs.returns
    mid = R.index[len(R) // 2]
    full = R.apply(lambda c: _score(c, by))
    h1 = R.loc[:mid].apply(lambda c: _score(c, by))
    h2 = R.loc[mid:].apply(lambda c: _score(c, by))
    df = pd.DataFrame(runs.params)
    df[by] = full.values
    df[f"{by}_h1"] = h1.values
    df[f"{by}_h2"] = h2.values
    df["is_default"] = [i == runs.default_idx for i in range(len(runs.params))]
    return df.sort_values(by, ascending=False).reset_index(drop=True)


def plateau_stats(pl: pd.DataFrame, by: str = "sharpe", benchmark_score: float = np.nan) -> Dict[str, float]:
    rho = float(pl[f"{by}_h1"].rank().corr(pl[f"{by}_h2"].rank()))  # Spearman without scipy
    return {
        f"median_{by}": round(float(pl[by].median()), 2),
        f"best_{by}": round(float(pl[by].max()), 2),
        f"pct_grid_above_benchmark": round(float((pl[by] > benchmark_score).mean() * 100), 1) if not np.isnan(benchmark_score) else None,
        "half_to_half_rank_corr": round(rho, 2),
        f"default_{by}": round(float(pl.loc[pl.is_default, by].iloc[0]), 2) if pl.is_default.any() else None,
        f"default_rank_of_{len(pl)}": int(pl.index[pl.is_default][0] + 1) if pl.is_default.any() else None,
    }
