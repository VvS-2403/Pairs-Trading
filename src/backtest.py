"""Walk-forward backtest: select on 12 months, trade the next 6 months, roll.

Timing (no look-ahead; tests/test_backtest.py checks every rule below):
  * pair selection, the tickers allowed in a window and every parameter use the
    formation window only;
  * the signal computed at the close of day t is executed at the close of day t+1
    (Gatev et al. 2006 one-day wait), so day t's return uses the position decided
    at the close of day t-2;
  * open positions are closed at the close of the last trading day of the window.

Returns: holding +1 spread = $1 long leg a and $beta short leg b. Because
r_a - beta r_b ~ d(ln a) - beta d(ln b) = dX, this position earns the change of the
log spread X that the OU model describes. The pair's daily return on gross capital
is position * (r_a - beta r_b) / (1 + |beta|), minus cost_bps per leg per transaction
on the gross amount traded. Positions are rebalanced to these dollar weights daily
at no cost (a simplification; the drift between rebalances is second order).
"""

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C
from .selection import select_cointegrated, select_distance
from .strategies import band_positions, kalman_hedge, positions

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
MAX_MISSING = 0.02        # a ticker joins a window if at most 2% of formation days are missing


@dataclass
class Window:
    i: int
    f0: int          # first formation day (position in the price index)
    t0: int          # first trading day
    t1: int          # one past the last trading day


@dataclass
class BacktestResult:
    strategy: str
    committed: pd.Series      # portfolio return on committed capital (K slots)
    employed: pd.Series       # portfolio return on capital in open pairs
    pair_returns: pd.DataFrame  # one column per (window, pair)
    trades: pd.DataFrame
    pairs: pd.DataFrame       # one row per selected pair and window
    diagnostics: pd.DataFrame # selection counts per window


def make_windows(n, formation=C.FORMATION_DAYS, trading=C.TRADING_DAYS):
    """Formation/trading windows over n days. Trading blocks tile time with no overlap;
    a final block shorter than 20 days is dropped (too short to open and close a trade)."""
    out, f0 = [], 0
    while f0 + formation + 20 <= n:
        t0 = f0 + formation
        out.append(Window(len(out), f0, t0, min(t0 + trading, n)))
        f0 += trading
    return out


def run_selection(market, prices, sectors, formation=C.FORMATION_DAYS, trading=C.TRADING_DAYS,
                  k=C.TOP_K, use_cache=True, verbose=True):
    """Select pairs for every window (cached on disk: it is the slow step)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"selection_v2_{market}_{formation}_{trading}_{k}.pkl"
    if use_cache and path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    logp = np.log(prices)
    sel = []
    for w in make_windows(len(prices), formation, trading):
        form = logp.iloc[w.f0:w.t0]
        # Which tickers may trade is decided on formation data only. Filtering on the
        # trading window would drop stocks that later stop trading: look-ahead.
        form = form.loc[:, form.isna().mean() <= MAX_MISSING].ffill().bfill()
        coint, diag, tested = select_cointegrated(form, sectors, k)
        dist = select_distance(form, sectors, k)
        diag.update(window=w.i, formation_start=prices.index[w.f0], trading_start=prices.index[w.t0],
                    trading_end=prices.index[w.t1 - 1])
        sel.append(dict(window=w, coint=coint, distance=dist, diag=diag, tested=tested))
        if verbose:
            print(f"  {market} window {w.i:2d} {prices.index[w.t0].date()}: "
                  f"{diag['n_eg']:3d}/{diag['n_tested']} pass EG, {diag['n_filtered']:2d} pass filters",
                  flush=True)
    if use_cache:
        with open(path, "wb") as f:
            pickle.dump(sel, f)
    return sel


def _pair_path(logp, rets, spec, w):
    """Trading-window log prices and returns of one pair. A price that stops updating
    is carried forward (its return is then 0), as if the position were frozen."""
    a, b = spec.a, spec.b
    la = logp[a].iloc[w.t0:w.t1].ffill().values
    lb = logp[b].iloc[w.t0:w.t1].ffill().values
    ra = rets[a].iloc[w.t0:w.t1].fillna(0).values
    rb = rets[b].iloc[w.t0:w.t1].fillna(0).values
    return la, lb, ra, rb


def pair_returns(desired, beta, ra, rb, cost, lag=1):
    """Daily net returns of one pair from desired positions.

    desired[t] is the position wanted after seeing the close of day t. It is executed
    at the close of day t + lag (lag=1 is the project's rule; lag=0 executes at the
    same close that produced the signal and is used only to measure that bias).
    beta may be a number or an array (time-varying hedge ratio, known one day ahead).
    Returns (net returns, held positions), where held[t] is the position after the
    close of day t, so day t's return is earned by held[t-1].
    """
    n = len(desired)
    held = np.zeros(n)
    held[lag:] = desired[:n - lag]
    held[-1] = 0.0                                  # forced close at the window's last close
    beta = np.broadcast_to(np.asarray(beta, dtype=float), (n,))
    gross = np.zeros(n)
    gross[1:] = held[:-1] * (ra[1:] - beta[:-1] * rb[1:]) / (1 + np.abs(beta[:-1]))
    trade = np.abs(np.diff(np.concatenate([[0.0], held])))
    return gross - cost * trade, held


def extract_trades(held, net, dates, tag, cost):
    """One row per round trip: open/close dates, direction, days held, net P&L.

    A trade opened at close s and closed at close t earns the returns of days s+1..t,
    pays cost on its opening and closing transactions, and nothing else. On a flip
    (long to short in one step) the two transactions are split between the old and
    the new trade, so the trade P&Ls add up exactly to the pair's total P&L.
    """
    trade_size = np.abs(np.diff(np.concatenate([[0.0], held])))
    gross = net + cost * trade_size
    rows, start = [], None
    for t in range(1, len(held)):
        if held[t] != held[t - 1]:
            if held[t - 1] != 0 and start is not None:
                size = abs(held[t - 1])
                rows.append(dict(pair=tag, open=dates[start], close=dates[t], side=int(np.sign(held[t - 1])),
                                 days=t - start,
                                 pnl=float(gross[start + 1:t + 1].sum() - 2 * cost * size)))
            start = t if held[t] != 0 else None
    return rows


def simulate(strategy, prices, selections, cost_bps, k=C.TOP_K, stop=C.STOP_LOSS, params=None,
             label=None, lag=1):
    """Run one strategy over pre-computed selections; returns a BacktestResult.

    Capital is split into k equal slots, one per selected pair. "committed" divides the
    day's P&L by k (idle slots earn 0); "employed" divides by the pairs actually open
    that day (Gatev et al. 2006 report both).
    """
    logp, rets = np.log(prices), prices.pct_change(fill_method=None)
    cost = cost_bps / 1e4
    cols, trades, pairs_rows, diags = {}, [], [], []
    for sel in selections:
        w = sel["window"]
        diags.append(sel["diag"])
        specs = sel["distance"] if strategy == "distance" else sel["coint"]
        dates = prices.index[w.t0:w.t1]
        for spec in specs[:k]:
            la, lb, ra, rb = _pair_path(logp, rets, spec, w)
            if strategy == "kalman":
                fa = logp[spec.a].iloc[w.f0:w.t1].ffill().values
                fb = logp[spec.b].iloc[w.f0:w.t1].ffill().values
                betas, _, errs, qs = kalman_hedge(fa, fb, ve=spec.sd ** 2, beta0=spec.beta, mu0=spec.mu)
                nf = w.t0 - w.f0
                z = errs[nf:] / np.sqrt(qs[nf:])
                e = (params or {}).get("entry", C.KALMAN["entry"])
                desired = band_positions(z, -e, e, 0.0, 0.0, stop)
                beta = betas[nf:]
            else:
                x = la - spec.beta * lb - spec.mu
                cost_rt = 2 * cost * (1 + abs(spec.beta))   # round trip, in spread units
                desired = positions(strategy, x, spec, cost_rt, stop, params)
                beta = spec.beta
            net, held = pair_returns(desired, beta, ra, rb, cost, lag=lag)
            tag = f"w{w.i:02d}:{spec.a}/{spec.b}"
            cols[tag] = pd.Series(net, index=dates)
            cols[tag + "#open"] = pd.Series((np.concatenate([[0.0], held[:-1]]) != 0).astype(float), index=dates)
            pair_trades = extract_trades(held, net, dates, tag, cost)
            trades += pair_trades
            pairs_rows.append(dict(window=w.i, pair=tag, a=spec.a, b=spec.b, sector=spec.sector,
                                   beta=spec.beta, half_life=spec.half_life, kappa=spec.kappa,
                                   eg_stat=spec.eg_stat, eg_pvalue=spec.eg_pvalue, ssd=spec.ssd,
                                   bertram_m=spec.extra.get("bertram_m", np.nan),
                                   pnl=float(net.sum()), n_trades=len(pair_trades)))
    full_index = prices.index[selections[0]["window"].t0:selections[-1]["window"].t1]
    df = pd.DataFrame(cols, index=full_index) if cols else pd.DataFrame(index=full_index)
    ret_cols = [c for c in df.columns if not c.endswith("#open")]
    open_cols = [c + "#open" for c in ret_cols]
    pr = df[ret_cols].fillna(0.0)
    is_open = df[open_cols].fillna(0.0).values
    committed = pr.sum(axis=1) / k
    n_open = is_open.sum(axis=1)
    employed = pd.Series(np.where(n_open > 0, pr.sum(axis=1).values / np.maximum(n_open, 1), 0.0),
                         index=full_index)
    return BacktestResult(label or strategy, committed, employed, pr, pd.DataFrame(trades),
                          pd.DataFrame(pairs_rows), pd.DataFrame(diags))


# ------------------------------------------------- look-ahead demonstration only

def peeking_selections(selections, prices):
    """DEMONSTRATION OF LOOK-AHEAD BIAS ONLY: never use for results.

    Keeps the honestly selected pairs but re-estimates beta, mu and the OU
    parameters on the trading window itself, i.e. with prices the trader could not
    have seen yet. Comparing simulate() on these against the honest selections
    shows how much a backtest with in-sample parameters overstates performance.
    """
    from dataclasses import replace

    from .cointegration import ols
    from .ou import fit_ou

    logp = np.log(prices)
    out = []
    for sel in selections:
        w, new = sel["window"], []
        for s in sel["coint"]:
            y = logp[s.a].iloc[w.t0:w.t1].ffill().values
            x = logp[s.b].iloc[w.t0:w.t1].ffill().values
            mu, beta, resid = ols(y, x)
            ou = fit_ou(resid)
            if beta > 0 and ou.valid:
                s = replace(s, beta=beta, mu=mu, sd=resid.std(), theta=ou.theta, sigma_eq=ou.sigma_eq,
                            kappa=ou.kappa, sigma=ou.sigma, half_life=ou.half_life, extra={})
            new.append(s)
        out.append(dict(sel, coint=new))
    return out
