#!/usr/bin/env python
"""PAPER test of the idea: buy ATM call options on many stocks on a momentum signal,
hold a few days, then sell. Prices options with Black-Scholes (IV = realised vol),
charges realistic option costs (wide bid-ask spread + STT/brokerage on premium).
No real money, no capital needed — this just answers 'does it work?' with data.
"""
from __future__ import annotations
import sys, warnings
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from math import log, sqrt, exp, erf
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices

def N(x): return 0.5*(1+erf(x/sqrt(2)))
def bs_call(S,K,T,sigma,r=0.065):
    if T<=0 or sigma<=0: return max(S-K,0.0)
    d1=(log(S/K)+(r+0.5*sigma*sigma)*T)/(sigma*sqrt(T)); d2=d1-sigma*sqrt(T)
    return S*N(d1)-K*exp(-r*T)*N(d2)

# parameters of the idea
DTE0=25/252.0          # buy ~25 trading days to expiry (monthly options)
MAX_HOLD=5             # hold up to 5 days (user's "hold a few days")
TARGET=0.5; STOP=-0.5  # exit at +50% or -50% on the premium
HALF_SPREAD=0.02       # options bid-ask ~4% wide -> 2% each side
PREM_COST=0.01         # STT+brokerage on premium, round trip approx

def run(universe):
    px=close_matrix(load_prices(UNIVERSES[universe],start="2019-01-01"))
    trades=[]
    for sym in px.columns:
        s=px[sym].dropna()
        if len(s)<260: continue
        vol=s.pct_change().rolling(20).std()*np.sqrt(252)
        hi20=s.rolling(20).max()
        sma200=s.rolling(200).mean()
        i=210
        while i < len(s)-MAX_HOLD-1:
            # signal: fresh 20-day breakout in an uptrend (classic momentum entry)
            if s.iloc[i]>=hi20.iloc[i-1] and s.iloc[i]>sma200.iloc[i] and vol.iloc[i]>0:
                S0=s.iloc[i]; K=round(S0)  # ATM
                iv=float(vol.iloc[i])*1.05
                entry=bs_call(S0,K,DTE0,iv)*(1+HALF_SPREAD)*(1+PREM_COST)
                if entry<=0: i+=1; continue
                exitp=None
                for h in range(1,MAX_HOLD+1):
                    S=s.iloc[i+h]; T=DTE0-h/252.0
                    val=bs_call(S,K,T,iv)
                    ret=val/entry-1
                    if ret>=TARGET or ret<=STOP or h==MAX_HOLD:
                        exitp=val*(1-HALF_SPREAD)*(1-PREM_COST); held=h; break
                r=exitp/entry-1
                trades.append({"sym":sym,"ret":r,"held":held})
                i+=MAX_HOLD  # no overlapping trade per name
            i+=1
    t=pd.DataFrame(trades)
    return t

for uni in ["nifty50"]:
    t=run(uni)
    if t.empty: print("no trades"); continue
    wins=(t.ret>0).mean()
    avg=t.ret.mean(); med=t.ret.median()
    # equal risk per trade: risk 5% of a notional book per option trade
    total=(1+t.ret*1.0).prod()  # if you rolled full stake each trade (illustrative)
    pf=t.ret[t.ret>0].sum()/max(1e-9,-t.ret[t.ret<0].sum())
    print(f"=== BUY-ATM-CALL, hold<= {MAX_HOLD}d, {uni} (2019-2026), costs on ===")
    print(f"  trades: {len(t)}  win rate: {wins:.1%}  avg/trade: {avg:+.1%}  median: {med:+.1%}  profit factor: {pf:.2f}")
    print(f"  best: {t.ret.max():+.0%}  worst: {t.ret.min():+.0%}  avg days held: {t.held.mean():.1f}")
    print(f"  expectancy per trade after costs: {avg:+.1%}  -> options-buying edge is {'POSITIVE' if avg>0 else 'NEGATIVE'}")
    # compare: same signal but BUY THE STOCK, hold 5d
    px=close_matrix(load_prices(UNIVERSES[uni],start="2019-01-01"))
    strk=[]
    for sym in px.columns:
        s=px[sym].dropna()
        if len(s)<260: continue
        hi20=s.rolling(20).max(); sma=s.rolling(200).mean()
        for i in range(210,len(s)-6):
            if s.iloc[i]>=hi20.iloc[i-1] and s.iloc[i]>sma.iloc[i]:
                strk.append(s.iloc[i+5]/s.iloc[i]-1-0.0019*2)  # 5d stock hold, delivery costs
    strk=pd.Series(strk)
    print(f"  SAME signal, BUY THE STOCK hold 5d: win {(strk>0).mean():.1%}  avg {strk.mean():+.2%}  (this is what we do now)")
