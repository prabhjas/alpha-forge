"""Risk manager - the part of the system that keeps you alive long enough to compound.

Rules are deliberately boring and mechanical. The manager is consulted BEFORE
every order batch, and it can veto or scale down. A kill-switch file lets you
halt everything from your phone (touch the file over SSH / Files app).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT / "data_cache" / "risk_state.json"
KILL_SWITCH = ROOT / "KILL_SWITCH"


@dataclass
class RiskLimits:
    max_position_pct: float = 0.20        # no single name > 20% of equity
    max_gross_exposure: float = 1.00      # no leverage
    max_daily_loss_pct: float = 0.03      # stop trading for the day after -3%
    max_drawdown_halve_pct: float = 0.10  # at -10% from peak, halve all sizes
    max_drawdown_stop_pct: float = 0.15   # at -15% from peak, flat + human review
    max_orders_per_day: int = 40          # well under SEBI's 10 orders/second threshold
    cash_buffer_pct: float = 0.01         # keep 1% in cash so slippage never bounces an order
    min_order_pct: float = 0.01           # skip rebalances smaller than 1% of equity (currency-agnostic)


@dataclass
class RiskDecision:
    allowed: bool
    scale: float
    reasons: List[str]


class RiskManager:
    def __init__(self, limits: Optional[RiskLimits] = None, state_file: Optional[Path] = None, account: str = "default"):
        self.limits = limits or RiskLimits()
        # one state file per account: a Rs 50k India book and a $570 US book must never share a peak-equity number
        self.state_file = state_file or (STATE_FILE.parent / f"risk_state_{account}.json")
        self.state = self._load()

    def _load(self) -> Dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"peak_equity": None, "day": None, "day_start_equity": None, "orders_today": 0}

    def _save(self):
        self.state_file.parent.mkdir(exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def update_equity(self, equity: float):
        today = date.today().isoformat()
        if self.state["day"] != today:
            self.state.update({"day": today, "day_start_equity": equity, "orders_today": 0})
        if self.state["peak_equity"] is None or equity > self.state["peak_equity"]:
            self.state["peak_equity"] = equity
        self.state["equity"] = equity
        self._save()

    def evaluate(self, equity: float, target_weights: Dict[str, float], n_orders: int) -> RiskDecision:
        self.update_equity(equity)
        L = self.limits
        reasons: List[str] = []
        scale = 1.0
        allowed = True

        if KILL_SWITCH.exists():
            return RiskDecision(False, 0.0, ["KILL_SWITCH file present - all trading halted"])

        peak = self.state["peak_equity"] or equity
        dd = equity / peak - 1.0
        if dd <= -L.max_drawdown_stop_pct:
            return RiskDecision(False, 0.0, [f"Drawdown {dd:.1%} breached stop {L.max_drawdown_stop_pct:.0%} - go flat, review"])
        if dd <= -L.max_drawdown_halve_pct:
            scale *= 0.5
            reasons.append(f"Drawdown {dd:.1%} - sizes halved")

        day_start = self.state["day_start_equity"] or equity
        day_pnl = equity / day_start - 1.0
        if day_pnl <= -L.max_daily_loss_pct:
            return RiskDecision(False, 0.0, [f"Daily loss {day_pnl:.1%} hit limit - done for today"])

        if self.state["orders_today"] + n_orders > L.max_orders_per_day:
            return RiskDecision(False, 0.0, [f"Order cap {L.max_orders_per_day}/day would be exceeded"])

        gross = sum(abs(w) for w in target_weights.values())
        if gross > L.max_gross_exposure + 1e-9:
            scale *= L.max_gross_exposure / gross
            reasons.append(f"Gross exposure {gross:.2f} scaled to {L.max_gross_exposure:.2f}")
        worst = max((abs(w) for w in target_weights.values()), default=0.0)
        if worst > L.max_position_pct + 1e-9:
            scale *= L.max_position_pct / worst
            reasons.append(f"Largest position {worst:.1%} scaled to cap {L.max_position_pct:.0%}")

        return RiskDecision(allowed, scale, reasons or ["ok"])

    def record_orders(self, n: int):
        self.state["orders_today"] = self.state.get("orders_today", 0) + n
        self._save()

    def to_dict(self) -> Dict:
        return {"limits": asdict(self.limits), "state": self.state}
