#!/bin/zsh
# Daily runner for one leg. Called by launchd. Usage: daily.sh india|us
set -u
LEG="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv313/bin/python"
LOG="$ROOT/data_cache/logs"; mkdir -p "$LOG"
STAMP="$(date +%Y%m%d_%H%M%S)"
cd "$ROOT" || exit 1
[ -f "$ROOT/.env" ] && set -a && source "$ROOT/.env" && set +a

# Weekend guard (launchd fires on the weekdays we ask for, but the US run lands on Sat IST for Fri's close)
DOW=$(date +%u); [ "${FORCE:-0}" = "1" ] && DOW=3  # FORCE=1 bypasses the weekend guard for testing
if [ "$LEG" = "india" ] && [ "$DOW" -gt 5 ]; then echo "weekend, skip" >> "$LOG/$LEG.log"; exit 0; fi
if [ "$LEG" = "us" ] && { [ "$DOW" -eq 7 ] || [ "$DOW" -eq 1 ]; }; then echo "no US session yesterday, skip" >> "$LOG/$LEG.log"; exit 0; fi

# Broker is configurable per leg via .env; defaults are paper. Live requires ALPHA_FORGE_LIVE=1 too.
if [ "$LEG" = "india" ]; then
  BROKER="${INDIA_BROKER:-paper}"
  echo "=== $STAMP india trend/india_etf via $BROKER" >> "$LOG/$LEG.log"
  "$PY" scripts/run_daily.py --strategy trend --universe india_etf --broker "$BROKER" --account india_paper --cash 50000 --live-close >> "$LOG/$LEG.log" 2>&1
  echo "=== $STAMP india A/B trend_hrp/nifty50 (paper only)" >> "$LOG/$LEG.log"
  "$PY" scripts/run_daily.py --strategy trend_hrp --universe nifty50 --broker paper --account india_ab_hrp --cash 50000 --live-close >> "$LOG/$LEG.log" 2>&1
  "$PY" scripts/run_daily.py --strategy trend --universe nifty50 --broker paper --account india_ab_trend --cash 50000 --live-close >> "$LOG/$LEG.log" 2>&1
  "$PY" scripts/run_daily.py --strategy ensemble --universe india_etf --broker paper --account india_ensemble --cash 50000 --live-close >> "$LOG/$LEG.log" 2>&1
  "$PY" scripts/run_daily.py --strategy sector_ensemble --universe nifty50 --broker paper --account india_sector --cash 50000 --live-close >> "$LOG/$LEG.log" 2>&1
else
  BROKER="${US_BROKER:-paper}"
  echo "=== $STAMP us ensemble/us_core via $BROKER" >> "$LOG/$LEG.log"
  "$PY" scripts/run_daily.py --strategy ensemble --universe us_core --broker "$BROKER" --account us_paper --cash 570 --fractional >> "$LOG/$LEG.log" 2>&1
fi
echo "=== $STAMP done rc=$?" >> "$LOG/$LEG.log"
