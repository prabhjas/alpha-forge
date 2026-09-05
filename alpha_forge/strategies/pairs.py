"""Statistical-arbitrage pairs within sectors.

Formation (every `reform` months, on the trailing `formation` days): for every pair
inside a sector, regress log(A) on log(B) to get the hedge ratio, form the spread,
fit an AR(1) to get the mean-reversion half-life, and keep pairs with correlation
> `min_corr` and half-life inside [min_hl, max_hl]. Rank by half-life, take `n_pairs`.

Trading: z-score of the spread over `z_window` days. Enter when |z| > `entry`,
exit when |z| < `exit` or after `max_hold` days, hard stop at |z| > `stop`.

Two modes:
  * neutral   : long the cheap leg, short the rich leg (dollar-neutral per pair).
                Needs shorting: stock futures in India, a margin account on Alpaca.
  * long_only : hold ONLY the cheap leg. No short. Carries market beta, but it is
                the version a Rs 50k cash account can actually run today.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

from alpha_forge.data.loader import ROOT, close_matrix
from .base import Strategy


def _half_life(spread: np.ndarray) -> float:
    s = spread - spread.mean()
    ds, lag = np.diff(s), s[:-1]
    if lag.std() == 0:
        return np.inf
    phi = np.dot(lag, ds) / np.dot(lag, lag)
    if phi >= 0:
        return np.inf
    return float(-np.log(2) / np.log(1 + phi))


def form_pairs(logp: pd.DataFrame, sectors: Dict[str, List[str]], min_corr: float, min_hl: float, max_hl: float, n_pairs: int) -> List[Tuple[str, str, float]]:
    cands = []
    for _, members in sectors.items():
        cols = [m for m in members if m in logp.columns]
        for a, b in combinations(cols, 2):
            x, y = logp[a].values, logp[b].values
            if np.isnan(x).any() or np.isnan(y).any():
                continue
            corr = np.corrcoef(x, y)[0, 1]
            if corr < min_corr:
                continue
            beta = np.polyfit(y, x, 1)[0]
            if beta <= 0:
                continue
            hl = _half_life(x - beta * y)
            if min_hl <= hl <= max_hl:
                cands.append((a, b, beta, hl))
    cands.sort(key=lambda t: t[3])
    return [(a, b, beta) for a, b, beta, _ in cands[:n_pairs]]


class PairsTrading(Strategy):
    name = "pairs"

    @classmethod
    def default_params(cls):
        return {"mode": "long_only", "formation": 252, "reform": 6, "z_window": 60, "entry": 2.0, "exit": 0.5,
                "stop": 4.0, "max_hold": 40, "n_pairs": 8, "min_corr": 0.7, "min_hl": 5, "max_hl": 60, "gross": 1.0}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        with open(ROOT / "config" / "sectors.yaml") as fh:
            sectors = yaml.safe_load(fh)
        closes = close_matrix(prices)
        logp = np.log(closes)
        idx = closes.index
        weights = pd.DataFrame(0.0, index=idx, columns=closes.columns)
        months = idx.to_period("M")
        month_starts = [i for i in range(1, len(idx)) if months[i] != months[i - 1]]
        pairs: List[Tuple[str, str, float]] = []
        open_pos: Dict[Tuple[str, str], Tuple[int, int]] = {}   # pair -> (direction, age)
        next_reform = 0
        per_pair = p["gross"] / p["n_pairs"]
        for i in range(p["formation"], len(idx)):
            if i in month_starts:
                next_reform -= 1
                if next_reform <= 0:
                    pairs = form_pairs(logp.iloc[i - p["formation"]:i], sectors, p["min_corr"], p["min_hl"], p["max_hl"], p["n_pairs"])
                    next_reform = p["reform"]
                    open_pos = {k: v for k, v in open_pos.items() if k in {(a, b) for a, b, _ in pairs}}
            row = pd.Series(0.0, index=closes.columns)
            for a, b, beta in pairs:
                s = (logp[a].iloc[i - p["z_window"] + 1:i + 1] - beta * logp[b].iloc[i - p["z_window"] + 1:i + 1]).values
                if np.isnan(s).any() or s.std() == 0:
                    continue
                z = (s[-1] - s.mean()) / s.std()
                key = (a, b)
                if key in open_pos:
                    d, age = open_pos[key]
                    if abs(z) < p["exit"] or abs(z) > p["stop"] or age >= p["max_hold"] or np.sign(z) == d:
                        del open_pos[key]
                    else:
                        open_pos[key] = (d, age + 1)
                elif z > p["entry"]:
                    open_pos[key] = (1, 0)     # A rich vs B: short A / long B
                elif z < -p["entry"]:
                    open_pos[key] = (-1, 0)    # A cheap vs B: long A / short B
                if key in open_pos:
                    d = open_pos[key][0]
                    if p["mode"] == "neutral":
                        row[a] += -d * per_pair / 2
                        row[b] += d * per_pair / 2
                    else:  # long_only: hold the cheap leg only
                        row[b if d == 1 else a] += per_pair
            weights.iloc[i] = row.values
        return weights
