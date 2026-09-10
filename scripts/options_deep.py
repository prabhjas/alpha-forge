#!/usr/bin/env python
"""Deep options analysis — all four quadrants, calls & puts, buying & selling.
Black-Scholes pricing (IV=realised vol), realistic costs (~4% option spread + fees).
Nifty 50 stocks, 2018-2026. Answers: which options strategy, if any, has an edge?"""
from __future__ import annotations
import sys, warnings
from math import log, sqrt, exp, erf
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.backtest.metrics import performance_summary

def Nn(x): return 0.5*(1+erf(x/sqrt(2)))
def d1d2(S,K,T,s,r=0.065):
    d1=(log(S/K)+(r+0.5*s*s)*T)/(s*sqrt(T)); return d1,d1-s*sqrt(T)
def bs_call(S,K,T,s,r=0.065):
    if T<=0 or s<=0: return max(S-K,0.0)
    d1,d2=d1d2(S,K,T,s,r); return S*Nn(d1)-K*exp(-r*T)*Nn(d2)
def bs_put(S,K,T,s,r=0.065):
    if T<=0 or s<=0: return max(K-S,0.0)
    d1,d2=d1d2(S,K,T,s,r); return K*exp(-r*T)*Nn(-d2)-S*Nn(-d1)

HALF=0.02; FEE=0.01; MDTE=21  # ~1-month options, 21 trading days
px=close_matrix(load_prices(UNIVERSES["nifty50"],start="2018-01-01"))
syms=[s for s in px.columns if px[s].dropna().shape[0]>500]

def realized(s,i,w=20): 
    v=s.pct_change().iloc[i-w:i].std()*np.sqrt(252); return float(v) if v>0 else 0.25

# ---- BUYING (directional, hold 5d) ----
def buy_dir(kind):
    trades=[]
    for sym in syms:
        s=px[sym].dropna(); 
        if len(s)<260: continue
        hi=s.rolling(20).max(); lo=s.rolling(20).min(); sma=s.rolling(200).mean()
        i=210
        while i<len(s)-6:
            up=s.iloc[i]>sma.iloc[i]
            sig = (s.iloc[i]>=hi.iloc[i-1] and up) if kind=="call" else (s.iloc[i]<=lo.iloc[i-1] and not up)
            if sig:
                S0=s.iloc[i];K=round(S0);iv=realized(s,i)*1.05;T=25/252
                price=(bs_call if kind=="call" else bs_put)(S0,K,T,iv)
                entry=price*(1+HALF)*(1+FEE)
                if entry>0:
                    S1=s.iloc[i+5];val=(bs_call if kind=="call" else bs_put)(S1,K,T-5/252,iv)
                    exitp=val*(1-HALF)*(1-FEE);trades.append(exitp/entry-1)
                i+=6
            i+=1
    t=pd.Series(trades)
    return {"n":len(t),"win":(t>0).mean(),"avg":t.mean(),"median":t.median(),
            "pf":t[t>0].sum()/max(1e-9,-t[t<0].sum())}

# ---- SELLING (monthly income), portfolio of stocks ----
def sell_premium(kind, otm=0.05):
    # per stock: monthly cycle; portfolio = equal-weight mean of monthly returns
    monthly={}
    for sym in syms:
        s=px[sym].dropna()
        if len(s)<260: continue
        i=210
        while i<len(s)-MDTE:
            S0=s.iloc[i];iv=realized(s,i);T=MDTE/252
            if kind=="covered_call":
                K=round(S0*(1+otm));prem=bs_call(S0,K,T,iv)*(1-HALF)*(1-FEE)
                S1=s.iloc[i+MDTE];ret=(S1-S0-max(S1-K,0)+prem)/S0   # own stock + short call
            else: # cash_secured_put
                K=round(S0*(1-otm));prem=bs_put(S0,K,T,iv)*(1-HALF)*(1-FEE)
                S1=s.iloc[i+MDTE];ret=(prem-max(K-S1,0))/S0          # collateral ~S0
            monthly.setdefault(i//MDTE,[]).append(ret)
            i+=MDTE
    port=pd.Series({k:np.mean(v) for k,v in monthly.items()}).sort_index()
    # annualize from ~monthly series
    yrs=len(port)/12
    cagr=(1+port).prod()**(1/max(yrs,1e-9))-1
    vol=port.std()*np.sqrt(12); sh=(port.mean()*12)/vol if vol>0 else np.nan
    eq=(1+port).cumprod(); dd=(eq/eq.cummax()-1).min()
    return {"cagr":cagr*100,"sharpe":sh,"maxdd":dd*100,"win_mo":(port>0).mean()*100,"n_mo":len(port)}

# buy-and-hold benchmark (same stocks, equal weight)
bh=performance_summary(px[syms].pct_change().mean(axis=1).dropna())

print("=== BUYING options (directional, hold 5d, costs on) ===")
for k in ["call","put"]:
    r=buy_dir(k)
    print(f"  BUY {k:4s}: {r['n']} trades  win {r['win']:.1%}  avg/trade {r['avg']:+.1%}  median {r['median']:+.1%}  PF {r['pf']:.2f}  -> {'EDGE' if r['avg']>0 else 'LOSES'}")
print("\n=== SELLING premium (monthly income, portfolio, costs on) ===")
for k,lbl in [("covered_call","Covered call (own stock, sell 5% OTM call)"),("cash_secured_put","Cash-secured put (sell 5% OTM put)")]:
    r=sell_premium(k)
    print(f"  {lbl}\n     CAGR {r['cagr']:.1f}%  Sharpe {r['sharpe']:.2f}  MaxDD {r['maxdd']:.1f}%  win-months {r['win_mo']:.0f}%")
print(f"\n  Benchmark BUY & HOLD stock: CAGR {bh['cagr_pct']}%  Sharpe {bh['sharpe']}  MaxDD {bh['max_drawdown_pct']}%")
