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
| M1 | about 296 words | 1, 7 | 2:00 + 2:00 = 4:00 |
| M2 | about 288 words | 4, 8 | 2:00 + 2:00 = 4:00 |
| M3 | about 294 words | 2, 10 | 2:30 + 1:30 = 4:00 |
| M4 | about 289 words | 3, 6 | 2:00 + 2:00 = 4:00 |
| M5 | about 278 words | 5, 9 | 2:00 + 2:00 = 4:00 |

Report words are counted on the current report (about 1,450 words of prose, outside the tables, figures and equations).
One presenter per slide: no slide is shared or cut in halves.

## 1. Report: paragraphs each member owns and can defend in the viva
- **M1:** Position P&L; Walk-forward protocol; Evaluation; "What would a perfect pair earn?" (E4); the individual-trades half of "What happens with real stocks?".
- **M2:** Introduction; Engle-Granger cointegration; Data; the E2b sentence and the E9 sentences (in "Can we measure and detect mean reversion?" and "Does it hold in India, and do pairs stay pairs?").
- **M3:** Spread; Ornstein-Uhlenbeck process; Exact discretisation and estimation; the E1 sentences; Conclusion.
- **M4:** ADF is a test of kappa = 0; Trading rules (the s-score and the two benchmarks); the E2a sentences; the table-and-Sharpe half of "What happens with real stocks?".
- **M5:** Trading rules (the optimal-bands part); the E3 sentences; the India (E8) sentences; the Results opening paragraph; Implementation.

Rule: nobody edits another member's paragraph. Send wording changes to the owner, so the report stays at 4 pages with no references.

## 2. Slides: 10 slides, 20:00 in total, two slides per member
The viva is 20 minutes, so the deck is 10 slides (2 minutes each, 12 pt type), and every slide has exactly one presenter. Each slide pairs a piece of theory with the experiment that tests it, in the order of the report.

| # | Slide | Report section | Presenter | Time |
| --- | --- | --- | --- | --- |
| 1 | Cover, idea and roadmap | Introduction | M1 | 2:00 |
| 2 | OU model and estimating kappa (E1) | Model, Results | M3 | 2:30 |
| 3 | ADF test and what one year can detect (E2a) | Model, Results | M4 | 2:00 |
| 4 | Engle-Granger and false pairs (E2b) | Model, Results | M2 | 2:00 |
| 5 | Bertram's bands and daily checking (E3) | Model, Results | M5 | 2:00 |
| 6 | The four trading rules and the walk-forward protocol | Model, Data and method | M4 | 2:00 |
| 7 | What would a perfect pair earn? (E4) | Results | M1 | 2:00 |
| 8 | US backtest (E5) | Results | M2 | 2:00 |
| 9 | India (E8) | Results | M5 | 2:00 |
| 10 | Do selected pairs stay pairs? (E9) and conclusions | Results, Conclusion | M3 | 1:30 |

**Speaking order:** M1, M3, M4, M2, M5, M4, M1, M2, M5, M3.
Every member presents exactly two slides and 4:00. Within each slide the theory comes first and its experiment second, as in the report's "Can we measure and detect mean reversion?" paragraph.

Each member answers the questions on their own topic. Their viva notes are in `notes/` (M1 has not written theirs yet).

### The deck is a LaTeX Beamer project in `slides/`
Built the way the SEIRD project's deck was built (see `slides/README.md`). It replaces the earlier deck on claude.ai, which no longer matches the plan.
- **One frame file per slide**, in the folder of the member who presents it: `slides/M1/` (slides 1, 7), `M2/` (4, 8), `M3/` (2, 10), `M4/` (3, 6), `M5/` (5, 9).
- **`slides/deck_style.tex`** holds the look (colours, frame title, footer, takeaway box) so all slides match.
- **Preview your own slides:** compile `slides/Mn/Mn_standalone.tex` with pdflatex from inside your folder (twice).
- **Full deck:** compile `slides/main_slides.tex` from the `slides/` folder (twice). `slides/main_slides.pdf` is the compiled 10-slide deck.
- Figures come from `figs/`, and every number on a slide comes from the report or `results/`.
- Edit only your own files. If you change a number in the report, check your slide.

## What changed from the original plan (and why)
- **The code part was removed from the split** (14 Nov): the plan covers the report and the slides only.
- **No shared slides.** India (slide 15) and E9 (slide 16) are separate slides, one per presenter, as are the protocol (8) and the perfect pair (13).
- **The deck was cut to 10 slides** (22 Nov): two slides per member, 4:00 each, 12 pt type so it is readable. Theory and its experiment share a slide (OU with E1, ADF with E2a, Engle-Granger with E2b, Bertram with E3), and the rules and protocol share one slide. The slides keep the report's order except that the four trading rules now sit with the protocol, just before the results.
- **The deck is now LaTeX Beamer** (`slides/`), one frame file per slide, instead of the claude.ai deck.
- **The individual-trades paragraph of the report is M1's.** In the original plan Table 1 was co-owned by M4 and M1.

## Before the viva
1. Each member re-reads their paragraphs and slides against the report as submitted (15 Nov), and compiles their preview (`slides/Mn/Mn_standalone.tex`).
2. Cross-training: each member teaches their slides in their time to the others.
3. Two timed mock vivas with questions on each member's topic.
