import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from alpha_forge.backtest import Backtester, CostModel
from alpha_forge.strategies.base import Strategy


def _prices(n=10, start=100.0, step=1.0):
    idx = pd.bdate_range("2024-01-01", periods=n)
    close = pd.Series(start + step * np.arange(n), index=idx)
    df = pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close, "Volume": 1000}, index=idx)
    return {"AAA": df}


class AlwaysLong(Strategy):
    name = "always_long"

    def generate_weights(self, prices):
        idx = prices["AAA"].index
        return pd.DataFrame({"AAA": 1.0}, index=idx)


def test_no_lookahead_and_costs():
    prices = _prices()
    res = Backtester(CostModel("t", 0, 0, 0), 100).run(AlwaysLong(), prices)
    # fully invested from day 1; total return equals asset return from day1 close to last close
    expected = prices["AAA"]["Close"].iloc[-1] / prices["AAA"]["Close"].iloc[0] - 1
    assert abs(res.summary["total_return_pct"] / 100 - expected) < 1e-9

    res_c = Backtester(CostModel("c", 10, 0, 0), 100).run(AlwaysLong(), prices)
    # one entry of 100% weight costs 10 bps once
    assert res.equity.iloc[-1] > res_c.equity.iloc[-1]
    assert abs((res.equity.iloc[-1] - res_c.equity.iloc[-1]) / res.equity.iloc[-1] - 0.001) < 1e-4


def test_gross_exposure_capped():
    class Levered(AlwaysLong):
        def generate_weights(self, prices):
            return pd.DataFrame({"AAA": 3.0}, index=prices["AAA"].index)

    res = Backtester(CostModel("t", 0, 0, 0), 100).run(Levered(), _prices())
    assert res.weights.abs().sum(axis=1).max() <= 1.0 + 1e-9


def test_risk_state_is_per_account(tmp_path, monkeypatch):
    from alpha_forge.risk import manager as rm
    monkeypatch.setattr(rm, "STATE_FILE", tmp_path / "risk_state.json")
    a = rm.RiskManager(account="india"); a.update_equity(50_000)
    b = rm.RiskManager(account="us"); b.update_equity(570)
    # the tiny US book must not be judged against the India book's peak
    d = b.evaluate(570, {"SPY": 0.5}, n_orders=1)
    assert d.allowed and d.scale == 1.0
    assert a.state_file != b.state_file
