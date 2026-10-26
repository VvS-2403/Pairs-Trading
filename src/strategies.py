"""Trading rules: map a standardised spread path to desired positions.

A position of +1 means long the spread (long $1 of leg a, short $beta of leg b).
Every rule returns the position wanted at each day's close; the backtest
executes it one day later.
"""

import numpy as np

from . import config as C
from .ou import bertram_bands


def band_positions(s, open_long, open_short, close_long, close_short, stop=None):
    """Generic two-sided band rule with optional stop-loss on |s|.

    Open long when s < open_long, open short when s > open_short, close a long
    when s > close_long and a short when s < close_short. After a stop-loss the
    pair may reopen only once |s| is back inside the entry band.
    """
    pos = np.zeros(len(s))
    p, blocked = 0, False
    for t, v in enumerate(s):
        if not np.isfinite(v):
            pos[t] = p
            continue
        if blocked and open_long <= v <= open_short:
            blocked = False
        if p != 0 and stop is not None and abs(v) > stop:
            p, blocked = 0, True
        elif p == 1 and v > close_long:
            p = 0
        elif p == -1 and v < close_short:
            p = 0
        if p == 0 and not blocked:
            if v < open_long:
                p = 1
            elif v > open_short:
                p = -1
        pos[t] = p
    return pos


def flip_positions(s, m):
    """Bertram's symmetric bands: go long at s <= -m, flip short at s >= m, and so on."""
    pos = np.zeros(len(s))
    p = 0
    for t, v in enumerate(s):
        if np.isfinite(v):
            if p <= 0 and v <= -m:
                p = 1
            elif p >= 0 and v >= m:
                p = -1
        pos[t] = p
    return pos


def positions(rule, x, spec, cost_rt=0.0, stop=C.STOP_LOSS, params=None):
    """Desired positions for spread path x (already a - beta b - mu) under one rule.

    cost_rt is the round-trip cost in spread units, used only by Bertram's bands.
    params overrides the rule's default thresholds (sensitivity analysis, E7).
    """
    if rule == "distance":
        e = (params or {}).get("entry", C.DISTANCE_ENTRY)
        z = x / spec.sd
        return band_positions(z, -e, e, 0.0, 0.0, stop)
    if rule == "zscore":
        p = dict(C.ZSCORE, **(params or {}))
        z = x / spec.sd
        return band_positions(z, -p["entry"], p["entry"], -p["exit"], p["exit"], stop)
    if rule == "sscore":
        p = dict(C.SSCORE, **(params or {}))
        s = (x - spec.theta) / spec.sigma_eq
        return band_positions(s, p["open_long"], p["open_short"], p["close_long"], p["close_short"], stop)
    if rule == "bertram":
        m = bertram_bands(spec.kappa, spec.sigma, cost_rt)
        spec.extra["bertram_m"] = m / spec.sigma_eq
        s = (x - spec.theta) / spec.sigma_eq
        return flip_positions(s, m / spec.sigma_eq)
    raise ValueError(f"unknown rule {rule}")


def kalman_hedge(a, b, delta=C.KALMAN["delta"], ve=None, beta0=1.0, mu0=0.0):
    """Kalman filter for a time-varying hedge ratio (Chan 2013; Elliott et al. 2005).

    State (mu_t, beta_t) follows a random walk; observation a_t = mu_t + beta_t b_t + e_t.
    Returns prior (one-step-ahead) beta, mu, forecast error and its variance, so
    every value at day t uses data up to day t-1 only.
    """
    n = len(a)
    vw = delta / (1 - delta) * np.eye(2)
    ve = np.var(a - beta0 * b - mu0) if ve is None else ve
    state = np.array([mu0, beta0])
    P = np.eye(2) * 1e-3
    betas, mus, errs, qs = (np.empty(n) for _ in range(4))
    for t in range(n):
        R = P + vw
        h = np.array([1.0, b[t]])
        yhat = h @ state
        q = h @ R @ h + ve
        e = a[t] - yhat
        mus[t], betas[t], errs[t], qs[t] = state[0], state[1], e, q
        K = R @ h / q
        state = state + K * e
        P = R - np.outer(K, h) @ R
    return betas, mus, errs, qs
