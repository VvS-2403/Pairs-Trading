"""Performance metrics with standard errors.

Sharpe-ratio standard error under IID returns (Lo 2002): SE = sqrt((1 + SR^2 / 2) / T),
with SR annualised and T in years. The t-statistic of the mean daily return uses
Newey-West (1987) HAC standard errors.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import config as C


def max_drawdown(r):
    wealth = (1 + r).cumprod()
    return float((wealth / wealth.cummax() - 1).min())


def newey_west_t(r, lags=C.NW_LAGS):
    y = np.asarray(r, dtype=float)
    if len(y) < 10 or np.allclose(y, 0):
        return np.nan
    fit = sm.OLS(y, np.ones_like(y)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(fit.tvalues[0])


def compute_metrics(r, benchmark=None, trades=None):
    """Annualised metrics for a daily return series."""
    r = pd.Series(r).dropna()
    years = len(r) / 252
    mu, sd = r.mean() * 252, r.std() * np.sqrt(252)
    sharpe = mu / sd if sd > 0 else np.nan
    downside = r[r < 0].std() * np.sqrt(252)
    mdd = max_drawdown(r)
    out = {
        "Ann. return %": 100 * mu,
        "Ann. vol %": 100 * sd,
        "Sharpe": sharpe,
        "Sharpe SE (Lo)": np.sqrt((1 + 0.5 * sharpe ** 2) / years) if np.isfinite(sharpe) else np.nan,
        "NW t-stat": newey_west_t(r),
        "Sortino": mu / downside if downside > 0 else np.nan,
        "Max DD %": 100 * mdd,
        "Calmar": mu / abs(mdd) if mdd < 0 else np.nan,
        "Total return %": 100 * ((1 + r).prod() - 1),
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
