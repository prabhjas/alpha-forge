#!/usr/bin/env python
"""Multi-sector stock strength analysis -> docs/SECTOR_ANALYSIS.md
Scans EVERY sector and every liquid F&O stock we track, ranks sectors by strength,
ranks stocks within them, and flags which are in a real uptrend. This is the
'where is the money moving across sectors' view — not just the index."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import yaml

from alpha_forge.data.loader import ROOT, close_matrix, load_prices

with open(ROOT / "config" / "sectors.yaml") as fh:
    SECTORS = yaml.safe_load(fh)

all_syms = sorted({s for v in SECTORS.values() for s in v})
prices = load_prices(all_syms, start="2023-01-01", use_cache=False)
c = close_matrix(prices)

def metrics(sym):
    px = c[sym].dropna()
    if len(px) < 200:
        return None
    mom6 = px.iloc[-1]/px.iloc[-126]-1
    mom3 = px.iloc[-1]/px.iloc[-63]-1
    mom1 = px.iloc[-1]/px.iloc[-21]-1
    above200 = px.iloc[-1] > px.rolling(200).mean().iloc[-1]
    vol = px.pct_change().rolling(21).std().iloc[-1]*np.sqrt(252)
    return dict(mom6=mom6*100, mom3=mom3*100, mom1=mom1*100, up=above200, vol=vol*100, last=px.iloc[-1])

rows = []
for sec, syms in SECTORS.items():
    for s in syms:
        m = metrics(s)
        if m:
            rows.append({"sector": sec, "stock": s.replace(".NS",""), **m})
df = pd.DataFrame(rows)

# sector ranking by median 3M momentum + % of names in uptrend
sec_rank = df.groupby("sector").agg(
    med_mom3=("mom3","median"), med_mom6=("mom6","median"),
    pct_uptrend=("up", lambda x: x.mean()*100), n=("stock","size")
).sort_values("med_mom3", ascending=False).round(1)

md = [f"# Multi-sector stock strength ({date.today()})", "",
      f"Scanned {len(df)} liquid F&O stocks across {df.sector.nunique()} sectors. "
      "Momentum = price change; 'uptrend' = above 200-day average. This is the sector-rotation view.", "",
      "## Sector ranking (strongest first)", "",
      sec_rank.to_markdown(), "",
      "## Strongest stocks overall (in an uptrend, ranked by 3-month momentum)", ""]
strong = df[df.up].sort_values("mom3", ascending=False).head(15)
md += [strong[["sector","stock","mom3","mom6","mom1","vol","last"]].round(1).to_markdown(index=False), "",
       "## Weakest stocks (avoid / short candidates when we can short)", ""]
weak = df[~df.up].sort_values("mom3").head(10)
md += [weak[["sector","stock","mom3","mom6","mom1","vol","last"]].round(1).to_markdown(index=False), "",
       "## How the engine uses this", "",
       "* We already hold the Nifty 50 across ALL these sectors in the cash market. This report shows WHERE the strength is so allocation tilts toward strong sectors and away from weak ones.",
       "* Stock F&O options come only at Phase 4 (needs ~Rs 20 lakh/lot capacity). Until then we express these views by BUYING THE STOCK, which captures the same direction without option decay or lot-size problems."]
Path("docs/SECTOR_ANALYSIS.md").write_text("\n".join(md))
print(sec_rank.to_string())
print("\nTop 8 stocks in uptrend by 3M momentum:")
print(strong[["sector","stock","mom3","mom6","up"]].head(8).round(1).to_string(index=False))
print("\nwrote docs/SECTOR_ANALYSIS.md")
