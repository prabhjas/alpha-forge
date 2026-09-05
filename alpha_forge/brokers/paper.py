"""In-memory paper broker with realistic-ish fills and a JSON journal.

Fills at the supplied/last price plus slippage in the adverse direction.
State persists to data_cache/paper_<account>.json so a daily cron can resume.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from .base import Broker, Fill, Order, Position

ROOT = Path(__file__).resolve().parents[2]


class PaperBroker(Broker):
    name = "paper"

    def __init__(self, account: str = "default", starting_cash: float = 100_000.0,
                 slippage_bps: float = 5.0, price_fn: Optional[Callable[[str], float]] = None):
        self.account = account
        self.slippage = slippage_bps / 1e4
        self.price_fn = price_fn or (lambda s: self._prices[s])
        self._prices: Dict[str, float] = {}
        self.path = ROOT / "data_cache" / f"paper_{account}.json"
        if self.path.exists():
            st = json.loads(self.path.read_text())
            self._cash = st["cash"]
            self._pos = {s: Position(**p) for s, p in st["positions"].items()}
            self.journal = st.get("journal", [])
        else:
            self._cash = starting_cash
            self._pos = {}
            self.journal = []

    # -- prices -------------------------------------------------------------
    def set_prices(self, prices: Dict[str, float]):
        self._prices.update(prices)

    def last_price(self, symbol: str) -> float:
        return float(self.price_fn(symbol))

    # -- account ------------------------------------------------------------
    def cash(self) -> float:
        return self._cash

    def positions(self) -> Dict[str, Position]:
        return {s: p for s, p in self._pos.items() if abs(p.qty) > 1e-9}

    # -- trading ------------------------------------------------------------
    def place(self, order: Order) -> Fill:
        px = self.last_price(order.symbol)
        px = px * (1 + self.slippage) if order.side == "BUY" else px * (1 - self.slippage)
        notional = px * order.qty
        if order.side == "BUY":
            if notional > self._cash + 1e-6:
                raise ValueError(f"insufficient cash for {order.symbol}: need {notional:.2f}, have {self._cash:.2f}")
            self._cash -= notional
            p = self._pos.get(order.symbol, Position(order.symbol, 0.0, 0.0))
            new_qty = p.qty + order.qty
            p.avg_price = (p.avg_price * p.qty + px * order.qty) / new_qty if new_qty else 0.0
            p.qty = new_qty
            self._pos[order.symbol] = p
        else:
            p = self._pos.get(order.symbol)
            if p is None or p.qty + 1e-9 < order.qty:
                raise ValueError(f"cannot sell {order.qty} {order.symbol}: hold {p.qty if p else 0}")
            p.qty -= order.qty
            self._cash += notional
        fill = Fill(order=order, price=px, broker_order_id=f"paper-{len(self.journal)+1}")
        self.journal.append({"ts": fill.ts, "symbol": order.symbol, "side": order.side,
                             "qty": order.qty, "price": round(px, 4), "tag": order.tag})
        self._save()
        return fill

    def _save(self):
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps({
            "cash": self._cash,
            "positions": {s: p.__dict__ for s, p in self._pos.items()},
            "journal": self.journal,
            "updated": datetime.now().isoformat(timespec="seconds"),
        }, indent=2))
