# Team plan: report and slides (final split, 14 Nov 2026)

Course rules (Project Component sheet): report of 3 to 4 pages, source code, and a viva of 15 to 20 minutes.
Marks out of 20: report 5, mathematical formulation 5, numerical results 5, viva 5.
Final submission: **15 November 2026**. Our report is 4 pages; the viva is 5 x 3.5 min = 17.5 min.
Each member's share is the report paragraphs they own and the slides they present. Code is not part of this split (it is submitted as it stands in the repository).

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
| Member | Report prose | Slides | Viva time |
| --- | --- | --- | --- |
| M1 | about 296 words | 1, 10, 11, 14 | 0:30 + 1:00 + 1:00 + 1:00 = 3:30 |
| M2 | about 288 words | 2, 3, 4 | 1:00 + 1:00 + 1:30 = 3:30 |
| M3 | about 294 words | 5, 6 | 2:00 + 1:30 = 3:30 |
| M4 | about 289 words | 7, 8, 12 | 1:30 + 0:45 + 1:15 = 3:30 |
| M5 | about 278 words | 9, 13 | 2:00 + 1:30 = 3:30 |

Report words are counted on the current report (about 1,450 words of prose, outside the tables, figures and equations).
One presenter per slide: no slide is shared or cut in halves.

## 1. Report: paragraphs each member owns and can defend in the viva
- **M1:** Position P&L; Walk-forward protocol; Evaluation; "What would a perfect pair earn?" (E4); the individual-trades half of "What happens with real stocks?".
- **M2:** Introduction; Engle-Granger cointegration; Data; the E2b sentence and the E9 sentences (in "Can we measure and detect mean reversion?" and "Does it hold in India, and do pairs stay pairs?").
- **M3:** Spread; Ornstein-Uhlenbeck process; Exact discretisation and estimation; the E1 sentences; Conclusion.
- **M4:** ADF is a test of kappa = 0; Trading rules (the s-score and the two benchmarks); the E2a sentences; the table-and-Sharpe half of "What happens with real stocks?".
- **M5:** Trading rules (the optimal-bands part); the E3 sentences; the India (E8) sentences; the Results opening paragraph; Implementation.

Rule: nobody edits another member's paragraph. Send wording changes to the owner, so the report stays at 4 pages with no references.

## 2. Slides: 14 slides, 17:30 in total
The slides follow the story (question, selection, model, tests, rules, protocol, results, conclusions) and each member's slides run one after another wherever the story allows.

| # | Slide | Presenter | Time |
| --- | --- | --- | --- |
| 1 | Cover and roadmap | M1 | 0:30 |
| 2 | The question and the data | M2 | 1:00 |
| 3 | Engle-Granger and the stricter critical value (E2b) | M2 | 1:00 |
| 4 | Do the pairs we select stay pairs? (E9) | M2 | 1:30 |
| 5 | The OU model | M3 | 2:00 |
| 6 | Estimating kappa (E1) | M3 | 1:30 |
| 7 | ADF test and what it can detect (E2a) | M4 | 1:30 |
| 8 | The four trading rules | M4 | 0:45 |
| 9 | Bertram's optimal bands (E3) | M5 | 2:00 |
| 10 | Walk-forward protocol, no look-ahead | M1 | 1:00 |
| 11 | What would a perfect pair earn? (E4) | M1 | 1:00 |
| 12 | Headline backtest on US stocks (E5) | M4 | 1:15 |
| 13 | India (E8) | M5 | 1:30 |
| 14 | Conclusions | M1 | 1:00 |

**Speaking order:** M1, M2 (slides 2-4), M3 (5-6), M4 (7-8), M5 (9), M1 (10-11), M4 (12), M5 (13), M1 (14).
M1 opens, presents the protocol and the perfect pair, and closes. M4 and M5 each appear twice because their topics sit at both ends of the story: the
rules (M4) and Bertram's bands (M5) must be explained before the protocol and the results, and the results (E5, India) must come after them.
Putting every member in one run would show the US and India results before the methods behind them.

Each member answers the questions on their own topic. Their viva notes are in `notes/` (M1 has not written theirs yet).

### The deck is a LaTeX Beamer project in `slides/`
Built the way the SEIRD project's deck was built (see `slides/README.md`). It replaces the earlier deck on claude.ai, which no longer matches the plan.
- **One frame file per slide**, in the folder of the member who presents it: `slides/M1/` (slides 1, 10, 11, 14), `M2/` (2, 3, 4), `M3/` (5, 6), `M4/` (7, 8, 12), `M5/` (9, 13).
- **`slides/deck_style.tex`** holds the look (colours, frame title, footer, takeaway box) so all slides match.
- **Preview your own slides:** compile `slides/Mn/Mn_standalone.tex` with pdflatex from inside your folder (twice).
- **Full deck:** compile `slides/main_slides.tex` from the `slides/` folder (twice). `slides/main_slides.pdf` is the compiled 14-slide deck.
- Figures come from `figs/`, and every number on a slide comes from the report or `results/`.
- Edit only your own files. If you change a number in the report, check your slide.

## What changed from the original plan (and why)
- **The code part was removed from the split** (14 Nov): the plan covers the report and the slides only.
- **No shared slides.** The old slide 11 (India and E9) became two slides, one per presenter (slides 4 and 13), and the old slide 9 (protocol and perfect pair) became slides 10 and 11.
- **The deck is now LaTeX Beamer** (`slides/`), one frame file per slide, instead of the claude.ai deck.
- **E1 moved from the old slide 10 (costs, cut with E6) to slide 6**, right after the OU model; the markets slide is now the India slide.
- **The individual-trades paragraph of the report is M1's.** In the original plan Table 1 was co-owned by M4 and M1.

## Before the viva
1. Each member re-reads their paragraphs and slides against the report as submitted (15 Nov), and compiles their preview (`slides/Mn/Mn_standalone.tex`).
2. Cross-training: each member teaches their slides in their time to the others.
3. Two timed mock vivas with questions on each member's topic.
