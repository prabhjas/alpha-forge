# Deep options analysis — calls & puts, buying & selling (Nifty 50, 2018-2026)

Black-Scholes pricing, IV = realised vol, realistic costs (~4% option bid-ask + fees).
All four quadrants tested honestly. Question: does ANY options strategy beat owning the stock?

## Results

### Buying options (directional, hold 5 days)
| Strategy | Trades | Win rate | Avg/trade | Median | Verdict |
|---|---|---|---|---|---|
| Buy CALL (on uptrend breakout) | 4,027 | 39.8% | −0.1% | −13.9% | **Loses** |
| Buy PUT (on downtrend breakdown) | 1,931 | 38.6% | +2.5% | −17.6% | Tail-driven only |

Buying calls loses. Buying puts shows a small positive average — but look at the detail:
you LOSE on 61% of trades and the median trade is −17.6%. The positive average comes entirely
from rare crash payoffs (Mar 2020 etc.). That is **crash insurance, not an income engine** —
brutal to hold, period-dependent, and not a reliable edge. Useful at most as an occasional
portfolio hedge in a confirmed downtrend, never as a way to "get big."

### Selling premium (monthly income, portfolio)
| Strategy | CAGR | Sharpe | MaxDD | Win-months |
|---|---|---|---|---|
| Covered call (own stock, sell 5% OTM call) | 14.2% | 0.90 | −33.6% | 75% |
| Cash-secured put (sell 5% OTM put) | 0.2% | 0.09 | −29.2% | 73% |
| **Buy & hold the stock (benchmark)** | **18.1%** | **1.06** | −38.2% | — |

Covered calls give steady income (75% of months green) but **cap upside** — in India's strong
bull market they underperformed simply owning the stock (14.2% vs 18.1%). Cash-secured puts were
basically flat here: small premiums, hit hard in drawdowns.

## The honest verdict
**In this market, no options strategy beat owning the stock.** Buying options loses (calls) or is
pure tail-insurance (puts). Selling premium is real income but caps growth and underperformed buy-hold.

This is the Buffett point, not against it: Buffett *sells* puts on companies he'd happily own, and
*never* buys speculative options. Even that conservative, correct use of options underperformed just
holding good stocks over this period. The growth engine is owning the right stocks; options are an
income/hedge overlay for later, not a path to fast riches.

## Where options fit for us (unchanged, now proven from every angle)
* **Phase 4 (~₹20 lakh):** covered calls on holdings we own, for income, accepting capped upside.
* **Occasional protective puts** as a hedge in a confirmed downtrend — insurance, budgeted, not for profit.
* **Never** buy calls/puts as a growth strategy. The data across 6,000 simulated trades says no.
