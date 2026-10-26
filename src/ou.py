"""Ornstein-Uhlenbeck process: simulation, estimation and Bertram's optimal bands.

Model:  dX_t = kappa (theta - X_t) dt + sigma dW_t,  kappa > 0.

Itô's lemma on e^{kappa t} X_t gives the exact solution
    X_t = theta + (X_0 - theta) e^{-kappa t} + sigma ∫_0^t e^{-kappa (t-s)} dW_s,
so over a step dt the process is an exact Gaussian AR(1):
    X_{t+dt} = a + b X_t + eps,  b = e^{-kappa dt},  a = theta (1 - b),
    Var(eps) = sigma^2 (1 - e^{-2 kappa dt}) / (2 kappa).
OLS of X_{t+dt} on X_t is therefore the conditional maximum-likelihood estimator.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import erfi

from .config import DT


@dataclass
class OUParams:
    kappa: float          # mean-reversion speed, per year
    theta: float          # long-run mean
    sigma: float          # diffusion coefficient, per sqrt(year)
    sigma_eq: float       # stationary standard deviation sigma / sqrt(2 kappa)
    half_life: float      # ln 2 / kappa, in trading days
    b: float              # AR(1) slope e^{-kappa dt}
    a: float              # AR(1) intercept
    resid_sd: float       # standard deviation of AR(1) residuals
    valid: bool           # True only when 0 < b < 1 (mean reverting)


def simulate_ou(kappa, theta, sigma, x0, n_steps, dt=DT, n_paths=1, method="exact", rng=None):
    """Simulate OU paths, shape (n_paths, n_steps + 1).

    method="exact" uses the Gaussian transition above (no discretisation error).
    method="euler" uses Euler-Maruyama X += kappa (theta - X) dt + sigma sqrt(dt) Z.
    For OU the noise is additive, so Milstein's correction is zero and
    Milstein coincides with Euler-Maruyama (Kloeden & Platen 1992).
    x0 may be a number or "stationary" to draw X_0 from N(theta, sigma^2 / 2 kappa).
    """
    rng = np.random.default_rng() if rng is None else rng
    z = rng.standard_normal((n_paths, n_steps))
    x = np.empty((n_paths, n_steps + 1))
    if isinstance(x0, str) and x0 == "stationary":
        x[:, 0] = theta + sigma / np.sqrt(2 * kappa) * rng.standard_normal(n_paths)
    else:
        x[:, 0] = x0
    if method == "exact":
        b = np.exp(-kappa * dt)
        sd = sigma * np.sqrt((1 - b * b) / (2 * kappa))
        for t in range(n_steps):
            x[:, t + 1] = theta + (x[:, t] - theta) * b + sd * z[:, t]
    elif method == "euler":
        sq = sigma * np.sqrt(dt)
        for t in range(n_steps):
            x[:, t + 1] = x[:, t] + kappa * (theta - x[:, t]) * dt + sq * z[:, t]
    else:
        raise ValueError("method must be 'exact' or 'euler'")
    return x


def ar1_fit(x):
    """OLS of x[1:] on x[:-1]; returns (a, b, residual sd)."""
    x = np.asarray(x, dtype=float)
    y, z = x[1:], x[:-1]
    zm, ym = z.mean(), y.mean()
    szz = ((z - zm) ** 2).sum()
    b = ((z - zm) * (y - ym)).sum() / szz if szz > 0 else np.nan
    a = ym - b * zm
    resid = y - a - b * z
    return a, b, resid.std(ddof=2)


def fit_ou(x, dt=DT, estimator="exact"):
    """Estimate OU parameters from one observed path by the AR(1) map.

    estimator="exact" inverts b = e^{-kappa dt}; estimator="euler" uses the
    Euler approximation b = 1 - kappa dt (biased by O(kappa dt), shown in E1).
    """
    a, b, s = ar1_fit(x)
    valid = bool(np.isfinite(b) and 0 < b < 1)
    if not valid:
        return OUParams(np.nan, np.nan, np.nan, np.nan, np.nan, b, a, s, False)
    if estimator == "exact":
        kappa = -np.log(b) / dt
        sigma = s * np.sqrt(2 * kappa / (1 - b * b))
    else:
        kappa = (1 - b) / dt
        sigma = s / np.sqrt(dt)
    theta = a / (1 - b)
    sigma_eq = s / np.sqrt(1 - b * b)
    return OUParams(kappa, theta, sigma, sigma_eq, np.log(2) / kappa / dt, b, a, s, True)


# ---------------------------------------------------------------- Bertram (2010)

def bertram_cycle_time(entry, exit_, kappa, sigma):
    """Expected time (years) for a centred OU to go entry -> exit -> entry.

    From the Kolmogorov backward equation  (1/2) sigma^2 u'' - kappa x u' = -1
    for first-passage times (Bertram 2010):
        E[T] = (pi / kappa) [erfi(m sqrt(kappa) / sigma) - erfi(a sqrt(kappa) / sigma)].
    """
    r = np.sqrt(kappa) / sigma
    return np.pi / kappa * (erfi(exit_ * r) - erfi(entry * r))


def bertram_return_rate(m, kappa, sigma, cost):
    """Expected return per unit time with symmetric bands a = -m, exit m, round-trip cost c."""
    return (2 * m - cost) / bertram_cycle_time(-m, m, kappa, sigma)


def bertram_bands(kappa, sigma, cost):
    """Optimal half-width m* (in spread units) maximising expected return per unit time."""
    sigma_eq = sigma / np.sqrt(2 * kappa)
    lo = max(cost / 2 * 1.0001, 1e-6 * sigma_eq)
    hi = max(4 * sigma_eq, cost * 2)
    res = minimize_scalar(lambda m: -bertram_return_rate(m, kappa, sigma, cost),
                          bounds=(lo, hi), method="bounded", options={"xatol": 1e-7 * sigma_eq})
    return float(res.x)


def first_passage_cycle_mc(kappa, sigma, m, n_steps=2_000_000, dt=DT / 50, rng=None):
    """Monte Carlo mean cycle time -m -> m -> -m of a centred OU (years), for E3."""
    rng = np.random.default_rng() if rng is None else rng
    b = np.exp(-kappa * dt)
    sd = sigma * np.sqrt((1 - b * b) / (2 * kappa))
    z = rng.standard_normal(n_steps)
    x, state, t_last, cycles = -m, -1, 0, []
    # state -1: waiting to hit +m; state +1: waiting to hit -m. A cycle ends back at -m.
    for i in range(n_steps):
        x = x * b + sd * z[i]
        if state == -1 and x >= m:
            state = 1
        elif state == 1 and x <= -m:
            state = -1
            cycles.append((i + 1 - t_last) * dt)
            t_last = i + 1
    return np.array(cycles)
