# 6_final: final presentation deck

- **Deck:** `PeakBaleen_Final_v1.pptx`, 13 slides plus 3 backup slides, with speaker notes in every slide (also collected in `SPEAKER_NOTES.md`; about 12 minutes of speech for the 13 main slides). A PDF render is in `preview/PeakBaleen_Final_v1.pdf`.
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
| `preview/` | PDF render and contact sheet |

## Rebuild and check
```
changes/0_reproduce/env/bin/python -B changes/6_final/code/recompute_final.py > changes/6_final/result/recompute_final_out.txt
cd changes/6_final
export SLIDE_KIT=<kit dir with ndslides.py and preview.py>; PY=<python with python-pptx 1.0.2>
PYTHONDONTWRITEBYTECODE=1 $PY build_deck.py PeakBaleen_Final_v1.pptx
PYTHONDONTWRITEBYTECODE=1 $PY $SLIDE_KIT/preview.py PeakBaleen_Final_v1.pptx preview --dpi 80
cd ../.. && python3 changes/6_final/code/check_sources.py   # expect: 159 rows checked, 0 problems
```
Previews render titles lighter than PowerPoint does (LibreOffice and the variable Plex font); the fonts are embedded in the deck.
