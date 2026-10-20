# Validator 1 (citation and fact check), round 2 of 5

**Target:** `changes/4_story/STORY.md` (story-writer round 2, run 20261020_154140, 103 findings).
**Validator run:** 2026-10-20. Read-only: no file other than this one was written.

## Method

1. **Automated check.** `python3 changes/4_story/code/check_story.py` reports `n_problems 0`, no warnings and `n_findings 103`.
   - It now checks that link targets and anchors exist.
   - It does **not** check:
     - that a target is tracked in git (see N27);
     - that an anchor contains the claim;
     - arm, instance or budget.
2. **Manual audit.**
   - **Scope:** all 9 P0 and all 44 P1 findings, plus 17 P2/P3 findings: F32, F40, F48, F51, F56, F58, F62, F63, F72, F77, F80, F87, F89, F98, F99, F101, F102.
   - **Also audited:** the header, abstract and legend; the P0 headline table; §8 (23 rows and the summary); §9; Appendix A.5–A.11; every commit hash and time in Appendix B (via `git show`); every Appendix D one-liner, re-run.
   - **Each ref** was opened at its anchor. Every number was checked for value, units, sign, arm, instance and budget. The wording, the evidence tag and how direct the ref is were also checked.
   - **Round-1 fixes:** every round-1 blocking item (B1–B14) was re-verified.
3. **Recomputation.** The stdout of `python3 changes/4_story/code/recompute.py` is byte-identical to `changes/4_story/result/recompute_out.txt`.
4. **Independent spot checks.** I recomputed from the raw CSVs with my own scripts, independent of `recompute.py` and not committed (see "Spot checks" below).
5. **Privacy.** `python3 -B tools/privacy_scrub.py --check` prints nothing (exit 0).

Classification is the same as in round 1:
- **BLOCKING:**
  - a wrong number or claim;
  - a claim its source contradicts;
  - a statement supported by no cited file and no explicit `(Fxx)` cross-reference;
  - a wrong evidence tag.
- **NON-BLOCKING:**
  - the claim is in a cited file but outside the anchor;
  - imprecise wording or omitted caveats;
  - rounding or wording inherited from the source.

## Round-1 blocking items: status

| Round-1 item | Status in round 2 |
|---|---|
| B1, B2 (abstract refs) | Fixed: L26 cites q3 L6–15; L36 cites WP3 L53–60, FINAL_REPORT L75 and WP10 L19. |
| B3 (F13) | Fixed: WP1 L26–27, PROTOCOL_v2_H2 and PROTOCOL_v2_H3 L58 are cited. |
| B4 (F21) | Fixed: "the worst (highest)". |
| B5 (F21) | Fixed in F21 itself, but **not carried into §8 rows 8/19 or F31**: see R2-B2 and R2-B3. |
| B6 (F44) | Fixed: "touched once in deployed mode"; F93 added. |
| B7 (F48/F40/F70) | Fixed: ≈1 instance SE, 3/6 each way, s0.5 = 90% of the summed difference. |
| B8 (F60), B9 (F71) | Fixed: both are TEST-POSTHOC and the legend explains why. |
| B10 (F64) | Fixed: the priority line matches T1 L61. |
| B11 (F72) | Fixed: the numbers match my recomputation (S5). |
| B12 (F77), B13 (F80), B14 (F89) | Fixed. |

## Blocking problems (round 2)

| # | Finding | Issue | Evidence (file:line) | Required fix |
|---|---|---|---|---|
| R2-B1 | F21 (STORY L610) and legend (STORY L69) | **Wrong claim.** The LP-start statement is false for two groups of label sets. F21 says "Both start from the classical LP + round + repair solution in phase 1 … and in every deployed label set"; the legend says "They start from the classical LP + round + repair solution in phase 1 and in every deployed label set". **(a) Phase-1 Q3.** The deployed labels (P0/T2/C2), which F33–F35 call "Ising-family peak labels", came from q3solve's PT. That PT starts from **Baleen's selection** and uses a native hard budget, not a QUBO penalty. **(b) Track C.** The ANC designs start from Baleen's set, and the STU designs start from the previous round's labels. | `changes/1_literature_review/explore/q3/src/q3solve.py:282-286` ("start: Baleen's selection …"); `changes/1_literature_review/explore/common/Q3_FORMULATION.md:17,44` ("native hard write budget"; "Baleen start 24.5180"); `changes/2_deployable_peak/wp8_trackC/src/labels_c.py:8,11,126-130` (`start = "baleen"`, `start = "prev_round"`). By contrast, harness_eval C2 does start from the repaired LP (`changes/1_literature_review/harness_eval/RESULTS.md:42`). | Narrow both sentences to "phase-1 Q1/Q2 (and harness_eval C2) and every deployed F1PT/F1EIM label set". State that the Q3 labels and the Track C anchored/student labels started from Baleen's set or from the previous round. Add the Baleen start to F14. |
| R2-B2 | F31 (STORY L809) | **Contradicted claim.** "[matrix-free SB] … is in no finalist or deployed configuration" is false. In harness_eval, C4 (matrix-free SB on the SoS QUBO) was one of the two best Ising arms and was taken to deployed mode with 3 retrains per region: Region7 40.07, Region6 43.20, retention +0.01. F21 itself cites that retention. | `changes/1_literature_review/harness_eval/RESULTS.md:197-198` ("The best Ising arms are C4 … These, plus C2 … were taken to deployed mode"); L231, L233, L250 | Write "in no phase-2 finalist or deployed test configuration; in phase-1 harness_eval, C4 was deployed on dev (sample 0) and tied Baleen". Cite harness_eval L197–198 and L231–233. |
| R2-B3 | §8 row 8 (STORY L1955) and row 19 (STORY L1966) | **Contradicted claim (B5 fix incomplete).** Row 8 says "SB itself is the weakest Ising solver by quality", and row 19 says "SB was the weakest Ising solver", both without scope. F21, which both rows cite, now limits this to phase-1 dev tuning and the WP5 rule. In harness_eval the SB arm C4 beat C5 analytically on both traces and was one of the two best Ising arms in simulation. | `changes/1_literature_review/harness_eval/RESULTS.md:166-167` (C4 24.343 / 23.044 vs C5 24.376 / 23.373), L197; STORY F21 L604–607 ("harness_eval is the exception") | Scope both rows as F21 does: "the weakest Ising solver in phase-1 dev tuning and by the WP5 rule (in harness_eval, C4 beat C5)". |
| R2-B4 | F70 (STORY L1472) | **Wrong number.** F70 says "At the retrain level used by the project's pass rules, two rows exceed 2 SE, one in each direction". In fact **three** rows exceed 2 retrain SE, **two of them favouring PT**: WP2 dev X1 vs Ea-1.0:F1CPSAT (2.68), the union XA:F1PT vs XA:F1CPSAT (0.77/0.36 = 2.14) and the H3′ test (2.50, CP-SAT). F70's own table row for the union shows "SE 0.36, 'about 2.1 SE'", so the finding contradicts itself. | `changes/3_autoresearch/result/FINAL_REPORT.md:85,88` (SE_retrain 0.36; "about 2.1 SE"). My recomputation from `changes/3_autoresearch/work/union/trials_dev.csv` (matched rows): +0.768, 6/10, SE_retrain 0.358 → 2.14, SE_inst 0.421 → 1.82 (S9) | Write "three rows exceed 2 retrain SE: WP2 dev (2.7) and the union dev (2.1) favour PT; the H3′ test (2.5) favours CP-SAT". Add the union's instance-level SE (0.42, 1.8 SE) to its row. Then align §8 row 23 (see N25). |
| R2-B5 | F95 (STORY L444) | **Missing ref.** "The thesis result is on Region3, which this project never ran" is in none of F95's four refs: SCOPE_v2 L23, lit_review REPORT L77–90, wp9 L15 and H4 protocol L53. The claim is true: no ledger contains Region3. | `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md:24` ("Region3 was not used: it lacks s0.4–0.6"); `changes/3_autoresearch/README.md:7` (Region3 0.1–0.3 is a test pool that was never spent); `grep -l Region3` over every tracked `*.csv`/`*.jsonl` finds nothing | Cite `PROTOCOL_v2_H5.md#L24` and `changes/3_autoresearch/README.md#L7` (or cross-reference F91), or drop the clause. |
| R2-B6 | F101 (STORY L714) | **Wrong instance.** "the largest gap 4.81 on Region4 s0.3" is wrong. The 4.81 gap is on **Region6 s0.9** (R0 33.62 vs the authors' 38.44); Region4 s0.3 is 4.01 (42.34 vs 46.35). The error comes from the source's summary line, which its own per-instance table contradicts. | `changes/2_deployable_peak/wp1_offline/RESULTS.md:37` (summary, wrong) vs L49 (Region4_s0.3: 46.35 / 42.34) and L75 (Region6_s0.9: 38.44 / 33.62). Recomputed from `wp1_offline/results/wp1_table.csv`: mean −0.553, mean \|d\| 1.015, max \|d\| 4.814 on Region6_s0.9 (S8) | Write "largest gap 4.81 on Region6 s0.9 (the source's summary line says Region4 s0.3, whose gap is 4.01)". Cite L49 and L75. |

## Non-blocking problems (fix recommended)

| # | Finding | Issue | Evidence (file:line) | Suggested fix |
|---|---|---|---|---|
| N1 | F03 | "the `tod` group, used only by WP2's D2 ablation" is too strong. `+load+tod` was also fitted in the learnability gate and parity-tested in WP0. D2 is the only *deployed* arm that used it. | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md:98,111`; `changes/2_deployable_peak/wp0_overlay/PROGRESS.md:20` | Write "the only deployed arm using it". |
| N2 | F13 | "used by every Q1/Q2 … configuration": Q2 dev tuning also ran F2b (F23 says so). | `changes/1_literature_review/explore/q2/RESULTS.md:145-147` | Write "every held-out Q1/Q2 configuration". |
| N3 | F15, F19 | "Ising arms 27.7–28.3, classical 27.6–28.3" leaves out the capacity-coupled C3 (29.00 / 29.28) and C3L (28.89 / 29.58). This is inherited from the source's summary line. | `changes/1_literature_review/harness_eval/RESULTS.md:135,138,155,157` | Add "(excluding C3/C3L, 28.9–29.6)". |
| N4 | F36 | Round-1 N14 is still open, although WRITER_NOTES says all N items were addressed. "Bit-identical on all 425 result keys" leaves out the wall-clock/RAM keys and `realtime_elapsed`. "+217/−6" counts non-blank lines (numstat gives +256/−6). | `changes/2_deployable_peak/wp0_overlay/CP1.md:66` | Add both qualifiers. |
| N5 | F41 | "2.4–2.8% vs Baleen's 8.7%" covers only D:F1PT and X1. The other F1 arms run 1.4–3.2%, and the Baleen arms 8.0–9.6%. This is the same issue as round-1 N23 for F72. | `changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt:18-30`; `RESULTS_dev.md:229` | Write "2–3% (D:F1PT 2.4%, X1 2.8%) vs 8–10% (A 8.7%)". |
| N6 | F44, F38 | Optional. F44's title says "lose to Baleen" although X1 wins 5/6 instances; the mean loss comes from one instance (the body says so). F38 relies on the (F94) cross-reference and does not cite `PLAN.md#L107` itself. | `changes/2_deployable_peak/wp3_test/RESULTS_test.md:10,34`; `changes/2_deployable_peak/PLAN.md:107` | Optional rewording, and add the PLAN ref. |
| N7 | F28 | The title "at re-solve budgets of 1, 3 and 10 s … not better" overgeneralises. At 3 s PT is ≤ best classical on 6/6 and has the lower mean (22.6008 vs 22.7157). The body says so. | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md:12,31,39` | Write "fail the pre-registered criteria (better only at 3 s)". |
| N8 | F31 | "in at most 214 MB" and "PT … at most 165 MB" are *extra* memory above the loaded instance (~355–410 MB). | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:343` | Write "+214 MB above the loaded instance". |
| N9 | F32 | "LS 10 s gives the best offline simulated P100 (27.067)" holds only among the 8-instance rows. "Same day-1 peak" rests on seed-1 means rounded to 0.1. | `wp5_ising/RESULTS_dev.md:208-210`; `wp2_deployed/RESULTS_dev.md:71-76` | Add both qualifiers. |
| N10 | F102 | Tag. These are per-level objectives on H2′ *test* instances, pre-declared "reported alongside, no verdict". By the legend (the rule applied to F30 from the same protocol), the tag is TEST-POSTHOC, not OFFLINE. | `changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md:78-80`; STORY L57 | Retag, or say in the legend that solver-objective analyses on test instances are OFFLINE. |
| N11 | F24 | The 94.5% uses the `lp` method's nested objective as a stand-in for PT's own LP start, which was not logged (the source makes the same equivalence). | `changes/1_literature_review/explore/q2/RESULTS.md:256-257` | Add "(the `lp` row as a proxy for the start)". |
| N12 | F35 | "25–42% of the window's accesses end beyond 8 MB" is inherited from the source. C2 on Region7 s0.3 has 0.18. | `changes/1_literature_review/explore/q3/RESULTS.md:286,294` | Write "18–42%". |
| N13 | F53 | Tagged TEST-PREREG, but it contains post-hoc decompositions of the test data: 69%, +0.434 and mean/SE_inst 1.55. | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md:17`; legend L55–57 | Mark the decomposition "(post hoc)". |
| N14 | F59 | Omitted caveat. On the Region1 test, PT fitted the neutral table (all multipliers 1.0, i.e. plain B models) on **10 of 18** retrains (s0.1 3, s0.2 2, s0.4 2, s0.5 3), so H5 largely tested arm B. Verified. | `changes/2_deployable_peak/wp10_schedule/results/solves_test.csv` (`mult`) | Add it. |
| N15 | F59, F60 (and the abstract's "did not help") | Understated. On Region1 the α arms are *worse* than A: A+α 1/6, −0.487 (2.7 instance SE, 7.9 retrain SE); B+α −0.338. TB:pt vs A is −0.314 (2.2 / 3.4 SE). F69 already says "null / worse". | `changes/4_story/result/recompute_out.txt:41,44,46` | Write "are worse than A (1/6, −0.49)". |
| N16 | F67, F57 | F67's title states the final report's interpretation as a cause. F57 (optional): the classical exhaustive reference enumerates all 3003 tables in 1.5–2.3 s, against 10 s for PT and CD. | `changes/3_autoresearch/result/FINAL_REPORT.md:71-75`; `changes/2_deployable_peak/wp10_schedule/PROGRESS.md:83` | Add "(final report's interpretation)", and optionally the timing. |
| N17 | F70 | (a) "PT had the better objective" on Track C holds for the mean only (13.55 vs 14.31); PT is lower on 11/24 cells. (b) It is tagged OFFLINE, but the deployed-label rows are DEV / TEST-POSTHOC. | `changes/2_deployable_peak/wp8_trackC/PROGRESS.md:94-96` | Write "lower mean objective (lower on 11/24 cells)". Label the Data column's tags. |
| N18 | F73 | "The H3′ outcome sat unevaluated for 11 days" is not in any cited file; the cited files show only that the ledger ends 10-05 and the result was committed 10-16. | `changes/2_deployable_peak/wp8_trackC/PROGRESS.md:86` (supports it, not cited) | Cite it, or write "committed 11 days after the run". |
| N19 | F68 | "X1 averaged 52.30" is at L26, outside the `#L42-L51` anchor. | `changes/2_deployable_peak/wp3_test/RESULTS_test.md:26` | Add `#L26`. |
| N20 | F92 | RESEARCH.md still says "reserve 0.7–0.9 untouched"; F92 corrects only the protocols. | `RESEARCH.md:121,124` | Optionally mention it. |
| N21 | F72 | (a) "via zero-value positives" over-generalises: C2 raised first-access admission to 14% "with few zero-value units". (b) D:P0 2.89% / 5.61% and D:T2 1.04% are labelled "recomputed", but `recompute_out.txt` L96 omits D:P0, D:T2, the Ea-* arms and Ex. They are in `mechanism_by_region.txt` (0.029 / 0.010) and reproduce from raw data (S5). | `changes/1_literature_review/explore/q3/RESULTS.md:28,247,256`; `changes/4_story/result/recompute_out.txt:96` | Write "mostly via zero-value positives". Either add the missing arms to `recompute.py`, or point "recomputed" at `mechanism_by_region.txt`. |
| N22 | F40, F70 and `recompute_out.txt` L94 | "2.681 retrain SE, 2.066 instance SE" divides the *reported* +1.26 / 0.47 / 0.61; it is not a recomputation. The raw recomputation reproduces +1.263, 0.472 and 0.610 only after merging the Ex-1.0 re-run rows into Ea-1.0, as the source does. Without the merge it gives +1.06, because Region6 s0.1 drops to 2 retrains. Appendix D's conventions do not state the merge. | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md:241` ("merged as the same configuration"); S4 | Add the Ax/Bx/Ex merge to Appendix D's conventions, or recompute L94 from raw data. |
| N23 | §8 row 19 | The −13.217% figure is at q2 RESULTS L139; the cited anchor `#L200-L211` (the held-out §8.1 table) does not contain it. | `changes/1_literature_review/explore/q2/RESULTS.md:132-143` | Use `#L132-L143`. |
| N24 | §8 row 7 | No new problem: the test rolling run was at 1 s only, and the row now says so. | — | — |
| N25 | §8 row 23 | "none beyond ≈2 SE" drops F70's "instance-level". At retrain level three rows exceed 2 SE (R2-B4). | STORY L1970; F70 L1472 | Write "none beyond ≈2 instance-level SE; three rows exceed 2 retrain SE, two favouring PT". |
| N26 | §9 item 1, F93 | No new problem: all deployed test pools except Region1 (H5) and Region2 (T1) appear in `wp1_table.csv` (Regions 4–7 × s0–0.9). | — | — |
| N27 | F74, F76, F100, Appendix C | Links point to files that exist on disk but are **not tracked in git**: `changes/2_deployable_peak/TIMING_IDLE`, `changes/2_deployable_peak/wp3_test/G3_SIGNED` and `changes/4_story/code/linkify.py`. Their mtimes (10-03 02:08, 10-05 14:13, 10-20 17:08) show the first two pre-date the story; `linkify.py` is the writer's new file. In the committed repo the first two links are dead. `check_story.py` checks only on-disk existence. | `git ls-files --error-unmatch` fails for all three; `git status` shows them as `??` | Quote G3_SIGNED's one-line content and TIMING_IDLE's existence in the text, and mark them "untracked file", or have them committed. |
| N28 | F77 (L1666) | It links to `.git/objects`, a directory that is not a repo file, so the link is dead on any host. | STORY L1666 | Drop the link and keep the text. |

Checked and found correct (no problem):
- **P0, P1 and P2 findings:** F01, F02, F07, F08, F11, F18, F20, F25, F26, F27, F33, F34, F37, F39, F45–F47, F48, F50, F51, F52, F54, F56, F58, F62–F66, F69, F71, F75, F76, F84, F93, F94.
- **P3 findings:** F77 (refs and counts), F80, F87, F89, F98, F99.
- **Numbers in findings that also have a non-blocking item:** F03, F13, F15, F19, F21, F24, F28, F31, F32, F35, F36, F38, F40, F41, F44, F53, F57, F59, F60, F67, F68, F70 (except the count in R2-B4), F72, F73, F92, F102.
- **The abstract.** Every number and ref checks:
  - 27.06 vs 32.28;
  - 36–37/39 and −13.0 to −13.7%;
  - ≈16% and 13–18%;
  - 94.5%;
  - H4 35.02 vs 36.17, 5/6, +1.16 ± 0.75 (≈1.5 SE), 69% and +0.43.
- **The legend**, except L69 (R2-B1).
- **Appendix A:** A.5 and A.6 match their sources. A.7, A.9, A.10 and A.11 match the raw ledgers cell by cell (S7).
- **Appendix B:** all 32 commit hashes and times match `git show`.
- **Appendix D:** items 3–8 were re-run and give the stated output (item 3: RESEARCH.md:36 and WP1 RESULTS:87; item 4: `changes/SCOPE.md` only; item 5: no output; item 6: 36.16; item 7: `2026-10-05T14:23:12 2026-10-05T17:41:42 126`; item 8: 12, with `.gitignore:10` = `inst/`).
- **Contradictions with RESEARCH.md:** no silent ones. The known drifts (date, ≈11.3%, ≈70k) are flagged in F08, F31 and F88.

## Spot checks (my own recomputation from raw CSVs, matched rows only)

My scripts are independent of `recompute.py`. A configuration's mean is the mean over instances of the per-instance retrain mean. SE_inst = sd(d_i)/√n; SE_retrain = √(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n.

| # | Story claim | Raw source | Recomputed | Verdict |
|---|---|---|---|---|
| S1 | F48: Dc+α 0.89 below X1, 3/6 each way, SE 0.36 / 0.84 (≈2.5 / ≈1 SE); per instance −0.433, −0.375, +0.107, −0.368, +4.808, +1.594; s0.5 = 4.81 of 5.33 (90%); other five +0.105 | `changes/2_deployable_peak/wp3_test/trials.csv` | +0.8888, 3/6, SE_ret 0.3555, SE_inst 0.8445 (2.500 / 1.052); same per-instance values; sum 5.333, share 0.902, other five 0.105 | match |
| S2 | Abstract, F52, F53, §8 row 15: A+α 35.02 vs A 36.17, 5/6, +1.16, SE 0.09 / 0.75, ≈1.5 SE; s0.5 69%; other five +0.43; −3.2% | `changes/2_deployable_peak/wp9_region5/trials.csv` | 35.020 vs 36.174, 5/6, +1.1546, 0.0938 / 0.7454 (1.549); s0.5 4.758 / 6.927 = 0.687; other five 0.434; −3.19% | match |
| S3 | F65, F66: Y vs A+α 1/5, −0.300, SE_ret 1.117; A+α vs A 5/5, +7.847, SE 0.446 / 5.125, −15%; s0.3 69% | `changes/3_autoresearch/work/t2u_region4/trials_test.csv` | 1/5, −0.3002, 1.1166; 5/5, +7.8474, 0.4462 / 5.1255; −15.47%; s0.3 27.186 / 39.237 = 0.693; other four +3.013 | match |
| S4 | F40, F70: WP2 dev X1 vs Ea-1.0:F1CPSAT 5/8, +1.26, SE 0.47 / 0.61; D:F1PT vs Dc 3/8, +0.37, 0.42 / 0.54 | `changes/2_deployable_peak/wp2_deployed/trials.csv` | With Ex-1.0 merged into Ea-1.0 (as the source does): 5/8, +1.2632, 0.4718 / 0.6099 (2.68 / 2.07). D:F1PT vs Dc 3/8, +0.3695, 0.4222 / 0.5372. Without the merge: +1.063 (see N22). | match (with the source's merge) |
| S5 | F72: Region6 first-access, D:P0 2.89% (max 5.61%), D:T2 1.04%, other WP2 arms ≤ 0.74%, Track C ≤ 1.3% | `wp2_deployed/trials.csv`, `changes/2_deployable_peak/wp8_trackC/trials.csv` | D:P0 2.89 / 5.61 (n = 4); D:T2 1.04 / 1.53; max other WP2 arm mean 0.74 (Bx-1.0); Track C max 1.26 (E8:ANC3) | match |
| S6 | Abstract, F25, §8 row 18: wins 36/36/37; 13.03 / 13.15 / 13.69%; Regions 5–7 ≈16%; per-region means averaged 12.8–13.5% | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv` | 36/36/37; 13.03 / 13.15 / 13.69; R5–7 15.57 / 16.19 / 16.18; per region 12.99–17.67; region-mean averages 12.82 / 12.90 / 13.48 | match |
| S7 | Appendix A.7, A.9, A.10, A.11, every model-arm cell | the four test ledgers | every per-instance and mean cell identical to 2 dp | match |
| S8 | F101: R0 − author OPT-AP mean −0.55, mean \|d\| 1.02, max 4.81 on Region4 s0.3 | `wp1_table.csv` | −0.553, 1.015, max 4.814 on **Region6_s0.9**; Region4_s0.3 is 4.014 | **mismatch → R2-B6** |
| S9 | F70: "two rows exceed 2 retrain SE" | `changes/3_autoresearch/work/union/trials_dev.csv` | XA:F1PT vs XA:F1CPSAT +0.768, 6/10, SE_ret 0.358 (2.14), SE_inst 0.421 (1.82): a third row above 2 retrain SE | **mismatch → R2-B4** |
| S10 | (N14) WP10 test fitted tables | `changes/2_deployable_peak/wp10_schedule/results/solves_test.csv` | 10 of 18 PT tables neutral (all multipliers 1.0) | new caveat |

## Counts

- **Findings audited:** 70 in full.
  - P0: 9/9.
  - P1: 44/44.
  - P2/P3: 17.
- **Also audited:** the header, abstract, legend and headline table; §8 (23 rows and the summary) and §9; Appendix A.5–A.11, B and D.
- **`check_story.py` problems:** 0.
- **Recomputed numbers:** 9 spot checks plus one new caveat (S1–S10). Seven match; S8 and S9 do not, and confirm R2-B6 and R2-B4.
- **Round-1 blocking items:** 14/14 fixed. B5's scope was not carried into §8 or F31.
- **Blocking problems: 6.**

  | Kind | Count | Items |
  |---|---|---|
  | Wrong number or claim | 4 | R2-B1 (F21 and legend), R2-B2 (F31), R2-B4 (F70), R2-B6 (F101) |
  | Unsupported or contradicted | 1 | R2-B3 (§8 rows 8/19) |
  | Wrong evidence tag | 0 | — |
  | Missing refs | 1 | R2-B5 (F95) |

  By priority:

  | Priority | Count | Items |
  |---|---|---|
  | P0 | 0 | — |
  | P1 | 4 | R2-B1 (F21), R2-B2 (F31), R2-B4 (F70), R2-B5 (F95) |
  | P3 | 1 | R2-B6 (F101) |
  | §8 claims table | 1 | R2-B3 |
- **Non-blocking problems: 26** (N1–N28; N24 and N26 are "no problem" confirmations, so they are not counted).

```
OPEN_FINDINGS=6
VALIDATOR_STATUS=FAIL
```
