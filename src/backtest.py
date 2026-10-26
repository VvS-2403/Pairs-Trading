"""Walk-forward backtest: select on 12 months, trade the next 6 months, roll.

Timing (no look-ahead):
  * pair selection and every parameter use the formation window only;
  * the signal computed at the close of day t is executed at the close of day t+1
    (Gatev et al. 2006 one-day wait), so day t's return uses the position decided
    at the close of day t-2;
  * open positions are closed at the close of the last trading day.

Returns: holding +1 spread = $1 long leg a and $beta short leg b. The pair's daily
return on gross capital is position * (r_a - beta r_b) / (1 + |beta|), minus
cost_bps per leg per transaction on the gross amount traded.
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
    out, f0 = [], 0
    while f0 + formation + 20 <= n:
        t0 = f0 + formation
        out.append(Window(len(out), f0, t0, min(t0 + trading, n)))
        f0 += trading
    return out


def run_selection(market, prices, sectors, formation=C.FORMATION_DAYS, trading=C.TRADING_DAYS,
                  k=C.TOP_K, use_cache=True):
    """Select pairs for every window (cached on disk: it is the slow step)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"selection_{market}_{formation}_{trading}_{k}.pkl"
    if use_cache and path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    logp = np.log(prices)
    sel = []
    for w in make_windows(len(prices), formation, trading):
        block = logp.iloc[w.f0:w.t1]
        ok = block.columns[block.isna().mean() <= 0.02]
        form = logp.iloc[w.f0:w.t0][ok].ffill().bfill()
        coint, diag, tested = select_cointegrated(form, sectors, k)
        dist = select_distance(form, sectors, k)
        diag.update(window=w.i, formation_start=prices.index[w.f0], trading_start=prices.index[w.t0],
                    trading_end=prices.index[w.t1 - 1])
        sel.append(dict(window=w, coint=coint, distance=dist, diag=diag, tested=tested))
        print(f"  {market} window {w.i:2d} {prices.index[w.t0].date()}: "
              f"{diag['n_eg']:3d}/{diag['n_tested']} pass EG, {diag['n_filtered']:2d} pass filters", flush=True)
    with open(path, "wb") as f:
        pickle.dump(sel, f)
    return sel


def _pair_path(logp, rets, spec, w):
    a, b = spec.a, spec.b
    la = logp[a].iloc[w.t0:w.t1].ffill().values
    lb = logp[b].iloc[w.t0:w.t1].ffill().values
    ra = rets[a].iloc[w.t0:w.t1].fillna(0).values
    rb = rets[b].iloc[w.t0:w.t1].fillna(0).values
    return la, lb, ra, rb


def pair_returns(desired, beta, ra, rb, cost):
    """Daily net returns of one pair from desired positions (executed one day later).

    beta may be a number or an array (time-varying hedge ratio, known one day ahead).
    Returns (net returns, held positions).
    """
    n = len(desired)
    held = np.zeros(n)
    held[1:] = desired[:-1]
    held[-1] = 0.0                                  # forced close at the window's last close
    beta = np.broadcast_to(np.asarray(beta, dtype=float), (n,))
    gross = np.zeros(n)
    gross[1:] = held[:-1] * (ra[1:] - beta[:-1] * rb[1:]) / (1 + np.abs(beta[:-1]))
    trade = np.abs(np.diff(np.concatenate([[0.0], held])))
    return gross - cost * trade, held


def extract_trades(held, net, dates, tag):
    """One row per round trip: open/close dates, direction, days held, net P&L."""
    rows, start = [], None
    for t in range(1, len(held)):
        if held[t] != held[t - 1]:
            if held[t - 1] != 0 and start is not None:
                rows.append(dict(pair=tag, open=dates[start], close=dates[t], side=int(held[t - 1]),
                                 days=t - start, pnl=float(net[start:t + 1].sum())))
            start = t if held[t] != 0 else None
    return rows


def simulate(strategy, prices, selections, cost_bps, k=C.TOP_K, stop=C.STOP_LOSS, params=None,
             label=None):
    """Run one strategy over pre-computed selections; returns a BacktestResult."""
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
                cost_rt = 2 * cost * (1 + abs(spec.beta))
                desired = positions(strategy, x, spec, cost_rt, stop, params)
                beta = spec.beta
            net, held = pair_returns(desired, beta, ra, rb, cost)
            tag = f"w{w.i:02d}:{spec.a}/{spec.b}"
            cols[tag] = pd.Series(net, index=dates)
            cols[tag + "#open"] = pd.Series((np.concatenate([[0.0], held[:-1]]) != 0).astype(float), index=dates)
            trades += extract_trades(held, net, dates, tag)
            pairs_rows.append(dict(window=w.i, pair=tag, a=spec.a, b=spec.b, sector=spec.sector,
                                   beta=spec.beta, half_life=spec.half_life, kappa=spec.kappa,
                                   eg_stat=spec.eg_stat, eg_pvalue=spec.eg_pvalue, ssd=spec.ssd,
                                   bertram_m=spec.extra.get("bertram_m", np.nan),
                                   pnl=float(net.sum()), n_trades=int((np.diff(held) != 0).sum())))
    full_index = prices.index[selections[0]["window"].t0:selections[-1]["window"].t1]
    df = pd.DataFrame(cols).reindex(full_index)
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
