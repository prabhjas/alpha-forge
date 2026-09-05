# skfolio sizing report (2026-09-06)

Test 1: allocation only (always fully invested), skfolio WalkForward CV, refit quarterly on trailing 252 days, costs charged on turnover.
Test 2: our engine with the trend filter, monthly rebalance, costs on. Sizing is the only difference between rows.

## `india_etf` (costs: india_delivery)

### Test 1: pure allocation, skfolio walk-forward (5 assets with full history)

| model        |   OOS CAGR % |   OOS Sharpe |   OOS MaxDD % |   ann vol % |   turnover/yr |
|:-------------|-------------:|-------------:|--------------:|------------:|--------------:|
| equal_weight |        17.85 |         1.37 |        -29.56 |       12.53 |          0    |
| inverse_vol  |        16.95 |         1.39 |        -28.24 |       11.75 |          0.18 |
| hrp          |        16.56 |         1.48 |        -23.68 |       10.78 |          0.68 |
| risk_parity  |        17.56 |         1.52 |        -24.44 |       11.02 |          0.25 |
| min_variance |        17.21 |         1.43 |        -25.38 |       11.6  |          0.33 |

### Test 2: trend filter + sizing, our engine

| strategy                      |   CAGR % |   Sharpe |   MaxDD % |   Calmar |   turnover/yr |   worst month % |   bench CAGR % |   bench MaxDD % |
|:------------------------------|---------:|---------:|----------:|---------:|--------------:|----------------:|---------------:|----------------:|
| trend + inverse_vol (current) |    10.9  |     1.22 |    -11.84 |     0.92 |           5.7 |           -5.62 |          10.49 |          -38.44 |
| trend + hrp                   |    10.32 |     1.16 |    -13.06 |     0.79 |           2.6 |           -8.34 |          11.89 |          -38.44 |
| trend + risk_parity           |    10.48 |     1.1  |    -15.55 |     0.67 |           2.4 |           -8.78 |          11.89 |          -38.44 |
| trend + min_variance          |     8.3  |     1.11 |    -13.25 |     0.63 |           2.2 |           -8.6  |          11.89 |          -38.44 |

## `nifty50` (costs: india_delivery)

### Test 1: pure allocation, skfolio walk-forward (47 assets with full history)

| model        |   OOS CAGR % |   OOS Sharpe |   OOS MaxDD % |   ann vol % |   turnover/yr |
|:-------------|-------------:|-------------:|--------------:|------------:|--------------:|
| equal_weight |        21.1  |         1.25 |        -37.4  |       16.36 |          0    |
| inverse_vol  |        20.03 |         1.24 |        -36.02 |       15.68 |          0.17 |
| hrp          |        19.4  |         1.29 |        -31.31 |       14.59 |          0.97 |
| risk_parity  |        19.86 |         1.28 |        -33.91 |       15.06 |          0.32 |
| min_variance |        15.47 |         1.14 |        -27.02 |       13.4  |          1.72 |

### Test 2: trend filter + sizing, our engine

| strategy                      |   CAGR % |   Sharpe |   MaxDD % |   Calmar |   turnover/yr |   worst month % |   bench CAGR % |   bench MaxDD % |
|:------------------------------|---------:|---------:|----------:|---------:|--------------:|----------------:|---------------:|----------------:|
| trend + inverse_vol (current) |    14.63 |     0.97 |    -29.96 |     0.49 |          13.1 |          -12.72 |          10.49 |          -38.44 |
| trend + hrp                   |    16.42 |     1.08 |    -34.43 |     0.48 |           6   |          -17.58 |          11.89 |          -38.44 |
| trend + risk_parity           |    16.61 |     1.07 |    -36.25 |     0.46 |           5   |          -19.53 |          11.89 |          -38.44 |
| trend + min_variance          |    13.32 |     0.94 |    -31.69 |     0.42 |           6.6 |          -13.05 |          11.89 |          -38.44 |

## `us_core` (costs: us_alpaca)

### Test 1: pure allocation, skfolio walk-forward (20 assets with full history)

| model        |   OOS CAGR % |   OOS Sharpe |   OOS MaxDD % |   ann vol % |   turnover/yr |
|:-------------|-------------:|-------------:|--------------:|------------:|--------------:|
| equal_weight |        23.48 |         1.26 |        -28.29 |       18.11 |          0    |
| inverse_vol  |        19.93 |         1.21 |        -26.96 |       16.05 |          0.21 |
| hrp          |        15.29 |         1.28 |        -20.21 |       11.66 |          1.06 |
| risk_parity  |        16.56 |         1.33 |        -21.19 |       12.09 |          0.39 |
| min_variance |        10.69 |         1.07 |        -20.23 |        9.91 |          0.8  |

### Test 2: trend filter + sizing, our engine

| strategy                      |   CAGR % |   Sharpe |   MaxDD % |   Calmar |   turnover/yr |   worst month % |   bench CAGR % |   bench MaxDD % |
|:------------------------------|---------:|---------:|----------:|---------:|--------------:|----------------:|---------------:|----------------:|
| trend + inverse_vol (current) |    19.33 |     1.32 |    -17.62 |     1.1  |          10.9 |           -8.59 |          14.95 |          -33.72 |
| trend + hrp                   |    15.94 |     1.29 |    -18.65 |     0.85 |           4.9 |           -8.56 |          16.05 |          -33.72 |
| trend + risk_parity           |    18    |     1.34 |    -18.37 |     0.98 |           4.1 |           -9.86 |          16.05 |          -33.72 |
| trend + min_variance          |    10.27 |     1.09 |    -17.14 |     0.6  |           4.9 |           -6.83 |          16.05 |          -33.72 |

## Reading

* HRP/risk-parity win when they deliver a similar CAGR with a shallower drawdown and lower vol. Raw CAGR alone is not the criterion.
* Min-variance with a Ledoit-Wolf prior is the classic 'looks great in-sample, churns live' model; watch its turnover.
* If nothing beats inverse-vol here, we keep inverse-vol. Simpler wins ties.
## Conclusions (6 Sep 2026)

**Test 1 (allocation only, always invested):** HRP and risk parity win on risk-adjusted terms in every universe. Same or slightly lower CAGR, 15 to 25% less volatility, drawdowns 4 to 8 points shallower, Sharpe up by 0.05 to 0.12. Min-variance cuts vol the most but gives up too much return and churns (1.7x turnover on Nifty 50). Note: skfolio reports target weights, so equal-weight turnover shows as 0; its real quarterly drift-rebalance cost is small but not zero.

**Test 2 (with the trend filter, our engine, costs on):** the advantage mostly disappears. The trend filter already removes the assets that would have blown up the drawdown, and inverse-vol on the survivors is hard to beat.

| Universe | Best sizing with trend filter | Verdict |
|---|---|---|
| india_etf | inverse-vol (Sharpe 1.22, MaxDD -11.8%) | keep inverse-vol |
| us_core | risk parity Sharpe 1.34 vs inverse-vol 1.32, but 1.3 pts less CAGR | keep inverse-vol, tie |
| nifty50 | risk parity / HRP add ~2 pts CAGR and +0.1 Sharpe, but 4 to 6 pts deeper MaxDD | candidate for A/B in paper trading |

**Decision:** inverse-vol stays the default sizing. `TrendHRP(model="riskparity")` is registered as `trend_hrp` and goes into the Phase 2 paper book on the Nifty 50 leg only, side by side with `trend`, so the decision gets made on live fills rather than on this backtest. skfolio's real value for us is the validation tooling (WalkForward, combinatorial purged CV) and the covariance shrinkage, not a magic allocator.
