#!/usr/bin/env python
"""Market news-context digest -> docs/NEWS_DIGEST.md  (INFORMATION ONLY, never a trade trigger)

Pulls fresh headlines from Google News RSS (free, no key): overall market, plus
one query per stock the engine currently holds. Groups by holding, dedupes,
and adds a NAIVE keyword sentiment tag (clearly labelled as rough). The engine
does NOT act on this — it sits next to the sector report so a human sees what's
driving moves. Deterministic: no LLM in the loop.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feedparser

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data_cache"

POS = {"surge","jump","gain","rally","rise","beat","record","high","upgrade","profit","strong","boost","soar","top","buy","bullish","outperform"}
NEG = {"fall","drop","slump","plunge","loss","miss","cut","downgrade","weak","crash","decline","slip","fear","sell","bearish","warn","probe","fraud","ban","default"}

NAME = {  # ticker (no .NS) -> better search term
    "RELIANCE":"Reliance Industries","TCS":"TCS","INFY":"Infosys","HDFCBANK":"HDFC Bank","ICICIBANK":"ICICI Bank",
    "SBIN":"SBI","BAJFINANCE":"Bajaj Finance","BAJAJFINSV":"Bajaj Finserv","SHRIRAMFIN":"Shriram Finance",
    "TITAN":"Titan Company","CIPLA":"Cipla","DIVISLAB":"Divis Labs","NESTLEIND":"Nestle India","INDUSINDBK":"IndusInd Bank",
    "HINDALCO":"Hindalco","JSWSTEEL":"JSW Steel","TATASTEEL":"Tata Steel","ADANIENT":"Adani Enterprises","ADANIPORTS":"Adani Ports",
    "BAJAJ-AUTO":"Bajaj Auto","MARUTI":"Maruti Suzuki","LT":"Larsen Toubro","BHARTIARTL":"Bharti Airtel","AXISBANK":"Axis Bank",
    "KOTAKBANK":"Kotak Bank","SUNPHARMA":"Sun Pharma","ULTRACEMCO":"UltraTech Cement","TRENT":"Trent",
}


def fetch(query: str, n: int = 6):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        feed = feedparser.parse(data)
        out = []
        for e in feed.entries[:n]:
            src = e.get("source", {}).get("title", "") if hasattr(e, "source") else ""
            out.append({"title": e.title, "src": src, "when": e.get("published", "")[:16]})
        return out
    except Exception as ex:
        return [{"title": f"[feed error: {type(ex).__name__}]", "src": "", "when": ""}]


def senti(title: str) -> str:
    t = title.lower()
    p = sum(w in t for w in POS); n = sum(w in t for w in NEG)
    return "▲" if p > n else ("▼" if n > p else "·")


def current_holdings():
    syms = set()
    for f in ["paper_india_sector.json", "paper_india_paper.json", "paper_india_ensemble.json"]:
        p = CACHE / f
        if p.exists():
            d = json.loads(p.read_text())
            syms |= {s.replace(".NS", "") for s, pos in d["positions"].items() if abs(pos["qty"]) > 1e-9}
    return sorted(syms)


def main():
    lines = [f"# Market news-context digest — {datetime.now():%a %d %b %Y %H:%M}", "",
             "**Information only. The engine does NOT trade on news.** Sentiment tags (▲ up / ▼ down / · neutral) are a naive keyword heuristic, not analysis.", "",
             "## Overall market", ""]
    for h in fetch("Nifty 50 Sensex Indian stock market", 6):
        lines.append(f"- {senti(h['title'])} {h['title']}  _( {h['src']} )_")
    lines += ["", "## Macro & events (RBI, inflation, FII flows, crude)", ""]
    for h in fetch("India RBI inflation FII crude rupee markets", 5):
        lines.append(f"- {senti(h['title'])} {h['title']}  _( {h['src']} )_")

    holds = current_holdings()
    lines += ["", f"## Headlines for our current holdings ({len(holds)} names)", ""]
    for sym in holds:
        q = NAME.get(sym, sym)
        items = fetch(f"{q} share stock", 3)
        tag = "".join(senti(i["title"]) for i in items)
        lines.append(f"### {sym}  {tag}")
        for h in items:
            lines.append(f"- {senti(h['title'])} {h['title']}  _( {h['src']} )_")
        lines.append("")
        time.sleep(0.4)  # be gentle on the feed

    lines += ["---", "_Use this to understand WHY a holding moved, and to spot event risk (results, regulatory, macro). "
              "Buy/sell decisions stay with the tested engine + risk manager._"]
    out = CACHE / f"news_{date.today():%Y%m%d}.md"
    out.write_text("\n".join(lines))
    (ROOT / "docs" / "NEWS_DIGEST.md").write_text("\n".join(lines))
    print("\n".join(lines[:22]))
    print(f"\n... wrote docs/NEWS_DIGEST.md ({len(holds)} holdings covered)")


if __name__ == "__main__":
    main()
