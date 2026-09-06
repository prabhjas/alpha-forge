# Alpha Forge

Research, backtesting and paper-trading engine for NSE (India) + US equities.
Long-only, cost-aware, risk-managed, paper-first. Read `docs/PLAN.md` first.

## Environments
Two virtualenvs, on purpose:
* `.venv313` (Python 3.13, Homebrew) - **primary**. Everything incl. skfolio sizing.
* `.venv` (Python 3.9, system) - kept only for the Kronos experiment (`research/`), whose pinned deps predate 3.13.

## Quick start
```bash
/opt/homebrew/bin/python3.13 -m venv .venv313 && . .venv313/bin/activate
pip install -r requirements.txt skfolio
pytest -q
python scripts/walk_forward_report.py        # walk-forward + parameter plateaus -> docs/WALK_FORWARD.md
python scripts/skfolio_sizing_report.py      # inverse-vol vs HRP / risk parity / min-var -> docs/SKFOLIO_SIZING.md
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

## Daily automation (macOS launchd)
```bash
./scripts/install_launchd.sh     # installs com.alphaforge.{india,us,brief}; re-run after editing daily.sh times
FORCE=1 ./scripts/daily.sh india # run a leg by hand (FORCE bypasses the weekend guard)
.venv313/bin/python scripts/morning_brief.py
tail -f data_cache/logs/india.log

# Read-only daily watchlist (no keys, no orders)
.venv313/bin/python scripts/sma_scanner.py --universe nifty50 --fast 6 --slow 30 --max-age 10
```
Brokers per leg are set in `.env` (`INDIA_BROKER=paper|kite|angelone`, `US_BROKER=paper|alpaca`). Everything is paper until
`ALPHA_FORGE_LIVE=1` is also set. The Mac must be awake at run time; see the header of `scripts/install_launchd.sh`.
