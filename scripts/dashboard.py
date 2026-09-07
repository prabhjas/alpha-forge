#!/usr/bin/env python
"""Generate a self-contained dashboard.html snapshot of the whole system."""
from __future__ import annotations
import json, subprocess, sys, warnings
from datetime import datetime, date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, yaml
from alpha_forge.data.loader import ROOT, UNIVERSES, close_matrix, load_prices

CACHE = ROOT / "data_cache"
sectors = yaml.safe_load(open(ROOT / "config" / "sectors.yaml"))
sec_of = {s: sec for sec, syms in sectors.items() for s in syms}

# --- market regime ---
nifty = close_matrix(load_prices(UNIVERSES["india_benchmark"], start="2024-06-01", use_cache=False)).iloc[:,0].dropna()
sma200 = nifty.rolling(200).mean().iloc[-1]
regime = "uptrend" if nifty.iloc[-1] > sma200 else "downtrend"
mkt = {"nifty": round(float(nifty.iloc[-1])), "sma200": round(float(sma200)),
       "regime": regime, "chg1d": round(float(nifty.iloc[-1]/nifty.iloc[-2]-1)*100,2),
       "chg1m": round(float(nifty.iloc[-1]/nifty.iloc[-22]-1)*100,1), "asof": str(nifty.index[-1].date())}

# --- paper books ---
def equity(path):
    d = json.loads(path.read_text())
    pos = {s:p for s,p in d["positions"].items() if abs(p["qty"])>1e-9}
    mv=0.0
    if pos:
        px = close_matrix(load_prices(list(pos), start=(date.today()-timedelta(days=10)).isoformat(), use_cache=False)).ffill().iloc[-1]
        mv = sum(p["qty"]*float(px.get(s,p["avg_price"])) for s,p in pos.items())
    return round(d["cash"]+mv,2), len(pos)
books=[]
LABEL={"india_sector":"Sector engine (Nifty 50)","india_paper":"Trend (ETFs)","india_ensemble":"Ensemble (ETFs)",
       "india_ab_trend":"A/B trend (Nifty 50)","india_ab_hrp":"A/B risk-parity (Nifty 50)","us_paper":"Ensemble (US)"}
for p in sorted(CACHE.glob("paper_*.json")):
    a=p.stem.replace("paper_",""); eq,n=equity(p); start=570 if a=="us_paper" else 50000
    books.append({"acct":a,"label":LABEL.get(a,a),"equity":eq,"start":start,
                  "pnl_pct":round((eq/start-1)*100,2),"positions":n,"ccy":"$" if a=="us_paper" else "₹"})

# --- sector-tilt holdings + flags (momentum/trend based, fast) ---
book = json.loads((CACHE/"paper_india_sector.json").read_text())
pos = {s:p for s,p in book["positions"].items() if abs(p["qty"])>1e-9}
c = close_matrix(load_prices(list(pos), start="2023-06-01", use_cache=False)); last=c.ffill().iloc[-1]
mv_total = sum(pos[s]["qty"]*float(last.get(s,pos[s]["avg_price"])) for s in pos)
holds=[]
for s in pos:
    px=c[s].dropna(); mom3=float(px.iloc[-1]/px.iloc[-63]-1)*100 if len(px)>63 else 0
    up = bool(px.iloc[-1]>px.rolling(200).mean().iloc[-1]) if len(px)>200 else True
    mv=pos[s]["qty"]*float(last.get(s,pos[s]["avg_price"]))
    flag = "exiting" if not up else ("shaky" if mom3<0 else "ok")
    holds.append({"stock":s.replace(".NS",""),"sector":sec_of.get(s,"?"),"wt":round(mv/mv_total*100,1),
                  "mom3":round(mom3,1),"trend":"up" if up else "down","flag":flag})
holds.sort(key=lambda h:-h["wt"])

# --- sector strength ---
allsyms=sorted({x for v in sectors.values() for x in v})
ca=close_matrix(load_prices(allsyms,start="2024-06-01",use_cache=False))
secrows=[]
for sec,syms in sectors.items():
    ms=[]
    for s in syms:
        px=ca.get(s)
        if px is not None and px.notna().sum()>63: ms.append(float(px.dropna().iloc[-1]/px.dropna().iloc[-63]-1)*100)
    if ms: secrows.append({"sector":sec,"mom3":round(float(np.median(ms)),1)})
secrows.sort(key=lambda r:-r["mom3"])

# --- activity (git) & retired ---
log = subprocess.run(["git","log","--pretty=%s|%ad","--date=format:%d %b","-16"],capture_output=True,text=True,cwd=ROOT).stdout.strip().split("\n")
activity=[{"msg":l.split("|")[0],"date":l.split("|")[1]} for l in log if "|" in l]
retired=[("Mean reversion (India)","loses after costs"),("Pairs / stat-arb","−5.7%/yr after retail costs"),
         ("SMA 6/30 crossover","churns 30–40×/yr, underperforms"),("FVG (fair value gap)","69 trades/yr, −30% DD")]

DATA={"generated":datetime.now().strftime("%a %d %b %Y, %H:%M IST"),"mkt":mkt,"books":books,"holds":holds,
      "sectors":secrows,"activity":activity,"retired":retired,
      "confidence":[{"q":"System is sound & safe","p":85},{"q":"Beats the index over 3 yrs","p":62},
                    {"q":"Profitable year","p":88},{"q":"No untouched-share risk","p":100}],
      "phase":"Paper trading — proving the engine","day": (date.today()-date(2026,9,5)).days + 1}

TEMPLATE = (ROOT / "scripts" / "dashboard_template.html").read_text()
html = TEMPLATE.replace("__DATA__", json.dumps(DATA))
(ROOT/"dashboard.html").write_text(html)
print(f"wrote dashboard.html  ({len(books)} books, {len(holds)} holdings, regime={regime})")
