"""Zerodha Kite Connect (India). DRY-RUN by default.

Kite Connect Personal is free for order placement but has no market data;
the paid plan (Rs 500/month) adds live + historical data. Under SEBI's
April-2026 retail algo framework the API key must be mapped to a static IP
and you must complete 2FA/OAuth login once every trading day - so this class
expects a fresh KITE_ACCESS_TOKEN each morning (scripts/kite_login.py).

Env: KITE_API_KEY, KITE_ACCESS_TOKEN
"""
from __future__ import annotations

import os
from typing import Dict

from .base import Broker, Fill, Order, Position, assert_live_allowed


class KiteBroker(Broker):
    name = "kite"

    def __init__(self, live: bool = False, exchange: str = "NSE", product: str = "CNC"):
        assert_live_allowed(live)
        from kiteconnect import KiteConnect
        self.live, self.exchange, self.product = live, exchange, product
        self.kite = KiteConnect(api_key=os.environ["KITE_API_KEY"])
        self.kite.set_access_token(os.environ["KITE_ACCESS_TOKEN"])

    @staticmethod
    def _sym(symbol: str) -> str:
        return symbol.replace(".NS", "")

    def cash(self) -> float:
        return float(self.kite.margins("equity")["available"]["live_balance"])

    def positions(self) -> Dict[str, Position]:
        out = {}
        for h in self.kite.holdings():
            out[h["tradingsymbol"] + ".NS"] = Position(h["tradingsymbol"] + ".NS", float(h["quantity"]), float(h["average_price"]))
        return out

    def last_price(self, symbol: str) -> float:
        key = f"{self.exchange}:{self._sym(symbol)}"
        return float(self.kite.ltp(key)[key]["last_price"])

    def place(self, order: Order) -> Fill:
        qty = int(order.qty)  # NSE: whole shares only
        if qty <= 0:
            raise ValueError("qty rounds to 0 - increase capital or drop this name")
        px = self.last_price(order.symbol)
        if not self.live:
            print(f"[DRY RUN kite] {order.side} {qty} {self._sym(order.symbol)} @~{px}")
            return Fill(order=order, price=px, broker_order_id="dry-run")
        oid = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR, exchange=self.exchange,
            tradingsymbol=self._sym(order.symbol), transaction_type=order.side,
            quantity=qty, product=self.product, order_type=self.kite.ORDER_TYPE_MARKET, tag=order.tag[:20] or "alphaforge",
        )
        return Fill(order=order, price=px, broker_order_id=str(oid))
