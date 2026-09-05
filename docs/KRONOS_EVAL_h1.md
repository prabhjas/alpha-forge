# Kronos zero-shot calibration test (NeoQuasar/Kronos-small, samples=32, lookback=400)

**NIFTYBEES.NS**, horizon 1 day(s), 250 rolling forecasts (2025-09-03 to 2026-09-02)

| metric | Kronos | naive baseline |
|---|---|---|
| directional accuracy (point forecast) | 48.8% | always-up: 52.0% |
| directional accuracy (P(up) > 0.5) | 49.6% | coin: 50% |
| Brier score (lower is better) | 0.3119 | constant base rate 0.54: 0.2502, coin: 0.2500 |
| median 10-90% band / actual |move| | 3.4x | 1.0x would mean band equals the move |
| mean |forecast move| vs mean |actual move| | 0.354% vs 0.555% | |

Reliability (forecast P(up) bucket -> observed frequency of up):

| p_up          |   n |   forecast |   observed |
|:--------------|----:|-----------:|-----------:|
| (-0.001, 0.3] |  90 |      0.181 |      0.522 |
| (0.3, 0.4]    |  30 |      0.344 |      0.5   |
| (0.4, 0.5]    |  40 |      0.448 |      0.525 |
| (0.5, 0.6]    |  29 |      0.561 |      0.517 |
| (0.6, 0.7]    |  28 |      0.656 |      0.429 |
| (0.7, 1.0]    |  33 |      0.813 |      0.606 |

**SPY**, horizon 1 day(s), 250 rolling forecasts (2025-09-08 to 2026-09-03)

| metric | Kronos | naive baseline |
|---|---|---|
| directional accuracy (point forecast) | 48.4% | always-up: 55.2% |
| directional accuracy (P(up) > 0.5) | 46.8% | coin: 50% |
| Brier score (lower is better) | 0.3946 | constant base rate 0.55: 0.2473, coin: 0.2500 |
| median 10-90% band / actual |move| | 4.9x | 1.0x would mean band equals the move |
| mean |forecast move| vs mean |actual move| | 0.994% vs 0.615% | |

Reliability (forecast P(up) bucket -> observed frequency of up):

| p_up          |   n |   forecast |   observed |
|:--------------|----:|-----------:|-----------:|
| (-0.001, 0.3] | 157 |      0.113 |      0.567 |
| (0.3, 0.4]    |  25 |      0.336 |      0.48  |
| (0.4, 0.5]    |  21 |      0.448 |      0.524 |
| (0.5, 0.6]    |  20 |      0.559 |      0.6   |
| (0.6, 0.7]    |  16 |      0.658 |      0.562 |
| (0.7, 1.0]    |  11 |      0.83  |      0.455 |
