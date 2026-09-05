#!/usr/bin/env python
"""Morning brief: read every paper/live account state + last run reports -> one screen of text.
Writes data_cache/brief_latest.md and prints it. Cron this at 08:30 IST, or run by hand."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data_cache"


def account_summary(path: Path) -> dict:
    st = json.loads(path.read_text())
    from alpha_forge.data.loader import load_prices, close_matrix
    pos = {s: p for s, p in st["positions"].items() if abs(p["qty"]) > 1e-9}
    mv, cost_basis = 0.0, 0.0
    if pos:
        px = close_matrix(load_prices(list(pos), start=(date.today() - pd.Timedelta(days=10)).isoformat(), use_cache=False)).ffill().iloc[-1]
        for s, p in pos.items():
            mv += p["qty"] * float(px.get(s, p["avg_price"]))
            cost_basis += p["qty"] * p["avg_price"]
    equity = st["cash"] + mv
    j = st.get("journal", [])
    first_ts = j[0]["ts"][:10] if j else st.get("updated", "")[:10]
    return {"account": path.stem.replace("paper_", ""), "equity": round(equity, 2), "cash": round(st["cash"], 2),
            "positions": len(pos), "unrealised_pnl": round(mv - cost_basis, 2), "fills_total": len(j), "since": first_ts}


def main():
    lines = [f"# Alpha Forge morning brief, {datetime.now():%a %d %b %Y %H:%M}", ""]
    accts = sorted(CACHE.glob("paper_*.json"))
    if accts:
        df = pd.DataFrame([account_summary(p) for p in accts])
        lines += ["## Accounts (paper)", "", df.to_markdown(index=False), ""]
    else:
        lines += ["No paper accounts yet. Run scripts/run_daily.py once.", ""]
    risk_files = sorted(CACHE.glob("risk_state_*.json"))
    lines += ["## Risk state", "", f"* kill switch: {'ACTIVE' if (ROOT / 'KILL_SWITCH').exists() else 'off'}"]
    for rf in risk_files:
        r = json.loads(rf.read_text())
        peak = r.get("peak_equity") or 0
        eq = r.get("equity") or 0
        dd = (eq / peak - 1) if peak else 0
        flag = " **HALVED**" if dd <= -0.10 else ""
        flag = " **STOPPED**" if dd <= -0.15 else flag
        lines.append(f"* {rf.stem.replace('risk_state_', '')}: equity {eq:,.2f}, peak {peak:,.2f}, drawdown {dd:.2%}{flag}, orders today {r.get('orders_today', 0)}")
    lines.append("")
    runs = sorted((CACHE / "runs").glob("*.json"))[-6:] if (CACHE / "runs").exists() else []
    if runs:
        lines += ["## Last runs", ""]
        for p in runs:
            rep = json.loads(p.read_text())
            reasons = rep.get("risk", {}).get("state", {})
            lines.append(f"* {rep['ts'][:16]} `{rep['strategy'].split('(')[0]}/{rep['universe']}` via {rep['broker']}: bar {rep['as_of_bar']}, "
                         f"{len(rep['targets'])} targets, {len(rep['fills'])} fills, equity {rep['equity_before']:,.2f}")
        lines.append("")
    logs = CACHE / "logs"
    if logs.exists():
        errs = []
        for lf in logs.glob("*.log"):
            tail = lf.read_text().splitlines()[-200:]
            errs += [f"{lf.name}: {l}" for l in tail if "Traceback" in l or "Error" in l]
        lines += ["## Errors in recent logs", ""] + ([f"* {e}" for e in errs[-10:]] or ["* none"]) + [""]
    out = "\n".join(lines)
    (CACHE / "brief_latest.md").write_text(out)
    print(out)


if __name__ == "__main__":
    main()
