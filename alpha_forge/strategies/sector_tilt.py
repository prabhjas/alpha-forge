"""Sector-tilt / sector-rotation strategy.

Two-level allocation, rebalanced monthly:
  1. SECTOR SELECTION: score each sector by the median momentum of its stocks;
     keep the top `top_sectors`. Weak sectors get zero (their budget -> cash).
  2. STOCK SELECTION: inside each chosen sector, keep only stocks in an uptrend
     (above 200-DMA), rank by momentum, take the top `top_stocks_per_sector`.
  3. WEIGHTING: stronger sectors get a bigger slice (budget ∝ sector score);
     within a sector, chosen stocks share the slice, capped per name.

This actively rotates toward where the strength is across sectors, instead of
holding the index equally. Long-only, no leverage. Causal: every score uses
only data up to the rebalance date.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
import yaml

from alpha_forge.data.loader import ROOT, close_matrix
from .base import Strategy


class SectorTilt(Strategy):
    name = "sector_tilt"

    @classmethod
    def default_params(cls):
        return {"lookback": 126, "top_sectors": 4, "top_stocks_per_sector": 3,
                "trend_sma": 200, "rebalance": "M", "max_weight": 0.15, "regime_filter": True}

    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params
        with open(ROOT / "config" / "sectors.yaml") as fh:
            sectors = yaml.safe_load(fh)
        closes = close_matrix(prices)
        cols = set(closes.columns)
        sectors = {sec: [s for s in syms if s in cols] for sec, syms in sectors.items()}
        sectors = {k: v for k, v in sectors.items() if len(v) >= 2}

        mom = closes / closes.shift(p["lookback"]) - 1.0
        sma = closes.rolling(p["trend_sma"]).mean()
        uptrend = closes > sma
        index_proxy = closes.mean(axis=1)
        regime_ok = index_proxy > index_proxy.rolling(p["trend_sma"]).mean()

        periods = closes.index.to_period(p["rebalance"])
        is_reb = pd.Series(periods != np.roll(periods, -1), index=closes.index)
        is_reb.iloc[-1] = True

        weights = pd.DataFrame(np.nan, index=closes.index, columns=closes.columns)
        for i in range(len(closes)):
            if not is_reb.iloc[i] or i < max(p["lookback"], p["trend_sma"]):
                continue
            row = pd.Series(0.0, index=closes.columns)
            if p["regime_filter"] and not bool(regime_ok.iloc[i]):
                weights.iloc[i] = row.values  # market below trend -> all cash
                continue
            # 1. sector scores = median stock momentum
            scores = {}
            for sec, syms in sectors.items():
                m = mom.iloc[i][syms].dropna()
                if len(m) >= 2:
                    scores[sec] = m.median()
            if not scores:
                weights.iloc[i] = row.values
                continue
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            chosen = [(sec, sc) for sec, sc in ranked[:p["top_sectors"]] if sc > 0]  # only positive-momentum sectors
            if not chosen:
                weights.iloc[i] = row.values
                continue
            budget_total = sum(sc for _, sc in chosen)
            for sec, sc in chosen:
                sec_budget = sc / budget_total
                syms = sectors[sec]
                cand = mom.iloc[i][syms][uptrend.iloc[i][syms]].dropna().sort_values(ascending=False)
                cand = cand[cand > 0].head(p["top_stocks_per_sector"])
                if len(cand) == 0:
                    continue
                per = sec_budget / len(cand)
                for s in cand.index:
                    row[s] += per
            row = row.clip(upper=p["max_weight"])
            g = row.sum()
            if g > 1.0:
                row = row / g
            weights.iloc[i] = row.values
        return weights.ffill().fillna(0.0)
