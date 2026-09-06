"""Robustness statistics: put error bars on every headline number.

A single Sharpe of 1.2 means little without knowing its uncertainty. These tools
answer the questions that separate a serious system from a backtest screenshot:
  * How likely is a losing year?
  * What is the 5th-percentile (bad-luck) max drawdown, not just the one we saw?
  * Is the Sharpe statistically distinguishable from zero, or could it be noise?

Methods:
  * Stationary block bootstrap of daily returns (preserves autocorrelation) ->
    distribution of CAGR, Sharpe, MaxDD.
  * Monte Carlo of annual outcomes from the bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from .metrics import max_drawdown, performance_summary


def _block_bootstrap(returns: np.ndarray, n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty(n)
    i = 0
    while i < n:
        start = rng.integers(0, len(returns))
        length = min(block, n - i)
        for k in range(length):
            out[i + k] = returns[(start + k) % len(returns)]
        i += length
    return out


@dataclass
class Robustness:
    n_boot: int
    summary: Dict[str, float]

    def to_markdown(self) -> str:
        s = self.summary
        return (
            f"| statistic | value |\n|---|---|\n"
            f"| observed CAGR | {s['obs_cagr']:.1f}% |\n"
            f"| CAGR 90% CI | {s['cagr_p5']:.1f}% to {s['cagr_p95']:.1f}% |\n"
            f"| observed Sharpe | {s['obs_sharpe']:.2f} |\n"
            f"| Sharpe 90% CI | {s['sharpe_p5']:.2f} to {s['sharpe_p95']:.2f} |\n"
            f"| P(Sharpe > 0) | {s['prob_sharpe_pos']:.0f}% |\n"
            f"| observed MaxDD | {s['obs_maxdd']:.1f}% |\n"
            f"| MaxDD 95th-pct (bad luck) | {s['maxdd_p95']:.1f}% |\n"
            f"| P(a given year is negative) | {s['prob_neg_year']:.0f}% |\n"
            f"| expected worst year in 5 | {s['worst_of_5_yr']:.1f}% |\n"
        )


def analyse(daily_returns: pd.Series, n_boot: int = 2000, block: int = 20, seed: int = 7) -> Robustness:
    r = daily_returns.dropna().values
    rng = np.random.default_rng(seed)
    years = len(r) / 252
    obs = performance_summary(daily_returns)
    cagrs, sharpes, maxdds, ann = [], [], [], []
    for _ in range(n_boot):
        b = _block_bootstrap(r, len(r), block, rng)
        eq = np.cumprod(1 + b)
        cagrs.append(eq[-1] ** (1 / years) - 1)
        vol = b.std() * np.sqrt(252)
        sharpes.append((b.mean() * 252) / vol if vol > 0 else 0)
        maxdds.append(max_drawdown(pd.Series(eq)))
        # sample one simulated year
        yr = _block_bootstrap(r, 252, block, rng)
        ann.append(np.prod(1 + yr) - 1)
    cagrs, sharpes, maxdds, ann = map(np.array, (cagrs, sharpes, maxdds, ann))
    worst_of_5 = np.mean([np.min(rng.choice(ann, 5)) for _ in range(1000)])
    summary = {
        "obs_cagr": obs["cagr_pct"], "cagr_p5": np.percentile(cagrs, 5) * 100, "cagr_p95": np.percentile(cagrs, 95) * 100,
        "obs_sharpe": obs["sharpe"], "sharpe_p5": np.percentile(sharpes, 5), "sharpe_p95": np.percentile(sharpes, 95),
        "prob_sharpe_pos": (sharpes > 0).mean() * 100,
        "obs_maxdd": obs["max_drawdown_pct"], "maxdd_p95": np.percentile(maxdds, 5) * 100,  # 5th pct of a negative = worst
        "prob_neg_year": (ann < 0).mean() * 100, "worst_of_5_yr": worst_of_5 * 100,
    }
    return Robustness(n_boot, summary)
