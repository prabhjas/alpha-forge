# System quality report (2026-09-06)

Does combining our signals and targeting volatility beat running them alone? Costs on, 2015-2026, long-only.

## `india_etf` (costs: india_delivery)

| config                    |   CAGR % |   Sharpe |   MaxDD % |   Calmar |   ann vol % |   worst month % |   turnover/yr |
|:--------------------------|---------:|---------:|----------:|---------:|------------:|----------------:|--------------:|
| trend only                |    10.9  |     1.22 |    -11.84 |     0.92 |        8.81 |           -5.62 |           5.7 |
| momentum only             |    10.78 |     1.18 |    -16.97 |     0.64 |        9.05 |           -5.26 |           5.8 |
| ensemble (no vol target)  |    10.69 |     1.25 |    -12.81 |     0.83 |        8.39 |           -4.86 |           5.6 |
| ensemble + vol target 12% |    10.6  |     1.27 |    -12.97 |     0.82 |        8.22 |           -3.98 |           5.9 |

**Chosen book: trend only** (best Calmar). Robustness (2000x block bootstrap):

| statistic | value |
|---|---|
| observed CAGR | 10.9% |
| CAGR 90% CI | 5.8% to 16.1% |
| observed Sharpe | 1.22 |
| Sharpe 90% CI | 0.67 to 1.77 |
| P(Sharpe > 0) | 100% |
| observed MaxDD | -11.8% |
| MaxDD 95th-pct (bad luck) | -22.5% |
| P(a given year is negative) | 13% |
| expected worst year in 5 | -0.0% |


## `us_core` (costs: us_alpaca)

| config                    |   CAGR % |   Sharpe |   MaxDD % |   Calmar |   ann vol % |   worst month % |   turnover/yr |
|:--------------------------|---------:|---------:|----------:|---------:|------------:|----------------:|--------------:|
| trend only                |    19.33 |     1.32 |    -17.62 |     1.1  |       14.19 |           -8.59 |          10.9 |
| momentum only             |    19.54 |     1.09 |    -26.74 |     0.73 |       17.87 |          -13.96 |           8   |
| ensemble (no vol target)  |    19.33 |     1.29 |    -19.71 |     0.98 |       14.52 |           -9.74 |           9.5 |
| ensemble + vol target 12% |    16.48 |     1.36 |    -13.97 |     1.18 |       11.7  |           -8.62 |           9.7 |

**Chosen book: ensemble + vol target 12%** (best Calmar). Robustness (2000x block bootstrap):

| statistic | value |
|---|---|
| observed CAGR | 16.5% |
| CAGR 90% CI | 10.5% to 22.5% |
| observed Sharpe | 1.36 |
| Sharpe 90% CI | 0.90 to 1.82 |
| P(Sharpe > 0) | 100% |
| observed MaxDD | -14.0% |
| MaxDD 95th-pct (bad luck) | -24.9% |
| P(a given year is negative) | 9% |
| expected worst year in 5 | 1.9% |


## What changed and why it's better

* The **ensemble** blends trend (60%) and momentum (40%). Two edges that fail at different times, combined, give a smoother ride than either alone.
* **Vol targeting (12%)** scales the whole book down when markets get wild and up when calm, holding risk roughly constant. It trades a little CAGR for a large cut in drawdown and a higher Calmar.
* **Confidence intervals** replace false precision. We now state P(losing year) and the bad-luck drawdown, not just the one backtest path.
* This ensemble+vol-target book is what goes into the paper A/B and, after 8 weeks, the small live pilot.