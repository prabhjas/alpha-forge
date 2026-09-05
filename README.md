# Alpha Forge

Research, backtesting and paper-trading engine for NSE (India) + US equities.
Long-only, cost-aware, risk-managed, paper-first. Read `docs/PLAN.md` first.

## Quick start
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
python scripts/backtest.py --strategy momentum --universe nifty50 --costs india_delivery --save
python scripts/backtest.py --strategy trend --universe us_core --costs us_alpaca --save
python scripts/research_report.py            # full scoreboard -> docs/RESULTS.md
python scripts/backtest_orb.py               # intraday smell test
python scripts/run_daily.py --strategy trend --universe us_core --broker paper --account us_paper --fractional
```

## Safety
* Every broker adapter is paper / dry-run unless constructed with `live=True` **and** `ALPHA_FORGE_LIVE=1` is exported.
* `touch KILL_SWITCH` in the repo root halts all order generation.
* Risk limits live in `alpha_forge/risk/manager.py` and are enforced before every order batch.

## Adding a strategy
Subclass `alpha_forge.strategies.base.Strategy`, implement `generate_weights(prices) -> DataFrame`
(rows = dates, columns = tickers, values = target weight using only past data), register it in
`alpha_forge/strategies/__init__.py`. The engine handles returns, costs, exposure caps and metrics.
