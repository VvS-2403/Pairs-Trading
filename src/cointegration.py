"""Unit-root and cointegration tests.

ADF regression:  dX_t = alpha + gamma X_{t-1} + sum_i delta_i dX_{t-i} + eps_t.
For a discretised OU spread gamma = e^{-kappa dt} - 1, so H0: gamma = 0 is
exactly H0: kappa = 0 (no mean reversion). Lag order by AIC (Said & Dickey 1984).

Engle-Granger (1987): regress a_t on b_t, then test the residuals for a unit
root. Because beta is fitted to make the residuals look stationary, the
residual test needs Engle-Granger critical values (MacKinnon 2010), which
statsmodels' `coint` provides. Running `adfuller` on the residuals instead
over-rejects; experiment E2 measures by how much.
"""

from dataclasses import dataclass

import numpy as np
from statsmodels.tsa.stattools import adfuller, coint


@dataclass
class EGResult:
    y: str
    x: str
    beta: float
    mu: float
    stat: float
    pvalue: float
    resid: np.ndarray


def adf_test(x, regression="c", autolag="AIC", maxlag=None):
    """ADF test; returns (statistic, p-value, lags used)."""
    stat, p, lags, *_ = adfuller(np.asarray(x, dtype=float), regression=regression,
                                 autolag=autolag, maxlag=maxlag)
    return stat, p, lags


def ols(y, x):
    """OLS of y on [1, x]; returns (mu, beta, residuals)."""
    xm, ym = x.mean(), y.mean()
    beta = ((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum()
    mu = ym - beta * xm
    return mu, beta, y - mu - beta * x


def engle_granger(y, x, y_name="y", x_name="x", maxlag=None):
    """Two-step Engle-Granger test of y on x with MacKinnon p-values."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    stat, p, _ = coint(y, x, trend="c", autolag="aic", maxlag=maxlag)
    mu, beta, resid = ols(y, x)
    return EGResult(y_name, x_name, beta, mu, stat, p, resid)


def engle_granger_both(a, b, a_name, b_name, maxlag=None):
    """Run Engle-Granger in both directions.

    Returns (result with the smaller p-value, larger of the two p-values). A pair
    counts as cointegrated only if the larger p-value is below the threshold.
    """
    r1 = engle_granger(a, b, a_name, b_name, maxlag)
    r2 = engle_granger(b, a, b_name, a_name, maxlag)
    best = r1 if r1.pvalue <= r2.pvalue else r2
    return best, max(r1.pvalue, r2.pvalue)


def naive_residual_adf(y, x):
    """The wrong test: plain ADF critical values applied to OLS residuals (E2)."""
    _, _, resid = ols(np.asarray(y, float), np.asarray(x, float))
    return adf_test(resid, regression="c")


def benjamini_hochberg(pvalues, q):
    """Number of hypotheses rejected by the Benjamini-Hochberg step-up rule."""
    p = np.sort(np.asarray(pvalues, dtype=float))
    if p.size == 0:
        return 0
    crit = q * np.arange(1, p.size + 1) / p.size
    below = np.nonzero(p <= crit)[0]
    return int(below[-1] + 1) if below.size else 0
