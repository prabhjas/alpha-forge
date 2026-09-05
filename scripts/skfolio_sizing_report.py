#!/usr/bin/env python
"""Does skfolio sizing beat our inverse-vol sizing? Two tests -> docs/SKFOLIO_SIZING.md

1. Pure allocation test using skfolio's own WalkForward cross-validation on each
   universe (no trend filter): equal weight vs inverse-vol vs HRP vs risk parity
   vs min-variance (Ledoit-Wolf). Out-of-sample by construction.
2. Our engine, costs on: TrendFollowing (inverse-vol) vs TrendHRP (hrp / riskparity / minvar).

Run with the Python 3.13 environment:  .venv313/bin/python scripts/skfolio_sizing_report.py
"""
from __future__ import annotations

import sys
import warnings
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

from alpha_forge.backtest import Backtester, COST_PRESETS
from alpha_forge.backtest.metrics import performance_summary
from alpha_forge.data.loader import UNIVERSES, close_matrix, load_prices
from alpha_forge.strategies import TrendFollowing, TrendHRP

from skfolio import RiskMeasure
from skfolio.model_selection import WalkForward, cross_val_predict
from skfolio.moments import LedoitWolf
from skfolio.optimization import EqualWeighted, HierarchicalRiskParity, InverseVolatility, MeanRisk, RiskBudgeting
from skfolio.prior import EmpiricalPrior

START = "2015-01-01"
UNIVERSE_COSTS = {"india_etf": ("india_delivery", "india_benchmark"), "nifty50": ("india_delivery", "india_benchmark"), "us_core": ("us_alpaca", "us_benchmark")}


def allocation_models():
    prior = EmpiricalPrior(covariance_estimator=LedoitWolf())
    return {
        "equal_weight": EqualWeighted(),
        "inverse_vol": InverseVolatility(prior_estimator=prior),
        "hrp": HierarchicalRiskParity(risk_measure=RiskMeasure.VARIANCE, prior_estimator=prior),
        "risk_parity": RiskBudgeting(risk_measure=RiskMeasure.VARIANCE, prior_estimator=prior),
        "min_variance": MeanRisk(risk_measure=RiskMeasure.VARIANCE, prior_estimator=prior, max_weights=0.25),
    }


def skfolio_walkforward(returns: pd.DataFrame, cost_per_side: float) -> pd.DataFrame:
    cv = WalkForward(train_size=252, test_size=63)  # refit every quarter on the trailing year
    rows = []
    for name, model in allocation_models().items():
        pred = cross_val_predict(model, returns, cv=cv, n_jobs=1)
        r = pd.Series(pred.returns, index=pred.observations)  # gross, no costs
        # charge turnover at each quarterly rebalance from the weight path
        w = pd.DataFrame(pred.weights_per_observation).reindex(r.index).ffill().fillna(0)
        turnover = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1).iloc[0])
        net = r - turnover * cost_per_side
        s = performance_summary(net)
        rows.append({"model": name, "OOS CAGR %": s["cagr_pct"], "OOS Sharpe": s["sharpe"], "OOS MaxDD %": s["max_drawdown_pct"],
                     "ann vol %": s["ann_vol_pct"], "turnover/yr": round(float(turnover.sum() / s["years"]), 2)})
    return pd.DataFrame(rows)


def main():
    md = [f"# skfolio sizing report ({date.today()})", "",
          "Test 1: allocation only (always fully invested), skfolio WalkForward CV, refit quarterly on trailing 252 days, costs charged on turnover.",
          "Test 2: our engine with the trend filter, monthly rebalance, costs on. Sizing is the only difference between rows.", ""]
    for uni, (cost_name, bench_key) in UNIVERSE_COSTS.items():
        print(f"== {uni}", flush=True)
        cost = COST_PRESETS[cost_name]
        prices = load_prices(UNIVERSES[uni], start=START)
        closes = close_matrix(prices)
        full = closes.dropna(axis=1, how="any")  # Test 1 needs a full-history panel (no NaN/zero-variance columns)
        rets = full.pct_change().dropna()
        print(f"  test 1 panel: {full.shape[1]} of {closes.shape[1]} assets have full history since {START}")
        bench = close_matrix(load_prices(UNIVERSES[bench_key], start=START)).iloc[:, 0]

        t1 = skfolio_walkforward(rets, cost.per_side)
        md += [f"## `{uni}` (costs: {cost_name})", "", f"### Test 1: pure allocation, skfolio walk-forward ({full.shape[1]} assets with full history)", "", t1.round(2).to_markdown(index=False), ""]
        print(t1.round(2).to_string())

        bt = Backtester(cost)
        rows = []
        for label, strat in [("trend + inverse_vol (current)", TrendFollowing()),
                             ("trend + hrp", TrendHRP(model="hrp")),
                             ("trend + risk_parity", TrendHRP(model="riskparity")),
                             ("trend + min_variance", TrendHRP(model="minvar"))]:
            res = bt.run(strat, prices, benchmark=bench)
            s = res.summary
            rows.append({"strategy": label, "CAGR %": s["cagr_pct"], "Sharpe": s["sharpe"], "MaxDD %": s["max_drawdown_pct"], "Calmar": s["calmar"],
                         "turnover/yr": s["avg_annual_turnover"], "worst month %": s["worst_month_pct"], "bench CAGR %": s["benchmark_cagr_pct"], "bench MaxDD %": s["benchmark_max_dd_pct"]})
            print(f"  {label:32s} CAGR {s['cagr_pct']:6.2f}  Sharpe {s['sharpe']:5.2f}  MaxDD {s['max_drawdown_pct']:6.2f}", flush=True)
        t2 = pd.DataFrame(rows)
        md += ["### Test 2: trend filter + sizing, our engine", "", t2.round(2).to_markdown(index=False), ""]
    md += ["## Reading", "",
           "* HRP/risk-parity win when they deliver a similar CAGR with a shallower drawdown and lower vol. Raw CAGR alone is not the criterion.",
           "* Min-variance with a Ledoit-Wolf prior is the classic 'looks great in-sample, churns live' model; watch its turnover.",
           "* If nothing beats inverse-vol here, we keep inverse-vol. Simpler wins ties."]
    Path("docs/SKFOLIO_SIZING.md").write_text("\n".join(md))
    print("wrote docs/SKFOLIO_SIZING.md")


if __name__ == "__main__":
    main()
