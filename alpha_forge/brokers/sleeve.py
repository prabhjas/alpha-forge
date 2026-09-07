"""SleeveBroker — the safety wrapper that quarantines the algo from your existing holdings.

Problem it solves: a live AngelOne/Kite account already holds shares you bought
yourself. The rebalancer sees positions() and could sell them to fund its targets.
Unacceptable.

SleeveBroker wraps any real broker and enforces:
  * positions() returns ONLY what the algo itself bought (tracked in a local ledger).
    Your pre-existing holdings are invisible to the strategy, so it never rebalances them.
  * cash() returns the ring-fenced ALLOCATION, not the account's whole balance.
  * place(SELL) can never sell more of a symbol than the sleeve owns — a hard cap,
    defense-in-depth even if a target somehow asked for more.
  * every fill updates a persistent ledger (data_cache/sleeve_<account>.json).

The underlying broker still executes real orders; the sleeve is the accounting and
guard-rail layer on top. Works identically over PaperBroker (for testing) and live brokers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .base import Broker, Fill, Order, Position

ROOT = Path(__file__).resolve().parents[2]


class SleeveBroker(Broker):
    def __init__(self, underlying: Broker, account: str, allocation: float):
        self.underlying = underlying
        self.account = account
        self.name = f"{underlying.name}_sleeve"
        self.path = ROOT / "data_cache" / f"sleeve_{account}.json"
        if self.path.exists():
            st = json.loads(self.path.read_text())
            self._cash = st["cash"]
            self._pos = {s: Position(**p) for s, p in st["positions"].items()}
            self.allocation = st.get("allocation", allocation)
        else:
            self._cash = allocation
            self._pos = {}
            self.allocation = allocation
            self._save()

    def _save(self):
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps({
            "account": self.account, "allocation": self.allocation, "cash": self._cash,
            "positions": {s: p.__dict__ for s, p in self._pos.items()},
        }, indent=2))

    # --- views the strategy/rebalancer sees: SLEEVE ONLY -------------------
    def cash(self) -> float:
        return self._cash

    def positions(self) -> Dict[str, Position]:
        return {s: p for s, p in self._pos.items() if abs(p.qty) > 1e-9}

    def last_price(self, symbol: str) -> float:
        return self.underlying.last_price(symbol)

    # --- execution: real order via underlying, ledger updated, sells capped -
    def place(self, order: Order) -> Fill:
        if order.side == "SELL":
            held = self._pos.get(order.symbol)
            owned = held.qty if held else 0.0
            if order.qty > owned + 1e-9:
                # HARD GUARD: never sell more than the sleeve owns -> pre-existing holdings are safe
                if owned <= 1e-9:
                    raise ValueError(f"sleeve refuses to SELL {order.symbol}: sleeve owns 0 (protecting your own holdings)")
                order = Order(order.symbol, owned, "SELL", order.order_type, order.limit_price, order.tag)

        fill = self.underlying.place(order)  # the real (or paper) order

        px = fill.price
        if order.side == "BUY":
            self._cash -= px * order.qty
            p = self._pos.get(order.symbol, Position(order.symbol, 0.0, 0.0))
            new_qty = p.qty + order.qty
            p.avg_price = (p.avg_price * p.qty + px * order.qty) / new_qty if new_qty else 0.0
            p.qty = new_qty
            self._pos[order.symbol] = p
        else:
            p = self._pos[order.symbol]
            p.qty -= order.qty
            self._cash += px * order.qty
            if abs(p.qty) < 1e-9:
                del self._pos[order.symbol]
        self._save()
        return fill

    def set_prices(self, prices):  # pass-through so paper underlying can be priced
        if hasattr(self.underlying, "set_prices"):
            self.underlying.set_prices(prices)
