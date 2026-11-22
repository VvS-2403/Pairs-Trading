# Presentation slides (LaTeX Beamer)

The viva deck: 17 short slides in the report's order, 20:00 in total, 4:00 per member, one presenter per slide. Same structure as the SEIRD project's deck: one frame file per slide,
grouped by the member who presents it, a shared look in one file, a standalone preview for each member, and a main deck that
inputs the frames in slide order. The slide plan and times are in `../notes/TEAM_PLAN.md` (section 2).

| File | What it is |
|---|---|
| `main_slides.tex` | The whole deck: inputs the 17 frames in order. `main_slides.pdf` is the compiled deck |
| `deck_style.tex` | Colours, fonts, frame title, footer and the takeaway box, shared by every file |
| `M1/` | `s01_cover`, `s08_protocol`, `s13_perfect_pair`, `s17_conclusions` (Lakshya: 0:45 + 1:15 + 1:15 + 0:45) |
| `M2/` | `s04_engle_granger`, `s07_data`, `s11_size_e2b`, `s16_persistence` (Nitin: 1:00 + 0:45 + 1:00 + 1:15) |
| `M3/` | `s02_ou_model`, `s09_estimating_kappa` (Tanishk: 2:15 + 1:45) |
| `M4/` | `s03_adf`, `s05_trading_rules`, `s10_adf_power`, `s14_us_backtest` (Vismay: 1:00 + 1:00 + 0:45 + 1:15) |
| `M5/` | `s06_bertram`, `s12_bertram_check`, `s15_india` (Saatwik: 1:15 + 1:15 + 1:30) |
| `M1/M1_standalone.tex` ... `M5/M5_standalone.tex` | Preview of one member's own slides |

**Preview your own slides:** compile `Mn/Mn_standalone.tex` with pdflatex from inside its folder (twice).
**Build the full deck:** compile `main_slides.tex` with pdflatex from this folder (twice for the page numbers), then commit `main_slides.pdf`.

Rules
- Edit only your own frame files. No slide is shared between two members.
- Figures are read from `../figs/` (PNG); no figure is copied into this folder.
- Every number on a slide comes from `report/main.tex` or `results/`; if the report changes, check your slide.
- One frame per file, so the slide numbers stay equal to the frame numbers. Do not add overlays.
- A frame file starts with a comment giving its slide number, presenter and time; keep the slide numbers in the subtitles and cross-references ("slide 7") in step if the order changes.
- Keep the plain-language style of the report and keep slides short (20-minute talk); the report's references are not repeated on the slides.
