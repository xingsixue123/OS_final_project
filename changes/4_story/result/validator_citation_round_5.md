# Citation and fact-check validator, round 5 of 5

**Target:** `changes/4_story/STORY.md`, writer round 5 (final), uncommitted working tree, run 20261020_154140.

**Method:**
- Every ref of every audited finding was opened at its cited lines.
- Numbers were checked for value, units, sign, arm, instance, budget and pool, and recomputed from the raw ledgers where possible. Matched rows only. A configuration's mean is the mean over instances of the per-instance retrain means. SE_inst = sd(d_i)/√n; SE_retrain = √(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n.
- Commit hashes and times were checked with `git show`.
- This report contains repo-relative paths only.

## 1. `check_story.py`

`python3 changes/4_story/code/check_story.py` reports `n_problems: 0` and no warnings over 105 findings: P0 9, P1 45, P2 34, P3 17.

The §0.1 index counts match the headings: DEV 21, INFRA 41, NEGATIVE-TEST 8, OFFLINE 13, REPRO 5, TEST-POSTHOC 14, TEST-PREREG 3. Every index row matches its heading's priority, tag and title once link markup is stripped.

`python3 changes/4_story/code/recompute.py` reproduces `result/recompute_out.txt` byte for byte.

## 2. Problems found

### Blocking problems: 1

| ID | Finding | Issue | Evidence (file and line) | Required fix |
|---|---|---|---|---|
| R5-B1 | F15 [P1] (STORY.md L527) | **Unsupported claim (overclaim).** The sentence before it sets an SE scale: "The only deployed arm more than 2 SE below Baleen online was the *classical* R2 on Region6 (−0.87, beyond 2 × SE = 0.85) … No Ising arm came close." On that scale the closest Ising arm did come close. EIM C2 on Region6 is 43.09 ± 0.16 over 3 retrains, 0.16 below Baleen online (43.25 ± 0.04, 9 retrains). The SE of the difference is 0.092, so the gap is **1.72 SE**, against R2's 2.05. The classical RB4 is at 1.89 SE. So the data do not support the implied split between the classical and Ising families. The cited source says only that the other arms were "within about 0.3 of Baleen online and above RejectX"; it gives no SEs for them. In points (0.16 vs 0.87) and against RejectX (C2 0.77 above it), the Ising arms were not close. The sentence does not say which reading it means. | `changes/1_literature_review/harness_eval/RESULTS.md:229` (R2 row), `:235` (C2 Region6: 43.09 ± 0.16, 3 reps), `:222` (Baleen online R6 43.25 ± 0.04, 9 retrains), `:246` (source wording). Recomputed from `changes/1_literature_review/harness_eval/results/deployed.csv` (matched rows; the duplicated R2 rep-2 row dropped) and `changes/0_reproduce/work/results/retrain_dist.csv`: C2 0.158 / 0.092 = 1.72; R2 0.870 / 0.424 = 2.05; RB4 0.273 / 0.145 = 1.89; C4 0.74; C5 0.31. On Region7 every Ising arm is ≤ 0.52 SE below Baleen or above it. | Replace "No Ising arm came close" with the numbers. For example: "The closest Ising arm, EIM C2 on Region6, was 0.16 below Baleen online (≈1.7 SE of the difference, recomputed) and 0.77 above RejectX." Cite `deployed.csv` and `retrain_dist.csv`, or add the computation to `recompute.py`. |

### Non-blocking problems

These are wording, scope, anchor or inherited-rounding issues. None is a wrong number, contradicted claim, wrong tag or missing ref for a stated number.

| ID | Finding | Issue | Evidence (file and line) | Required fix |
|---|---|---|---|---|
| R5-N1 | F15 (L523) | "Every Region7 arm scored 40.06–40.85". The 40.06 is C5's source mean, which includes an unmatched retrain (rep 2, wr 34.899 MB/s, `matched=False`), although the source says "All rows are at matched WR". Matched rows only: C5 is 40.095 (2 retrains) and the range is 40.07 (C4) to 40.85. F99 does not list this deviation. | `harness_eval/results/deployed.csv` (Region7 C5 rep 2); `harness_eval/RESULTS.md:223`, `:238` (WR 34.90–35.80) | Write "40.07–40.85 (matched retrains)" and add the unmatched C5 retrain to F99. |
| R5-N2 | F11 (L436) | "In the median over seeds, no Ising arm reaches LP-round + repair at any size" holds only for the median gap as a share of headroom (LP 9.8% vs dwave_sa 10.5% at 1k). By median repaired peak, dwave_sa (0.9605) and five more Ising arms (0.9611–0.9645) are below LP + repair (0.9666) at n = 1k. The source's own wording is the same ("No Ising arm reaches …", L158), so the claim is inherited. The next sentence ("comparable at 1k") softens it. | `changes/1_literature_review/ising_followup/audit/AUDIT.md:66-80` (lp L66, dwave_sa L73), `:158-159` | "By median gap as a share of headroom, no Ising arm …; by median repaired peak several Ising arms are below LP + repair at 1k." |
| R5-N3 | F03 priority line (L272); abstract (L34) | "at most ≈1.2 instance SE in its favour" leaves out the descriptive T1 (Region2), where B+α vs A+α is 1.44 instance SE in the feature's favour. F105 states it ("1.4 on the descriptive T1"). The abstract scopes the figure to "(H4, H5)"; F03 does not. | `changes/4_story/result/recompute_out.txt:153`; STORY.md L1538 | Add "(H4, H5; 1.4 on the descriptive T1)" in F03. |
| R5-N4 | F13 title (L485) | "true min–max F1 over the post-day-1 windows". The label solves use the day-1 windows at f = 1.0, as the body says. | `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:69-70` | "post-day-1 windows offline; day-1 windows for labels". |
| R5-N5 | F25 (L717); legend caveat 2 (L65) | "Without them H1′ still passes". The pre-registered set is the 39 instances, so the 33 are a sensitivity subset. All numbers recompute exactly: LP 30/33 12.54%, CP-SAT 30/33 12.53%, PT 31/33 13.18%; the six alone 6/6, 15.73–16.56%; 18 rows from 09-28 18:54:30 to 09-29 01:05:51; `27fb6f0` at 09-29 15:06:02. Also, Region6/7 s0 are the phase-1 dev instances, whose F1 dev simulations were known before PLAN. Dropping them too gives 28/31, 28/31, 29/31 and 12.07 / 12.01 / 12.74%, which still clears the bar. The committing PLAN itself reports Q1 (L11), which is the most direct ref for "Q1 outcome was known". | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`; `wp1_offline/trials.csv` (phase `wp1_reused_phase1_heldout`); `changes/2_deployable_peak/PLAN.md:11`, `:19`; `changes/1_literature_review/explore/q2/RESULTS.md:156-158` | Write "the remaining 33 still meet both H1′ thresholds", optionally add the 31-instance variant, and cite `PLAN.md#L11`. |
| R5-N6 | F26 title (L722; index L133) | "almost never is the simulated one". The planned window coincides with the simulated one on 6/39, 9/39 and 6/39 instances (15–23%). The body and source say "rarely" / "only". | `changes/2_deployable_peak/wp1_offline/RESULTS.md:101-103` | "rarely". |
| R5-N7 | F19 (L596) | The upper ends of "Ising arms 27.7–28.3 vs classical 27.5–28.3" (C2 28.34, R3 28.31) are in the Region7 harness table, which is not cited. | `changes/1_literature_review/harness_eval/RESULTS.md:124-141` | Add the anchor. |
| R5-N8 | F31 (L852, new); §8 row 8 (L2070) | The new paragraph is correct. Three arms, no classical arm (`scaling.jsonl` holds only mfsb/dense/pt); ≤ 1.7 s at 200k (AUDIT L148); LP and CP-SAT returned feasible, within-budget solutions on all 39 WP1 instances. Three precision issues: (a) "measures cost per step, not solution quality". `scaling.jsonl` does log per-run peaks, but the source calls the run "pure solver cost, no repair loop", so the wording is supported; it would be more exact to say the peaks were logged but not reported. (b) "Not a scaling advantage" states a negative that was never tested at union size, and it leaves out that the exact MILP found no incumbent at 200k. (c) "solved every real full-trace instance" can be read as "to optimality", and the direct ref `wp1_offline/RESULTS.md#L29` ("All 117 solves ok") is not cited. Row 8's "LP handled 200k variables" leaves out "synthetic". Separately, L838 "On the full traces: 1.5–3.6 s per step and 12–22 GB": the dense package ran on only 4 of the 15 full traces. | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:333-345`; `wp5_ising/results/scaling_summary.md`; `changes/1_literature_review/ising_followup/audit/AUDIT.md:148`, `:162`; `changes/2_deployable_peak/wp1_offline/RESULTS.md:29` | "Not shown to be a scaling advantage …"; add "(the exact MILP found no incumbent at 200k)", "feasible, within-budget", the RESULTS#L29 ref, "on the synthetic audit" in row 8, and "on the 4 full traces it was run on" at L838. |
| R5-N9 | F39 (L1003) | "PLAN's ablation arm E (D + α)". "Ablation" is supported only by `PLAN.md#L60`, which F39 does not cite, and PLAN's E also includes the load-aware ML-When. | `changes/2_deployable_peak/PLAN.md:59-60` | Cite `PLAN.md#L59-L60`, or move the F94 cross-ref onto this bullet. |
| R5-N10 | F45 (L1101, new) | All numbers recompute: without Region7 s0.5, X1 beats A 5/5 by +1.128 and leads A+α by +0.395 (3/5); on Region5 without s0.5 it trails by −0.990 (2/5), with s0.6 at −5.588. But "+0.39" is only 1.9 retrain SE and 0.7 instance SE. And X1's 3/6 wins vs A+α fail the wins condition whether or not s0.5 is counted, so the loss does not "rest on" s0.5 for the wins part. | `changes/4_story/result/recompute_out.txt:165-168`; `changes/2_deployable_peak/wp3_test/trials.csv` | "… and leads A+α on the mean by +0.39 (3/5; 1.9 retrain SE, 0.7 instance SE); the 3/6 wins vs A+α fail the rule regardless." |
| R5-N11 | F52 (L1208); F53 (L1239) | "B+α … is more concentrated". This is correct by magnitude (75.2% vs A+α's 68.7%), but the cited source says "B+α is more uniform (6/6)", and neither finding reconciles the two. §9 item 4 does ("uniform in sign … concentrated in magnitude"). | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md:17`; STORY.md L2112 | Add "(more uniform in sign, more concentrated in magnitude)". |
| R5-N12 | F53 (L1243) | "(X1 used seeds 1–3)" has no cited line. It is true: in `wp9_region5/trials.csv` the `label_file` values are seeds 1–3 only. The refs also cite `PROGRESS.md#L67-L68` and `#L65-L70`, which overlap. | `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md:55`, `:64`; `wp9_region5/trials.csv` | Cite `PROTOCOL_v2_H4.md#L64` (or trials.csv) and drop the overlapping anchor. |
| R5-N13 | F54 priority line (L1270) | "the second fresh-region failure". H3′ tested held-out samples of the dev regions Region6/7, not a fresh region. Also, the label statistics are 6-seed means, while X1 deployed seeds 1–3 only (for seeds 1–3, day-1 peak 17.22–22.12 and Jaccard 0.395–0.602, vs 17.11–22.11 and 0.426–0.550). The "below Baleen on every instance" conclusion holds either way. | `changes/2_deployable_peak/wp9_region5/INSTANCES.md:33-38`; `wp9_region5/trials.csv` | "the second held-out failure (the first on a fresh region)"; optionally note seeds 1–3. |
| R5-N14 | F57 (L1301-L1305) | The test sentences ("On the 18 test fits, PT = exhaustive = CD"; "TB:cd produced the same tables") report items that PROTOCOL_v2_H5 listed as "Reported, no claim". By the legend's precedence rule (L58) these are TEST-POSTHOC, inside an OFFLINE finding. Also, the neutral-table peak is 31.28 in PROGRESS L85 but 31.2747 in raw `solves_dev.csv`. | `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md:62-66`; `wp10_schedule/PROGRESS.md:85`; `wp10_schedule/results/solves_dev.csv` | Mark those two sentences "test, pre-declared, no pass/fail ([F59](#F59))", or leave them only in F59. |
| R5-N15 | F105 (L1538) | "the feature improved the threshold arm beyond 2 SE on H4 and H5 … and hurt it on none of the test pools". At retrain level B+α is worse on H3′ (−0.078, 0.3 SE) and on T2 (−0.995, 1.8 SE). The sentence is true only if "beyond 2 SE" carries over to "hurt". | `changes/4_story/result/recompute_out.txt:149`, `:152` | "… and hurt it beyond 2 retrain SE on none (T2: −0.995, 1.8 retrain SE)". |
| R5-N16 | F105 refs (L1543) | The T1 rows come from `changes/3_autoresearch/work/t1u_region2/trials_test.csv`, which is not cited. The values are in the cited `recompute_out.txt` (L153). | as stated | Add the ledger. |
| R5-N17 | F69 title (L1490; index L178) and Region1 row | "worse on Region1 (post hoc, no pass rule)". PROTOCOL_v2_H5 listed the comparison in advance, and F60 and the legend call it "pre-declared, no pass/fail". The TEST-POSTHOC tag is right; only the words are inconsistent. | `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md:62-64`; STORY.md L58, L1342 | "(pre-declared, no pass rule)". |
| R5-N18 | F70 (L1568, L1576); F100 (L1839, L1846) | "0.16–0.31%" for Region5_s0. Raw `label_peak_util`: +0.170%, +0.1548% and −0.310%, so 0.15–0.31% at two decimals. The 0.16 is `FINAL_REPORT.md:78`'s rounding (cited by F100), so the value is an inherited rounding. It is not in Appendix D's "Agreement" list of inherited roundings, and `recompute_out.txt:159` prints only the signed extremes. "CP-SAT lower on 2 of 3", "Region1_s0 ties exactly" (3/3, identical to the last digit) and 3/3 matched retrains in all 12 cells are correct. | `changes/3_autoresearch/work/union/labels/Region5_s0_F1{PT,CPSAT}_s{1,2,3}.json`; `changes/3_autoresearch/result/FINAL_REPORT.md:78` | Write "0.15–0.31%", or keep 0.16 and add it to the Agreement list. |
| R5-N19 | F71 title (L1585; index L181); L1591 | "never approached the proposal's 60% target for any Ising-label configuration" and "The highest test retentions belong to … A+α 0.31 and B+α 0.46". Both hold for the tests that declared and reported retention (H3′, H4); the body and title parenthesis scope it that way. On T2 (not declared), F71's formula applied to the Ising-label union Y gives an undefined value on Region4 s0.2 (zero offline headroom) and 9.13 on s0.3. That is because the threshold's gain exceeds Region4's tiny headroom (A+α gives 9.28 there), so the metric is degenerate there and does not contradict the point. | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv` (Region4 s0.2–0.6 R0 − pt: 0.00, 2.93, 1.67, 3.88, 3.39); `changes/3_autoresearch/work/t2u_region4/trials_test.csv` | Scope to "on the tests that report it (H3′, H4)", and add one line saying retention is undefined or above 100% on Region4, where it measures the threshold rather than label distillation. |
| R5-N20 | F100 (L1828, L1844) | "WP2's 144 main label sets ran … before H2′, on cores 8–11 and 20–23 only". This is true: the label JSON mtimes are 10-01 16:28–16:45, and `run_labels.py` pins every solve to `BUSY_CPUS`. But the cited `PROGRESS.md#L85` and `#L106` document only the later seed-4/5 sets. | `changes/2_deployable_peak/wp2_deployed/PROGRESS.md:21`, `:37`; `wp2_deployed/src/run_labels.py:20-22` | Add these anchors. |
| R5-N21 | F100 (L1846) | "Their Region5_s0 labels were solved by the auto-research union driver, on shared cores". The 12 sets were solved by the union pipeline's `labels.py`, run through `src/sbx.sh`, whose default is `taskset -c 0-23`. They finished three at a time, 03:58:23–03:58:45. "Shared cores" is true, but no cited ref shows it for these solves: `union.py#L47-L53` shows only the reuse of WP2's D retrains, which is confirmed. | `changes/3_autoresearch/result/LAB_NOTEBOOK.md:208-211`; `changes/3_autoresearch/work/union/src/sbx.sh:11` | "solved with the union pipeline's `labels.py` (`sbx.sh`, `taskset -c 0-23`)"; cite both. |
| R5-N22 | F73 H4 row (L1641) | "the 14 dumps and 36 F1PT label sets … and their sha256 hashes … were committed". `c8f655a` commits sha256 hashes for the 14 dumps only (`results/instances_sha256.csv`, INSTANCES.md). The 36 label sets have JSON summaries and `labels_summary.csv`, but no hashes. Everything else in the row checks out: 36 label JSONs (6 instances × seeds 1–6), no .npz files, the `.gitignore` rules, mtimes 20:30–20:46, and X1's seeds 1–3. | `git show --stat c8f655a`; `changes/2_deployable_peak/wp9_region5/.gitignore:9` | "the dumps' sha256 hashes". |
| R5-N23 | F32 title (L857; index L141) | "on WP2 dev the deployed F1 label sets of PT and CP-SAT have the same day-1 peak". The body is more exact: equal seed-1 means at 0.1 precision (21.504 / 21.482), and near-ties either way over 24 pairs (10/10/4, ±0.56%). | STORY.md L873; `changes/2_deployable_peak/wp2_deployed/labels/*.json` | "near-identical day-1 peaks". |
| R5-N24 | Appendix C (L2381) | `documents/prompt.txt`: "its author is not recorded". The commit author is recorded (`2264e66`, 2026-09-14 10:53:49, the captain's git account); only who wrote the prompt text is not. | `git log -- documents/prompt.txt` | "committed in `2264e66` (09-14); who wrote the text is not recorded". |
| R5-N25 | Silent contradiction (RESEARCH.md, not in F88) | RESEARCH.md L50 says the threshold "carries the deployed gain so far (post-hoc)", but its own L44 records H4 = **Yes (pre-registered)**. The story is correct (F52), but F88's drift list does not include this stale line. | `RESEARCH.md:44`, `:50` | Add it to F88. |
| R5-N26 | F70 tag (unchanged) | F70 is OFFLINE but contains deployed test rows (H3′, T1, T2). They are disclosed in the Data column with their own tags, which is acceptable. | STORY.md L58 | Optional legend note for mixed findings. |
| R5-N27 | Trivial | F18 (L580): the source's WR range 35.26–35.95 is 35.25–35.94 in raw `q2/results/sims.jsonl`; both are within ±1%. F65: "reported, no pass/fail" for the CP-SAT control is most directly sourced from `changes/3_autoresearch/documents/GOOD_RESULT.md:9-10`. | as stated | Optional. |

**Checked and consistent (no item):**
- The F37 learnability ± 0.005 vs raw 0.00446 is already disclosed in Appendix D "Agreement".
- F74's new T1/T2 bullet is right: `union/src/eval_test.py` and `union_t2/src/eval_test.py` are identical. Lines 68–73 average static P100 without a `matched` filter, as `validate.py` does (`validator_integrity_stats_round_2.md:204-209`).
- F88's two new items are correct: `git log --all -- '*PROTOCOL_v2.md'` is empty, and `RESULTS_dev.md:343` gives the ~355–410 MB base.

## 3. Round-4 items: resolution checked

| Item | Status | How checked |
|---|---|---|
| R4-B1 (F100: union rows) | **Fixed** | F100 now lists four non-optimal comparisons with deployed rows (WP2 dev, WP3, union dev, Track C). No "two comparisons" or "no deployed row" wording remains in F100 or F70. The union facts recompute: Region5_s0 +0.170 / +0.155 / −0.310%; Region1_s0 identical on 3/3; XA/XG × F1PT/F1CPSAT 3/3 matched on both instances. `union.py:47-53` shows the DEV8 reuse of `D_<labels>` r1–r3, which the ledger's `x_model` column confirms. The only residue is the inherited 0.16 rounding (R5-N18). |
| R4-N1 to N16 | **Done** | The abstract (L23) separates the WP5 configuration from the deployed one and adds "18 deployed". F104/F13 duplicate refs are gone. F70's title says ≈2.07. F32 says "At 10 s". Legend caveat 2 mentions the six reused instances. F18 gives 6.0–7.3. F105 distinguishes pool means from single instances (0.755, 0.542, recomputed). The attribution anchors are L14–L17. F68 gives both ranges. "18 deployed" matches the `label_file` seeds. F73/F53 dumps and labels (see R5-N22). F84 says R0–R4. F74 is retitled. §8 row 7's evidence column is fixed. Appendix B shows "15:02 / 15:06" (`be284a3` 15:02:03, `27fb6f0` 15:06:02). F88 has both new items. |
| Grill round 4, item 1 (B+α vs A+α) | **Present and correct** | The F105 table, its bullets, §8 row 24, F03, the abstract and §9 items 2/4 all recompute (S1, S2 below). Wording notes: R5-N3, R5-N11, R5-N15. |

## 4. Findings audited (59 in full)

**P0, all 9: F18, F20, F25, F28, F33, F44, F52, F59, F65.** Every number, verdict, tag, protocol hash and time is correct.
- F18 and F25 have only wording notes (R5-N27, R5-N5).
- F28 recomputes from `wp5_ising/trials.csv`: 324/324 ok; PT 1/6, 6/6, 4/6; 22.7336 vs 22.7166; first row 01:24:28.
- F20 recomputes from `q2/trials.csv`: 5/6, 2/6, 1/6; 22.524 / 22.508 / 22.503 vs 22.569 / 22.415 / 22.313.
- F44, F52, F59 and F65 recompute from their ledgers.

**P1, all 45:**
- F01, F02, F03, F07, F08, F11, F95, F13, F15;
- F19, F21, F24, F26, F27;
- F31, F34, F35, F36, F37, F38, F39, F41;
- F45, F46, F47, F50, F53, F54, F57;
- F60, F64, F66, F67, F68, F69, F105;
- F70, F71, F73, F94, F75, F76, F84, F92, F93.

All are correct apart from:
- the blocking item R5-B1 (F15);
- the non-blocking notes on F15, F11, F03, F13, F26, F19, F31, F39, F45, F53, F54, F57, F105, F69, F70, F71 and F73 (R5-N1 to N22).

Recomputed this round from the raw files, among others:
- F38/F39 (X1 37.199, vs A +1.301, 0.251 / 0.643);
- F44 (−1.265 / −1.359);
- F47 (+0.965, 5/6);
- F48/F70 (CP-SAT −0.889, 0.355 / 0.844; union +0.768 / +0.437 with both SE ratios);
- F57 (PT 48/48, CD 46/48);
- F59 (−0.314, 2.22 / 3.43);
- F60 (−0.487);
- F64 (T1 means);
- F65 (Y 43.170, −0.300);
- F66 (93.5%, 69.3%);
- F69 (dev Region1_s0 26.97 → 26.23).

**P2/P3, 5 in full:**
- F100: the R4-B1 rewrite; notes R5-N18, N20, N21.
- F32: the table matches `wp5_ising/RESULTS_dev.md:220-235`; note R5-N23.
- F74: correct.
- F88: correct; note R5-N25.
- F96: 6.0–7.3 = 5.99–7.32 raw.

F40 and F48 were read, and their numbers were checked through the F70 recomputation.

**Also audited:**
- **Header, abstract, legend, §0.1 index:** correct apart from R5-N3.
- **§8, rows 1–24 and the summary:**
  - Statuses follow the closed list.
  - Row 7 "Partly supported": Q2 PT ≤ best classical on 5/6 at 10 s; H2′ PT 6/6 at 3 s.
  - Row 24's −1.00 to +0.54 matches the test pools (T2 −0.995, H4 +0.541).
- **Appendix B:** the rows changed this round.
- **Appendix D:** the round-5 additions are present in `recompute_out.txt` L148–L168.

## 5. Spot checks: my own recomputation from the raw files

My scripts are independent of `recompute.py` and use matched rows only.

| # | Story claim | Raw source | Recomputed | Verdict |
|---|---|---|---|---|
| S1 | F105 table, B+α vs A+α: WP2 dev 37.88 / 38.43 / −0.550 / 5/8 / 0.517 (1.1) / 0.097 (5.7); H3′ 38.302 / 38.380 / −0.078 / 1/6 / 0.247 (0.3) / 0.272 (0.3); H4 35.020 / 34.479 / +0.541 / 4/6 / 0.492 (1.1) / 0.216 (2.5); H5 24.624 / 24.476 / +0.148 / 4/6 / 0.119 (1.2) / 0.060 (2.5); T2 42.870 / 43.865 / −0.995 / 1/5 / 0.464 (2.1) / 0.546 (1.8); T1 10.188 / 10.135 / +0.053 / 3/4 / 0.037 (1.4) / 0.024 (2.2) | `wp2_deployed/trials.csv` (Ax→Aa, Bx→Ba), `wp3_test/trials.csv`, `wp9_region5/trials.csv`, `wp10_schedule/trials_test.csv`, `t2u_region4/trials_test.csv`, `t1u_region2/trials_test.csv` (s0.3–0.6) | Identical to 3 dp in every cell. Ratios 1.06 / 5.67, 0.32 / 0.29, 1.10 / 2.51, 1.24 / 2.46, 2.14 / 1.82, 1.44 / 2.19. WP2 dev: 5 positive d, mean pulled down by R6 s0.1 −3.764 | match |
| S2 | F105, F52, F53: H4 A+α − B+α −0.235, +0.650, +0.183, +0.064, +2.899, −0.314 (89%; others +0.070); H5 s0.4 69%; A − B+α +0.373, +0.404, +0.435, +0.439, +7.656, +0.869 (75% of 10.175; others +0.504 = 1.4%); vs B 78% of 11.321; B+α −4.7%, 6/6 | `wp9_region5/trials.csv`, `wp10_schedule/trials_test.csv` | Identical. 2.899 / 3.247 = 89.3%; 0.613 / 0.889 = 69.0%; 7.656 / 10.176 = 75.2%; 2.520 / 5 = 0.504 = 1.39% of 36.174; 8.849 / 11.321 = 78.2%; 1.6959 / 36.174 = 4.69% | match |
| S3 | F25 / legend caveat 2: without the six reused instances, LP 30/33 12.54%, CP-SAT 30/33 12.53%, PT 31/33 13.18%; the six 6/6, 15.73–16.56%; 18 rows 09-28 18:54 → 09-29 01:05; `27fb6f0` 15:06 | `wp1_offline/results/wp1_table.csv`, `wp1_offline/trials.csv`, `git show` | Identical (PT on the six 16.49%). 18 rows 18:54:30 → 01:05:51; 27fb6f0 15:06:02. The full set reproduces 36/36/37 and 13.03 / 13.15 / 13.69 | match |
| S4 | F45: without Region7 s0.5, X1 vs A 5/5 +1.13, vs A+α +0.39 (3/5); Region5 without s0.5 −0.99 (2/5), driven by s0.6 | `wp3_test/trials.csv`, `wp9_region5/trials.csv` | +1.129 (5/5); +0.395 (3/5); −0.990 (2/5), s0.6 −5.588 | match (wording note R5-N10) |
| S5 | F70 / F100: union Region5_s0 0.16–0.31%, CP-SAT lower 2/3; Region1_s0 ties | `union/labels/Region{5,1}_s0_F1{PT,CPSAT}_s{1,2,3}.json` | +0.170%, +0.155%, −0.309%; Region1_s0 15.582686 on all six | lower bound is 0.15 raw (R5-N18); rest match |
| S6 | F70 / abstract / §8 rows 7, 23: CP-SAT lower on 36/36 H3′ pairs (18 deployed, 18/18), 0.040–0.198 (0.20–0.89%), means 21.057 vs 20.965 | `wp3_test/labels/*.json`; `label_file` in `wp3_test/trials.csv` | 36/36; seeds 1–3 18/18; +0.0404 to +0.1981; 0.197–0.893%; 21.057 / 20.965 | match |
| S7 | F15: "No Ising arm came close" (to > 2 SE below Baleen online) | `harness_eval/results/deployed.csv`, `0_reproduce/work/results/retrain_dist.csv` | EIM C2 Region6 1.72 SE; R2 2.05; RB4 1.89 | **contradicted → R5-B1** |
| S8 | Abstract / F53: A+α vs A on H4 +1.16 ± 0.75 (≈1.5 SE), s0.5 69%, others +0.43 | `wp9_region5/trials.csv` | +1.1546, SE_inst 0.7454 (1.55), SE_retrain 0.0938; 4.758 / 6.927 = 68.7%; 2.169 / 5 = 0.434 | match |
| S9 | F71 scope check: retention on T2 | `wp1_offline/results/wp1_table.csv`, `t2u_region4/trials_test.csv` | Y: undefined on s0.2, 9.13 / 0.29 / −0.02 / 0.32 on s0.3–0.6; A+α 9.28 on s0.3 | degenerate metric (R5-N19) |
| S10 | Appendix D: `recompute_out.txt` reproduces | `python3 changes/4_story/code/recompute.py` | byte-identical | match |

## 6. Counts

- **`check_story.py` problems:** 0.
- **Findings audited in full:** 59, of which P0 9/9, P1 45/45 and P2/P3 5 (F100, F32, F74, F88, F96). F40 and F48 were checked through F70. Also audited: the header, abstract, legend, index, §8 (24 rows and the summary), the changed Appendix B and C rows, and the Appendix D round-5 additions.
- **Recomputed spot checks:** 10 (S1–S10). S1–S4, S6, S8 and S10 match. S5 finds an inherited rounding (R5-N18). S7 confirms R5-B1. S9 is a scope note (R5-N19).
- **Round-4 items:** the blocking R4-B1 is fixed, and N1–N16 are done.
- **Blocking problems: 1.**

  | Kind | Count | Items |
  |---|---|---|
  | Wrong number | 0 | — |
  | Unsupported or contradicted claim | 1 | R5-B1 (F15, P1) |
  | Wrong evidence tag | 0 | — |
  | Missing ref | 0 | — |

- **Non-blocking problems:** 27 (R5-N1 to R5-N27).

```
OPEN_FINDINGS=1
VALIDATOR_STATUS=FAIL
```
