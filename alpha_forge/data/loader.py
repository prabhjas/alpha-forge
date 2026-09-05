"""Price data loading with a local cache.

Primary source is Yahoo Finance (free, delayed, good enough for research).
Broker feeds (Kite/SmartAPI/Alpaca) can be plugged in later via the same
return shape: {ticker: DataFrame[Open, High, Low, Close, Volume]}.
"""
from __future__ import annotations

import pickle
import time
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

with open(ROOT / "config" / "universes.yaml") as fh:
    UNIVERSES: Dict[str, List[str]] = yaml.safe_load(fh)

OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def _cache_path(tickers: Iterable[str], start: str, end: str, interval: str) -> Path:
    key = f"{'_'.join(sorted(tickers))}_{start}_{end}_{interval}"
    if len(key) > 150:  # keep filenames sane
        import hashlib
        key = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{key}.pkl"


def _download(tickers: List[str], start: str, end: str, interval: str) -> Dict[str, pd.DataFrame]:
    import yfinance as yf

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    out: Dict[str, pd.DataFrame] = {}
    if raw is None or raw.empty:
        return out
    if len(tickers) == 1:
        df = raw.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)
        out[tickers[0]] = df[OHLCV].dropna(how="all")
        return out
    for t in tickers:
        if t not in raw.columns.get_level_values(0):
            continue
        df = raw[t].copy()
        df = df[OHLCV].dropna(how="all")
        if len(df) > 0:
            out[t] = df
    return out


def clean_split_glitches(df: pd.DataFrame, lo: float = 0.2, hi: float = 5.0, window: int = 15) -> pd.DataFrame:
    """Yahoo occasionally leaves a stretch of bars un-adjusted around a split
    (e.g. NIFTYBEES 1:10 in Dec-2019 shows -90% then +900% four days later).
    A liquid stock/ETF never truly moves 5x in a day, so any such move is a data
    error. Paired move within `window` bars -> rescale the bars in between.
    Unpaired move -> treat as unadjusted split and back-adjust prior history."""
    df = df.copy()
    px = ["Open", "High", "Low", "Close"]
    ratio = df["Close"] / df["Close"].shift(1)
    flags = list(df.index[(ratio < lo) | (ratio > hi)])
    used = set()
    for i, ts in enumerate(flags):
        if ts in used:
            continue
        pos = df.index.get_loc(ts)
        r_i = ratio.iloc[pos]
        partner = None
        for ts2 in flags[i + 1:]:
            pos2 = df.index.get_loc(ts2)
            if pos2 - pos > window:
                break
            r_j = ratio.iloc[pos2]
            if (r_i < lo and r_j > hi) or (r_i > hi and r_j < lo):
                partner = pos2
                used.add(ts2)
                break
        if partner is not None:
            df.iloc[pos:partner, [df.columns.get_loc(c) for c in px]] *= (1.0 / r_i)
        else:
            df.iloc[:pos, [df.columns.get_loc(c) for c in px]] *= r_i
            df.iloc[:pos, df.columns.get_loc("Volume")] /= r_i
    return df


def load_prices(
    tickers: Iterable[str],
    start: str = "2015-01-01",
    end: Optional[str] = None,
    interval: str = "1d",
    use_cache: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Return {ticker: OHLCV DataFrame} indexed by timestamp."""
    tickers = list(tickers)
    end = end or date.today().isoformat()
    path = _cache_path(tickers, start, end, interval)
    if use_cache and path.exists():
        with open(path, "rb") as fh:
            return pickle.load(fh)
    data = _download(tickers, start, end, interval)
    missing = [t for t in tickers if t not in data]
    for attempt in range(2):  # Yahoo is flaky under batch load; retry stragglers one by one
        if not missing:
            break
        time.sleep(1.5 * (attempt + 1))
        for t in list(missing):
            try:
                got = _download([t], start, end, interval)
            except Exception:
                got = {}
            if t in got:
                data[t] = got[t]
                missing.remove(t)
    if missing:
        print(f"[loader] WARNING no data for: {missing}")
    data = {t: clean_split_glitches(df) for t, df in data.items()}
    if data:
        with open(path, "wb") as fh:
            pickle.dump(data, fh)
    return data


def load_intraday(tickers: Iterable[str], days: int = 55, interval: str = "5m") -> Dict[str, pd.DataFrame]:
    """Yahoo gives ~60 days of 5m bars. Enough to sanity-check an intraday idea,
    NOT enough to trust it - use broker historical APIs for real intraday research."""
    end = date.today()
    start = end - pd.Timedelta(days=days)
    return load_prices(tickers, start.isoformat(), end.isoformat(), interval=interval)


def close_matrix(prices: Dict[str, pd.DataFrame], field: str = "Close") -> pd.DataFrame:
    """Wide matrix: index=date, columns=ticker."""
    mat = pd.DataFrame({t: df[field] for t, df in prices.items()})
    mat.index = pd.to_datetime(mat.index)
    if getattr(mat.index, "tz", None) is not None:
        mat.index = mat.index.tz_localize(None)
    return mat.sort_index().ffill(limit=5)
