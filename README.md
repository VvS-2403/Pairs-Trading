# Pairs Trading with Mean-Reverting Stochastic Processes

MAC F244 group project (Topic 17). We model the log-price spread of a stock pair as an
Ornstein-Uhlenbeck process, select pairs with ADF and Engle-Granger tests, and compare four
published trading rules on US and Indian stocks (2010-2026):

| ID | Strategy | Paper |
| --- | --- | --- |
| S0 | Distance method | Gatev, Goetzmann & Rouwenhorst (2006) |
| S1 | Cointegration z-score | Engle & Granger (1987) |
| S2 | OU s-score | Avellaneda & Lee (2010) |
| S3 | OU optimal bands | Bertram (2010) |

## Layout

```text
Project_Tracker.csv     tasks per member: update the Status column when you finish a task
notebook.ipynb          master notebook: every experiment, figure and table (sections tagged by owner)
report/main.tex         report, sections tagged by owner; report/refs.bib holds every reference
src/config.py           every parameter (windows, filters, thresholds, costs) in one place
src/data.py             universes, download and loading (Yahoo Finance via yfinance)
src/ou.py               OU simulation (exact and Euler-Maruyama), estimation, Bertram bands
src/cointegration.py    ADF, Engle-Granger both directions, Benjamini-Hochberg
src/selection.py        pair selection on one formation window
src/strategies.py       trading rules and the Kalman hedge ratio
src/backtest.py         walk-forward engine with one-day execution lag and costs
src/metrics.py          Sharpe with Lo (2002) SE, Newey-West t, drawdown, beta
src/plots.py            figure style; savefig() writes figs/<name>.png and .eps
data/raw/               cached prices (see data/raw/README.md for source and date)
figs/  results/         written by the notebook
```

## Setup

```bash
pip install -r requirements.txt
jupyter notebook notebook.ipynb
```

Prices are already in `data/raw/`. Run `python -m src.data` only to refresh them.
Sections 8-13 of the notebook run the full backtests; set `RUN_HEAVY = True` in section 1.
Pair selection is cached in `results/cache/` after the first run.

## Team workflow

1. Edit only the notebook and report sections tagged with your member code (M1-M5).
2. Change a parameter in `src/config.py`, never inside a module, and tell the group.
3. Save every figure with `savefig(fig, name)` so it lands in `figs/` as PNG and EPS.
4. Mark your task in `Project_Tracker.csv` as `In progress` or `Done`.
5. Before submission, M1 runs Restart & Run All on the notebook and compiles the report.

## Status

The `src/` modules are first drafts and have not been run end to end yet. Each owner tests
their module in their notebook section (tracker tasks T08-T23).

## Data

Yahoo Finance daily adjusted closes, retrieved 26 Oct 2026 via `yfinance`. The ticker lists
are today's large caps, so the sample has survivorship bias (stated in the report).
