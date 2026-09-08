#!/usr/bin/env python
"""Bull & Bear research brief -> docs/RESEARCH_BRIEF.md  (INFORMATION ONLY)

Borrows TradingAgents' multi-analyst idea but keeps it DETERMINISTIC and AUDITABLE:
every bull/bear point is generated from a real, cited metric (trend, momentum,
volatility, RSI, distance from 200-DMA, 52-week range, sector strength, news tone).
No LLM opinions, no fabrication. A human reads this; the engine still decides.

  python scripts/research_brief.py                # all sector-book holdings
  python scripts/research_brief.py --symbol TITAN # one name
"""
from __future__ import annotations
import argparse, json, sys, time, warnings
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, yaml
from alpha_forge.data.loader import ROOT, close_matrix, load_prices
from scripts.news_digest import NAME, senti, fetch

CACHE = ROOT / "data_cache"
sectors = yaml.safe_load(open(ROOT / "config" / "sectors.yaml"))
sec_of = {s: sec for sec, syms in sectors.items() for s in syms}


def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return float((100 - 100/(1 + up/dn.replace(0, np.nan))).iloc[-1])


def sector_ranks(allsyms):
    ca = close_matrix(load_prices(allsyms, start="2024-06-01"))
    rank = {}
    scores = {}
    for sec, syms in sectors.items():
        ms = [float(ca[s].dropna().iloc[-1]/ca[s].dropna().iloc[-63]-1)*100
              for s in syms if s in ca and ca[s].notna().sum() > 63]
        if ms: scores[sec] = float(np.median(ms))
    for i, (sec, _) in enumerate(sorted(scores.items(), key=lambda kv:-kv[1]), 1):
        rank[sec] = (i, len(scores), round(scores[sec], 1))
    return rank


def brief_for(sym, px, secrank, news):
    s = px.dropna()
    last = float(s.iloc[-1]); sma200 = float(s.rolling(200).mean().iloc[-1]); sma50 = float(s.rolling(50).mean().iloc[-1])
    m1 = (last/float(s.iloc[-22])-1)*100; m3 = (last/float(s.iloc[-63])-1)*100; m6 = (last/float(s.iloc[-126])-1)*100
    vol = float(s.pct_change().rolling(21).std().iloc[-1]*np.sqrt(252)*100)
    r = rsi(s); hi52 = float(s.iloc[-252:].max()); lo52 = float(s.iloc[-252:].min())
    off_hi = (last/hi52-1)*100; ext = (last/sma200-1)*100
    sec = sec_of.get(sym, "?"); sr = secrank.get(sec, (0, 0, 0))
    net = sum({"▲":1,"▼":-1,"·":0}[senti(h["title"])] for h in news)

    bull, bear = [], []
    if last > sma200: bull.append(f"Uptrend intact — price ₹{last:.0f} is {ext:+.0f}% above its 200-day avg (₹{sma200:.0f}).")
    else: bear.append(f"Trend broken — price is {ext:.0f}% BELOW its 200-day avg; the engine exits names here.")
    if last > sma50: bull.append(f"Short-term strong — above the 50-day avg (₹{sma50:.0f}).")
    else: bear.append(f"Short-term weak — below the 50-day avg (₹{sma50:.0f}).")
    if m3 > 10: bull.append(f"Strong 3-month momentum (+{m3:.0f}%).")
    elif m3 < 0: bear.append(f"Negative 3-month momentum ({m3:.0f}%) — this is the 'shaky' trigger.")
    if m6 > 15: bull.append(f"Powerful 6-month run (+{m6:.0f}%).")
    if m1 < -5: bear.append(f"Sharp recent pullback ({m1:.0f}% in a month).")
    if sr[0] and sr[0] <= 4: bull.append(f"Sector '{sec}' is strong — ranked #{sr[0]} of {sr[1]} (median +{sr[2]}%).")
    if sr[0] and sr[0] > sr[1]-3: bear.append(f"Sector '{sec}' is weak — ranked #{sr[0]} of {sr[1]} (median {sr[2]}%).")
    if off_hi > -5: bull.append(f"Near its 52-week high (only {off_hi:.0f}% off ₹{hi52:.0f}).")
    if off_hi < -25: bear.append(f"Far below its 52-week high ({off_hi:.0f}% off ₹{hi52:.0f}).")
    if vol < 25: bull.append(f"Calm — annualised volatility {vol:.0f}%.")
    if vol > 40: bear.append(f"Volatile — {vol:.0f}% annualised; bigger swings, bigger risk.")
    if r > 75: bear.append(f"Overbought — RSI {r:.0f} (>75), stretched short-term.")
    elif r < 30: bear.append(f"Falling knife — RSI {r:.0f} (<30).")
    elif 45 <= r <= 68: bull.append(f"Healthy RSI ({r:.0f}) — trending, not overbought.")
    if ext > 22: bear.append(f"Extended — {ext:.0f}% above its 200-day avg; prone to mean-revert.")
    if net > 0: bull.append(f"News tone net-positive ({net:+d} across recent headlines).")
    elif net < 0: bear.append(f"News tone net-negative ({net:+d}).")

    verdict = "HOLD (bull case leads)" if len(bull) > len(bear) else ("WATCH (balanced/leaning bear)" if len(bull)==len(bear) else "CAUTION (bear case leads)")
    return {"last": last, "m3": m3, "vol": vol, "rsi": r, "sector": sec, "sec_rank": sr,
            "bull": bull, "bear": bear, "verdict": verdict, "net_news": net, "news": news[:2]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbol"); a = ap.parse_args()
    book = json.loads((CACHE/"paper_india_sector.json").read_text())
    holds = [s for s, p in book["positions"].items() if abs(p["qty"]) > 1e-9]
    if a.symbol:
        holds = [a.symbol.upper()+".NS" if not a.symbol.endswith(".NS") else a.symbol.upper()]
    allsyms = sorted({x for v in sectors.values() for x in v})
    secrank = sector_ranks(allsyms)
    px = close_matrix(load_prices(holds, start="2022-06-01"))
    lines = [f"# Bull & Bear research brief ({date.today()})", "",
             "**Information only.** Every point below is generated from a cited metric — no AI opinions. "
             "The engine's buy/sell decisions are unchanged; this is context for a human.", ""]
    for sym in holds:
        if sym not in px: continue
        nm = NAME.get(sym.replace(".NS",""), sym.replace(".NS",""))
        news = fetch(f"{nm} share stock", 3); time.sleep(0.3)
        b = brief_for(sym, px[sym], secrank, news)
        lines += [f"## {sym.replace('.NS','')}  —  {b['verdict']}",
                  f"_₹{b['last']:.0f} · {b['sector']} (sector rank #{b['sec_rank'][0]}/{b['sec_rank'][1]}) · 3-mo {b['m3']:+.0f}% · vol {b['vol']:.0f}% · RSI {b['rsi']:.0f}_", "",
                  "**Bull case**"] + [f"- ✓ {x}" for x in b["bull"]] + ["", "**Bear case**"] + [f"- ✗ {x}" for x in b["bear"]] + ["", "**In the news**"]
        for h in b["news"]:
            lines.append(f"- {senti(h['title'])} {h['title']}  _( {h['src']} )_")
        lines.append("")
        print(f"{sym.replace('.NS',''):12s} {b['verdict']:28s} bull {len(b['bull'])} / bear {len(b['bear'])}")
    (ROOT/"docs"/"RESEARCH_BRIEF.md").write_text("\n".join(lines))
    print("\nwrote docs/RESEARCH_BRIEF.md")


if __name__ == "__main__":
    main()
