"""E4: a synthetic cointegrated pair with a known OU spread, run through the pipeline.

Leg B is a geometric random walk and ln A = mu + beta ln B + X, where X is an exact
OU path. Because the truth is known, Bertram's (2010) formula predicts the return
of his optimal bands, and we can add the frictions of a real backtest one at a time
and measure what each one costs (the "ladder"):

  L0  theory: continuous monitoring, true parameters, no delay
  L1  spread observed once a day, traded at the same close, true parameters
  L2  + one-day execution lag (the project's rule)
  L3  + 6-month trading windows: start flat, forced close at the end
  L4a + OU parameters (kappa, theta, sigma) estimated on the formation window, true beta
  L4  + beta and mu estimated too (everything a real trader must estimate)
  L5  + pair traded only when it passes the Engle-Granger and OU filters (full pipeline)

The traded rule is the flip version of Bertram's bands: long at s <= -m, short at
s >= m. Over one cycle -m -> m -> -m it earns 2m twice and pays the round-trip cost
c twice, so its return per unit time is twice Bertram's (2m - c) / E[T].
"""

from dataclasses import replace

import numpy as np
import pandas as pd

from . import config as C
from .backtest import Window, make_windows, run_selection, simulate
from .ou import bertram_bands, bertram_cycle_time, fit_ou, simulate_ou
from .selection import PairSpec, select_cointegrated
from .strategies import flip_positions

DEFAULTS = dict(kappa=25.0, sig_eq=0.03, beta=1.2, mu=0.1, years=12, cost_bps=5)


def synthetic_pair(rng, kappa, sig_eq, beta, mu, years, b_vol=0.015, b_drift=0.0003):
    """Prices of a cointegrated pair: ln A = mu + beta ln B + X, X ~ OU(kappa, 0, sigma)."""
    n = DAYS_PER_YEAR * years
    sigma = sig_eq * np.sqrt(2 * kappa)
    log_b = np.log(50) + np.cumsum(b_drift + b_vol * rng.standard_normal(n))
    x = simulate_ou(kappa, 0.0, sigma, "stationary", n - 1, rng=rng)[0]
    idx = pd.bdate_range("2010-01-01", periods=n)
    return pd.DataFrame({"A": np.exp(mu + beta * log_b + x), "B": np.exp(log_b)}, index=idx)


DAYS_PER_YEAR = 252


def bertram_flip_theory(kappa, sig_eq, beta, cost_bps):
    """L0: expected annual return on gross capital of the flip rule at the optimal band.

    Returns (annual return, m* in units of sigma_eq). Costs and P&L are in spread
    units per $1 of leg A; dividing by 1 + beta converts to return on gross capital.
    """
    sigma = sig_eq * np.sqrt(2 * kappa)
    c_rt = 2 * cost_bps / 1e4 * (1 + beta)
    m = bertram_bands(kappa, sigma, c_rt)
    rate = 2 * (2 * m - c_rt) / bertram_cycle_time(-m, m, kappa, sigma)   # per year, spread units
    return rate / (1 + beta), m / sig_eq


def fine_grid_flip(rng, kappa, sig_eq, beta, cost_bps, years=200, steps_per_day=50):
    """Flip rule on an OU path observed steps_per_day times a day, no delay.

    As steps_per_day grows this approaches continuous monitoring, so it checks
    the L0 formula (and the P&L bookkeeping) by simulation.
    """
    sigma = sig_eq * np.sqrt(2 * kappa)
    c_rt = 2 * cost_bps / 1e4 * (1 + beta)
    m = bertram_bands(kappa, sigma, c_rt)
    dt = C.DT / steps_per_day
    x = simulate_ou(kappa, 0.0, sigma, "stationary", DAYS_PER_YEAR * years * steps_per_day, dt=dt, rng=rng)[0]
    pos = flip_positions(x, m)
    pnl = (pos[:-1] * np.diff(x)).sum() - c_rt / 2 * np.abs(np.diff(np.r_[0.0, pos])).sum()
    return pnl / years / (1 + beta)


def _oracle_spec(kappa, sig_eq, beta, mu):
    sigma = sig_eq * np.sqrt(2 * kappa)
    return PairSpec("A", "B", "Synthetic", "coint", beta, mu, sig_eq, theta=0.0, sigma_eq=sig_eq,
                    kappa=kappa, sigma=sigma, half_life=np.log(2) / kappa / C.DT)


def _fitted_unfiltered(px, windows):
    """Formation-window estimates for every window, with every test switched off."""
    logp = np.log(px)
    out = []
    for w in windows:
        specs, diag, _ = select_cointegrated(logp.iloc[w.f0:w.t0], {"Synthetic": ["A", "B"]}, k=1,
                                             pmax=1.01, hl_range=(0, np.inf), min_cross=0)
        out.append(dict(window=w, coint=specs, distance=[], diag=diag, tested=[]))
    return out


def ladder_once(rng, kappa, sig_eq, beta, mu, years, cost_bps):
    """One synthetic pair through levels L1-L5. Returns annual mean returns and diagnostics."""
    px = synthetic_pair(rng, kappa, sig_eq, beta, mu, years)
    windows = make_windows(len(px))
    oracle = _oracle_spec(kappa, sig_eq, beta, mu)
    one_window = [dict(window=Window(0, 0, windows[0].t0, windows[-1].t1), coint=[oracle], diag={})]
    walk_oracle = [dict(window=w, coint=[oracle], diag={}) for w in windows]
    fitted = _fitted_unfiltered(px, windows)
    selected = run_selection("synthetic", px, {"Synthetic": ["A", "B"]}, k=1, use_cache=False, verbose=False)

    def ann(sel, lag=1, rule="bertram"):
        return simulate(rule, px, sel, cost_bps, k=1, lag=lag).committed.mean() * DAYS_PER_YEAR

    # L4 split in two: true hedge ratio but OU parameters fitted on the formation spread
    logp = np.log(px)
    true_beta_fit = []
    for w in windows:
        ou = fit_ou((logp.A - beta * logp.B - mu).iloc[w.f0:w.t0].values)
        spec = replace(oracle, theta=ou.theta, sigma_eq=ou.sigma_eq, kappa=ou.kappa, sigma=ou.sigma, extra={})
        true_beta_fit.append(dict(window=w, coint=[spec] if ou.valid else [], diag={}))

    fit_specs = [s["coint"][0] for s in fitted if s["coint"]]
    return {
        "L1": ann(one_window, lag=0),
        "L2": ann(one_window),
        "L3": ann(walk_oracle),
        "L4a": ann(true_beta_fit),
        "L4": ann(fitted),
        "beta_abs_err": np.median([abs(s.beta - beta) if s.a == "A" else abs(1 / s.beta - beta) for s in fit_specs]),
        "L5": ann(selected),
        "sscore_L5": ann(selected, rule="sscore"),
        "selected_share": np.mean([len(s["coint"]) > 0 for s in selected]),
        "kappa_hat_over_true": np.median([s.kappa for s in fit_specs]) / kappa,
        "m_hat_in_sig_eq": np.median([bertram_bands(s.kappa, s.sigma, 2 * cost_bps / 1e4 * (1 + abs(s.beta)))
                                        / s.sigma_eq for s in fit_specs]),
    }


def run_ladder(reps=200, seed=C.SEED, **kw):
    """Average the ladder over `reps` independent synthetic pairs."""
    p = dict(DEFAULTS, **kw)
    rng = np.random.default_rng(seed)
    rows = [ladder_once(rng, **p) for _ in range(reps)]
    df = pd.DataFrame(rows)
    theory, m_star = bertram_flip_theory(p["kappa"], p["sig_eq"], p["beta"], p["cost_bps"])
    fine = fine_grid_flip(np.random.default_rng(seed + 1), p["kappa"], p["sig_eq"], p["beta"], p["cost_bps"])
    return df, dict(theory=theory, m_star=m_star, fine_grid=fine, **p)
