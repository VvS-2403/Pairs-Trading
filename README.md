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
src/metrics.py          Sharpe with Lo (2002) SE, Newey-West t, drawdown, beta, Sharpe-difference bootstrap
src/synthetic.py        E4: synthetic OU pair and the theory-to-pipeline friction ladder
tests/                  unit tests of the engine and metrics (run `pytest -q`)
src/plots.py            figure style; savefig() writes figs/<name>.png and .eps
data/raw/               cached prices (see data/raw/README.md for source and date)
figs/  results/         written by the notebook
```

## Setup

```bash
pip install -r requirements.txt
pytest -q                      # 20 checks of the engine and metrics, about 3 s
jupyter notebook notebook.ipynb
```

Prices are already in `data/raw/`. Run `python -m src.data` only to refresh them.
Sections 8-10 of the notebook run the full backtests; set `RUN_HEAVY = True` in section 1.
Pair selection is cached in `results/cache/` after the first run.

## Team workflow

1. Edit only the notebook and report sections tagged with your member code (M1-M5).
2. Change a parameter in `src/config.py`, never inside a module, and tell the group.
3. Save every figure with `savefig(fig, name)` so it lands in `figs/` as PNG and EPS.
4. Mark your task in `Project_Tracker.csv` as `In progress` or `Done`.
5. Before submission, M1 runs Restart & Run All on the notebook and compiles the report.

## Status

`backtest.py` and `metrics.py` are tested (`tests/`, 20 tests) and the pipeline runs end to end
on real data (notebook section 7). Other modules are tested by their owners in their sections.

## Decision log (engine and metrics, M1)

| Decision | Why | Alternative considered |
| --- | --- | --- |
| Walk-forward 252-day formation, 126-day trading, roll 126 | Gatev et al. (2006) protocol; every trade uses only past data | Single in-/out-of-sample split: one test period, no re-estimation |
| Non-overlapping trading blocks | One clean daily return series, simple to test | Gatev's six overlapping portfolios: smoother, harder to audit |
| Tickers allowed in a window decided on formation data only | Filtering on the trading window drops stocks that later stop trading (look-ahead) | Old draft filtered on formation + trading window |
| Signal at close t, trade at close t+1 | Cannot trade at the close used to compute the signal; Gatev's one-day wait | Same close (lag 0): measured, adds about 0.03-0.1 Sharpe |
| Forced close at window end | Parameters are re-estimated each window; positions must not outlive them | Carry positions: mixes two parameter sets |
| Return on gross capital, pos (r_a - beta r_b) / (1 + abs(beta)) | Tracks dX of the log spread; comparable across pairs with different beta | Return on long leg only: overstates by 1 + beta |
| Cost per leg per transaction on gross traded; flip = 2 units | Every share bought or sold pays the spread | Per round trip: hides the cost of flips |
| Committed capital (K = 20 slots, idle slots earn 0) headline; employed reported too | Conservative and what an investor holds; Gatev report both | Employed only: ignores idle capital |
| Sharpe SE from Lo (2002) at daily frequency | Matches the data frequency; checked by Monte Carlo | Annual-frequency formula overstated SE by up to 70% |
| Newey-West t with lag floor(4 (n/100)^(2/9)) | Returns autocorrelated over holding periods; published automatic rule | Fixed 5 lags: shorter than typical holding periods |
| Strategy comparison by block bootstrap of Sharpe difference + Holm | Same days resampled for both rules keeps their correlation; three tests | Comparing two Sharpe SEs separately ignores correlation |
| E4 averaged over 200 synthetic pairs | One 12-year path is noisy (SD 2.9% a year across pairs) | One seed: gave 8.6% vs 12.7% mean |

## Data

Yahoo Finance daily adjusted closes, retrieved 26 Oct 2026 via `yfinance`. The ticker lists
are today's large caps, so the sample has survivorship bias (stated in the report).
