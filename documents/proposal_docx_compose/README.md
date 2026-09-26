# PeakBaleen proposal (docx)

- `PeakBaleen_Proposal.docx` — the deliverable (9 pages, US Letter).
- `PeakBaleen_Proposal.pdf` — rendered preview.
- `proposal.js` — generator (docx-js). Rebuild: `node proposal.js`
- `figures/fig1.py`, `figures/fig2.py` — the two diagrams. Rebuild: `python3 figures/fig1.py && python3 figures/fig2.py`

Rendering a preview: `soffice --headless --convert-to pdf PeakBaleen_Proposal.docx`

## Evidence the text relies on (verified while writing)
- Baleen paper text: `../../lit_review/papers/fast24-baleen-.../paper.txt`
  - §3.1 "…leave that for future work" (peak optimisation deferred)
  - §5.6 failed peak attempt + "scoring episodes by their usefulness in reducing Peak DT"
  - App. A.3 "whack-the-mole game" (peak window is policy-dependent)
  - §5.6 16% gap to OPT; 9% of DT lost to late admissions
- Code: `../../lit_review/top8/repos/baleen/BCacheSim/`
  - `episodic_analysis/policies.py` — `PolicyUtilityPeakServiceTimeSize`,
    `PolicyUtilityPeakServiceTimeWeightedSize`, `score_peak_service_time_size`
  - `episodic_analysis/episodes.py:422,468-480` — `add_peak_to_eps`, single oracle window
    (`peak_ts1_start` / `peak_ts1_end`, asserted non-None)
- Solver packages available without root: simulated-bifurcation 2.0.0, dwave-neal 0.6.0,
  dimod, pyqubo (checked with `pip index versions`)
