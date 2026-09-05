from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Order:
    symbol: str
    qty: float
    side: str                     # "BUY" | "SELL"
    order_type: str = "MARKET"    # v1: MARKET only (SEBI converts API market orders to MPP anyway)
    limit_price: Optional[float] = None
    tag: str = ""


@dataclass
class Fill:
    order: Order
    price: float
    ts: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    broker_order_id: str = ""


@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float


class LiveTradingDisabled(RuntimeError):
    pass


def assert_live_allowed(live: bool):
    """Two independent switches must both be on for a real order to leave this machine."""
    if live and os.environ.get("ALPHA_FORGE_LIVE") != "1":
        raise LiveTradingDisabled(
            "Broker constructed with live=True but ALPHA_FORGE_LIVE != 1. "
            "Refusing to place real orders. Set the env var only after Phase 2 sign-off."
        )


class Broker(ABC):
    name = "broker"

    @abstractmethod
    def cash(self) -> float: ...

    @abstractmethod
    def positions(self) -> Dict[str, Position]: ...

    @abstractmethod
    def last_price(self, symbol: str) -> float: ...

    @abstractmethod
    def place(self, order: Order) -> Fill: ...

    def equity(self) -> float:
        return self.cash() + sum(p.qty * self.last_price(s) for s, p in self.positions().items())

    def place_all(self, orders: List[Order]) -> List[Fill]:
        # sells first so cash is available for buys
        ordered = sorted(orders, key=lambda o: 0 if o.side == "SELL" else 1)
        return [self.place(o) for o in ordered]
