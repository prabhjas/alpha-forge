#!/usr/bin/env python
"""Weekly paper-trading review -> data_cache/weekly/weekly_YYYYMMDD.md
For each paper account: equity now, week change, positions, and benchmark comparison.
Snapshots equity to data_cache/weekly/equity_history.json so week-over-week works."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data_cache"
WK = CACHE / "weekly"; WK.mkdir(parents=True, exist_ok=True)
HIST = WK / "equity_history.json"


def account_equity(path: Path) -> tuple[float, int]:
    from alpha_forge.data.loader import load_prices, close_matrix
    st = json.loads(path.read_text())
    pos = {s: p for s, p in st["positions"].items() if abs(p["qty"]) > 1e-9}
    mv = 0.0
    if pos:
        px = close_matrix(load_prices(list(pos), start=(date.today() - timedelta(days=12)).isoformat(), use_cache=False)).ffill().iloc[-1]
        mv = sum(p["qty"] * float(px.get(s, p["avg_price"])) for s, p in pos.items())
    return round(st["cash"] + mv, 2), len(pos)


def bench_week(sym: str) -> float:
    from alpha_forge.data.loader import load_prices, close_matrix
    c = close_matrix(load_prices([sym], start=(date.today() - timedelta(days=15)).isoformat(), use_cache=False)).iloc[:, 0].dropna()
    return round((c.iloc[-1] / c.iloc[-6] - 1) * 100, 2) if len(c) > 6 else 0.0


def main():
    hist = json.loads(HIST.read_text()) if HIST.exists() else {}
    today = date.today().isoformat()
    lines = [f"# Weekly paper review — {datetime.now():%A %d %B %Y}", "",
             "Paper trading only. No real money. Benchmarks: Nifty 50 (India), S&P 500 (US).", ""]
    rows = []
    bench_map = {"india": "^NSEI", "us": "SPY"}
    for path in sorted(CACHE.glob("paper_*.json")):
        acct = path.stem.replace("paper_", "")
        eq, npos = account_equity(path)
        prev = hist.get(acct, {}).get("equity")
        wk_chg = round((eq / prev - 1) * 100, 2) if prev else None
        bench = bench_week("^NSEI" if acct.startswith("india") else "SPY")
        rows.append({"account": acct, "equity": eq, "positions": npos,
                     "week %": wk_chg if wk_chg is not None else "first snapshot",
                     "benchmark week %": bench,
                     "vs benchmark": round(wk_chg - bench, 2) if wk_chg is not None else "-"})
        hist[acct] = {"equity": eq, "date": today}
    if rows:
        lines += [pd.DataFrame(rows).to_markdown(index=False), ""]
    # count fills this week from run reports
    since = datetime.now() - timedelta(days=7)
    fills = 0
    for rp in (CACHE / "runs").glob("*.json"):
        try:
            d = json.loads(rp.read_text())
            if datetime.fromisoformat(d["ts"]) >= since:
                fills += len(d.get("fills", []))
        except Exception:
            pass
    lines += [f"* Fills executed this week (all books): {fills}",
              f"* Kill switch: {'ACTIVE' if (ROOT / 'KILL_SWITCH').exists() else 'off'}", "",
              "_Interpretation: 'vs benchmark' is what matters. Positive means the engine beat just buying the index that week. One week is noise; the 8-week trend is the signal._"]
    HIST.write_text(json.dumps(hist, indent=2))
    out = WK / f"weekly_{date.today():%Y%m%d}.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
