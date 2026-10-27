# 5_midterm: mid-term progress slides (7 slides)

- **Live deck:** https://claude.ai/artifact/XTyrUmxzuVWm4A2p1NVZH4. It is private until shared from its Share menu, and downloads as .pptx or PDF.
- **This folder** holds the deck's full source, so it is contained in the repo. Every number on the slides points back to a result file in the repo.

| Slide | Content |
|---|---|
| 1 | Title |
| 2 | The task: flash-cache admission under a write budget; minimize the peak 10-minute disk load (P100); Meta Tectonic traces (Region = one storage cluster) |
| 3 | Baselines we ran: CoinFlip, RejectX, Baleen and Baleen's offline OPT, per Region |
| 4 | PeakBaleen design: offline min–max QUBO + Ising solver → labels; online load meter + adaptive admission bar |
| 5 | Algorithm 1 (Baleen) vs Algorithm 2 (PeakBaleen), LaTeX algorithm with highlighted changes |
| 6 | Results so far |
| 7 | Next steps |

## Files
| Path | What |
|---|---|
| `slides/project/deck.json`, `slides/project/slides/*.html` | The deck source: one 1920×1080 HTML slide per file, with speaker notes in `<aside>` (each ends with its "Sources:") |
| `algorithm/alg.tex`, `algorithm/alg1.png`, `algorithm/alg2.png`, `algorithm/build.sh` | Slide 5's algorithms: LaTeX source and the 300-dpi renders. In the live deck, `algorithm.html` references these images by their uploaded asset ids (`/_blob/…`). |
| `SOURCES.md` | Every value on every slide, mapped to `file#line` in the repo |
| `code/recompute.py`, `result/recompute_out.txt` | Recomputes the derived values (Baleen's offline OPT column, the 14–25% gap, the % changes) from raw CSVs |
| `code/check_sources.py` | Checks that each `SOURCES.md` row's value appears in its cited lines |

## Reproduce and check
```
changes/0_reproduce/env/bin/python -B changes/5_midterm/code/recompute.py > changes/5_midterm/result/recompute_out.txt
python3 changes/5_midterm/code/check_sources.py        # expect: 68 rows checked, 0 problems
bash changes/5_midterm/algorithm/build.sh              # rebuild the algorithm images (needs tectonic)
```

## Notes
- Trace names follow the Baleen paper. **Region1–7** are seven Meta Tectonic storage clusters (each can span a datacenter), recorded in 2019 (Regions 1–3), 2021 (Region4) and 2023 (Regions 5–7). A sample `sX` is a 0.1% slice of a cluster's blocks.
- The deck's claims follow `changes/4_story/STORY.md`; slide 6 keeps the evidence level of each result (pre-registered, or observed post hoc).
