#!/usr/bin/env python
"""Daily paper/live rebalance. Cron this after market close.

  python scripts/run_daily.py --strategy trend --universe us_core --broker paper --account us_paper --fractional
  python scripts/run_daily.py --strategy momentum --universe nifty50 --broker paper --account india_paper
  python scripts/run_daily.py --strategy momentum --universe nifty50 --broker kite      # dry-run prints orders
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alpha_forge.brokers import get_broker
from alpha_forge.data.loader import UNIVERSES
from alpha_forge.paper import run_daily
from alpha_forge.strategies import REGISTRY


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True, choices=list(REGISTRY))
    ap.add_argument("--universe", required=True, choices=list(UNIVERSES))
    ap.add_argument("--broker", default="paper", choices=["paper", "alpaca", "kite", "angelone"])
    ap.add_argument("--account", default="default", help="paper account name")
    ap.add_argument("--cash", type=float, default=50_000, help="paper starting cash")
    ap.add_argument("--fractional", action="store_true", help="allow fractional shares (US/Alpaca)")
    ap.add_argument("--live", action="store_true", help="REAL MONEY. Also needs ALPHA_FORGE_LIVE=1")
    ap.add_argument("--sleeve-allocation", type=float, default=None,
                    help="ring-fence this capital; algo manages only what it buys, never your existing holdings")
    a = ap.parse_args()

    try:
        from dotenv import load_dotenv; load_dotenv()
    except ImportError:
        pass

    if a.broker == "paper":
        broker = get_broker("paper", account=a.account, starting_cash=a.cash)
    else:
        broker = get_broker(a.broker, live=a.live)
    if a.sleeve_allocation is not None:
        from alpha_forge.brokers import SleeveBroker
        broker = SleeveBroker(broker, account=a.account, allocation=a.sleeve_allocation)

    report = run_daily(a.strategy, a.universe, broker, fractional=a.fractional)
    print(json.dumps({k: v for k, v in report.items() if k != "risk"}, indent=2, default=str))
    print("equity after:", round(broker.equity(), 2))


if __name__ == "__main__":
    main()
