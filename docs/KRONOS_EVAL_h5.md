# Kronos zero-shot calibration test (NeoQuasar/Kronos-small, samples=32, lookback=400)

**NIFTYBEES.NS**, horizon 5 day(s), 120 rolling forecasts (2026-03-13 to 2026-09-02)

| metric | Kronos | naive baseline |
|---|---|---|
| directional accuracy (point forecast) | 53.3% | always-up: 47.5% |
| directional accuracy (P(up) > 0.5) | 54.2% | coin: 50% |
| Brier score (lower is better) | 0.2927 | constant base rate 0.58: 0.2600, coin: 0.2500 |
| median 10-90% band / actual |move| | 2.8x | 1.0x would mean band equals the move |
| mean |forecast move| vs mean |actual move| | 0.745% vs 1.416% | |

Reliability (forecast P(up) bucket -> observed frequency of up):

| p_up          |   n |   forecast |   observed |
|:--------------|----:|-----------:|-----------:|
| (-0.001, 0.3] |  52 |      0.184 |      0.462 |
| (0.3, 0.4]    |  19 |      0.357 |      0.368 |
| (0.4, 0.5]    |  15 |      0.45  |      0.533 |
| (0.5, 0.6]    |   6 |      0.557 |      0.333 |
| (0.6, 0.7]    |   6 |      0.656 |      0.667 |
| (0.7, 1.0]    |  22 |      0.849 |      0.545 |

**SPY**, horizon 5 day(s), 120 rolling forecasts (2026-03-16 to 2026-09-03)

| metric | Kronos | naive baseline |
|---|---|---|
| directional accuracy (point forecast) | 41.7% | always-up: 58.3% |
| directional accuracy (P(up) > 0.5) | 40.8% | coin: 50% |
| Brier score (lower is better) | 0.4204 | constant base rate 0.62: 0.2441, coin: 0.2500 |
| median 10-90% band / actual |move| | 3.7x | 1.0x would mean band equals the move |
| mean |forecast move| vs mean |actual move| | 2.135% vs 1.622% | |

Reliability (forecast P(up) bucket -> observed frequency of up):

| p_up          |   n |   forecast |   observed |
|:--------------|----:|-----------:|-----------:|
| (-0.001, 0.3] |  88 |      0.128 |      0.591 |
| (0.3, 0.4]    |   9 |      0.337 |      0.667 |
| (0.4, 0.5]    |   4 |      0.438 |      0.75  |
| (0.5, 0.6]    |   2 |      0.547 |      0.5   |
| (0.6, 0.7]    |   1 |      0.625 |      0     |
| (0.7, 1.0]    |  16 |      0.83  |      0.5   |
