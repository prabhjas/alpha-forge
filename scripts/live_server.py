#!/usr/bin/env python
"""Live dashboard server — real-time prices from AngelOne, auto-refreshing page.

  .venv313/bin/python scripts/live_server.py     then open  http://localhost:8787

Serves '/' (the page) and '/api/data' (JSON the page polls every 15s). AngelOne
session is created ONCE at startup and reused. Live prices power the India books,
holdings, and market pulse; the US book shows last close (AngelOne can't price US).
Slow analytics (sectors, activity) load once. Stdlib only — no extra deps.
"""
from __future__ import annotations
import json, sys, time, warnings, threading
from datetime import datetime, date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); warnings.filterwarnings("ignore")
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
import yaml
from alpha_forge.data.loader import CACHE_DIR as _CD  # noqa
from alpha_forge.data.loader import ROOT as AR, close_matrix, load_prices

CACHE = AR / "data_cache"
PORT = 8787
LABEL={"india_sector":"Sector engine (Nifty 50)","india_paper":"Trend (ETFs)","india_ensemble":"Ensemble (ETFs)",
       "india_ab_trend":"A/B trend (Nifty 50)","india_ab_hrp":"A/B risk-parity (Nifty 50)","us_paper":"Ensemble (US)"}

_broker=None; _lock=threading.Lock(); _price_cache={"t":0,"px":{}}
_flag_cache={"t":0,"flags":{}}

def daily_flags(symbols):
    """mom3 + trend flag per symbol, from daily closes. Cached 10 min (slow to compute)."""
    symbols=list(symbols)
    now=time.time()
    if now-_flag_cache["t"]<600 and all(s in _flag_cache["flags"] for s in symbols):
        return dict(_flag_cache["flags"])
    out=dict(_flag_cache["flags"])
    try:
        c=close_matrix(load_prices(symbols, start="2023-06-01"))
        for s in symbols:
            px=c[s].dropna() if s in c else None
            if px is None or len(px)<200:
                out[s]={"mom3":0.0,"flag":"ok"}; continue
            mom3=float(px.iloc[-1]/px.iloc[-63]-1)*100
            up=bool(px.iloc[-1]>px.rolling(200).mean().iloc[-1])
            flag="exiting" if not up else ("shaky" if mom3<0 else "ok")
            out[s]={"mom3":round(mom3,1),"flag":flag}
        _flag_cache["t"]=now; _flag_cache["flags"]=out
    except Exception:
        pass
    return out

def broker():
    global _broker
    if _broker is None:
        from alpha_forge.brokers.angelone_broker import AngelOneBroker
        _broker = AngelOneBroker(live=False)
    return _broker

def live_prices(symbols):
    """Cache LTPs for 15s so polling never hammers the API."""
    now=time.time()
    with _lock:
        if now-_price_cache["t"]<15 and all(s in _price_cache["px"] for s in symbols):
            return dict(_price_cache["px"])
        px=dict(_price_cache["px"])
        try:
            b=broker()
            for s in symbols:
                try: px[s]=b.last_price(s)
                except Exception: pass
            _price_cache["t"]=now; _price_cache["px"]=px
        except Exception:
            pass
        return px

def prev_close_map(symbols):
    if not symbols: return {}
    c=close_matrix(load_prices(symbols, start=(date.today()-timedelta(days=12)).isoformat()))
    return {s: float(c[s].dropna().iloc[-1]) for s in symbols if s in c and c[s].notna().any()}

def payload():
    india_books=[p for p in sorted(CACHE.glob("paper_*.json"))]
    held=set()
    book_pos={}
    for p in india_books:
        d=json.loads(p.read_text()); a=p.stem.replace("paper_","")
        pos={s:v for s,v in d["positions"].items() if abs(v["qty"])>1e-9}
        book_pos[a]=(d["cash"],pos)
        if a!="us_paper": held|=set(pos)
    lp=live_prices((held | {"NIFTYBEES.NS"}) if held else {"NIFTYBEES.NS"})
    prev=prev_close_map(sorted(held|{"NIFTYBEES.NS"}))
    books=[]
    for a,(cash,pos) in book_pos.items():
        use_live = a!="us_paper"
        mv=0.0
        for s,v in pos.items():
            px = lp.get(s) if use_live else None
            if px is None: px = prev.get(s, v["avg_price"])
            mv+=v["qty"]*px
        start=570 if a=="us_paper" else 50000; eq=cash+mv
        books.append({"acct":a,"label":LABEL.get(a,a),"equity":round(eq,2),"pnl_pct":round((eq/start-1)*100,2),
                      "positions":len(pos),"ccy":"$" if a=="us_paper" else "₹","live":use_live})
    books.sort(key=lambda b:(b["ccy"]=="$", -b["equity"]))
    # market pulse via NIFTYBEES live
    nb=lp.get("NIFTYBEES.NS"); nbp=prev.get("NIFTYBEES.NS")
    pulse={"px":round(nb,2) if nb else None,"chg":round((nb/nbp-1)*100,2) if nb and nbp else None}
    # sector-tilt live holdings
    cash,pos=book_pos.get("india_sector",(0,{}))
    mvt=sum(v["qty"]*(lp.get(s) or prev.get(s,v["avg_price"])) for s,v in pos.items()) or 1
    flags=daily_flags(list(pos))
    holds=[]
    for s,v in pos.items():
        px=lp.get(s) or prev.get(s,v["avg_price"]); pc=prev.get(s,px)
        f=flags.get(s,{"mom3":0.0,"flag":"ok"})
        holds.append({"stock":s.replace(".NS",""),"px":round(px,1),"day":round((px/pc-1)*100,2),
                      "wt":round(v["qty"]*px/mvt*100,1),"live":s in lp,"mom3":f["mom3"],"flag":f["flag"]})
    holds.sort(key=lambda h:-h["wt"])
    shaky=[h["stock"] for h in holds if h["flag"]=="shaky"]
    exiting=[h["stock"] for h in holds if h["flag"]=="exiting"]
    return {"ts":datetime.now().strftime("%H:%M:%S"),"date":datetime.now().strftime("%a %d %b %Y"),
            "pulse":pulse,"books":books,"holds":holds,"shaky":shaky,"exiting":exiting,
            "market_open": _mkt_open()}

def _mkt_open():
    n=datetime.now(); return (n.isoweekday()<=5) and (9*60+15 <= n.hour*60+n.minute <= 15*60+30)

PAGE = """<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Alpha Forge · LIVE</title><style>
:root{--bg:#0e1319;--card:#161d26;--line:#28313f;--ink:#e7ecf3;--soft:#9aa6b6;--up:#43c07a;--down:#e8746f;--accent:#79a3d6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px -apple-system,system-ui,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:20px}
.top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:18px}
h1{font-size:22px;margin:0}.sub{color:var(--soft);font-size:12px;margin-top:3px}
.live{display:inline-flex;gap:7px;align-items:center;font-size:12px;font-weight:600;color:var(--up)}
.blink{width:8px;height:8px;border-radius:50%;background:var(--up);animation:b 1.4s infinite}@keyframes b{50%{opacity:.25}}
.closed .blink{background:var(--soft)}.closed{color:var(--soft)}
.mono{font-variant-numeric:tabular-nums;font-family:ui-monospace,Menlo,monospace}
.pulse{font-size:34px;font-weight:700}.up{color:var(--up)}.down{color:var(--down)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .l{color:var(--soft);font-size:12px;min-height:32px}.card .e{font-size:22px;font-weight:700;margin-top:4px}
.card .m{font-size:12px;color:var(--soft);display:flex;justify-content:space-between;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:8px}
th{text-align:left;color:var(--soft);font-size:11px;text-transform:uppercase;letter-spacing:.05em;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:8px;border-bottom:1px solid var(--line)}td.n{text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,monospace}
h2{font-size:13px;color:var(--soft);margin:22px 0 4px}.dim{opacity:.55}
.chip{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}
.chip.ok{background:#132a1e;color:var(--up)}.chip.shaky{background:#2a2213;color:#d8a445}.chip.exiting{background:#2c1a1a;color:var(--down)}
.banner{background:#2a2213;border:1px solid #4a3c1a;color:#e6c675;border-radius:10px;padding:10px 14px;font-size:13px;margin:14px 0}
.banner b{color:#f0d78a}.banner.hide{display:none}
</style></head><body><div class="wrap">
<div class="top"><div><h1>Alpha Forge · Live</h1><div class="sub" id="date"></div></div>
<div class="live" id="livebadge"><span class="blink"></span><span id="livetext">LIVE</span> · <span id="clock" class="mono"></span></div></div>
<div class="card" style="display:flex;gap:24px;align-items:center;flex-wrap:wrap">
<div><div class="sub">Nifty pulse (NIFTYBEES)</div><div class="pulse mono" id="pulse">—</div></div>
<div><div class="sub">Today</div><div class="mono" id="pchg" style="font-size:20px">—</div></div>
<div class="sub" id="note" style="max-width:360px"></div></div>
<div class="banner hide" id="shakybar"></div>
<h2>Paper books — equity at live prices</h2><div class="grid" id="books"></div>
<h2>Sector engine — live holdings</h2>
<div style="overflow-x:auto"><table><thead><tr><th>Stock</th><th class="n">Weight</th><th class="n">Price</th><th class="n">Today</th><th class="n">3-mo</th><th>Signal</th></tr></thead><tbody id="holds"></tbody></table></div>
<div class="sub" style="margin-top:6px">Signal: <b>ok</b> healthy · <b>shaky</b> trend up but momentum turned down (watch) · <b>exiting</b> trend broke, sells next rebalance.</div>
<div class="sub" style="margin-top:20px">Paper only · figures simulated · India live via AngelOne, US shows last close · refreshes every 15s</div>
</div><script>
const $=i=>document.getElementById(i);
const sg=v=>v==null?'—':(v>=0?'+':'')+v+'%',cl=v=>v==null?'':(v>=0?'up':'down');
async function tick(){try{const r=await fetch('/api/data',{cache:'no-store'});const d=await r.json();
 $('date').textContent=d.date;$('clock').textContent=d.ts;
 const lb=$('livebadge');if(d.market_open){lb.classList.remove('closed');$('livetext').textContent='LIVE';}else{lb.classList.add('closed');$('livetext').textContent='MARKET CLOSED';}
 $('pulse').textContent=d.pulse.px?('₹'+d.pulse.px):'—';
 $('pchg').innerHTML='<span class="'+cl(d.pulse.chg)+'">'+sg(d.pulse.chg)+'</span>';
 $('note').textContent=d.market_open?'Market open — prices update live.':'Market closed — showing last traded prices.';
 $('books').innerHTML=d.books.map(b=>`<div class="card ${b.live?'':'dim'}"><div class="l">${b.label}</div>
  <div class="e mono">${b.ccy}${b.equity.toLocaleString('en-IN')}</div>
  <div class="m"><span class="${cl(b.pnl_pct)}">${sg(b.pnl_pct)}</span><span>${b.positions} pos${b.live?'':' · EOD'}</span></div></div>`).join('');
 $('holds').innerHTML=d.holds.map(h=>`<tr><td>${h.stock}${h.live?'':' <span class=sub>EOD</span>'}</td>
  <td class="n">${h.wt}%</td><td class="n">₹${h.px}</td><td class="n ${cl(h.day)}">${sg(h.day)}</td>
  <td class="n ${cl(h.mom3)}">${sg(h.mom3)}</td><td><span class="chip ${h.flag}">${h.flag}</span></td></tr>`).join('');
 const sb=$('shakybar');
 if((d.shaky&&d.shaky.length)||(d.exiting&&d.exiting.length)){sb.classList.remove('hide');
   sb.innerHTML=(d.shaky.length?`⚠ <b>Shaky (watch):</b> ${d.shaky.join(', ')}. `:'')+(d.exiting.length?`✖ <b>Exiting:</b> ${d.exiting.join(', ')} (sells next rebalance).`:'');
 }else sb.classList.add('hide');
}catch(e){$('livetext').textContent='reconnecting…';}}
tick();setInterval(tick,15000);
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path.startswith("/api/data"):
            body=json.dumps(payload()).encode()
            self.send_response(200);self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
        else:
            body=PAGE.encode()
            self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)

if __name__=="__main__":
    print(f"Alpha Forge live dashboard -> http://localhost:{PORT}  (Ctrl-C to stop)")
    broker()  # login once up front
    ThreadingHTTPServer(("127.0.0.1",PORT),H).serve_forever()
