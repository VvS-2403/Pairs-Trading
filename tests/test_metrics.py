"""Checks of the performance metrics on series with known answers (tracker T23)."""

import numpy as np
import pandas as pd
import pytest

from src.metrics import (compute_metrics, max_drawdown, newey_west_t, nw_lags,
                         sharpe_diff_bootstrap)


def test_max_drawdown_by_hand():
    # wealth 1.10, 0.55, 0.66: worst fall is 1.10 -> 0.55, i.e. -50%
    assert max_drawdown(pd.Series([0.10, -0.50, 0.20])) == pytest.approx(-0.5)


def test_sharpe_and_volatility_recover_true_values():
    rng = np.random.default_rng(1)
    mu_d, sd_d = 0.0004, 0.01                      # true annual Sharpe = 0.0004/0.01*sqrt(252) = 0.635
    r = pd.Series(mu_d + sd_d * rng.standard_normal(252 * 400))
    m = compute_metrics(r)
    assert m["Ann. vol %"] == pytest.approx(100 * sd_d * np.sqrt(252), rel=0.01)
    # even 400 years of data pin the Sharpe ratio down only to SE = 1/sqrt(400) = 0.05
    assert m["Sharpe"] == pytest.approx(mu_d / sd_d * np.sqrt(252), abs=3 / np.sqrt(400))


def test_lo_standard_error_matches_monte_carlo_spread():
    """Lo (2002): under IID returns the annualised Sharpe of Y years of daily data
    has SE sqrt((1 + SR_d^2 / 2) / n) * sqrt(252). Check it against the actual
    spread of Sharpe estimates over many simulated 4-year histories, at a high
    true Sharpe (2.0) where a wrong frequency in the SR^2 term shows clearly."""
    rng = np.random.default_rng(2)
    sr_true, years, reps = 2.0, 4, 3000
    sd_d = 0.01
    mu_d = sr_true / np.sqrt(252) * sd_d
    sims = mu_d + sd_d * rng.standard_normal((reps, 252 * years))
    est = sims.mean(1) / sims.std(1, ddof=1) * np.sqrt(252)
    reported = compute_metrics(pd.Series(sims[0]))["Sharpe SE (Lo)"]
    assert reported == pytest.approx(est.std(), rel=0.08)


def test_newey_west_controls_size_under_autocorrelation():
    """Positively autocorrelated returns with zero mean: the IID t-test rejects far
    too often; the Newey-West t should stay close to the nominal 5%."""
    rng = np.random.default_rng(3)
    reps, n, phi = 400, 1000, 0.5
    naive = nw = 0
    for _ in range(reps):
        e = rng.standard_normal(n)
        r = np.empty(n)
        r[0] = e[0]
        for t in range(1, n):
            r[t] = phi * r[t - 1] + e[t]
        naive += abs(r.mean() / (r.std(ddof=1) / np.sqrt(n))) > 1.96
        nw += abs(newey_west_t(r, lags=nw_lags(n))) > 1.96
    assert naive / reps > 0.15
    assert nw / reps < 0.10


def test_sortino_uses_downside_deviation():
    r = pd.Series([0.02, -0.01, 0.03, -0.02] * 100)
    downside = np.sqrt(np.mean(np.minimum(r, 0) ** 2)) * np.sqrt(252)
    assert compute_metrics(r)["Sortino"] == pytest.approx(r.mean() * 252 / downside)


def test_market_beta():
    rng = np.random.default_rng(4)
    idx = pd.bdate_range("2020-01-01", periods=3000)
    m = pd.Series(0.01 * rng.standard_normal(3000), index=idx)
    r = 0.5 * m + pd.Series(0.005 * rng.standard_normal(3000), index=idx)
    assert compute_metrics(r, benchmark=m)["Market beta"] == pytest.approx(0.5, abs=0.03)


def test_sharpe_difference_bootstrap():
    rng = np.random.default_rng(5)
    n = 252 * 10
    noise = rng.standard_normal((2, n)) * 0.01
    same = sharpe_diff_bootstrap(noise[0] + 0.0003, noise[1] + 0.0003, n_boot=500, rng=rng)
    diff = sharpe_diff_bootstrap(noise[0] + 0.0012, noise[1], n_boot=500, rng=rng)
    assert same["p_value"] > 0.05
    assert diff["p_value"] < 0.01 and diff["ci_low"] > 0
