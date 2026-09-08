#!/usr/bin/env python
"""Idempotent catch-up: whenever the Mac wakes, run any of today's scheduled jobs
that were missed (because the Mac was asleep at the scheduled minute). Safe to run
repeatedly — each job runs at most once per day, only if its output for today is absent
and its scheduled time has passed. Wired to launchd with RunAtLoad + every-30-min."""
from __future__ import annotations
import subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data_cache"
PY = str(ROOT / ".venv313" / "bin" / "python")
LOG = CACHE / "logs" / "catch_up.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
now = datetime.now()
today = now.strftime("%Y%m%d")
dow = now.isoweekday()  # 1=Mon..7=Sun


def log(msg): 
    with open(LOG, "a") as f: f.write(f"{now:%Y-%m-%d %H:%M} {msg}\n")


def ran_today(glob_pat: str) -> bool:
    return any(today in p.name for p in CACHE.glob(glob_pat)) or \
           any(today in p.name for p in (CACHE / "runs").glob(glob_pat)) if (CACHE/"runs").exists() else \
           any(today in p.name for p in CACHE.glob(glob_pat))


def run(cmd, label):
    log(f"CATCH-UP running {label}: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=str(ROOT), timeout=900,
                       stdout=open(CACHE/"logs"/f"catchup_{label}.out","a"),
                       stderr=subprocess.STDOUT)
        log(f"  {label} done")
    except Exception as e:
        log(f"  {label} FAILED {e}")


def report_exists_today(substr: str) -> bool:
    d = CACHE / "runs"
    return d.exists() and any(today in p.name and substr in p.name for p in d.glob("*.json"))


jobs = []
# news 08:15 -> file news_YYYYMMDD.md
if now.hour*60+now.minute >= 8*60+15 and not (CACHE/f"news_{today}.md").exists():
    jobs.append(([PY, "scripts/news_digest.py"], "news"))
# brief 08:30 -> brief_latest.md mtime today
brief = CACHE/"brief_latest.md"
if now.hour*60+now.minute >= 8*60+30 and not (brief.exists() and datetime.fromtimestamp(brief.stat().st_mtime).strftime("%Y%m%d")==today):
    jobs.append(([PY, "scripts/morning_brief.py"], "brief"))
# India market run 16:00 Mon-Fri -> a run report dated today for an india universe
if dow <= 5 and now.hour >= 16 and not report_exists_today("india"):
    jobs.append((["/bin/zsh", "scripts/daily.sh", "india"], "india"))
# US run 03:00 Tue-Sat -> a us_core run report dated today
if 2 <= dow <= 6 and now.hour >= 3 and not report_exists_today("us_core"):
    jobs.append((["/bin/zsh", "scripts/daily.sh", "us"], "us"))
# dashboard 17:00 -> dashboard.html mtime today
dash = ROOT/"dashboard.html"
if now.hour >= 17 and not (dash.exists() and datetime.fromtimestamp(dash.stat().st_mtime).strftime("%Y%m%d")==today):
    jobs.append(([PY, "scripts/dashboard.py"], "dashboard"))

if not jobs:
    log("nothing to catch up")
for cmd, label in jobs:
    run(cmd, label)
