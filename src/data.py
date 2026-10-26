"""Price data: universes, download, cleaning and loading.

Source: Yahoo Finance daily adjusted closes (splits and dividends) through the
`yfinance` package. Prices are downloaded once with `python -m src.data` and
committed as CSV under data/raw/, so experiments never depend on a live API.
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

US_SECTORS = {
    "Banks": ["JPM", "BAC", "C", "WFC", "GS", "MS", "USB", "PNC"],
    "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "HAL", "OXY", "VLO"],
    "Consumer staples": ["KO", "PEP", "PG", "CL", "KMB", "GIS", "CLX", "HSY"],
    "Technology": ["AAPL", "MSFT", "ORCL", "IBM", "INTC", "CSCO", "QCOM", "TXN"],
    "Retail": ["HD", "LOW", "WMT", "TGT", "COST", "DG", "ROST", "TJX"],
    "Utilities": ["DUK", "SO", "AEP", "ED", "XEL", "NEE", "D", "PEG"],
    "Industrials": ["CAT", "DE", "EMR", "ITW", "ETN", "PH", "DOV", "GD"],
}
INDIA_SECTORS = {
    "Banks": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
    "Auto": ["MARUTI", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT"],
    "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN"],
}

UNIVERSES = {
    "us": dict(start="2010-01-01", end="2026-09-30", benchmark="SPY",
               sectors=US_SECTORS, extra=["EWA", "EWC"]),
    "india": dict(start="2012-01-01", end="2026-09-30", benchmark="^NSEI",
                  sectors={s: [t + ".NS" for t in ts] for s, ts in INDIA_SECTORS.items()},
                  extra=[]),
}

MAX_GAP_DAYS = 3        # forward-fill gaps up to this many days
JUMP_FLAG = 0.25        # one-day moves above 25% are listed for inspection


def sectors(market):
    """Sector -> list of tickers for a market ('us' or 'india')."""
    return UNIVERSES[market]["sectors"]


def tickers(market):
    u = UNIVERSES[market]
    return [t for ts in u["sectors"].values() for t in ts] + u["extra"] + [u["benchmark"]]


def download(market):
    """Download adjusted closes for one market and save data/raw/<market>_prices.csv."""
    import yfinance as yf

    u = UNIVERSES[market]
    raw = yf.download(tickers(market), start=u["start"], end=u["end"],
                      auto_adjust=True, progress=False, threads=True)
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    close = close.sort_index().dropna(how="all")
    RAW.mkdir(parents=True, exist_ok=True)
    close.to_csv(RAW / f"{market}_prices.csv", float_format="%.6f")
    return close


def load_prices(market):
    """Adjusted closes, cleaned: gaps up to 3 days forward-filled, benchmark excluded."""
    path = RAW / f"{market}_prices.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing: run `python -m src.data` first")
    px = pd.read_csv(path, index_col=0, parse_dates=True).sort_index()
    px = px.ffill(limit=MAX_GAP_DAYS)
    bench = UNIVERSES[market]["benchmark"]
    return px.drop(columns=[bench], errors="ignore")


def benchmark_returns(market):
    """Daily simple returns of the market benchmark (SPY or NIFTY 50)."""
    px = pd.read_csv(RAW / f"{market}_prices.csv", index_col=0, parse_dates=True)
    b = px[UNIVERSES[market]["benchmark"]].ffill(limit=MAX_GAP_DAYS)
    return b.pct_change()


def jump_report(px):
    """List one-day moves above JUMP_FLAG (possible split or spin-off errors)."""
    r = px.pct_change(fill_method=None)
    hits = r[(r.abs() > JUMP_FLAG)].stack()
    hits.index.names = ["date", "ticker"]
    return hits.rename("return").reset_index()


def write_readme(summaries):
    lines = [
        "# Raw price data",
        "",
        f"Daily adjusted closes from Yahoo Finance via `yfinance`, retrieved {date.today().isoformat()}.",
        "Adjusted for splits and dividends (`auto_adjust=True`). Regenerate with `python -m src.data`.",
        "",
        "| File | Tickers | First date | Last date | Rows |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, px in summaries.items():
        lines.append(f"| {name}_prices.csv | {px.shape[1]} | {px.index[0].date()} | {px.index[-1].date()} | {len(px)} |")
    lines += ["", "One-day moves above 25%, listed for inspection. Those checked match real events",
              "(for example the 9 March 2020 oil-price crash), not split or spin-off errors:", ""]
    for name, px in summaries.items():
        jr = jump_report(px)
        if jr.empty:
            lines.append(f"- {name}: none")
        for _, row in jr.iterrows():
            lines.append(f"- {name}: {row['ticker']} on {pd.Timestamp(row['date']).date()}: {row['return']:+.1%}")
    (RAW / "README.md").write_text("\n".join(lines) + "\n", encoding="utf8")


if __name__ == "__main__":
    out = {}
    for m in UNIVERSES:
        px = download(m)
        missing = [t for t in tickers(m) if t not in px.columns or px[t].notna().sum() == 0]
        print(f"{m}: {px.shape[1]} tickers, {px.index[0].date()} to {px.index[-1].date()}, missing: {missing}")
        out[m] = px
    write_readme(out)
