"""Tests of src/selection.py: within-sector pairs, Engle-Granger filter, OU filters, top-K (task T28).

Simulated prices use fixed seeds. The last test runs the real US selection on one window.
"""

import numpy as np
import pandas as pd
import pytest

from src import config as C
from src.data import load_prices, sectors
from src.selection import (candidate_pairs, mean_crossings_per_year, select_cointegrated,
                           select_distance)

pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")

N = 252


def _walk(rng, n=N, sd=0.01):
    return np.cumsum(rng.standard_normal(n) * sd)


def _ou(rng, n=N, phi=0.8, sd=0.01):
    u = np.zeros(n)
    for t in range(1, n):
        u[t] = phi * u[t - 1] + sd * rng.standard_normal()
    return u


def _market(seed=0):
    """Two sectors. 'S1' holds a truly cointegrated pair (A1, B1; beta 0.8, half-life ~3 d),
    a negative-beta cointegrated pair (A2, B2), and an independent walk (C1).
    'S2' holds two independent walks (X, Y). The pair A1/X is cointegrated but crosses sectors."""
    rng = np.random.default_rng(seed)
    b1, b2, c1, x, y = (_walk(rng) for _ in range(5))
    cols = {"A1": 1.0 + 0.8 * b1 + _ou(rng), "B1": b1,
            "A2": 2.0 - 0.8 * b2 + _ou(rng), "B2": b2,
            "C1": c1, "X": x, "Y": y}
    return pd.DataFrame(cols), {"S1": ["A1", "B1", "A2", "B2", "C1"], "S2": ["X", "Y"]}


# ------------------------------------------------------------------ candidate pairs

def test_candidate_pairs_within_sector_only():
    sec = {"S1": ["a", "b", "c"], "S2": ["d", "e"]}
    pairs = candidate_pairs(sec, {"a", "b", "c", "d", "e"})
    assert len(pairs) == 3 + 1
    assert all(sec_of(sec, i) == sec_of(sec, j) == s for s, i, j in pairs)
    assert len({frozenset((i, j)) for _, i, j in pairs}) == len(pairs)   # no duplicates


def sec_of(sec, t):
    return next(s for s, ts in sec.items() if t in ts)


def test_candidate_pairs_drops_unavailable_tickers():
    sec = {"S1": ["a", "b", "c"]}
    assert {(i, j) for _, i, j in candidate_pairs(sec, {"a", "c"})} == {("a", "c")}
    assert candidate_pairs(sec, {"a"}) == []


def test_us_universe_has_196_candidate_pairs():
    s = sectors("us")
    assert len(candidate_pairs(s, {t for ts in s.values() for t in ts})) == 7 * 28


# ------------------------------------------------------------------ crossings

def test_mean_crossings_per_year_known_answers():
    alt = np.tile([1.0, -1.0], 126)                      # crosses its mean every day
    assert mean_crossings_per_year(alt) == pytest.approx(251 / (252 / 252))
    assert mean_crossings_per_year(np.arange(252.0)) == pytest.approx(1.0)   # one crossing
    sine = np.sin(np.linspace(0, 2 * np.pi * 6, 252))    # six full cycles: about 12 crossings
    assert 10 <= mean_crossings_per_year(sine) <= 13


# ------------------------------------------------------------------ select_cointegrated

def test_select_cointegrated_finds_true_pair_with_right_beta():
    df, sec = _market()
    chosen, diag, tested = select_cointegrated(df, sec)
    pairs = {frozenset((s.a, s.b)) for s in chosen}
    assert frozenset(("A1", "B1")) in pairs
    s = next(s for s in chosen if {s.a, s.b} == {"A1", "B1"})
    assert s.beta == pytest.approx(0.8, abs=0.1) or s.beta == pytest.approx(1 / 0.8, abs=0.15)
    assert s.method == "coint" and s.sector == "S1"


def test_only_within_sector_pairs_are_tested():
    df, sec = _market()
    _, diag, tested = select_cointegrated(df, sec)
    assert diag["n_tested"] == 10 + 1 == len(tested)           # C(5,2) + C(2,2)
    assert all(sec_of(sec, s.a) == sec_of(sec, s.b) == s.sector for s in tested)


def test_every_selected_pair_passes_every_filter():
    df, sec = _market()
    chosen, _, _ = select_cointegrated(df, sec)
    assert chosen
    for s in chosen:
        assert s.eg_pvalue < C.EG_PVALUE
        assert s.beta > 0
        assert C.HALF_LIFE_RANGE[0] <= s.half_life <= C.HALF_LIFE_RANGE[1]
        assert s.crossings >= C.MIN_CROSSINGS_PER_YEAR


def test_negative_beta_pair_is_cointegrated_but_rejected():
    df, sec = _market()
    chosen, _, tested = select_cointegrated(df, sec)
    neg = next(s for s in tested if {s.a, s.b} == {"A2", "B2"})
    assert neg.eg_pvalue < 0.05 and neg.beta < 0               # passes EG, fails the sign filter
    assert all({s.a, s.b} != {"A2", "B2"} for s in chosen)


def test_half_life_filter_binds():
    df, sec = _market()
    chosen, _, _ = select_cointegrated(df, sec, hl_range=(50, 63))   # true half-life is ~3 days
    assert all(50 <= s.half_life <= 63 for s in chosen)
    assert all({s.a, s.b} != {"A1", "B1"} for s in chosen)


def test_crossings_filter_binds():
    df, sec = _market()
    chosen, _, _ = select_cointegrated(df, sec, min_cross=1000)
    assert chosen == []


def test_pvalue_filter_binds():
    df, sec = _market()
    chosen, diag, _ = select_cointegrated(df, sec, pmax=1e-12)
    assert diag["n_eg"] <= diag["n_tested"] and all(s.eg_pvalue < 1e-12 for s in chosen)


def test_ranked_by_eg_statistic_and_top_k_truncates():
    rng = np.random.default_rng(2)
    base = {f"B{i}": _walk(rng) for i in range(4)}
    cols = dict(base)
    for i in range(4):                                         # four cointegrated pairs, increasing noise
        cols[f"A{i}"] = 1 + 0.9 * base[f"B{i}"] + _ou(rng, sd=0.005 * (i + 1))
    df = pd.DataFrame(cols)
    sec = {f"S{i}": [f"A{i}", f"B{i}"] for i in range(4)}
    full, diag, _ = select_cointegrated(df, sec, k=20)
    assert len(full) == diag["n_filtered"] >= 2
    stats = [s.eg_stat for s in full]
    assert stats == sorted(stats)                              # most negative first
    top1, _, _ = select_cointegrated(df, sec, k=1)
    assert len(top1) == 1 and (top1[0].a, top1[0].b) == (full[0].a, full[0].b)


def test_diagnostics_are_consistent():
    df, sec = _market()
    chosen, diag, tested = select_cointegrated(df, sec)
    assert diag["n_filtered"] >= len(chosen)
    assert diag["n_bh"] <= diag["n_eg"] + diag["n_tested"]
    assert diag["n_filtered"] <= diag["n_eg"] <= diag["n_tested"]
    assert diag["n_eg"] == sum(s.eg_pvalue < C.EG_PVALUE for s in tested)


def test_both_direction_rule_uses_larger_p_value():
    df, sec = _market()
    _, _, tested = select_cointegrated(df, sec)
    from src.cointegration import engle_granger
    s = next(s for s in tested if {s.a, s.b} == {"A1", "B1"})
    p_ab = engle_granger(df["A1"].values, df["B1"].values).pvalue
    p_ba = engle_granger(df["B1"].values, df["A1"].values).pvalue
    assert s.eg_pvalue == pytest.approx(max(p_ab, p_ba))


def test_selection_ignores_data_after_the_window():
    """Only the frame passed in is used: appending future rows cannot change the choice."""
    df, sec = _market()
    again, _, _ = select_cointegrated(df.copy(), sec)
    first, _, _ = select_cointegrated(df, sec)
    assert [(s.a, s.b, s.eg_stat) for s in first] == [(s.a, s.b, s.eg_stat) for s in again]


def test_independent_walks_rarely_selected():
    """Size check: 28 independent pairs, 252 days; expect about 5% to pass EG in both directions
    (fewer, since both must pass)."""
    rng = np.random.default_rng(7)
    passed = 0
    for _ in range(10):
        df = pd.DataFrame({f"t{i}": _walk(rng) for i in range(8)})
        _, diag, _ = select_cointegrated(df, {"S": list(df.columns)})
        passed += diag["n_eg"]
    assert passed / (10 * 28) < 0.10


# ------------------------------------------------------------------ select_distance

def test_distance_ranks_by_ssd_and_uses_gatev_definition():
    rng = np.random.default_rng(1)
    base = _walk(rng)
    df = pd.DataFrame({"a": base, "b": base + 0.001 * _walk(rng),      # nearly identical
                       "c": base + 0.05 * _walk(rng, sd=1), "d": _walk(rng)})
    top = select_distance(df, {"S": list("abcd")}, k=20)
    assert len(top) == 6
    assert [s.ssd for s in top] == sorted(s.ssd for s in top)
    assert (top[0].a, top[0].b) == ("a", "b")
    norm = df - df.iloc[0]
    for s in top:
        d = (norm[s.a] - norm[s.b]).values
        assert s.ssd == pytest.approx((d ** 2).sum()) and s.sd == pytest.approx(d.std())
        assert s.beta == 1.0 and s.method == "distance"
        assert s.mu == pytest.approx(df[s.a].iloc[-1] - df[s.b].iloc[-1])
    assert len(select_distance(df, {"S": list("abcd")}, k=2)) == 2


def test_distance_is_within_sector_only():
    rng = np.random.default_rng(3)
    df = pd.DataFrame({t: _walk(rng) for t in "abcd"})
    top = select_distance(df, {"S1": ["a", "b"], "S2": ["c", "d"]})
    assert {frozenset((s.a, s.b)) for s in top} == {frozenset("ab"), frozenset("cd")}


# ------------------------------------------------------------------ real US data

def test_real_us_window_selection_works():
    px = load_prices("us")
    form = np.log(px.iloc[-C.FORMATION_DAYS:]).dropna(axis=1)
    chosen, diag, tested = select_cointegrated(form, sectors("us"))
    assert diag["n_tested"] == len(tested) == 196
    assert diag["n_filtered"] == len(chosen) <= C.TOP_K
    assert diag["n_filtered"] <= diag["n_eg"] <= 196
    assert all(s.eg_pvalue < C.EG_PVALUE and s.beta > 0 for s in chosen)
    assert all(s.sector == next(k for k, v in sectors("us").items() if s.a in v) for s in chosen)
    assert len(select_distance(form, sectors("us"))) == C.TOP_K
