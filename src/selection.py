"""Pair selection on one formation window. Only formation data enters here."""

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from . import config as C
from .cointegration import benjamini_hochberg, engle_granger_both, ols
from .ou import fit_ou


@dataclass
class PairSpec:
    a: str                    # leg held long when the spread is bought
    b: str                    # hedge leg
    sector: str
    method: str               # "coint" or "distance"
    beta: float               # hedge ratio: spread = log a - beta log b - mu
    mu: float
    sd: float                 # formation standard deviation of the spread
    theta: float = 0.0        # OU long-run mean of the spread
    sigma_eq: float = np.nan  # OU stationary standard deviation
    kappa: float = np.nan     # per year
    sigma: float = np.nan
    half_life: float = np.nan # trading days
    eg_stat: float = np.nan
    eg_pvalue: float = np.nan
    ssd: float = np.nan
    crossings: float = np.nan # mean crossings per year
    extra: dict = field(default_factory=dict)


def candidate_pairs(sectors, available):
    """All within-sector pairs whose tickers have data in this window."""
    out = []
    for sector, names in sectors.items():
        names = [n for n in names if n in available]
        out += [(sector, i, j) for i, j in combinations(names, 2)]
    return out


def mean_crossings_per_year(x):
    s = np.sign(x - x.mean())
    s = s[s != 0]
    return np.count_nonzero(s[1:] != s[:-1]) / (len(x) / 252)


def select_cointegrated(logp, sectors, k=C.TOP_K, pmax=C.EG_PVALUE,
                        hl_range=C.HALF_LIFE_RANGE, min_cross=C.MIN_CROSSINGS_PER_YEAR):
    """Engle-Granger + OU filters (Sarmento & Horta 2020), ranked by EG statistic.

    Returns (selected PairSpecs, diagnostics, every tested pair as PairSpec).
    """
    cands = candidate_pairs(sectors, set(logp.columns))
    tested, pvals = [], []
    for sector, i, j in cands:
        best, pboth = engle_granger_both(logp[i].values, logp[j].values, i, j)
        pvals.append(pboth)
        spec = PairSpec(best.y, best.x, sector, "coint", best.beta, best.mu, best.resid.std(),
                        eg_stat=best.stat, eg_pvalue=pboth)
        ou = fit_ou(best.resid)
        if ou.valid:
            spec.theta, spec.sigma_eq, spec.kappa = ou.theta, ou.sigma_eq, ou.kappa
            spec.sigma, spec.half_life = ou.sigma, ou.half_life
        spec.crossings = mean_crossings_per_year(best.resid)
        tested.append(spec)

    def passes(s):
        return (s.eg_pvalue < pmax and s.beta > 0 and np.isfinite(s.half_life)
                and hl_range[0] <= s.half_life <= hl_range[1] and s.crossings >= min_cross)

    eg_pass = [s for s in tested if s.eg_pvalue < pmax]
    survivors = sorted([s for s in tested if passes(s)], key=lambda s: s.eg_stat)
    diag = dict(n_tested=len(tested), n_eg=len(eg_pass),
                n_bh=benjamini_hochberg(pvals, C.BH_Q), n_filtered=len(survivors))
    return survivors[:k], diag, tested


def select_distance(logp, sectors, k=C.TOP_K):
    """Gatev et al. (2006): smallest sum of squared deviations of normalised prices."""
    norm = logp - logp.iloc[0]
    out = []
    for sector, i, j in candidate_pairs(sectors, set(logp.columns)):
        d = (norm[i] - norm[j]).values
        out.append(PairSpec(i, j, sector, "distance", 1.0,
                            float(logp[i].iloc[-1] - logp[j].iloc[-1]), d.std(),
                            ssd=float((d ** 2).sum())))
    out.sort(key=lambda s: s.ssd)
    return out[:k]
