"""Checks of the walk-forward engine (tracker T14, T22, T24). Run with `pytest -q`.

Each test states one property the engine must have, on inputs small enough to
work out by hand.
"""

import numpy as np
import pandas as pd
import pytest

from src.backtest import extract_trades, make_windows, pair_returns, run_selection, simulate
from src.ou import simulate_ou


# ----------------------------------------------------------------- execution lag

def test_signal_at_t_is_held_from_t_plus_1():
    desired = np.zeros(30)
    desired[10:20] = 1
    _, held = pair_returns(desired, 1.0, np.full(30, 0.01), np.zeros(30), cost=0.0)
    assert held[10] == 0 and held[11] == 1          # decided at close 10, bought at close 11
    assert held[20] == 1 and held[21] == 0          # exit decided at close 20, sold at close 21


def test_no_return_is_earned_before_the_position_is_held():
    desired = np.zeros(30)
    desired[10:20] = 1
    net, _ = pair_returns(desired, 1.0, np.full(30, 0.01), np.zeros(30), cost=0.0)
    assert net[:12].sum() == 0                      # first return is close 11 -> close 12
    assert net[12] > 0


def test_lag_zero_executes_at_the_signal_close():
    desired = np.zeros(30)
    desired[10:20] = 1
    _, held = pair_returns(desired, 1.0, np.zeros(30), np.zeros(30), cost=0.0, lag=0)
    assert held[9] == 0 and held[10] == 1


def test_position_is_closed_on_the_last_day():
    desired = np.ones(10)
    _, held = pair_returns(desired, 1.0, np.zeros(10), np.zeros(10), cost=0.0)
    assert held[-1] == 0


# ----------------------------------------------------------------- P&L and costs

def test_daily_return_on_gross_capital():
    # long the spread: $1 of A long, $beta of B short, on capital 1 + beta
    beta, ra, rb = 1.5, 0.02, 0.01
    desired = np.array([1, 1, 1, 0, 0], float)
    net, _ = pair_returns(desired, beta, np.full(5, ra), np.full(5, rb), cost=0.0)
    assert net[2] == pytest.approx((ra - beta * rb) / (1 + beta))


def test_round_trip_costs_two_transactions():
    c = 0.001
    desired = np.array([0, 1, 1, 0, 0, 0], float)
    net, _ = pair_returns(desired, 1.0, np.zeros(6), np.zeros(6), cost=c)
    assert net.sum() == pytest.approx(-2 * c)       # open once, close once


def test_flip_costs_two_transactions():
    c = 0.001
    desired = np.array([1, 1, -1, -1, 0, 0], float)
    net, held = pair_returns(desired, 1.0, np.zeros(6), np.zeros(6), cost=c)
    assert np.abs(np.diff(np.r_[0, held])).sum() == 4   # open, flip (2), close
    assert net.sum() == pytest.approx(-4 * c)


def test_trade_pnls_add_up_to_total_pnl_even_with_flips():
    rng = np.random.default_rng(0)
    n = 200
    desired = np.sign(np.sin(np.arange(n) / 7))     # flips long/short with no flat days
    ra, rb = 0.01 * rng.standard_normal((2, n))
    net, held = pair_returns(desired, 0.8, ra, rb, cost=0.0005)
    trades = extract_trades(held, net, pd.RangeIndex(n), "x", cost=0.0005)
    assert sum(t["pnl"] for t in trades) == pytest.approx(net.sum())
    assert all(t["days"] > 0 for t in trades)


# ----------------------------------------------------------------- windows

def test_windows_are_walk_forward_and_do_not_overlap():
    ws = make_windows(2000, formation=252, trading=126)
    for w in ws:
        assert w.t0 - w.f0 == 252                   # full formation year before trading
        assert w.t1 - w.t0 <= 126
    for prev, nxt in zip(ws, ws[1:]):
        assert nxt.t0 == prev.t1                    # trading blocks tile time, no overlap
    assert ws[-1].t1 <= 2000


# ----------------------------------------------------------------- look-ahead

def _toy_market(seed=3, n=900):
    """Two cointegrated pairs and a random walk, in one sector."""
    rng = np.random.default_rng(seed)
    lb = np.log(40) + np.cumsum(0.012 * rng.standard_normal(n))
    ld = np.log(60) + np.cumsum(0.012 * rng.standard_normal(n))
    x1 = simulate_ou(30, 0, 0.03 * np.sqrt(60), 0, n - 1, rng=rng)[0]
    x2 = simulate_ou(20, 0, 0.03 * np.sqrt(40), 0, n - 1, rng=rng)[0]
    px = pd.DataFrame({"A": np.exp(0.05 + 1.1 * lb + x1), "B": np.exp(lb),
                       "C": np.exp(0.2 + 0.9 * ld + x2), "D": np.exp(ld)},
                      index=pd.bdate_range("2015-01-01", periods=n))
    return px, {"Toy": list(px.columns)}


@pytest.mark.parametrize("strategy", ["distance", "zscore", "sscore", "bertram"])
def test_future_prices_cannot_change_past_returns(strategy):
    """The core look-ahead test: scramble every price after day t, including
    knocking out data, and the strategy's returns up to day t must not move."""
    px, sec = _toy_market()
    t_cut = 700
    sel = run_selection("toy", px, sec, k=2, use_cache=False, verbose=False)
    base = simulate(strategy, px, sel, 10, k=2).committed

    garbage = px.copy()
    rng = np.random.default_rng(99)
    garbage.iloc[t_cut + 1:] *= np.exp(np.cumsum(0.05 * rng.standard_normal(garbage.iloc[t_cut + 1:].shape), axis=0))
    garbage.iloc[t_cut + 5:t_cut + 60, 0] = np.nan  # A stops trading in the future
    sel_g = run_selection("toy", garbage, sec, k=2, use_cache=False, verbose=False)
    after = simulate(strategy, garbage, sel_g, 10, k=2).committed

    cut = px.index[t_cut]
    pd.testing.assert_series_equal(base[:cut], after[:cut])
