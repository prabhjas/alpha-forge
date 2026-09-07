# Alpha Forge — Wealth-by-Trading Master Plan

*Prepared 5 September 2026 for Prabhjas. Capital in scope: ₹1,00,000 (₹50k India + ₹50k / ~$570 US). Brokers available: Angel One, Groww, Zerodha (India); Alpaca recommended for the US leg.*

---

## 0. The one thing to get right before anything else: the target

You asked for 10% per day. Here is what that number actually means, so we can replace it with a target that lets us win.

| Daily return | Yearly multiple (250 trading days) | ₹1 lakh becomes in 1 year | Who has ever done this |
|---|---|---|---|
| 10% / day | 22,400,000,000× | ₹2,240 lakh crore (≈ 7× India's GDP) | Nobody. Not possible. |
| 1% / day | 12× | ₹12 lakh | Nobody, sustained. Best hedge fund ever is 1/6th of this |
| 0.2% / day (≈ 66% / yr) | 1.66× | ₹1.66 lakh | Renaissance Medallion, gross, with 300 PhDs and billions in infra |
| 0.1% / day (≈ 28% / yr) | 1.28× | ₹1.28 lakh | Elite systematic traders in good years |
| 0.06% / day (≈ 15% / yr) | 1.15× | ₹1.15 lakh | Nifty 50 long-run average, zero skill needed |

Facts to anchor on:

* Renaissance Medallion, the best trading operation in history, averaged about 66% per year gross and 39% net over 30 years. That is roughly 0.2% per day. Anyone advertising 10%/day is showing you a lucky week, a demo account, or a lie.
* SEBI's own studies: 93% of individual F&O traders lost money FY22 to FY24, aggregate losses over ₹1.8 lakh crore. In FY25 losses widened another 41% to ₹1.05 lakh crore and 91% still lost. The profits went to large algo entities. That is who is on the other side of a retail intraday trade.
* Instagram accounts like fidetolabs (checked: they post build logs about AI agents for quant trading, no return claims) are useful as engineering inspiration, not as evidence of returns.

**The real target**: a systematic, low-cost, diversified engine that beats its benchmark by 5 to 15 percentage points a year with a max drawdown under 20%, and that you keep feeding with savings. That, compounded, is how every real fortune you named was built. Buffett's lifetime CAGR is about 20%. He is the richest investor alive because he did 20% for 60 years, not 10% for a day.

**Wealth formula we are actually optimising**: `Wealth = (Savings rate × Time) ^ (edge + discipline)`. Trading edge is the exponent. Savings and time are the base. The engine below is built to protect the base while we grow the exponent.

---

## 1. What already exists (verified today)

| Piece | Status | Notes |
|---|---|---|
| Zerodha Kite Connect | Personal API free (orders, positions, no data). Paid ₹500/mo adds live + historical data | Official MCP server at `mcp.kite.trade` (hosted, OAuth) |
| Angel One SmartAPI | Free API, TOTP login, historical candles included | Community MCP servers exist (ameernoufil, bhavesh0009). No official one |
| Groww Trade API | ₹499/mo, equity + F&O, NSE/BSE/MCX, Python SDK | Launched 2025. No MCP server yet |
| Alpaca (US) | Free paper + live accounts, commission-free, fractional shares, accepts international clients | Official MCP server with 65 tools. Paper keys are instant |
| INDmoney US account | App only, no API | Keep for manual investing; not usable for automation |
| SEBI retail algo framework | **In force since 1 April 2026** | Static IP whitelisted per API key; OAuth login + 2FA every trading day; below 10 orders/second per exchange you need no algo registration; market orders become MPP orders |

Implications:
* India automation must run from a machine with a **static IP** (a ₹300 to 500/month VPS in Mumbai, or a static IP add-on from your ISP). Your laptop's home Wi-Fi will not be accepted.
* Daily re-login is mandatory. The system needs a 9:00 IST "login step" you complete on your phone, then it runs alone.
* MCP connectors are for **you talking to your account** (checking, reviewing, one-off orders). The algo itself must be plain code on a schedule. Do not put an LLM in the order path: it is slow, non-deterministic, and un-auditable.

---

## 2. Capital plan (₹1,00,000 total)

| Leg | Amount | Broker | Instruments | Strategy family | Why |
|---|---|---|---|---|---|
| India core | ₹50,000 | Zerodha (Kite Personal, free) or Angel One (free) | Nifty 50 stocks + NIFTYBEES/JUNIORBEES/GOLDBEES ETFs, delivery (CNC) | Cross-sectional momentum + trend | Costs are 19 bps per side; only low-turnover strategies survive. No F&O until Phase 4 |
| US core | ₹50,000 (~$570) | Alpaca (paper first, live later) | SPY/QQQ/sector ETFs + 12 mega caps, fractional | Trend following, inverse-vol sized | Zero commission, fractional means a $570 account can hold 15 names. PDT rule forbids day trading under $25k, so this leg is positional by law |
| Research reserve | ₹0 cash, ₹500 to 1,000/mo | Kite Connect paid plan or VPS | Data + infra | Optional until Phase 2 |

Money you send abroad falls under LRS: fine at this size, 20% TCS only applies above ₹10 lakh per year.

Taxes to model now, not later: India delivery gains held under 1 year are STCG at 20%; over 1 year LTCG at 12.5% above ₹1.25 lakh/yr; intraday is speculative business income at slab rate. US gains for an Indian resident are taxed in India (no US capital gains tax for non-residents, 25% withholding on dividends under DTAA).

---

## 2b. What the engine actually trades, and where calls/puts fit

**Today, both legs: buy stocks and ETFs, hold while the trend holds, sell when it breaks.** No shorting, no leverage, no derivatives. India: delivery (CNC) on NSE. US: cash account on Alpaca, fractional shares, ETFs and mega caps. A position that has gone up is sold either when price closes back under its 200-day average (trend broken) or when the weekly rebalance trims it because another asset now deserves more weight.

**Options (calls and puts) are Phase 4, not Phase 1, for arithmetic reasons, not caution:**

| Fact (verified Sep 2026) | Consequence for ₹50k |
|---|---|
| Nifty lot = 65 units, contract value ₹15 to 20 lakh by SEBI rule | One contract is 30 to 40x our India capital |
| Margin to sell one Nifty option: ₹1.5 to 2 lakh | Selling is impossible below ~₹4 lakh capital (need buffer for adverse moves) |
| Buying one at-the-money weekly Nifty option: ₹8k to 15k premium | Possible, but 20 to 30% of the book on one bet that decays every day |
| SEBI FY26 study: 87.7% of individual F&O traders lost money; options were 92% of losses; option **sellers** were the only group with positive median return | The buyer side is where retail money goes to die. The seller side needs capital we do not have yet |
| 59% of index-option turnover happens on expiry day | This is a professional's game against retail impatience |

Our edge is slow: trends measured in weeks and months. Options bleed value daily, so a slow edge expressed through bought options is worse than the same edge expressed through the underlying. When the India book reaches roughly ₹20 lakh (one Nifty lot of NIFTYBEES-equivalent exposure), covered calls and cash-secured puts become a yield overlay on holdings we already own, historically worth 5 to 10% a year on top. That is the version of "playing calls and puts" that survives.

**US leg, leverage without expiry:** leveraged ETFs (SSO 2x S&P, TQQQ 3x Nasdaq) give options-like exposure with no expiry and no theta, only volatility drag. Trend-filtered leveraged ETF is a well-known retail-feasible strategy. Added to Phase 1 as a test item: `trend` on QQQ with a capped TQQQ sleeve, judged by drawdown, not CAGR. Nothing changes until it passes walk-forward.

## 2f. Multi-sector coverage (COO directive, 7 Sep 2026)

We are NOT limited to Nifty/BankNifty/Sensex. `scripts/sector_analysis.py` scans every liquid F&O stock across 10 sectors, ranks sectors by strength, ranks stocks within them, and flags real uptrends (`docs/SECTOR_ANALYSIS.md`). The engine already holds Nifty 50 names across all sectors in the CASH market; this report tilts allocation toward strong sectors. Single-stock F&O options remain Phase 4 (lot-size + capital + decay), expressed until then by buying the stock.

## 3. Phases, gates and kill criteria

Every phase has a gate. We do not move until the gate is passed. This is what separates an engine from a gamble.

### Phase 0 — Foundation (this week) ✅ built today
* Repo `~/Projects/alpha-forge`: data loader with cache, cost-aware vectorised backtester, 4 strategies, risk manager, paper broker, adapters for Alpaca / Kite / Angel One (dry-run by default), daily runner, ORB intraday smell test.
* Gate: tests pass, backtests run on both universes with costs on, results written to `docs/RESULTS.md`.

### Phase 1 — Research (weeks 2 to 6) — in progress
1. ✅ Walk-forward validation of every strategy (train 3y / test 1y, rolling). Results in `docs/WALK_FORWARD.md`: trend and momentum beat their benchmark out of sample in all three universes with 100% of the parameter grid above benchmark; mean reversion fails in India after costs and is retired from the India book.
2. ✅ Parameter robustness: plateau heat maps in `docs/WALK_FORWARD.md`. Trend parameters are stable across halves of history (rank corr 0.57 to 0.58 on stocks); momentum parameters are noise but every set works, which is fine.
2b. ✅ skfolio sizing tested (`docs/SKFOLIO_SIZING.md`): inverse-vol stays default; risk parity to be A/B tested on the Nifty 50 leg in paper.
2c. ✅ Pairs / stat-arb tested (`docs/PAIRS.md`): tiny gross edge, destroyed by retail costs. Retired.
2e. ✅ System hardened to 'best' spec (`docs/SYSTEM.md`): ensemble (trend 60% + momentum 40%) with 12% volatility targeting, plus bootstrap confidence intervals on every metric. Result: ensemble+vol-target is the US book (Sharpe 1.36, MaxDD -14%, was -18%); trend-only stays the India ETF book (too few ETFs to diversify). Robustness: US book P(losing year) 9%, bad-luck MaxDD -25%.
2d. ✅ Daily automation installed (launchd: India 16:00 IST Mon-Fri, US 03:00 IST Tue-Sat, morning brief 08:30 IST). Paper books running: india_paper (trend/ETF), us_paper (trend/US), india_ab_trend vs india_ab_hrp (Nifty 50 A/B).
3. Cost sensitivity: double the slippage assumption. If the edge disappears, it was never there.
4. Regime slices: 2018 (sideways), 2020 (crash), 2022 (rate shock), 2024-26. Know what each strategy does in each.
5. Add strategies in order of evidence: momentum (strongest academic record incl. NSE), trend, mean-reversion on ETFs only, then pairs/stat-arb on Nifty 50, then intraday ORB only if broker intraday data confirms it after costs.
* Gate: at least 2 uncorrelated strategies with OOS Sharpe > 0.8, MaxDD < 20%, each beating its benchmark after costs.

### Phase 2 — Paper trading (weeks 6 to 14, minimum 8 weeks)
* US: Alpaca paper account, real fills, daily cron.
* India: `PaperBroker` with last-close fills, plus Kite/Angel dry-run showing the exact orders it *would* send.
* Track: live vs backtest slippage, missed fills, login failures, cron misses. Fix every operational bug here, where it is free.
* Gate: 8 weeks of paper results within 1 standard deviation of backtest expectation; zero unhandled exceptions in the last 4 weeks; kill switch tested.

### Phase 3 — Live, small (month 4 onward)
* Set `ALPHA_FORGE_LIVE=1` on **one** leg first (US, because costs and legal friction are lowest). ₹25k. Then India at ₹25k two weeks later. Then full ₹50k each.
* Risk manager limits are law: 20% max position, no leverage, -3% day stops trading, -10% drawdown halves size, -15% goes flat and we review together.
* Weekly review ritual (Sunday, 30 min): equity vs benchmark, drawdown, slippage, one improvement.
* Gate to scale capital: 3 consecutive months where live tracks backtest and drawdown stayed inside limits. Then add capital in steps of 50%, never doubling.

### Phase 4 — Expansion (month 7+, only if Phase 3 passed)
* Options overlays (covered calls / cash-secured puts) once the India book can cover one Nifty lot (~₹20 lakh) plus margin buffer. Seller side only, on holdings we own, never naked.
* Pairs / stat-arb book.
* Intraday only if intraday data proves it net of costs AND a static-IP VPS is running.
* Rent the engine: same code serving family accounts is a second income line, but only after your own track record exists.

### Kill criteria (any one triggers full stop and review)
* Drawdown hits 15% from peak.
* Live results diverge from backtest by more than 2 standard deviations for 4 weeks.
* Any unexplained order, fill or login event.
* You feel the urge to override the system by hand. That urge is the signal, every time.

---

## 4. Realistic money projection (so expectations are written down)

Assumptions: engine delivers 20% CAGR (ambitious but achievable for a disciplined systematic retail book), benchmark 13%, you add ₹25,000 per month from other income.

| Year | Engine only, ₹1L start | Engine + ₹25k/month contributions |
|---|---|---|
| 1 | ₹1.2 L | ₹4.5 L |
| 3 | ₹1.7 L | ₹13.6 L |
| 5 | ₹2.5 L | ₹26 L |
| 10 | ₹6.2 L | ₹95 L |
| 15 | ₹15.4 L | ₹2.6 Cr |

The right-hand column is the wealth engine. Trading edge multiplies it; savings feed it. Both matter, and the second matters more at this capital size. The passive-income projects you are already building are the fuel line for this column.

---

## 5. Architecture (what is in the repo)

```
alpha-forge/
├── config/universes.yaml        # nifty50, india_etf, us_core, benchmarks
├── alpha_forge/
│   ├── data/loader.py           # Yahoo -> cached OHLCV dict; swap in Kite/SmartAPI later
│   ├── strategies/              # momentum, trend, meanrev, buyhold (weights matrices)
│   ├── backtest/                # costs.py (India/US presets), engine.py, metrics.py
│   ├── risk/manager.py          # position caps, daily loss, drawdown ladder, KILL_SWITCH file
│   ├── brokers/                 # paper, alpaca (paper default), kite (dry-run), angelone (dry-run)
│   └── paper/runner.py          # daily rebalance: weights -> risk -> orders -> journal
├── scripts/
│   ├── backtest.py              # one strategy x universe with costs, --save for charts
│   ├── research_report.py       # full scoreboard -> docs/RESULTS.md
│   ├── run_daily.py             # cron entry point (paper / alpaca / kite / angelone)
│   └── backtest_orb.py          # intraday ORB smell test on 5m bars
└── tests/test_engine.py         # look-ahead and cost accounting checks
```

Safety design: two independent switches (`live=True` in code AND `ALPHA_FORGE_LIVE=1` in the environment) must both be on before any adapter sends a real order. A file named `KILL_SWITCH` in the repo root halts all trading instantly. Every run writes a JSON report to `data_cache/runs/`.

---

## 6. Next actions

**You (30 minutes total)**
1. Create a free Alpaca account and generate **paper** API keys. Put them in `.env`.
2. Log in to Kite Connect developer console and create a free Personal API app (note the static-IP requirement; for now dry-run mode needs no IP).
3. Enable TOTP on Angel One and copy the TOTP secret (needed only if we choose Angel over Zerodha for the India leg).
4. Send the remaining reference links you mentioned. I will evaluate each one the same way I did fidetolabs.

**Me (next sessions)**
1. Walk-forward and parameter-plateau reports for all four strategies.
2. Pairs/stat-arb strategy on Nifty 50.
3. Kite historical-data adapter so intraday research uses real NSE data.
4. A daily "morning brief" that reads the previous run's JSON and shows equity, drawdown and today's orders.
5. launchd/cron setup for the two daily runs (16:00 IST, 16:30 ET).
