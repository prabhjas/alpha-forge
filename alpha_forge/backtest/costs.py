"""Transaction cost models. All figures in basis points PER SIDE of a trade.

Costs are the single biggest reason retail algos that look great in a
backtest lose money live. Every backtest in this repo charges them.

India (delivery, per side): STT 0.1% = 10 bps, brokerage ~0.03% for a
Rs 20 flat on ~Rs 60k trades = ~3 bps, exchange + SEBI + stamp + GST ~ 1 bp,
slippage on liquid Nifty50 names ~ 5 bps  ->  ~19 bps.
India (intraday): STT 0.025% sell-side only (~1.25 bps avg per side),
brokerage ~3 bps, other ~1 bp, slippage ~5 bps -> ~10 bps.
US (Alpaca): commission 0, regulatory fees ~0.1 bp, slippage ~3 bps -> ~3 bps.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    name: str
    commission_bps: float
    tax_bps: float
    slippage_bps: float

    @property
    def per_side_bps(self) -> float:
        return self.commission_bps + self.tax_bps + self.slippage_bps

    @property
    def per_side(self) -> float:
        return self.per_side_bps / 1e4

    def round_trip_pct(self) -> float:
        return 2 * self.per_side_bps / 100.0


COST_PRESETS = {
    "india_delivery": CostModel("india_delivery", commission_bps=3, tax_bps=11, slippage_bps=5),
    "india_intraday": CostModel("india_intraday", commission_bps=3, tax_bps=2.25, slippage_bps=5),
    "us_alpaca": CostModel("us_alpaca", commission_bps=0, tax_bps=0.1, slippage_bps=3),
    "zero": CostModel("zero", 0, 0, 0),  # only to show how much costs matter
}
