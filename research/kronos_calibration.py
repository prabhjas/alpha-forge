#!/usr/bin/env python
"""Is Kronos (NeoQuasar) worth anything for us? Test what the Instagram comment asked:
does it produce a CALIBRATED probability of direction, and is its forecast band
narrower than the move it is forecasting?

Method: rolling zero-shot. For each of the last N trading days, feed the previous
`lookback` daily bars, sample `n_samples` forecast paths for the next `horizon`
bars, and read off P(up) = fraction of samples whose close > today's close.
Score with directional accuracy, Brier score vs. a constant base-rate forecast,
and a reliability table. No fine-tuning, no cherry-picking of windows.
"""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor" / "Kronos"))
warnings.filterwarnings("ignore")

from alpha_forge.data.loader import load_prices  # noqa: E402


def sample_paths(predictor, x_df, x_ts, y_ts, horizon, n_samples, T=1.0, top_p=0.9):
    """Like predictor.predict but returns every sampled path instead of their mean."""
    holder = {}
    tok = predictor.tokenizer
    orig = tok.decode

    def capture(tokens, half=False):
        z = orig(tokens, half=half)
        holder["z"] = z.detach().cpu().numpy()
        return z

    tok.decode = capture
    try:
        predictor.predict(x_df, x_ts, y_ts, pred_len=horizon, T=T, top_p=top_p, sample_count=n_samples, verbose=False)
    finally:
        tok.decode = orig
    z = holder["z"]                                   # (n_samples, seq, 6) normalised
    x = x_df[["open", "high", "low", "close", "volume", "amount"]].values.astype(np.float32)
    mean, std = x.mean(axis=0), x.std(axis=0)
    z = z * (std + 1e-5) + mean
    return z[:, -horizon:, 3]                          # sampled closes, shape (n_samples, horizon)


def evaluate(symbol, df, predictor, n_days, lookback, horizon, n_samples):
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna().copy()
    df["amount"] = df["volume"] * df[["open", "high", "low", "close"]].mean(axis=1)
    df.index = pd.to_datetime(df.index)
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    rows = []
    t0 = time.time()
    end_positions = range(len(df) - horizon - n_days, len(df) - horizon)
    for k, end in enumerate(end_positions):
        x_df = df.iloc[end - lookback:end].reset_index(drop=True)
        x_ts = pd.Series(df.index[end - lookback:end])
        y_ts = pd.Series(df.index[end:end + horizon])
        last = float(df["close"].iloc[end - 1])
        actual = float(df["close"].iloc[end + horizon - 1])
        closes = sample_paths(predictor, x_df, x_ts, y_ts, horizon, n_samples)
        final = closes[:, -1]
        rows.append({
            "date": df.index[end + horizon - 1], "symbol": symbol,
            "p_up": float((final > last).mean()),
            "point_ret": float(final.mean() / last - 1),
            "band_width": float(np.percentile(final, 90) / last - np.percentile(final, 10) / last),
            "actual_ret": actual / last - 1,
        })
        if k % 20 == 0:
            print(f"  {symbol} {k}/{n_days}  {time.time()-t0:.0f}s", flush=True)
    return pd.DataFrame(rows)


def report(res: pd.DataFrame, train_base_rate: float, horizon: int) -> str:
    up = (res.actual_ret > 0).astype(float)
    dir_acc = float(((res.point_ret > 0) == (res.actual_ret > 0)).mean())
    prob_acc = float(((res.p_up > 0.5) == (res.actual_ret > 0)).mean())
    brier = float(((res.p_up - up) ** 2).mean())
    brier_base = float(((train_base_rate - up) ** 2).mean())
    brier_coin = 0.25
    band_vs_move = float((res.band_width / res.actual_ret.abs().replace(0, np.nan)).median())
    bins = pd.cut(res.p_up, [0, .3, .4, .5, .6, .7, 1.0], include_lowest=True)
    rel = res.groupby(bins, observed=True).agg(n=("p_up", "size"), forecast=("p_up", "mean")).assign(observed=up.groupby(bins, observed=True).mean())
    lines = [
        f"**{res.symbol.iloc[0]}**, horizon {horizon} day(s), {len(res)} rolling forecasts ({res.date.min().date()} to {res.date.max().date()})", "",
        "| metric | Kronos | naive baseline |", "|---|---|---|",
        f"| directional accuracy (point forecast) | {dir_acc:.1%} | always-up: {up.mean():.1%} |",
        f"| directional accuracy (P(up) > 0.5) | {prob_acc:.1%} | coin: 50% |",
        f"| Brier score (lower is better) | {brier:.4f} | constant base rate {train_base_rate:.2f}: {brier_base:.4f}, coin: {brier_coin:.4f} |",
        f"| median 10-90% band / actual |move| | {band_vs_move:.1f}x | 1.0x would mean band equals the move |",
        f"| mean |forecast move| vs mean |actual move| | {res.point_ret.abs().mean():.3%} vs {res.actual_ret.abs().mean():.3%} | |",
        "", "Reliability (forecast P(up) bucket -> observed frequency of up):", "",
        rel.round(3).to_markdown(), "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=["NIFTYBEES.NS", "SPY"])
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--lookback", type=int, default=400)
    ap.add_argument("--horizon", type=int, default=1)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--model", default="NeoQuasar/Kronos-small")
    a = ap.parse_args()

    from model import Kronos, KronosTokenizer, KronosPredictor  # vendor/Kronos
    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    model = Kronos.from_pretrained(a.model)
    predictor = KronosPredictor(model, tokenizer, max_context=512)
    print("device:", predictor.device)

    prices = load_prices(a.symbols, start="2015-01-01")
    out = [f"# Kronos zero-shot calibration test ({a.model}, samples={a.samples}, lookback={a.lookback})", ""]
    for sym in a.symbols:
        df = prices[sym]
        n_total = len(df)
        train = df["Close"].iloc[: n_total - a.horizon - a.days]
        base_rate = float((train.pct_change(a.horizon).dropna() > 0).mean())
        res = evaluate(sym, df, predictor, a.days, a.lookback, a.horizon, a.samples)
        res.to_csv(ROOT / "reports" / f"kronos_{sym.replace('.', '_')}_h{a.horizon}.csv", index=False)
        block = report(res, base_rate, a.horizon)
        print(block)
        out.append(block)
    Path(ROOT / "docs" / f"KRONOS_EVAL_h{a.horizon}.md").write_text("\n".join(out))
    print(f"wrote docs/KRONOS_EVAL_h{a.horizon}.md")


if __name__ == "__main__":
    main()
