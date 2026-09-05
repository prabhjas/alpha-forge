"""Alpaca (US). Paper by default. Needs env: ALPACA_API_KEY, ALPACA_SECRET_KEY.
Get free paper keys at https://app.alpaca.markets (paper account is instant).

Note for a <$25k account: FINRA's Pattern Day Trader rule limits you to 3 day
trades per rolling 5 days. Our US strategies are swing/positional so this
never bites, but do not bolt an intraday strategy onto this account.
"""
from __future__ import annotations

import os
from typing import Dict

from .base import Broker, Fill, Order, Position, assert_live_allowed


class AlpacaBroker(Broker):
    name = "alpaca"

    def __init__(self, live: bool = False):
        assert_live_allowed(live)
        from alpaca.trading.client import TradingClient
        from alpaca.data.historical import StockHistoricalDataClient

        key, secret = os.environ.get("ALPACA_API_KEY"), os.environ.get("ALPACA_SECRET_KEY")
        if not key or not secret:
            raise EnvironmentError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY (paper keys) in .env")
        self.live = live
        self.client = TradingClient(key, secret, paper=not live)
        self.data = StockHistoricalDataClient(key, secret)

    def cash(self) -> float:
        return float(self.client.get_account().cash)

    def positions(self) -> Dict[str, Position]:
        return {p.symbol: Position(p.symbol, float(p.qty), float(p.avg_entry_price)) for p in self.client.get_all_positions()}

    def last_price(self, symbol: str) -> float:
        from alpaca.data.requests import StockLatestTradeRequest
        t = self.data.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=symbol))
        return float(t[symbol].price)

    def place(self, order: Order) -> Fill:
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        req = MarketOrderRequest(
            symbol=order.symbol,
            qty=round(order.qty, 4),  # fractional allowed
            side=OrderSide.BUY if order.side == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        o = self.client.submit_order(req)
        px = float(o.filled_avg_price) if o.filled_avg_price else self.last_price(order.symbol)
        return Fill(order=order, price=px, broker_order_id=str(o.id))
