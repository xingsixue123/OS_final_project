# PeakBaleen: research index

**Single source of truth for the project.**
- **Last updated:** 2026-10-16 (H3′ FAIL; Track C negative on dev, no finalist; Region5 H4 PASS; X1 fails again).
- **Team:** Ching-Hao Chiu, Jie Fu, Sixue Xing (captain).
- **Branch:** `phase2-deployable-peak`. Phase 1 lives on `phase1-reproduce-and-litreview`.

Update this file at every checkpoint. Detailed evidence lives in each folder's `RESULTS*.md` / `PROGRESS.md`.

## 1. The question
Baleen (FAST '24) chooses which blocks to admit to a flash cache. It optimises *average* disk-head time (DT), but provisioning is set by *peak* DT. Our proposal asks two things:
1. Can episode selection that targets the peak (min-max over 10-minute windows, formulated as a QUBO/Ising problem) lower peak backend load at the same flash write rate?
2. Does that gain survive deployment through Baleen's online ML model?

## 2. Status at a glance
| Phase / track | What | State |
|---|---|---|
| 0: Reproduction | Baleen artifact, sandboxed and frozen | **done** (`changes/0_reproduce/RESULTS.md`) |
| 1: Literature + real-harness tests | QUBO/Ising reviews, synthetic audit, harness tests, deep-explore Q1–Q3 | **done** (`changes/1_literature_review/`) |
| 2 · WP0 | Overlay adding a causal demand-load feature (scope v2) | **done**, CP1 (`f79808f`) |
| 2 · WP1 | H1′ offline breadth, Regions 4–7 × 10 samples | **done** (`08ad0d2`) |
| 2 · WP5 | Ising track: tight-budget tuning, H2′ test, rolling variant, scaling | **done** (`fd54e76`, `b6f44e2`) |
| 2 · WP2 | Deployed 2×2 study on dev (labels × `load`) | **done**, CP2-A (`cba9970`); finalists X1/X2 |
| 2 · WP3 | H3′ test on samples 0.4–0.6 | **done: H3′ NO, H3′-labels NO** (`wp3_test/RESULTS_test.md`) |
| 2 · WP8 (Track C) | Deployment-aware Ising objectives on dev | **done, negative** (`wp8_trackC/RESULTS_dev.md`). Stage 1: cheap proxy NOT valid. Stage 2 (64 full-sim evaluations): no config passed the pre-registered screen gate (S1: STU10R1 −0.26, ANC3 −0.84, ANC10 −1.80). Mechanism: Baleen anchoring fixes Region7 (first-access admission back, best Region7 P100 36.46) but gives back Region6's scan gain. No Track C arm in Stage 3. |
| 2 · WP9 (Region5) | Fresh deployed test: H4 = load-adaptive threshold on Baleen models (A+α) vs A, B; X1 as Ising record | **done: H4 YES** (A+α 35.02 vs A 36.17, 5/6; B+α 34.48, 6/6); X1 fails again (s0.5 51.46). `wp9_region5/RESULTS_test.md` |
| 2 · WP4/6/7 | Mechanism analysis, mid-term report, paper | to do |

## 3. Hypothesis ledger
Only valid results are listed: held-out or test data, matched write rate within ±1%, every seed and retrain included.

| ID | Hypothesis | Verdict | Key evidence | Where |
|---|---|---|---|---|
| R | The released artifact reproduces the paper | **Yes, with nuance** | RejectX and CoinFlip bit-exact; Baleen within ±0.6 of the authors' released-metric runs. The paper's Figure 9 Region6/7 Baleen bars use an unreleased `tracedrop` metric and cannot be reproduced. Re-averaged with a consistent metric, the 12% headline is ≈11.3%. | `0_reproduce/RESULTS.md` |
| Q1 / H1 | A peak-aware selection lowers peak load offline | **Yes** | 6/6 held-out instances: 27.0 vs 32.3 (−16%) | `1_literature_review/explore/q2/RESULTS.md` |
| H1′ | The offline gain holds broadly (Regions 4–7 × 10 samples) | **Yes** | 39 instances: PT (Ising) 37/39 wins, −13.7%; CP-SAT −13.2%; LP −13.0%. Regions 5–7: 30/30 wins, ≈−16%. Region4: only −3 to −5%. | `2_deployable_peak/wp1_offline/RESULTS.md` |
| Q2 | Ising beats classical solvers at 10/60/300 s | **No** | Best only at 10 s; CP-SAT wins at 60–300 s | `explore/q2/RESULTS.md` |
| H2′ | Ising beats classical at tight budgets of 1/3/10 s (pre-registered) | **No** | PT: 1/6, 6/6, 4/6 instances; EIM: 0/6, 5/6, 3/6. Ising best only at 3 s. | `wp5_ising/RESULTS_test.md` |
| S | Ising scaling (a contribution, no pass/fail) | **Reported** | Matrix-free SB: ≤214 MB up to 126k variables. The dense SB package runs out of memory beyond ≈70k variables. | `wp5_ising/RESULTS_dev.md` |
| Q3 | Peak labels survive distillation with frozen features | **No** | 2/6 wins; 0.4–1.1 points worse than Baleen online on average | `explore/q3/RESULTS.md` |
| H3′ | Ising peak labels + causal `load` signal beat Baleen and Baleen + `load` (deployed) | **No** (test) | X1 40.53 vs A 39.27 / B 39.17; wins 5/6 but one catastrophic instance (Region7 s0.5: 52.3; its peak is a big-offset scan the F1-label models do not admit). H3′-labels also NO (3/6 vs A+α). Post-hoc, not pre-registered: the load-adaptive threshold on Baleen's own models is best (A+α 38.30, 5/6 vs A, −2.5%). | `wp3_test/RESULTS_test.md` |
| H4 | Load-adaptive admission threshold on Baleen's own models beats Baleen (deployed, fresh Region5) | **Yes** (pre-registered) | A+α 35.02 vs A 36.17 / B 36.37 (5/6, +1.16, retrain SE 0.09); B+α 34.48 (6/6). Gain concentrated on s0.5 (instance SE 0.75) | `wp9_region5/RESULTS_test.md` |

**What the evidence says so far:**
- The **min-max formulation** is the source of the gain, and it is robust offline.
- **Ising/QUBO solvers are competitive** (best mean offline peak in H1′; best at a 3 s budget), but not better than classical solvers by the pre-registered criteria.
- **Deployability failed the pre-registered test.** Day-1 min-max labels are brittle when the peak type changes (scan vs burst). The load-adaptive threshold, not the Ising labels, carries the deployed gain so far (post-hoc).

## 4. Decision log
| Date | Decision | Record |
|---|---|---|
| 09-26 | Reproduce Baleen first; freeze the artifact; sandbox every run (no writes outside `changes/`) | `0_reproduce/README.md` |
| 09-27 | Fix the swap boundary: only the offline selection `Policy` may change | `changes/SCOPE.md` |
| 09-27 | Exclude Wong's thesis method from the baselines (cite it as related work only) | chat with captain |
| 09-28 | Reject "LP as the main method"; keep searching for Ising/QUBO selectors | captain |
| 09-28 | Pre-register Q1–Q3 with dev/held-out splits | `explore/PROTOCOL.md` |
| 09-29 | Scope v2: allow one causal demand-side `load` feature, via an overlay with bit-exact gates | `changes/SCOPE_v2.md` |
| 10-01 | Restore Ising as required: H3′ uses Ising labels, H2′ is required, scaling is reported | `2_deployable_peak/PLAN.md` (`5e49299`) |
| 10-01 | CP1 accepted: GET-only demand, one-line `train.py` plumbing, the artifact's own retrain nondeterminism | `SCOPE_v2.md` §1a |
| 10-01 | CPU topology: logical CPUs k and k+12 share a core; timing on 0–7 keeps 12–19 idle | `SCOPE_v2.md` §1a |
| 10-03 | H2′ protocol committed before any test run | `wp5_ising/PROTOCOL_v2_H2.md` (`fd54e76`) |
| 10-03 | WP2 finalist rule written before the confirmation retrains (score S vs the better of A and B) | `wp2_deployed/PROGRESS.md` |
| 10-04 | H3′ protocol committed (X1 primary, X2 secondary, H3′-labels attribution vs A+α / B+α); WP3 waits on G3 | `wp2_deployed/PROTOCOL_v2_H3.md` (`cba9970`) |
| 10-16 | H3′ failed on test. H4 (load-adaptive threshold on Baleen's models, A+α) pre-registered for a fresh Region5 test, which runs whether or not Track C yields a finalist | `wp8_trackC/PLAN_C.md` §6 (`d10e572`) |

## 5. Checkpoints and pre-registrations
| Checkpoint | Gate | Commit |
|---|---|---|
| Phase-1 protocol | Q1–Q3 criteria before tuning | `be284a3` (`explore/PROTOCOL.md`) |
| CP1 | Overlay G1 (bit-exact) + train/serve parity; coordinator review | `f79808f` |
| CP2-B | H2′ protocol before the test | `fd54e76` |
| CP2-A | H3′ protocol before the test | `cba9970` |
| G3 | Teammate review of `PATCH.diff` before any WP3 test run | **waived by the captain 2026-10-05** (`SCOPE_v2.md` §1a) |

## 6. Where things are
```
OS_final_project/
  RESEARCH.md                 this index
  documents/                  course spec, proposal (PeakBaleen_Proposal.pdf), Baleen paper
  lit_review/                 initial paper survey that chose Baleen
  changes/
    SCOPE.md, SCOPE_v2.md     swap boundary v1 (phase 1) and v2 (phase 2)
    0_reproduce/              frozen artifact + sandboxed reproduction (env/, work/ not in git)
    1_literature_review/      lit reviews, ising_followup (synthetic audit), harness_eval, explore (Q1–Q3)
    2_deployable_peak/        PLAN.md; wp0_overlay, wp1_offline, wp5_ising, wp2_deployed
```
- **Environments (not in git):**
  - Baleen env: `changes/0_reproduce/env`
  - Solver env: `changes/1_literature_review/explore/env`
- **Data:** `explore/common/data` (all 70 trace samples, sha1-checked).
- **Instances:** `explore/common/inst`, `wp1_offline/inst`.

## 7. How to resume after an interruption (humans or agents)
Sessions end without warning; every track is resumable from files.
1. **Check what's running.** `ps -eo pid,etimes,args | grep 2_deployable_peak`. If nothing is running, the track died.
2. **Read the track's progress log.** Each track's `PROGRESS.md` ends with its latest status and a RESUME section. Its `trials.csv` is the ledger: every evaluation, with a unique key and a matched flag.
3. **Restart the drivers.** Re-launch the resumable drivers listed there. Partially finished simulations cannot be reused, so restart those evaluations cleanly. Never change a pre-registered rule, config, seed or instance.
4. **Rules that always apply:**
   - nothing under `0_reproduce/` or `1_literature_review/` is modified;
   - every Baleen process runs under `bwrap` with a private `/tmp`;
   - one `train` at a time (`flock changes/2_deployable_peak/.train.lock`);
   - timing runs hold cores 0–7, and CPUs 12–19 stay idle while they run (`TIMING_IDLE` flag);
   - leak check and `check_frozen.sh` at every milestone;
   - only small results go to git (see each `.gitignore`);
   - **before every push, `python3 tools/privacy_scrub.py --check` must print nothing** (no paths or process names from outside the project).

## 8. Integrity incidents (all disclosed in the track reports)
- **Phase 1:** a 25 s overlap of two tuning jobs (rows flagged, study re-run); one `__pycache__` file written into `0_reproduce` (removed, verified).
- **Phase 2:**
  - One unpinned script of Track B ran on the timing cores for ≈3 minutes. Tuning was restarted and the Region4 s0 solves re-run.
  - The SMT-sibling exposure was found. The 1-s dev evaluation was re-run.
  - A foreign job (`<another project>`) ran during 55 tuning runs. They are flagged; none is a selected config.
- **Leak-check hits** outside the project come from other tools: the editor, Copilot, desktop files, and `<another project>`. None of them come from this work.
- **Privacy redaction (2026-10-04).** The repo is **public**. Leak-check listings, CPU audits and notes had included paths and process names from the user's unrelated work and machine (file names only, never contents). They were replaced by category labels with counts, using `tools/privacy_scrub.py`. Code, results and numbers are unchanged. **Earlier commits still contain the originals:** purging them needs a history rewrite and force-push (captain's decision).

## 9. Next steps and dates
1. **H3′ done (FAIL).** Candidate new pre-registration: the load-adaptive threshold (A+α) as a hypothesis of its own, on a fresh region (Region5) together with any Track C finalist.
2. **WP8 / Track C:** stage 1 = validated proxy + offline/learnability screen on dev (no sims while H3′ runs). Stage 2 = full-sim dev screen with a finalist rule written first. Stage 3 = fresh pre-registered test on Region5 (never run deployed); reserve 0.7–0.9 untouched. Track C never reads H3′ test outputs.
3. **WP4:** mechanism. Retention, the 2×2 interaction, scan windows, and the Region6 vs Region7 split.
4. **WP6: mid-term talk and report** (date TBC, after mid-term break). Cover the reproduction nuance, H1′, the solver story (H2/H2′/scaling) and the H3′ status.
5. **WP7: paper** (Nov 2 – Dec 2). Reserve samples 0.7–0.9 are touched once, for the final claims.
