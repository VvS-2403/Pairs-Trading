"""Tests of src/cointegration.py: ADF, Engle-Granger in both directions, Benjamini-Hochberg (task T09).

Simulated series use fixed seeds. The size check (independent random walks) takes a few seconds.
"""

import numpy as np
import pytest
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import coint

from src.cointegration import (adf_test, benjamini_hochberg, engle_granger, engle_granger_both,
                               naive_residual_adf, ols)

# statsmodels >= 0.15 warns that adfuller's return type will change; the code still works.
pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")


def _walk(rng, n):
    return np.cumsum(rng.standard_normal(n))


def _ar1(rng, n, phi):
    u = np.zeros(n)
    for t in range(1, n):
        u[t] = phi * u[t - 1] + rng.standard_normal()
    return u


def test_ols_recovers_exact_line():
    x = np.linspace(0, 10, 50)
    mu, beta, resid = ols(2.0 + 1.5 * x, x)
    assert mu == pytest.approx(2.0) and beta == pytest.approx(1.5)
    assert np.abs(resid).max() < 1e-9


def test_adf_rejects_stationary_but_not_random_walk():
    rng = np.random.default_rng(0)
    stat_ar, p_ar, lags = adf_test(_ar1(rng, 500, 0.9))
    _, p_rw, _ = adf_test(_walk(rng, 500))
    assert p_ar < 0.01 and p_rw > 0.05
    assert isinstance(lags, (int, np.integer))


def test_engle_granger_detects_cointegrated_pair_and_beta():
    rng = np.random.default_rng(0)
    x = _walk(rng, 500)
    a = 1.0 + 0.8 * x + _ar1(rng, 500, 0.9)           # spread is stationary
    r = engle_granger(a, x, "a", "x")
    assert r.pvalue < 0.01
    assert r.beta == pytest.approx(0.8, abs=0.1)       # super-consistent estimate
    assert (r.y, r.x) == ("a", "x") and len(r.resid) == 500


def test_engle_granger_does_not_reject_independent_walks():
    rng = np.random.default_rng(0)
    assert engle_granger(_walk(rng, 500), _walk(rng, 500)).pvalue > 0.05


def test_engle_granger_matches_statsmodels_coint():
    rng = np.random.default_rng(3)
    x = _walk(rng, 300)
    a = 0.5 + 1.2 * x + _ar1(rng, 300, 0.8)
    stat, p, _ = coint(a, x, trend="c", autolag="aic")
    r = engle_granger(a, x)
    assert r.stat == pytest.approx(stat) and r.pvalue == pytest.approx(p)


def test_engle_granger_both_uses_larger_p_and_smaller_p_direction():
    rng = np.random.default_rng(4)
    x = _walk(rng, 252)
    a = 1.0 + 0.8 * x + _ar1(rng, 252, 0.85)
    r1, r2 = engle_granger(a, x, "a", "x"), engle_granger(x, a, "x", "a")
    best, p_both = engle_granger_both(a, x, "a", "x")
    assert p_both == pytest.approx(max(r1.pvalue, r2.pvalue))
    assert best.pvalue == pytest.approx(min(r1.pvalue, r2.pvalue))
    assert best.pvalue <= p_both
    assert {best.y, best.x} == {"a", "x"}


@pytest.fixture(scope="module")
def size_experiment():
    """Independent random walks, 252 days (the formation window): the null is true."""
    rng = np.random.default_rng(1)
    eg, naive = [], []
    for _ in range(300):
        y, x = _walk(rng, 252), _walk(rng, 252)
        eg.append(engle_granger(y, x).pvalue < 0.05)
        naive.append(naive_residual_adf(y, x)[1] < 0.05)
    return float(np.mean(eg)), float(np.mean(naive))


def test_engle_granger_size_near_five_percent(size_experiment):
    assert size_experiment[0] < 0.10


def test_naive_residual_adf_over_rejects(size_experiment):
    """Why MacKinnon critical values are needed (E2b): plain ADF on OLS residuals rejects too often."""
    eg_rate, naive_rate = size_experiment
    assert naive_rate > 0.12 and naive_rate > eg_rate + 0.05


def test_benjamini_hochberg_worked_example():
    p = [0.003, 0.012, 0.03, 0.04, 0.20]
    assert benjamini_hochberg(p, 0.10) == 4            # thresholds .02 .04 .06 .08 .10
    assert benjamini_hochberg(p[::-1], 0.10) == 4      # order of input does not matter
    assert sum(pv < 0.05 / len(p) for pv in p) == 1    # Bonferroni keeps only one


def test_benjamini_hochberg_edge_cases():
    assert benjamini_hochberg([], 0.10) == 0
    assert benjamini_hochberg([0.5, 0.6, 0.9], 0.10) == 0
    assert benjamini_hochberg([1e-6] * 10, 0.10) == 10


def test_benjamini_hochberg_matches_statsmodels():
    rng = np.random.default_rng(5)
    for q in (0.05, 0.10, 0.20):
        p = rng.uniform(size=196) ** 3                  # skewed towards small p-values
        assert benjamini_hochberg(p, q) == int(multipletests(p, alpha=q, method="fdr_bh")[0].sum())
