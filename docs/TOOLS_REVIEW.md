# Instagram tool review — 5 September 2026

Five tools from the post you sent, each checked against its own repo/docs today, plus a real test of the one that makes the biggest claim.

## Scorecard

| Tool | What it actually is | Markets | Python | Verdict for Alpha Forge |
|---|---|---|---|---|
| **Kronos** (NeoQuasar, AAAI 2026, 23k stars) | Open-source foundation model that tokenises OHLCV candles and predicts the next candles. Sizes 4M to 102M params open, 499M closed | Any candles | any | **Tested. Not usable as a signal.** See below |
| **skfolio** | scikit-learn style portfolio construction: HRP, risk parity, mean-risk, NCO, covariance shrinkage, walk-forward and purged CV, copula stress tests | Any | 3.10+ | **Adopt in Phase 1** for position sizing and robust validation. Needs a Python 3.11 venv |
| **NautilusTrader** | Rust-core event-driven backtest and live engine. 22 adapters: Binance, Bybit, OKX, Coinbase, Kraken, Hyperliquid, dYdX, Interactive Brokers, Betfair, Polymarket, Databento | Crypto, IBKR, sports and prediction markets | 3.12 to 3.14 | **Not now.** No Alpaca, no Zerodha, no Angel One, no Groww adapter. Serious tool for tick-level and HFT work we are not doing. Revisit only if we move the US leg to Interactive Brokers |
| **Freqtrade** | Crypto bot: strategies in Python, backtesting, hyperopt, FreqAI machine learning, dry-run, Telegram control | Crypto only (Binance, Kraken, OKX, Bybit, Gate) | 3.11+ | **No.** Crypto only, and India taxes crypto at flat 30% with 1% TDS and **no loss set-off**, which makes active crypto trading mathematically hostile for an Indian resident |
| **Hummingbot** | Market-making and cross-exchange arbitrage framework for crypto CEX and DEX | Crypto only | 3.10+ | **No.** Market making is a capital- and infrastructure-intensive game against professionals, in crypto, under the same tax regime |

## Kronos: what we measured

The top comment on the post asked the right question: a model can look 85% confident while being right 58% of the time, so show a reliability diagram and a Brier score before any capital goes in. I ran exactly that test. Zero-shot Kronos-small, 32 sampled forecast paths per day, rolling over the last 250 trading days, on NIFTYBEES (India) and SPY (US). Script: `research/kronos_calibration.py`. Full tables: `docs/KRONOS_EVAL_h1.md`.

| 1-day horizon | NIFTYBEES | SPY | What a useful model needs |
|---|---|---|---|
| Directional accuracy of point forecast | 48.8% | 48.4% | above the always-up base rate (52% / 55%) |
| Directional accuracy of P(up) > 0.5 | 49.6% | 46.8% | above 50% |
| Brier score (lower is better) | 0.312 | 0.395 | below the constant base-rate forecast (0.250 / 0.247) |
| Median 10-90% forecast band vs actual move | 3.4x | 4.9x | near 1x |

| 5-day horizon (120 forecasts) | NIFTYBEES | SPY | What a useful model needs |
|---|---|---|---|
| Directional accuracy of point forecast | 53.3% | 41.7% | above the always-up base rate (47.5% / 58.3%) |
| Brier score (lower is better) | 0.293 | 0.420 | below the constant base-rate forecast (0.260 / 0.244) |
| Median 10-90% forecast band vs actual move | 2.8x | 3.7x | near 1x |

At 5 days Kronos is weakly right on Nifty direction, but its probabilities are still worse than the base rate, and on SPY it was bearish in 88 of 120 weeks while the index rose in 58% of them. Full tables: `docs/KRONOS_EVAL_h5.md`.

Reliability at 1 day: when Kronos said P(up) was 11 to 18%, the market actually went up 52 to 57% of the time. When it said 81 to 83%, the market went up 46 to 61% of the time. Its confidence carries no information at 1-day horizon, and the Brier score is worse than simply guessing the historical up-rate every day. The forecast band is 3 to 5 times wider than the move it is forecasting, which is the "band wider than the move" failure the comment predicted.

This is not a knock on the research. Kronos was benchmarked on forecasting error of the price path, and the authors say plainly that their trading example is not a production system. It just means the impressive-looking demo is not a trading edge. If we ever use it, it would be as one feature among many, fine-tuned on NSE data, and it would have to earn its place through the same walk-forward test as everything else.

## The pattern behind these posts

Every one of these five is a real, respectable open-source project. The Instagram edit stitches their screenshots into one "system" that nobody in the video has actually run end to end. The tell is the comment below the post: an account replying "check your messages, I've sent info" is the standard funnel to a paid signals group or a "managed account". Do not reply to those.

## What we take from this

1. **skfolio** goes on the Phase 1 list: hierarchical risk parity sizing for the ETF book and combinatorial purged cross-validation for strategy selection. This is a genuine upgrade over the inverse-vol sizing we have now.
2. **Kronos** stays in `vendor/` as a research toy with a documented negative result. Negative results are worth money: they stop you deploying capital on a demo.
3. **NautilusTrader** is bookmarked for a future Interactive Brokers move; our current broker set has no adapter for it.
4. **Freqtrade and Hummingbot** are ruled out on tax grounds alone, before even asking whether the strategies work.

---

# Round 2 — 6 September 2026 (BullGPT, Sensibull, algo-trading links, SMA scanner)

| Tool / link | What it actually is | Verdict |
|---|---|---|
| **BullGPT** (bullgpt.io) | AI that reads a chart *screenshot* and writes technical analysis (support/resistance, RSI, entry/SL/TP). $40/mo or $180 lifetime. Operator: Veutino LLC. No broker connection, no automation. | **Skip.** It generates opinions from a picture, not a tested edge. Its own site says "be wary of any tool that claims" guaranteed profits — correct. No free tier, no refund. We already generate signals from data we control; a screenshot-reader adds nothing and can't be backtested. |
| **Sensibull** (sensibull.com) | Legit SEBI-registered options analytics platform. Strategy builder, option chain, Greeks, draft P&L. **Manual execution only** — it will not auto-trade. ₹800/mo (Zerodha) to ₹1,300/mo. | **Bookmark for Phase 4.** Genuinely the best retail options-analysis tool in India and worth the money *when we trade options* (i.e. when the book clears ~₹20 lakh). Useless to us now — we hold no options. Do not pay for it yet. |
| **Groww / Angel One "what is algo trading" articles** | Educational explainers. | Background reading. Nothing to integrate. Confirms what we already built: API + strategy + broker. |
| **Angel One SmartAPI** (smartapi.angelone.in) | Free broker API. | **Already integrated** — `alpha_forge/brokers/angelone_broker.py` (dry-run). Reviewed round 1. |
| **Kite Connect** (developers.kite.trade, kite.trade/docs) | Zerodha's API. | **Already integrated** — `alpha_forge/brokers/kite_broker.py` (dry-run). The login URL in your screenshot is the normal OAuth step; the api_key in the URL is fine, the api_secret is NOT and must never be shared. |
| **YouTube tutorial + SMA scanner screenshot** (nifty100_sma_scanner.py) | Build a script that scans Nifty 100 for SMA 6/30 crossovers and ranks by recency. | **Built as `scripts/sma_scanner.py`**, but read-only. See below. |

## The SMA crossover scanner: built, but know what it is

The tutorial's idea (scan for SMA 6/30 crossovers) is a fine *screening* tool and a poor *strategy*. I built the scanner (`scripts/sma_scanner.py`, read-only, no orders, runs Monday with no keys) AND backtested the SMA 6/30 rule as an actual strategy, costs on, 2015–2026:

| Universe | SMA 6/30 CAGR | SMA 6/30 Sharpe | SMA 6/30 MaxDD | Turnover/yr | vs our `trend` (Sharpe) |
|---|---|---|---|---|---|
| nifty50 | 8.2% | 0.58 | -35.3% | 40x | trend 0.93 |
| india_etf | 12.2% | 0.95 | -28.6% | 32x | trend 1.15, MaxDD -11.8% |
| us_core | 17.4% | 1.06 | -28.8% | 39x | trend 1.32, MaxDD -17.6% |

SMA 6/30 churns 30–40x a year (ours: 5–10x), has ~2x the drawdown, lower Sharpe everywhere, and on Nifty 50 it underperforms buy-and-hold after costs. The fast 6-day average whipsaws in sideways markets — a documented failure mode. **Conclusion:** keep the scanner as a daily watchlist to eyeball what's moving, but the trades still go through the validated `trend` engine + risk manager. The scanner informs; it does not decide.
