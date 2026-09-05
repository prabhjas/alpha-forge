from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def performance_summary(daily_returns: pd.Series, periods_per_year: int = 252) -> Dict[str, float]:
    r = daily_returns.dropna()
    if len(r) < 2:
        return {}
    equity = (1 + r).cumprod()
    years = len(r) / periods_per_year
    cagr = equity.iloc[-1] ** (1 / years) - 1 if years > 0 else np.nan
    vol = r.std() * np.sqrt(periods_per_year)
    sharpe = (r.mean() * periods_per_year) / vol if vol > 0 else np.nan
    downside = r[r < 0].std() * np.sqrt(periods_per_year)
    sortino = (r.mean() * periods_per_year) / downside if downside > 0 else np.nan
    mdd = max_drawdown(equity)
    calmar = cagr / abs(mdd) if mdd < 0 else np.nan
    monthly = (1 + r).resample("ME").prod() - 1
    return {
        "total_return_pct": round((equity.iloc[-1] - 1) * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "ann_vol_pct": round(vol * 100, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "max_drawdown_pct": round(mdd * 100, 2),
        "calmar": round(calmar, 2),
        "best_month_pct": round(monthly.max() * 100, 2),
        "worst_month_pct": round(monthly.min() * 100, 2),
        "pct_positive_months": round((monthly > 0).mean() * 100, 1),
        "avg_daily_return_pct": round(r.mean() * 100, 4),
        "years": round(years, 2),
    }
