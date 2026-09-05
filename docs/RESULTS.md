# Backtest scoreboard (generated 2026-09-05)

Period start 2015-01-01. Daily bars from Yahoo Finance, adjusted closes. Long-only, no leverage.
Costs charged per side (see alpha_forge/backtest/costs.py). 'zero' rows exist only to show cost impact.

| universe   | strategy   | costs          |   CAGR % |   Sharpe |   MaxDD % |   Calmar |   Turnover/yr |   Cost drag % (total) |   Bench CAGR % |   Bench MaxDD % |   Best mo % |   Worst mo % |   Years |
|:-----------|:-----------|:---------------|---------:|---------:|----------:|---------:|--------------:|----------------------:|---------------:|----------------:|------------:|-------------:|--------:|
| nifty50    | momentum   | india_delivery |    13.97 |     0.88 |    -29.14 |     0.48 |          11.7 |                 22.56 |          11.72 |          -38.44 |       13.02 |       -11.47 |   10.21 |
| nifty50    | momentum   | zero           |    16.52 |     1.01 |    -25.04 |     0.66 |          11.7 |                  0    |          11.72 |          -38.44 |       13.26 |       -11.43 |   10.21 |
| nifty50    | trend      | india_delivery |    14.15 |     0.94 |    -29.36 |     0.48 |          13.1 |                 26.36 |          10.49 |          -38.44 |       14.96 |       -11.92 |   10.66 |
| nifty50    | trend      | zero           |    17    |     1.1  |    -28.96 |     0.59 |          13.1 |                  0    |          10.49 |          -38.44 |       15.11 |       -11.39 |   10.66 |
| nifty50    | meanrev    | india_delivery |   -12.89 |    -0.59 |    -78.63 |    -0.16 |         146.2 |                296.28 |          10.47 |          -38.44 |        9.57 |       -22.91 |   10.67 |
| nifty50    | meanrev    | zero           |    15.01 |     0.81 |    -36.82 |     0.41 |         146.2 |                  0    |          10.47 |          -38.44 |       11.89 |       -21.58 |   10.67 |
| nifty50    | buyhold    | india_delivery |    18.28 |     1.13 |    -37.48 |     0.49 |           0.1 |                  0.21 |           9.56 |          -38.44 |       16.05 |       -23.12 |   11.46 |
| nifty50    | buyhold    | zero           |    18.3  |     1.13 |    -37.48 |     0.49 |           0.1 |                  0    |           9.56 |          -38.44 |       16.05 |       -23.12 |   11.46 |
| india_etf  | momentum   | india_delivery |    10.78 |     1.18 |    -16.97 |     0.64 |           5.8 |                 11.27 |          11.45 |          -38.44 |        7.58 |        -5.26 |   10.19 |
| india_etf  | momentum   | zero           |    12.01 |     1.3  |    -15.37 |     0.78 |           5.8 |                  0    |          11.45 |          -38.44 |        7.78 |        -5    |   10.19 |
| india_etf  | trend      | india_delivery |    10.9  |     1.22 |    -11.84 |     0.92 |           5.7 |                 11.42 |          10.49 |          -38.44 |        7.34 |        -5.62 |   10.66 |
| india_etf  | trend      | zero           |    12.09 |     1.34 |    -11.63 |     1.04 |           5.7 |                  0    |          10.49 |          -38.44 |        7.43 |        -5.57 |   10.66 |
| india_etf  | meanrev    | india_delivery |    -8.21 |    -0.58 |    -64.89 |    -0.13 |          66.1 |                133.81 |          10.44 |          -38.44 |       13.15 |       -14.08 |   10.66 |
| india_etf  | meanrev    | zero           |     4.08 |     0.37 |    -26.82 |     0.15 |          66.1 |                  0    |          10.44 |          -38.44 |       14.3  |       -12.98 |   10.66 |
| india_etf  | buyhold    | india_delivery |    15.44 |     1.22 |    -29.56 |     0.52 |           0.1 |                  0.25 |           9.56 |          -38.44 |       13.02 |       -16.22 |   11.46 |
| india_etf  | buyhold    | zero           |    15.46 |     1.23 |    -29.56 |     0.52 |           0.1 |                  0    |           9.56 |          -38.44 |       13.02 |       -16.22 |   11.46 |
| us_core    | momentum   | us_alpaca      |    19.54 |     1.09 |    -26.74 |     0.73 |           8   |                  2.59 |          15.93 |          -33.72 |       13.03 |       -13.96 |   10.5  |
| us_core    | momentum   | zero           |    19.83 |     1.1  |    -26.6  |     0.75 |           8   |                  0    |          15.93 |          -33.72 |       13.04 |       -13.76 |   10.5  |
| us_core    | trend      | us_alpaca      |    19.33 |     1.32 |    -17.62 |     1.1  |          10.9 |                  3.67 |          14.95 |          -33.72 |       10.28 |        -8.59 |   10.86 |
| us_core    | trend      | zero           |    19.74 |     1.34 |    -17.45 |     1.13 |          10.9 |                  0    |          14.95 |          -33.72 |       10.32 |        -8.53 |   10.86 |
| us_core    | meanrev    | us_alpaca      |    20.29 |     1.06 |    -31.9  |     0.64 |         120   |                 40.14 |          14.62 |          -33.72 |       16.16 |       -13.94 |   10.81 |
| us_core    | meanrev    | zero           |    24.84 |     1.25 |    -30.72 |     0.81 |         120   |                  0    |          14.62 |          -33.72 |       16.57 |       -13.6  |   10.81 |
| us_core    | buyhold    | us_alpaca      |    22.61 |     1.23 |    -28.29 |     0.8  |           0.1 |                  0.03 |          13.86 |          -33.72 |       13.48 |       -10.68 |   11.65 |
| us_core    | buyhold    | zero           |    22.62 |     1.23 |    -28.29 |     0.8  |           0.1 |                  0    |          13.86 |          -33.72 |       13.48 |       -10.68 |   11.65 |

## How to read this

* Beat the benchmark CAGR **and** have a shallower MaxDD, or the strategy has no reason to exist.
* Turnover/yr x cost per side = the tax you pay for activity. High-turnover ideas die here.
* Best month tells you what a lucky month looks like. Nobody's best month is +300% (i.e. 10%/day).
* These are in-sample with default parameters. Walk-forward validation is Phase 1 work before any live money.
* **Survivorship bias**: universes are today's index members, i.e. the companies that won. That inflates every
  number here, buy-and-hold most of all. Phase 1 replaces this with point-in-time constituents from the exchange.