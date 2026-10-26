"""Shared settings for every module and experiment.

Change a value here, never inside a module, so that every result in
results/ and figs/ comes from one set of choices. Paper defaults are used
wherever a paper fixes the number, so no threshold is tuned on results.
"""

SEED = 42
DT = 1 / 252                      # one trading day, in years

# Walk-forward protocol (Gatev, Goetzmann & Rouwenhorst 2006)
FORMATION_DAYS = 252              # 12-month formation window
TRADING_DAYS = 126                # 6-month trading window, rolled every 6 months
TOP_K = 20                        # pairs traded per window (capital slots)

# Pair selection filters
EG_PVALUE = 0.05                  # Engle-Granger, MacKinnon (2010) p-values, both directions
BH_Q = 0.10                       # Benjamini-Hochberg q, reported as a diagnostic only
HALF_LIFE_RANGE = (2, 63)         # trading days; at most half the trading window
MIN_CROSSINGS_PER_YEAR = 12       # Sarmento & Horta (2020)

# Transaction costs: basis points per leg per transaction
COST_BPS = {"us": 10, "india": 15}

# Trading rules (thresholds taken from the papers, not fitted)
DISTANCE_ENTRY = 2.0                                  # Gatev et al. (2006): 2 formation sigmas
ZSCORE = dict(entry=2.0, exit=0.5)                    # classic cointegration z-score rule
SSCORE = dict(open_long=-1.25, open_short=1.25,       # Avellaneda & Lee (2010)
              close_long=-0.50, close_short=0.75)
STOP_LOSS = None                                      # |s| level; E7 tests 4.0
KALMAN = dict(delta=1e-4, entry=1.0)                  # Chan (2013), stretch strategy

# Evaluation
TEST_START = "2022-01-01"         # design frozen on earlier data; this block is out of sample
SUB_PERIODS = {
    "2010-14": ("2010-01-01", "2014-12-31"),
    "2015-19": ("2015-01-01", "2019-12-31"),
    "2020 (COVID)": ("2020-01-01", "2020-12-31"),
    "2021-26": ("2021-01-01", "2026-12-31"),
}
NW_LAGS = 5                       # Newey-West lags for the t-statistic of mean return

STRATEGY_LABELS = {
    "distance": "S0 Distance (Gatev 2006)",
    "zscore": "S1 Cointegration z-score",
    "sscore": "S2 OU s-score (Avellaneda-Lee 2010)",
    "bertram": "S3 OU optimal bands (Bertram 2010)",
    "kalman": "S4 Kalman hedge ratio (stretch)",
}
