"""Tests of src/data.py: loading, cleaning and the jump report (task T08).

Real-data checks read the committed CSVs in data/raw/. Cleaning checks use small
synthetic files, because the real stock columns contain no gaps to forward-fill.
"""

import numpy as np
import pandas as pd
import pytest

from src import data as D


def _write_prices(tmp_path, df, market="us"):
    df.to_csv(tmp_path / f"{market}_prices.csv")


@pytest.mark.parametrize("market,n_cols", [("us", 58), ("india", 26)])
def test_load_prices_real_data(market, n_cols):
    px = D.load_prices(market)
    u = D.UNIVERSES[market]
    expected = [t for ts in u["sectors"].values() for t in ts] + u["extra"]
    assert px.shape[1] == n_cols
    assert set(px.columns) == set(expected)            # every sector ticker, nothing else
    assert u["benchmark"] not in px.columns            # benchmark is never traded
    assert px.index.is_monotonic_increasing and not px.index.duplicated().any()
    assert px.notna().all().all()                      # no gaps left after cleaning
    assert (px > 0).all().all() and np.isfinite(px.values).all()


def test_forward_fill_limit(tmp_path, monkeypatch):
    idx = pd.bdate_range("2020-01-01", periods=12)
    df = pd.DataFrame({"A": np.arange(1, 13.0), "B": np.arange(1, 13.0) * 2,
                       "SPY": np.arange(1, 13.0)}, index=idx)
    df.loc[idx[2:5], "A"] = np.nan                     # 3-day gap: filled
    df.loc[idx[6:11], "B"] = np.nan                    # 5-day gap: only first 3 filled
    _write_prices(tmp_path, df)
    monkeypatch.setattr(D, "RAW", tmp_path)
    px = D.load_prices("us")
    assert list(px.columns) == ["A", "B"]
    assert px["A"].notna().all() and (px["A"].iloc[2:5] == df["A"].iloc[1]).all()
    assert px["B"].iloc[6:9].notna().all() and px["B"].iloc[9:11].isna().all()


def test_load_prices_sorts_and_reports_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "RAW", tmp_path)
    with pytest.raises(FileNotFoundError):
        D.load_prices("us")
    idx = pd.bdate_range("2020-01-01", periods=4)[::-1]            # unsorted on disk
    _write_prices(tmp_path, pd.DataFrame({"A": [4.0, 3, 2, 1], "SPY": [4.0, 3, 2, 1]}, index=idx))
    assert D.load_prices("us").index.is_monotonic_increasing


def test_jump_report_flags_only_large_moves():
    idx = pd.bdate_range("2020-01-01", periods=8)
    px = pd.DataFrame({"A": [100, 101, 131.3, 132, 100, 101, 102, 103.0],     # +30% then -24% (not flagged)
                       "B": [50, 50.5, 37, 37.2, 37.4, 37.5, 37.6, 37.7]},   # -26.7% on day 2
                      index=idx)
    px.loc[idx[5], "B"] = np.nan                                             # gap must not create a hit
    jr = D.jump_report(px)
    assert list(jr.columns) == ["date", "ticker", "return"]
    assert sorted(zip(jr["ticker"], jr["date"].dt.date.astype(str))) == [
        ("A", "2020-01-03"), ("B", "2020-01-03")]
    assert (jr["return"].abs() > D.JUMP_FLAG).all()


def test_jump_report_empty_when_no_jumps():
    px = pd.DataFrame({"A": [100.0, 101, 102, 101]}, index=pd.bdate_range("2020-01-01", periods=4))
    assert D.jump_report(px).empty


@pytest.mark.parametrize("market", ["us", "india"])
def test_jump_report_matches_committed_readme(market):
    """README lists each flagged jump; the report on the raw file must reproduce that list."""
    raw = pd.read_csv(D.RAW / f"{market}_prices.csv", index_col=0, parse_dates=True)
    jr = D.jump_report(raw)
    listed = [ln for ln in (D.RAW / "README.md").read_text(encoding="utf8").splitlines()
              if ln.startswith(f"- {market}:")]
    assert 0 < len(jr) < 50 and len(jr) == len(listed)


@pytest.mark.parametrize("market", ["us", "india"])
def test_benchmark_returns(market):
    b = D.benchmark_returns(market)
    assert len(b) == len(D.load_prices(market))
    assert np.isfinite(b.dropna().values).all() and b.isna().sum() <= 2   # leading NaN(s) only