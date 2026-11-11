"""Performance metrics with standard errors (tests/test_metrics.py checks each one).

Returns are treated as excess returns: a pair is long $1 and short $beta, so it is
self-financing and the risk-free rate is not subtracted (as in Gatev et al. 2006).

Sharpe standard error under IID returns (Lo 2002): for n daily returns with daily
Sharpe SR_d, SE(SR_d) = sqrt((1 + SR_d^2 / 2) / n), and the annualised SE is
sqrt(252) times that. The SR^2/2 term is the cost of estimating the volatility.

Pairs returns are autocorrelated (a position lasts days), which IID formulas ignore.
The t-statistic of the mean daily return therefore uses Newey-West (1987) HAC
standard errors with the Newey-West (1994) lag rule floor(4 (n/100)^(2/9)).
Since t ~ SR_annual * sqrt(years), "Sharpe SE (HAC)" = Sharpe / t is the matching
autocorrelation-robust Sharpe standard error.

Whether one strategy beats another is tested on the difference of Sharpe ratios
with a circular block bootstrap that resamples both return series on the same
days (Politis & Romano 1992; the idea of Ledoit & Wolf 2008).
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import config as C

DAYS = 252


def max_drawdown(r):
    """Largest peak-to-trough fall of wealth (1 + r).cumprod(), as a negative fraction."""
    wealth = (1 + pd.Series(r)).cumprod()
    return float((wealth / wealth.cummax() - 1).min())


def nw_lags(n):
    """Newey-West (1994) automatic lag: floor(4 (n / 100)^(2/9)); 9 lags for 16 years."""
    return int(np.floor(4 * (n / 100) ** (2 / 9)))


def newey_west_t(r, lags=C.NW_LAGS):
    """t-statistic of the mean return with HAC (Bartlett kernel) standard errors."""
    y = np.asarray(r, dtype=float)
    if len(y) < 10 or np.allclose(y, 0):
        return np.nan
    lags = nw_lags(len(y)) if lags is None else lags
    fit = sm.OLS(y, np.ones_like(y)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(fit.tvalues[0])


def sharpe_se_lo(r):
    """Annualised IID standard error of the annualised Sharpe ratio (Lo 2002)."""
    r = np.asarray(r, dtype=float)
    sr_d = r.mean() / r.std(ddof=1)
    return float(np.sqrt((1 + 0.5 * sr_d ** 2) / len(r)) * np.sqrt(DAYS))


def compute_metrics(r, benchmark=None, trades=None):
    """Annualised metrics for a daily return series."""
    r = pd.Series(r).dropna()
    years = len(r) / DAYS
    mu, sd = r.mean() * DAYS, r.std() * np.sqrt(DAYS)
    sharpe = mu / sd if sd > 0 else np.nan
    downside = np.sqrt(np.mean(np.minimum(r, 0) ** 2)) * np.sqrt(DAYS)   # deviation below 0
    mdd = max_drawdown(r)
    t_nw = newey_west_t(r)
    out = {
        "Ann. return %": 100 * mu,
        "Ann. vol %": 100 * sd,
        "Sharpe": sharpe,
        "Sharpe SE (Lo)": sharpe_se_lo(r) if np.isfinite(sharpe) else np.nan,
        "Sharpe SE (HAC)": abs(sharpe / t_nw) if np.isfinite(sharpe) and np.isfinite(t_nw) and t_nw != 0 else np.nan,
        "NW t-stat": t_nw,
        "Sortino": mu / downside if downside > 0 else np.nan,
        "Max DD %": 100 * mdd,
        "Calmar": mu / abs(mdd) if mdd < 0 else np.nan,
        "Total return %": 100 * ((1 + r).prod() - 1),
        "Years": years,
    }
    if benchmark is not None:
        j = pd.concat([r, benchmark], axis=1, join="inner").dropna()
        if len(j) > 30 and j.iloc[:, 1].std() > 0:
            c = np.cov(j.iloc[:, 0], j.iloc[:, 1])
            out["Market beta"] = c[0, 1] / c[1, 1]
            out["Market corr"] = float(j.corr().iloc[0, 1])
    if trades is not None and len(trades):
        out["Trades"] = len(trades)
        out["Hit rate %"] = 100 * float((trades["pnl"] > 0).mean())
        out["Avg days held"] = float(trades["days"].mean())
    return out


def metrics_table(results, benchmark=None, use="committed"):
    rows = {}
    for res in results:
        rows[res.strategy] = compute_metrics(getattr(res, use), benchmark, res.trades)
    return pd.DataFrame(rows).T


def sharpe_diff_bootstrap(r1, r2, block=21, n_boot=5000, rng=None):
    """Is Sharpe(r1) - Sharpe(r2) different from 0?

    Circular block bootstrap: draw blocks of `block` consecutive days (21 = one month,
    longer than a typical holding period, so autocorrelation survives inside blocks)
    and use the same days for both series, so their correlation is kept. The p-value
    compares the bootstrap distribution of (d* - d) with the observed d.
    """
    rng = np.random.default_rng(C.SEED) if rng is None else rng
    x = np.column_stack([np.asarray(r1, float), np.asarray(r2, float)])
    x = x[np.isfinite(x).all(axis=1)]
    n = len(x)

    def sharpe(a):
        return a.mean(axis=-2) / a.std(axis=-2, ddof=1) * np.sqrt(DAYS)

    s = sharpe(x)
    d = float(s[0] - s[1])
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(n_boot, nb))
    idx = ((starts[:, :, None] + np.arange(block)) % n).reshape(n_boot, -1)[:, :n]
    sb = sharpe(x[idx])
    db = sb[:, 0] - sb[:, 1]
    return dict(sharpe_1=float(s[0]), sharpe_2=float(s[1]), diff=d,
                ci_low=float(np.quantile(db, 0.025)), ci_high=float(np.quantile(db, 0.975)),
                p_value=float(np.mean(np.abs(db - d) >= abs(d))))
