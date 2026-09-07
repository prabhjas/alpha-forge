#!/usr/bin/env python
"""Combined view: the sector-tilt book's holdings + news for each -> docs/HOLDINGS_NEWS.md"""
from __future__ import annotations
import json, sys, time, urllib.parse, urllib.request, warnings
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, yaml, feedparser
from alpha_forge.data.loader import ROOT, UNIVERSES, close_matrix, load_prices
from scripts.news_digest import NAME, senti, fetch

acct = ROOT / "data_cache" / "paper_india_sector.json"
book = json.loads(acct.read_text())
pos = {s: p for s, p in book["positions"].items() if abs(p["qty"]) > 1e-9}
sectors = yaml.safe_load(open(ROOT / "config" / "sectors.yaml"))
sec_of = {s: sec for sec, syms in sectors.items() for s in syms}

prices = load_prices(list(pos), start="2023-06-01", use_cache=False)
c = close_matrix(prices)
last = c.ffill().iloc[-1]

def news_score(sym):
    items = fetch(f"{NAME.get(sym, sym)} share stock", 3)
    net = sum({"▲":1,"▼":-1,"·":0}[senti(i["title"])] for i in items)
    return net, items

rows = []
news_cache = {}
mv_total = sum(pos[s]["qty"] * float(last.get(s, pos[s]["avg_price"])) for s in pos)
for s in pos:
    px = c[s].dropna()
    mom3 = (px.iloc[-1]/px.iloc[-63]-1)*100 if len(px) > 63 else np.nan
    up = px.iloc[-1] > px.rolling(200).mean().iloc[-1] if len(px) > 200 else np.nan
    mv = pos[s]["qty"] * float(last.get(s, pos[s]["avg_price"]))
    sym = s.replace(".NS","")
    net, items = news_score(sym); news_cache[sym] = items
    # FLAG: held (trend up) but momentum negative AND news net-negative -> shaky/watch
    if not up:
        flag = "✖ exiting (trend down)"
    elif (mom3 is not None and mom3 < 0) and net < 0:
        flag = "⚠ SHAKY (mom- & news-)"
    elif (mom3 is not None and mom3 < 0) or net < 0:
        flag = "○ watch"
    else:
        flag = "ok"
    rows.append({"stock": sym, "sector": sec_of.get(s,"?"),
                 "wt%": round(mv/mv_total*100,1), "qty": round(pos[s]["qty"]),
                 "last": round(float(last.get(s, np.nan)),1), "mom3%": round(mom3,1),
                 "trend": "up" if up else "down", "news": {1:"+",0:"0",-1:"-"}.get(max(-1,min(1,net)),str(net)), "flag": flag}); import time as _t; _t.sleep(0.3)
df = pd.DataFrame(rows).sort_values("wt%", ascending=False)

shaky = df[df["flag"].str.contains("SHAKY")]["stock"].tolist()
watch = df[df["flag"].str.contains("watch")]["stock"].tolist()
lines = [f"# Sector-tilt book — holdings + news ({datetime.now():%a %d %b %Y %H:%M})", "",
         f"**⚠ Shaky (trend up but momentum AND news negative): {', '.join(shaky) or 'none'}**",
         f"○ Watch (one of momentum/news negative): {', '.join(watch) or 'none'}", "",
         "Book: `india_sector` (sector_ensemble). Info-only news; engine does not trade on it.", "",
         "## Holdings", "", df.to_markdown(index=False), "",
         "## Latest headline per holding", ""]
for _, r in df.iterrows():
    sym = r["stock"]; items = news_cache.get(sym, [])[:2]
    lines.append(f"**{sym}** ({r['sector']}, {r['wt%']}%, trend {r['trend']}, {r['flag']})")
    for h in items:
        lines.append(f"- {senti(h['title'])} {h['title']}  _( {h['src']} )_")
    lines.append("")

# sector concentration
bysec = df.groupby("sector")["wt%"].sum().sort_values(ascending=False)
lines += ["## Sector concentration", "", bysec.round(1).to_markdown(), ""]
out = ROOT / "docs" / "HOLDINGS_NEWS.md"
out.write_text("\n".join(lines))
print("\n".join([f"# Sector-tilt book — {len(df)} holdings"] + [""] + [df.to_markdown(index=False)]))
print("\nSector concentration:"); print(bysec.round(1).to_string())
print("\nwrote docs/HOLDINGS_NEWS.md")
