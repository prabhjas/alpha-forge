"""Daily rebalance loop: prices -> strategy weights -> risk check -> orders -> broker -> journal.

Same code path for paper and live; only the broker object differs. Run once per
day after the close (India ~16:00 IST, US ~16:30 ET) via cron / launchd.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd

from alpha_forge.brokers import Broker, Order
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.risk import RiskManager
from alpha_forge.strategies import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "data_cache" / "runs"


def rebalance_to_targets(broker: Broker, targets: Dict[str, float], prices: Dict[str, float],
                         risk: RiskManager, fractional: bool, tag: str) -> List[Order]:
    equity = broker.equity()
    decision = risk.evaluate(equity, targets, n_orders=len(targets))
    if not decision.allowed:
        return []
    pos = broker.positions()
    min_order_value = equity * risk.limits.min_order_pct
    orders: List[Order] = []
    for sym in set(list(targets) + list(pos)):
        px = prices.get(sym) or broker.last_price(sym)
        target_val = equity * (1 - risk.limits.cash_buffer_pct) * targets.get(sym, 0.0) * decision.scale
        cur_qty = pos[sym].qty if sym in pos else 0.0
        target_qty = target_val / px
        if not fractional:
            target_qty = float(int(target_qty))
        delta = target_qty - cur_qty
        if abs(delta * px) < min_order_value:
            continue
        orders.append(Order(sym, abs(delta), "BUY" if delta > 0 else "SELL", tag=tag))
    return orders


def run_daily(strategy_name: str, universe: str, broker: Broker, params: Dict = None,
              fractional: bool = False, start: str = "2018-01-01") -> Dict:
    strat = REGISTRY[strategy_name](**(params or {}))
    tickers = UNIVERSES[universe]
    prices = load_prices(tickers, start=start, use_cache=False)
    closes = close_matrix(prices)
    weights = strat.generate_weights(prices)
    today_w = weights.iloc[-1]
    targets = {t: float(w) for t, w in today_w.items() if abs(w) > 1e-6}
    last_px = {t: float(closes[t].dropna().iloc[-1]) for t in closes.columns}
    if hasattr(broker, "set_prices"):
        broker.set_prices(last_px)  # paper broker fills at last close
    risk = RiskManager(account=getattr(broker, 'account', broker.name))
    orders = rebalance_to_targets(broker, targets, last_px, risk, fractional, tag=strategy_name)
    fills = broker.place_all(orders) if orders else []
    risk.record_orders(len(fills))
    report = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "as_of_bar": str(closes.index[-1].date()),
        "strategy": strat.describe(),
        "universe": universe,
        "broker": broker.name,
        "equity_before": round(broker.equity(), 2),
        "targets": {k: round(v, 4) for k, v in targets.items()},
        "orders": [o.__dict__ for o in orders],
        "fills": [{"symbol": f.order.symbol, "side": f.order.side, "qty": f.order.qty, "price": f.price, "id": f.broker_order_id} for f in fills],
        "risk": risk.to_dict(),
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{strategy_name}_{universe}_{broker.name}.json").write_text(json.dumps(report, indent=2, default=str))
    return report
