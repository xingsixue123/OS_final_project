# 6_final: final presentation deck

## Current version: v3 (use this one)
- `PeakBaleen_Final_v3.pptx` / `.pdf` = v2 with slide 2 (motivation) rewritten as three short points and a sketch of where Baleen's savings land, slide 3 (task) cut to the flow diagram plus budget, goal and data, slide 4 (baselines) with a new title, no footnote, no Region1 row, and three bullets on the 14–25% gap, slide 5 (key idea) without formulas, slide 8 (offline) with three reasons instead of big numbers, slide 9 (solver) with three plain bullets, and slide 10 (online) with three reasons. Built by `build_deck_v3.py`; numbers in `SOURCES_v3.md`; notes in `SPEAKER_NOTES_v3.md`.

## v2
- **Deck:** `PeakBaleen_Final_v2.pptx` and `PeakBaleen_Final_v2.pdf`; 13 slides plus 2 backup slides, speaker notes in every slide (also in `SPEAKER_NOTES_v2.md`).
- **Story:** the Ising min–max oracle offline (−13.7%), the Ising solver, a model trained on Ising labels online (dev −3.4%, Region6 −6.6%), and PeakBaleen = Baleen's model + the Ising peak model with load-aware admission: 10/10 development samples, −14.9% on the unseen Region4, and the pre-registered Region5 test of load-aware admission.
- **Files:** `build_deck_v2.py`, `algorithm_v2/` (updated Algorithm 2), `code/recompute_final_v2.py` → `result/numbers_v2.json`, `SOURCES_v2.md` (check: `python3 changes/6_final/code/check_sources.py SOURCES_v2.md`, 138 rows, 0 problems).
- **Rebuild:** as below, with `build_deck_v2.py PeakBaleen_Final_v2.pptx` after running both recompute scripts.

## v1 (superseded 2026-11-24)
- **Deck:** `PeakBaleen_Final_v1.pptx`, 13 slides plus 3 backup slides, with speaker notes in every slide (also collected in `SPEAKER_NOTES.md`; about 12 minutes of speech for the 13 main slides). The PDF version is `PeakBaleen_Final_v1.pdf`, exported with static IBM Plex fonts so it matches PowerPoint.
- **Outline:** approved 2026-11-24. The planned slide on the one-shot final test (samples 0.7–0.9) was dropped at the captain's decision, so the reserve samples are still untouched by deployed runs.
- **No new experiments.** Every result comes from runs already recorded in `RESEARCH.md`; this folder only recomputes and presents them.
- **Style:** the team's ND/EMNLP slide kit (python-pptx, kept outside this repo; point `SLIDE_KIT` at it).

| Slide | Message |
|---|---|
| 1 | Title |
| 2 | Disks are bought for the busiest 10 minutes, but Baleen optimizes the average |
| 3 | The task and how we test |
| 4 | Baselines: Baleen sits 14–25% above its own offline oracle |
| 5 | Key idea: min–max over all windows, as an Ising/QUBO energy |
| 6 | Design: three components (new labels, load feature, adaptive bar) |
| 7 | Algorithm 1 (Baleen) vs Algorithm 2 (PeakBaleen) |
| 8 | Result 1: offline, −13.7% and 37 of 39 samples |
| 9 | Result 2: the gain is the objective; Ising ties LP and CP-SAT |
| 10 | Result 3: deployed, the full design collapses on two samples; the adaptive bar is steady |
| 11 | Result 4: ablation by component on four test pools |
| 12 | Result 5: why the labels fail (scans at the peak) |
| 13 | What we learned, next steps |
| 14–17 | Backup: Region5 statistics, reproduction, earlier load-based attempts |

## Files
| Path | What |
|---|---|
| `build_deck.py` | Builds the deck and `SPEAKER_NOTES.md` |
| `code/recompute_final.py`, `result/recompute_final_out.txt`, `result/numbers.json` | Recompute every charted number from the raw result CSVs |
| `SOURCES.md`, `code/check_sources.py` | Every number on the slides mapped to `file#line`, and the checker |
| `assets/` | Algorithm images copied from `changes/5_midterm/algorithm/` |
| `PeakBaleen_Final_v1.pdf` | The deck as PDF |
| `preview/` | Layout-check contact sheet |

## Rebuild and check
```
changes/0_reproduce/env/bin/python -B changes/6_final/code/recompute_final.py > changes/6_final/result/recompute_final_out.txt
cd changes/6_final
export SLIDE_KIT=<kit dir with ndslides.py and preview.py>; PY=<python with python-pptx 1.0.2>
PYTHONDONTWRITEBYTECODE=1 $PY build_deck.py PeakBaleen_Final_v1.pptx
PYTHONDONTWRITEBYTECODE=1 $PY $SLIDE_KIT/preview.py PeakBaleen_Final_v1.pptx preview --dpi 80
cd ../.. && python3 changes/6_final/code/check_sources.py   # expect: 159 rows checked, 0 problems
```
The `preview.py` render shows titles lighter than PowerPoint (LibreOffice cannot bold the variable Plex font); for the PDF, export with the static IBM Plex Sans fonts (github.com/IBM/plex) on the fontconfig path:
```
FONTCONFIG_FILE=<fonts.conf listing the static Plex dir> soffice --headless --convert-to pdf --outdir changes/6_final changes/6_final/PeakBaleen_Final_v1.pptx
```
