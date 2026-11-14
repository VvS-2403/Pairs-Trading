# Team plan: report, code understanding and slides (final split, 14 Nov 2026)

Course rules (Project Component sheet): report of 3 to 4 pages, source code, and a viva of 15 to 20 minutes.
Marks out of 20: report 5, mathematical formulation 5, numerical results 5, viva 5.
Final submission: **15 November 2026**. Our report is 4 pages; the viva is 5 x 3.5 min = 17.5 min.

## Who is who
| Code | Name | ID | Topic (unchanged from the original plan) |
| --- | --- | --- | --- |
| M1 | Lakshya Satya | 2024ADPS0828G | Backtest engine, walk-forward protocol, the perfect-pair test (E4) |
| M2 | Nitin Sureshkumar | 2024ADPS0881G | Cointegration, Engle-Granger, pair selection, data (E2b, E9) |
| M3 | Tanishk Tasgaonkar | 2024ADPS0875G | The OU process, estimation (E1) |
| M4 | Vismay Shanbhag | 2024ADPS0876G | ADF test, trading rules S0-S2, headline backtest (E2a, E5) |
| M5 | Saatwik Tiwari | 2024ADPS0878G | Bertram's optimal bands (E3), India (E8) |

(M5 = Saatwik is by elimination: the other four codes match the authors of the pull requests. Correct this if wrong.)

## The split at a glance (each member carries about the same)
| Member | Report prose | Code to explain line by line | Slides (viva time) |
| --- | --- | --- | --- |
| M1 | about 296 words | `backtest.py` (235 lines) | 1, 9, 12 = 3:30 |
| M2 | about 288 words | `data.py`, `cointegration.py`, `plots.py` (241 lines) | 2, 6, half of 11 = 3:30 |
| M3 | about 294 words | `ou.py` OU half, `selection.py`, `config.py` (211 lines) | 3, 4 = 3:30 |
| M4 | about 289 words | `strategies.py`, `metrics.py` (232 lines) | 5, 7, 10 = 3:30 |
| M5 | about 278 words | `ou.py` Bertram half, `synthetic.py` (210 lines) | 8, half of 11 = 3:30 |

Words are counted on the current report (about 1,450 words of prose, outside the tables, figures and equations).
Lines are counted on `src/` (about 1,130 lines in total).

## 1. Report: paragraphs each member owns and can defend in the viva
- **M1:** Position P&L; Walk-forward protocol; Evaluation; "What would a perfect pair earn?" (E4); the individual-trades half of "What happens with real stocks?".
- **M2:** Introduction; Engle-Granger cointegration; Data; the E2b sentence and the E9 sentences (in "Can we measure and detect mean reversion?" and "Does it hold in India, and do pairs stay pairs?").
- **M3:** Spread; Ornstein-Uhlenbeck process; Exact discretisation and estimation; the E1 sentences; Conclusion.
- **M4:** ADF is a test of kappa = 0; Trading rules (the s-score and the two benchmarks); the E2a sentences; the table-and-Sharpe half of "What happens with real stocks?".
- **M5:** Trading rules (the optimal-bands part); the E3 sentences; the India (E8) sentences; the Results opening paragraph; Implementation.

Rule: nobody edits another member's paragraph. Send wording changes to the owner, so the report stays at 4 pages with no references.

## 2. Code understanding: what each member must be able to explain
Each member explains their files in the viva (what each function does and why), and knows the tests for them
(`pytest -q`, 60 checks): M1 `test_backtest`, M2 `test_data` and `test_cointegration`, M3 `test_selection`, M4 `test_metrics`.
- **M1, `backtest.py`:** make_windows, run_selection's cache, simulate, pair_returns (one-day lag, costs), extract_trades, why there is no look-ahead.
- **M2, `data.py`, `cointegration.py`, `plots.py`:** loading and cleaning prices, the jump report, adf_test, engle_granger_both, naive_residual_adf, benjamini_hochberg, the figure style.
- **M3, `ou.py` (OU half), `selection.py`, `config.py`:** OUParams, simulate_ou (exact and Euler), ar1_fit, fit_ou; how select_cointegrated applies the half-life and crossing filters; where each parameter lives.
- **M4, `strategies.py`, `metrics.py`:** band_positions, flip_positions, positions (S0-S3 rules); compute_metrics, sharpe_se_lo, newey_west_t, sharpe_diff_bootstrap, max_drawdown.
- **M5, `ou.py` (Bertram half), `synthetic.py`:** bertram_cycle_time, bertram_return_rate, bertram_bands, first_passage_cycle_mc; the theory and fine-grid functions behind E4 (M1 explains the experiment's result, M5 the code that computes the theory).
- Shared and not assigned: `kalman_hedge` in `strategies.py` is unused (E10 was cut); say so if asked.

## 3. Slides: 12 slides, 17:30 in total
| # | Slide | Owner | Time |
| --- | --- | --- | --- |
| 1 | Cover and roadmap | M1 | 0:30 |
| 2 | The question and the data | M2 | 1:00 |
| 3 | The OU model | M3 | 2:00 |
| 4 | Estimating kappa (E1) | M3 | 1:30 |
| 5 | ADF test and what it can detect (E2a) | M4 | 1:30 |
| 6 | Engle-Granger and the stricter critical value (E2b) | M2 | 1:00 |
| 7 | The four trading rules | M4 | 0:45 |
| 8 | Bertram's optimal bands (E3) | M5 | 2:00 |
| 9 | Walk-forward protocol and the perfect pair (E4) | M1 | 2:00 |
| 10 | Headline backtest on US stocks (E5) | M4 | 1:15 |
| 11 | India (M5, 1:30) and do pairs stay pairs? (E9) (M2, 1:30) | M5 + M2 | 3:00 |
| 12 | Conclusions | M1 | 1:00 |

Each member answers the questions on their own topic. Their viva notes are in `notes/` (M1 has not written theirs yet).

## What changed from the original plan (and why)
- **Slide 10 (costs) became "Estimating kappa" (E1) and moved to slide 4.** E6 was cut, and E1 belongs right after the OU model.
- **Slide 11 (markets) is now India plus E9.** E7, the sector tables and the Kalman filter were cut.
- **`metrics.py` moved from M1 to M4.** M4 already interprets Table 1 (Sharpe error, Newey-West t), and M1's `backtest.py` is large enough alone.
- **`selection.py` and `config.py` went to M3, and `synthetic.py` to M5**, to even out the code, because M3 and M5 had the smallest modules.
- **The individual-trades paragraph is now M1's.** In the original plan Table 1 was co-owned by M4 and M1.

## Before the viva
1. Each member re-reads their paragraphs and slides against the report as submitted (15 Nov).
2. Cross-training: each member teaches their slides in 3.5 minutes to the others.
3. Two timed mock vivas with questions on each member's topic.
