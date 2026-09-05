"""Vectorised portfolio backtester.

A Strategy returns a target-weight matrix W (index=date, columns=ticker),
where W.loc[t] is the weight held FROM the close of day t until the close of
day t+1 (signals are computed on data up to t, so there is no look-ahead).

Portfolio return on day t+1 = sum(W[t] * r[t+1]) - turnover[t] * cost_per_side
where turnover[t] = sum(|W[t] - W[t-1]|).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .costs import CostModel, COST_PRESETS
from .metrics import performance_summary


@dataclass
class BacktestResult:
    name: str
    daily_returns: pd.Series
    equity: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    cost_drag: pd.Series
    benchmark_returns: Optional[pd.Series] = None
    summary: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.summary = performance_summary(self.daily_returns)
        self.summary["avg_annual_turnover"] = round(float(self.turnover.sum() / max(self.summary.get("years", 1), 1e-9)), 1)
        self.summary["total_cost_drag_pct"] = round(float(self.cost_drag.sum() * 100), 2)
        if self.benchmark_returns is not None:
            b = performance_summary(self.benchmark_returns.reindex(self.daily_returns.index).fillna(0))
            self.summary["benchmark_cagr_pct"] = b.get("cagr_pct")
            self.summary["benchmark_max_dd_pct"] = b.get("max_drawdown_pct")
            self.summary["benchmark_sharpe"] = b.get("sharpe")

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"equity": self.equity, "daily_return": self.daily_returns, "turnover": self.turnover})


class Backtester:
    def __init__(self, cost_model: CostModel = COST_PRESETS["india_delivery"], initial_capital: float = 100_000):
        self.cost = cost_model
        self.initial_capital = initial_capital

    def run(self, strategy, prices: Dict[str, pd.DataFrame], benchmark: Optional[pd.Series] = None) -> BacktestResult:
        from alpha_forge.data.loader import close_matrix

        closes = close_matrix(prices)
        weights = strategy.generate_weights(prices).reindex(closes.index).fillna(0.0)
        weights = weights.reindex(columns=closes.columns).fillna(0.0)
        # Guard: never exceed 100% gross exposure (no leverage in v1).
        gross = weights.abs().sum(axis=1)
        weights = weights.div(gross.where(gross > 1.0, 1.0), axis=0)

        asset_returns = closes.pct_change().fillna(0.0)
        # weights at t earn returns at t+1
        strat_gross = (weights.shift(1).fillna(0.0) * asset_returns).sum(axis=1)
        turnover = weights.diff().abs().sum(axis=1)
        if len(turnover):
            turnover.iloc[0] = weights.abs().sum(axis=1).iloc[0]  # initial entry is a trade too
        cost_drag = turnover.shift(1).fillna(0.0) * self.cost.per_side
        net = strat_gross - cost_drag
        # drop warm-up period where strategy held nothing yet
        first = weights.abs().sum(axis=1).ne(0).idxmax()
        net = net.loc[first:]
        equity = self.initial_capital * (1 + net).cumprod()
        bench = None
        if benchmark is not None:
            bench = benchmark.pct_change().reindex(net.index).fillna(0.0)
        return BacktestResult(
            name=getattr(strategy, "name", strategy.__class__.__name__),
            daily_returns=net,
            equity=equity,
            weights=weights.loc[first:],
            turnover=turnover.loc[first:],
            cost_drag=cost_drag.loc[first:],
            benchmark_returns=bench,
        )


def walk_forward_splits(index: pd.DatetimeIndex, train_years: int = 3, test_years: int = 1):
    """Yield (train_start, train_end, test_start, test_end) rolling windows."""
    years = sorted(set(index.year))
    for i in range(0, len(years) - train_years):
        tr_start = pd.Timestamp(f"{years[i]}-01-01")
        tr_end = pd.Timestamp(f"{years[i + train_years - 1]}-12-31")
        te_start = pd.Timestamp(f"{years[i + train_years]}-01-01")
        te_end = pd.Timestamp(f"{min(years[-1], years[i + train_years] + test_years - 1)}-12-31")
        yield tr_start, tr_end, te_start, te_end
