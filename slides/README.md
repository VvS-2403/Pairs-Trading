# Presentation slides (LaTeX Beamer)

The viva deck: 14 slides, 17:30 in total, 3:30 per member, one presenter per slide. Same structure as the SEIRD project's deck: one frame file per slide,
grouped by the member who presents it, a shared look in one file, a standalone preview for each member, and a main deck that
inputs the frames in slide order. The slide plan and times are in `../notes/TEAM_PLAN.md` (section 2).

| File | What it is |
|---|---|
| `main_slides.tex` | The whole deck: inputs the 14 frames in order. `main_slides.pdf` is the compiled deck |
| `deck_style.tex` | Colours, fonts, frame title, footer and the takeaway box, shared by every file |
| `M1/` | `s01_cover`, `s10_protocol`, `s11_perfect_pair`, `s14_conclusions` (Lakshya: 0:30 + 1:00 + 1:00 + 1:00) |
| `M2/` | `s02_question_data`, `s03_engle_granger`, `s04_persistence` (Nitin: 1:00 + 1:00 + 1:30) |
| `M3/` | `s05_ou_model`, `s06_estimating_kappa` (Tanishk: 2:00 + 1:30) |
| `M4/` | `s07_adf`, `s08_trading_rules`, `s12_us_backtest` (Vismay: 1:30 + 0:45 + 1:15) |
| `M5/` | `s09_bertram`, `s13_india` (Saatwik: 2:00 + 1:30) |
| `M1/M1_standalone.tex` ... `M5/M5_standalone.tex` | Preview of one member's own slides |

**Preview your own slides:** compile `Mn/Mn_standalone.tex` with pdflatex from inside its folder (twice).
**Build the full deck:** compile `main_slides.tex` with pdflatex from this folder (twice for the page numbers), then commit `main_slides.pdf`.

Rules
- Edit only your own frame files. No slide is shared between two members.
- Figures are read from `../figs/` (PNG); no figure is copied into this folder.
- Every number on a slide comes from `report/main.tex` or `results/`; if the report changes, check your slide.
- One frame per file, so the slide numbers stay equal to the frame numbers. Do not add overlays.
- A frame file starts with a comment giving its slide number, presenter and time; keep the slide numbers in the subtitles and cross-references ("slide 7") in step if the order changes.
- Keep the plain-language style of the report; no citations, as in the report.
