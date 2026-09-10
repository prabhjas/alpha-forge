# Options paper test — does buying calls on many stocks and holding a few days work?

Tested the exact idea on 8 years of real Nifty 50 data (2019-2026). Buy an at-the-money
call on a 20-day breakout in an uptrend, hold up to 5 days, sell. Black-Scholes pricing,
IV = realised vol, realistic option costs (≈4% bid-ask spread + STT/brokerage on premium).

## Result: it loses money

| Metric | Buy the CALL option | Same signal, BUY THE STOCK |
|---|---|---|
| Trades | 3,851 | — |
| Win rate | 41.9% | 47.7% |
| Avg per trade (after costs) | **−1.8%** | +0.08% |
| Median trade | **−10.6%** | — |
| Profit factor | 0.92 (<1 = losing) | — |
| Best / worst | +348% / −99% | — |

## Why it loses even when direction is right 42% of the time
* **Theta decay:** the option loses value every day just from time passing. Holding "a few days" bleeds premium.
* **Wide spreads:** stock options trade ~4% bid-ask; you pay that round-trip on every trade.
* The median trade loses 10.6%. A few +300% lottery wins don't offset the constant bleed.

This matches SEBI's finding that option buyers are the ones funding the market, and the AngelOne
analyst-call screenshot (CE calls down 36-62%). The same directional view, expressed by BUYING THE
STOCK, is roughly break-even-positive with none of the decay. That is why our engine buys stocks.

## When options make sense for us: Phase 4, as the SELLER
At ~₹20 lakh the account can run covered calls / cash-secured puts on holdings we already own —
collecting premium (theta works FOR us), the only options side the data shows is profitable.
