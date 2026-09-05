"""Angel One SmartAPI (India). DRY-RUN by default. Free API.
pip install smartapi-python pyotp
Env: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD (MPIN), ANGEL_TOTP_SECRET
SmartAPI needs a symbol->token map; we lazily fetch the public instrument JSON.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from .base import Broker, Fill, Order, Position, assert_live_allowed

INSTRUMENT_URL = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"


class AngelOneBroker(Broker):
    name = "angelone"

    def __init__(self, live: bool = False):
        assert_live_allowed(live)
        from SmartApi import SmartConnect  # type: ignore
        import pyotp  # type: ignore
        self.live = live
        self.api = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
        totp = pyotp.TOTP(os.environ["ANGEL_TOTP_SECRET"]).now()
        data = self.api.generateSession(os.environ["ANGEL_CLIENT_CODE"], os.environ["ANGEL_PASSWORD"], totp)
        if not data.get("status"):
            raise RuntimeError(f"Angel One login failed: {data}")
        self._tokens: Optional[Dict[str, str]] = None

    def _token(self, symbol: str) -> str:
        if self._tokens is None:
            import requests
            rows = requests.get(INSTRUMENT_URL, timeout=30).json()
            self._tokens = {r["symbol"]: r["token"] for r in rows if r.get("exch_seg") == "NSE" and r["symbol"].endswith("-EQ")}
        return self._tokens[symbol.replace(".NS", "") + "-EQ"]

    def cash(self) -> float:
        return float(self.api.rmsLimit()["data"]["availablecash"])

    def positions(self) -> Dict[str, Position]:
        out = {}
        for h in (self.api.holding().get("data") or []):
            out[h["tradingsymbol"].replace("-EQ", "") + ".NS"] = Position(h["tradingsymbol"].replace("-EQ", "") + ".NS", float(h["quantity"]), float(h["averageprice"]))
        return out

    def last_price(self, symbol: str) -> float:
        base = symbol.replace(".NS", "")
        return float(self.api.ltpData("NSE", base + "-EQ", self._token(symbol))["data"]["ltp"])

    def place(self, order: Order) -> Fill:
        qty = int(order.qty)
        px = self.last_price(order.symbol)
        if qty <= 0:
            raise ValueError("qty rounds to 0")
        if not self.live:
            print(f"[DRY RUN angelone] {order.side} {qty} {order.symbol} @~{px}")
            return Fill(order=order, price=px, broker_order_id="dry-run")
        base = order.symbol.replace(".NS", "")
        oid = self.api.placeOrder({
            "variety": "NORMAL", "tradingsymbol": base + "-EQ", "symboltoken": self._token(order.symbol),
            "transactiontype": order.side, "exchange": "NSE", "ordertype": "MARKET", "producttype": "DELIVERY",
            "duration": "DAY", "quantity": str(qty),
        })
        return Fill(order=order, price=px, broker_order_id=str(oid))
