# Alpha Forge — CEO Mandate

*Prabhjas (owner/board) has asked Claude to act as financial CEO: make the trading decisions, own the results, and report. This is the charter. Updated 6 Sep 2026.*

## 1. The honest target (what "75% in a month" becomes)

A CEO who promises the board 75% profit in a month is either lying or about to lose everything. So here is the real objective I commit to and will be measured on:

| Objective | Commitment | Grounded in |
|---|---|---|
| **Profitable year** | ≥ 85% probability | Bootstrap: US book P(losing year) 9%, India trend 13% |
| **Annual return** | 15–20%, target 18% | Out-of-sample walk-forward, costs on |
| **Positive months** | 65–72% of months | Historical monthly hit-rate of the chosen books |
| **Max drawdown** | held under 20%, halt at 15% | Risk manager + vol targeting |
| **Beat the index** | by 3–8 points/year after costs | Every walk-forward fold |

"75% success" is achievable read as **a 75%+ chance of a good year and ~70% of months green.** Read as "75% profit in a month," it is not achievable by anyone alive without gambling, and I will not pretend otherwise or risk your money chasing it.

## 2. How the money actually grows

Wealth = your capital × time × (1 + return)^years, fed by monthly contributions. At 18%/year, ₹1 lakh plus ₹25k/month becomes ~₹13.6 lakh in 3 years and ~₹95 lakh in 10. The engine's job is the 18% and, more importantly, never blowing up so the compounding never resets. Lakhs come from time, not from a month.

## 3. Decision rights (what I decide without asking)

* Which strategies run, their parameters, position sizing, when to enter/exit, rebalancing.
* Killing strategies that fail the cost-aware out-of-sample test. Retired so far: mean-reversion (India), pairs, SMA crossover, FVG.
* The current books: **US = ensemble (trend+momentum) + 12% vol target; India ETF = trend; Nifty 50 = trend vs risk-parity A/B.**

## 4. Board decisions (only you can make these)

* Adding real money, and how much. I never move real funds; you execute, I build and monitor.
* Going live (setting `ALPHA_FORGE_LIVE=1`).
* Providing broker API keys.

## 5. Risk limits (non-negotiable, protect the capital)

20% max per position · no leverage (pre-Phase 4) · stop trading a book at -3% day · halve size at -10% drawdown · flat + review at -15% · `KILL_SWITCH` file halts everything.

## 5b. Pre-live safety findings (AngelOne connected 7 Sep 2026)

The live read of the AngelOne account revealed two things that MUST be handled before real orders:

1. **Existing holdings present** (EIHOTEL, IOC, CESC, HUDCO, SUZLON, etc.). The rebalancer currently treats every holding as part of its book, so live it could try to SELL your existing shares to fund targets. **Fix before live: sleeve isolation** — the algo tracks and trades only the positions IT opened (via order tags + a local ledger), and never touches your pre-existing holdings.
2. **Available cash ₹21.** The account has almost no free cash. A real pilot needs funds added, ring-fenced as the algo's sleeve.

Until sleeve isolation ships and is tested, the India book stays on the PAPER broker even after keys are in. AngelOne is used for live DATA only, not live orders.

## 6. Reporting

* **Daily**: automated morning brief (08:30 IST).
* **Weekly**: automated review every Sunday 18:00 IST, equity vs benchmark per book.
* **Monthly**: I write up performance, what worked, what I changed.

## 7. The path (unchanged, this is the plan we execute)

1. **Now → ~8 weeks**: paper books run daily (LIVE NOW). Prove fills match the backtest.
2. **After 8 weeks of clean paper**: small real pilot, amount you can afford to lose, you executing.
3. **After 3 clean months live**: scale capital in steps.
4. **At ~₹20 lakh book**: covered-call/cash-secured-put options overlay for extra yield.

## 8. What I need from the board to start the clock

1. Alpaca **paper** API keys → `.env`.
2. A Kite Connect Personal app (free) → `.env`.

Until then the engine runs on simulated fills, which proves the logic but not the execution. The 8-week clock starts when real paper fills do.
