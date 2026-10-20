# Citation and fact-check validator, round 4 of 5

Target: `changes/4_story/STORY.md` (writer round 4, uncommitted working tree, run 20261020_154140). Every ref was opened at its cited lines. Numbers were checked for value, units, sign, arm, instance and budget. Times and hashes were checked against `git show` and the ledgers.

## 1. `check_story.py`

`python3 changes/4_story/code/check_story.py` reports `n_problems: 0` and no warnings, over 105 findings: P0 9, P1 45, P2 34, P3 17. The index counts (§0.1) match the headings: DEV 21, INFRA 41, NEGATIVE-TEST 8, OFFLINE 13, REPRO 5, TEST-POSTHOC 14, TEST-PREREG 3. Every index row matches its heading's priority, tag and title. The only differences are link markup in the F27 and F77 titles.

## 2. Problems found

**Blocking problems: 1.**

| ID | Finding | Issue | Evidence (file and line) | Required fix |
|---|---|---|---|---|
| R4-B1 | F100 [P3] (STORY.md L1823; new in round 4 as the R3-B4 fix) | **Claim contradicted by the ledger.** F100 says "The two non-optimal 10 s comparisons with deployed rows ran under contention: WP3's … and Track C's", and that "the auto-research Region5_s0 dev solves … have no deployed PT-vs-CP-SAT row of their own". In fact the Region5_s0 label solves feed deployed PT-vs-CP-SAT rows: F70's union dev rows XA:F1PT vs XA:F1CPSAT and XG:F1PT vs XG:F1CPSAT. Both have 3 matched retrains on Region5_s0 (and on Region1_s0) for each label solver. On Region5_s0 the objectives are not equal: PT − CP-SAT is +0.170%, +0.155% and −0.309% for seeds 1–3. These solves ran on shared cores (F100's own list includes "the auto-research label solves"). So the union dev comparison is a third non-optimal 10 s comparison with deployed rows that ran (in part) under contention. It is also the row F70 counts as 2.1 retrain-level SE in PT's favour. The union rows' other 8 instances reuse WP2's D retrains, so they sit on WP2's near-tie labels (10/10/4 pairs, within ±0.56%; solved before H2′), not on exact ties. No cited ref supports "no deployed row". | `changes/3_autoresearch/work/union/trials_dev.csv` (arms XA/XG-F1PT/F1CPSAT; instances include Region5_s0 and Region1_s0, 3/3 matched each); `changes/3_autoresearch/work/union/labels/Region5_s0_F1{PT,CPSAT}_s{1,2,3}.json` (`label_peak_util` 21.6284 / 21.5917, 21.6230 / 21.5896, 21.6230 / 21.6901); `changes/3_autoresearch/work/union/src/union.py:6`, `:44-48` (DEV8 instances reuse WP2's `D_<labels>` retrains; other instances solve labels here); `changes/3_autoresearch/result/FINAL_REPORT.md:78` | In F100, replace the "two … comparisons" sentence. State that the union dev rows (F70) include Region5_s0, whose objectives differ by 0.16–0.31% and which was solved on shared cores; that Region1_s0 ties; and that the other 8 instances use WP2's near-tie labels. Cite `union/trials_dev.csv` and the union label JSONs. Optionally add the same note to F70's union rows' Data column, as the reason that row is not a pure co-optimal-set effect either. |

**Non-blocking problems (wording or refs; no wrong number, claim, tag or missing ref):**

| ID | Finding | Issue | Evidence (file and line) | Required fix |
|---|---|---|---|---|
| R4-N1 | Abstract (STORY.md L23) | The lead clause "lost … on the day-1 label instances that produce the deployed labels" also covers the WP5 dev day-1 table. Its instances are the same dev day-1 instances WP2 labelled (Region6/7 s0–0.3), but F32 says these are "not the configuration that produced the deployed labels". The parenthesis "(WP5-tuned configurations, nested objective)" scopes the claim, so this is not an overclaim. Still, a reader can take "that produce the deployed labels" to describe the solver runs as well as the instances. Also, on the f = 1 column (the single level the deployed labels use), EIM, not a classical solver, is best at 1 s (22.0753); F32 discloses this. | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:220-237` ("Day-1 (label-size) instances, dev Region7/6 s0-0.3"; eim 1 s f = 1 22.0753); STORY.md L857, L866 | Optional. For example: "on the day-1 label-size instances: on WP5 dev (WP5-tuned configurations, not the deployed one; nested objective) …, and on the H3′ test label solves themselves …". |
| R4-N2 | F104 refs (L336); F13 refs (L504) | F104 cites `changes/SCOPE_v2.md#L23-L24` twice, and F13 cites `changes/1_literature_review/harness_eval/RESULTS.md#L31` twice. F104's attribution claim is itself sourced: L8 credits the proposal (§4.1, H3) with the load features and the ML-When gate, L24 calls item 3 "the proposal's load-adaptive gate", and L23 (item 2, the threshold) carries no attribution. | `changes/SCOPE_v2.md:8`, `:23`, `:24`; the F13 Refs line | Drop the duplicate refs. |
| R4-N3 | F70 title (L1526) vs body (L1540) | The title's "at most ≈2.1 instance-level SE" is the WP2 X1 row's 2.07, rounded. The body gives 2.07, and the union XA row's 2.1 in the table is a *retrain*-level ratio (2.14). The two readings agree, but "2.1" could be misread as the union row. | Recomputed: WP2 X1 vs Ea-1.0:F1CPSAT +1.263 / 0.610 = 2.07; union XA +0.768 / 0.421 = 1.82 (instance) and / 0.359 = 2.14 (retrain) | Optional: "≈2.07". |
| R4-N4 | F32 (L868) | "The WP5-tuned PT is the worst of the four" is unqualified, but on the nested objective it is true only at 10 s (PT 22.6071). At 1 s and 3 s CP-SAT is worst (23.0674 and 22.4531, vs PT 22.8104 and 22.4066). The rest of the sentence talks about the 10-s configuration, and F70 says "at 10 s", so this is ambiguous rather than wrong. | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:224-235` | Write "At 10 s the WP5-tuned PT is the worst of the four". |
| R4-N5 | Legend caveat 2 (L65) | The caveat says H1′'s criterion was fixed in `PLAN.md#L19` "before WP1 ran". But 6 of WP1's 39 instances reuse phase-1 Q2 held-out solves (18 rows, 09-28 18:54:30 → 09-29 01:05:51). Their Q1 outcomes were known before the PLAN commit `27fb6f0` (09-29 15:06:02). F73 discloses the reuse; the tag is OFFLINE, so no evidence label is affected. | `changes/2_deployable_peak/wp1_offline/trials.csv` (phase `wp1_reused_phase1_heldout`); `changes/4_story/result/protocol_commits.txt` | Add "(6 instances reuse phase-1 solves; [F73](#F73))". |
| R4-N6 | F18 (L586) | "F2b's dev selections were equally far below the oracle" is loose. F96 gives F2b dev 6.0–7.3 points below OPT on dev s0, while Q1 is −5.21 on held-out s0.1–0.3: different instances, and roughly comparable distances. | STORY.md F96 (L1692); `changes/4_story/result/recompute_out.txt` | "comparably far (6.0–7.3 points on dev; [F96](#F96))". |
| R4-N7 | F105 (L1518) | "At most B was 0.094 better than A" holds for pool means only. On single instances B was better by up to 0.755 (H3′ Region7 s0.5) and 0.542 (WP2 Region6 s0). | Recomputed from `changes/2_deployable_peak/wp3_test/trials.csv` and `changes/2_deployable_peak/wp2_deployed/trials.csv` (per-instance A − B) | "on any pool mean, at most 0.094". |
| R4-N8 | F105 (L1520), F53 (L1234) | The "(5/8)" for B − B+α is in the wins column of `attribution.txt` L14. The cited anchors are L16–L17 (F105) and L17 (F53); they give "+0.016 ± 0.386" and the per-instance values, from which 5/8 can be counted but is not stated. | `changes/2_deployable_peak/wp2_deployed/results/attribution.txt:14`, `:17` | Widen the anchors to `#L14-L17`. |
| R4-N9 | F68 (L1469) vs F35 (L934) | F68 quotes the Q3 scan-window share as "25–42%", which is the source's text (`q3/RESULTS.md` L294). F35 corrects this to 18–42% from the same report's table. The story is inconsistent with itself, though F68's number is in its cited ref. | `changes/1_literature_review/explore/q3/RESULTS.md:265-289` (table, minimum 0.18), `:294` (text, 25–42%) | Use F35's 18–42% in F68, or add "(text; table 18–42%, [F35](#F35))". |
| R4-N10 | F70 (L1537), abstract (L23), §8 rows 7 and 23 | "All 36 seed-matched H3′ test label pairs" is correct, but only seeds 1–3 (18 pairs) trained deployed models. Seeds 4–6 were solved and never used. CP-SAT is also lower on all 18 deployed pairs, so no conclusion changes. | `changes/2_deployable_peak/wp3_test/trials.csv` (`label_file` seeds 1–3 only for F1PT/F1CPSAT); `changes/2_deployable_peak/wp3_test/labels/` (seeds 1–6) | Optional: "36 pairs (18 deployed)". |
| R4-N11 | F73 H4 row (L1621), F53 | Only the static replays are disclosed as coming before the H4 protocol commit (21:30:11). In the same 20:29–21:00 window WP9 also built the 14 dumps and X1's 36 F1PT label sets. Those label sets and `INSTANCES.md` (the label statistics F54 uses) were committed together with the protocol in `c8f655a`. None carries an arm outcome. F65 discloses the equivalent T2 case. | `changes/2_deployable_peak/wp9_region5/PROGRESS.md:68`; `git show c8f655a --stat` (36 `labels/` files, `INSTANCES.md`) | Add "dumps and X1's 36 label sets (statistics in INSTANCES.md) were also built before the commit; no arm outcome". |
| R4-N12 | F84 item 1 (L1885) | "R0–R2 had no git attestation … Their headers were written with guessed times and rewritten in place with `sed`." The sed rewrite covered R0–R4 (R3 03:58→03:56, R4 04:52→04:48), not only R0–R2. | `changes/3_autoresearch/result/validator_red_team_round_1.md:106`; `changes/3_autoresearch/result/FINAL_REPORT.md:101` | "The rule headers (R0–R4) were …". |
| R4-N13 | F74, auto-research bullet (L1667) | "The evaluator is identical to the contract's `validate.py`." The protocol says the *rule*, computed by `eval_test.py`, is identical to `validate.py`'s; they are separate files. The title's "validated on earlier data" claim has no cited check for T2. | `changes/3_autoresearch/work/t2u_region4/PROTOCOL.md:45` | "the rule `eval_test.py` computes is identical to `validate.py`'s", and scope the title for T2. |
| R4-N14 | §8 row 7 (L2043) | The Evidence column says only TEST-POSTHOC, but the row now also rests on WP5 dev day-1 data (DEV) and on label-objective comparisons, which the legend's precedence rule tags OFFLINE. | STORY.md L58, L2043 | "TEST-POSTHOC + DEV + OFFLINE", as in row 23. |
| R4-N15 | Appendix B, 09-29 row (L2321) | The row is headed 15:02 but also lists `27fb6f0`, committed at 15:06:02 (as F73 says). | `git show -s 27fb6f0` | "15:02 / 15:06". |
| R4-N16 | Silent contradiction (RESEARCH.md vs F31) | RESEARCH.md L41's "Matrix-free SB: ≤214 MB" reads as absolute memory. Per F31 it is memory *above* the loaded instance (+214 MB over ~355–410 MB). F88's drift list does not include it. Separately, PLAN §2 names a single `PROTOCOL_v2.md`, which never existed in git; the protocols were split into `PROTOCOL_v2_H2.md` etc. The story never says so. | `RESEARCH.md:41`; `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:333-392`; `changes/2_deployable_peak/PLAN.md:18`, `:70`, `:120`; `git log --all -- '*PROTOCOL_v2.md'` (empty) | Add both to F88. |
| R4-N17 | Story-wide (carried over from round 3, N22) | The inherited source roundings listed in Appendix D "Agreement" are disclosed, not fixed. That disclosure is acceptable. | Appendix D item 1 | None. |

**Checked and consistent with its source (no item):** F28's "PT better only at 3 s". At 10 s PT's mean is 22.6004 vs best classical 22.6006, but the source calls 10 s a tie ("ties at 10 s"), and PT is ≤ best classical on only 4/6 instances there, below the ≥ 5/6 count rule (`changes/2_deployable_peak/wp5_ising/RESULTS_test.md:16-18`).

## 3. Round-3 blocking items: resolution checked

| Item | Status | How checked |
|---|---|---|
| R3-B1 (F70: tie wording) | **Fixed** | The H3′ claim is split out and now matches raw. Label JSONs `changes/2_deployable_peak/wp3_test/labels/*.json` show CP-SAT lower on 36/36 seed-matched pairs, PT − CP-SAT +0.040 to +0.198 (+0.197% to +0.893%), means 21.057 vs 20.965. WP2 dev has 24 pairs: 10 CP-SAT lower, 10 PT lower, 4 equal, −0.564% to +0.543%. All the PT solves are LP-started with budget 10.0 and `use_frac` 1.0, so they are the deployed phase-1 configuration at f = 1. §8 rows 22/23 and F32's title are scoped. |
| R3-B2 (F21/F24: missing refs) | **Fixed** | `PROTOCOL_v2_H3.md#L70`, `PROTOCOL_v2_H4.md#L55`, `wp9_region5/INSTANCES.md#L29` and `t1u_region2/PROTOCOL.md#L41` each state the phase-1 PT configuration (LP start, 10 s). |
| R3-B3 (F73: Track C end time) | **Fixed** | `ledger_labels.csv`: the last 10-05 row is 15:25:55. `proxy_ledger.csv`: the last is 15:18:51. PROGRESS L82–86 gives ~15:05. F44, F73 and Appendix B are consistent. |
| R3-B4 (F100: WP3 comparison) | **Fixed** | `wp3_test/PROGRESS.md:63-65` gives 16:26 → 16:40 under `taskset -c 0-23`, and the 36/36 result is as above. "No comparison" is now limited to WP9. |
| R3-B5 (F103: title) | **Fixed** | `harness_eval/RESULTS.md:270-276`: the C3 occupancy model was implemented, but the source asks the team to confirm it. |
| R3-B6 (header) | **Fixed** | `validator_citation_round_1.md` has two scratchpad paths, on one line, both redacted. |

## 4. Findings audited (64 in full)

- **P0, all 9:** F18, F20, F25, F28, F33, F44, F52, F59 and F65. Every number, verdict, tag, protocol hash and time is correct, apart from the F18 wording in R4-N6. The header, abstract, legend and §0.1 headline table are correct apart from R4-N1 and R4-N5.
- **P1, all 45:**
  - F01, F02, F03, F07, F08, F11, F13, F15, F19, F21, F24, F26, F27, F31, F34–F39, F41 and F95;
  - F45–F47, F50, F53, F54, F57, F60, F64, F66–F71 and F105;
  - F73, F75, F76, F84, F92, F93 and F94.
  - All are correct apart from non-blocking notes: F70 (R4-N3, R4-N10), F13 (duplicate ref, R4-N2), F105 (R4-N7, R4-N8), F53 (R4-N8) and F68 (R4-N9).
- **P2/P3, 10 in full:** F40, F48, F61, F83, F86 and F103 are correct. F104 has only the R4-N2 note, F32 only R4-N4, and F74 only R4-N13. **F100 has the blocking item R4-B1**; its other numbers are correct: WP3's 72 solves at 16:26–16:40, WP2's 144 + 4 sets, the TIMING_IDLE times, and the ANC10 / ANC10CP windows.
- **§8 rows 1–24 and the summary.** Statuses follow the closed list and the pre-registered rules. Row 18's 12.8–13.5% recomputes as 12.82 / 12.90 / 13.48.
- **Appendix B.** Every hash and time matches git. The new row "10-05 ~15:26 → 10-16" matches the ledgers and PROGRESS L92–110.
- **Appendix D.**
  - Items 2–8 and 10 were re-run and give the stated output.
  - Item 9 was run to stdout only, not to its file, and matches `untracked_evidence.txt`.
  - Item 3 gives `RESEARCH.md:36` and `wp1_offline/RESULTS.md:87`. Item 7 gives `2026-10-05T14:23:12 2026-10-05T17:41:42 126`. Item 8 gives 12. Item 10 gives `2264e66 2026-09-14 10:53:49` and `527f8bc 2026-09-26 14:02:59`.
- **New round-4 content, checked line by line:**
  - F105: every table cell, the per-retrain values and the quotes.
  - F66: 93.5%, the RejectX values and "within ~1 point".
  - F53: B+α's only prior support.
  - F59: 10/18 neutral, 9 of 10 equal to B, 23.062 vs 22.750, and 0.69–0.88 s.
  - F57: 1.50–2.41 s.
  - F73: the launch times, and H1′'s 6 reused instances (18 rows, 09-28 18:54:30 → 09-29 01:05:51).
  - F27: the Region4 windows and reductions.
  - F32: the day-1 table against `wp5_ising/RESULTS_dev.md:220-239`; seed-1 means 21.504 / 21.482 / 21.609.
  - F104: the attribution chain.
  - F03: its priority line.

**Timing.** Every protocol commit precedes its test launch (earliest `ts − wall_secs`):

| Test | Protocol commit | Test launch |
|---|---|---|
| H2′ | 10-03 01:13:51 | first row 01:24:28 |
| H3′ | 10-04 09:16:01 | 10-05 14:13:16 |
| H4 | 10-16 21:30:11 | 21:30:16 |
| H5 | 10-19 19:23:04 | 19:23:09 |
| T1 | 10-20 04:36:45 | TEST_GO 06:26:50 |
| T2 | 10-20 05:19:24 | TEST_GO 07:05:04 |

**Contradictions with RESEARCH.md.** None are silent. The headline numbers in RESEARCH.md L26–L45 match the story:
- 35.02 vs 36.17 (5/6); 24.45 vs 24.14; 40.53 vs 39.27 / 39.17;
- 27.0 vs 32.3 (−16%) = (32.28 − 27.06) / 32.28;
- the H1′ wins and means.

The known drifts are all flagged: ≈11.3% (F08), ≈70k (F31), "untouched" reserve (F92), stale header (F88).

## 5. Spot checks: my own recomputation from the raw files

My scripts are independent of `recompute.py` and use matched rows only. A configuration's mean is the mean over instances of the per-instance retrain means. SE_inst = sd(d_i)/√n; SE_retrain = √(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n.

| # | Story claim | Raw source | Recomputed | Verdict |
|---|---|---|---|---|
| S1 | F105 table: B − A −0.058 (5/8; 0.232 / 0.110), −0.094 (4/6; 0.155 / 0.104), +0.191 (3/6; 0.233 / 0.095), +0.402 (1/6; 0.167 / 0.116), +5.994 (2/5; 4.382 / 1.346), T1 −0.054 paired (3/4); T1 B 10.201 on s0.3–0.6; Region1 B worse on 5/6 | `wp2_deployed/trials.csv`, `wp3_test/trials.csv`, `wp9_region5/trials.csv`, `wp10_schedule/trials_test.csv`, `t2u_region4/trials_test.csv`, `t1u_region2/trials_test.csv` | Identical to 3 dp. A means 38.500 / 39.267 / 36.174 / 24.138 / 50.718 / 10.255; B 38.443 / 39.173 / 36.365 / 24.540 / 56.711. T1 B over s0.3–0.6 is 10.201 (10.092 over 5 instances incl. s0.1, correctly not used). Region1 d: 5 negative, 1 positive (+0.03) | match |
| S2 | F105 / §8 row 24: Region4 s0.5 B 55.31 / 55.12 / 55.31 vs A 32.86 / 32.85 / 32.86 (+22.39); s0.4 B 73.03 / 52.56 / 53.20 vs A 51.23–52.18 | `t2u_region4/trials_test.csv` | B 55.309 / 55.116 / 55.313; A 32.855 / 32.851 / 32.855; instance d −22.392; s0.4 B 73.035 / 52.564 / 53.196, A 52.183 / 51.233 / 51.731 | match |
| S3 | F70, F100, F32, §8 rows 7/23: H3′ labels CP-SAT lower 36/36, +0.040 to +0.198 (0.20–0.89%), means 20.965 vs 21.057; WP2 10/10/4 of 24, within ±0.56%; WP2 seed-1 means 21.5 / 21.5 / 21.6 | `wp3_test/labels/*.json`, `wp2_deployed/labels/*.json` (`label_peak_util`) | 36/36, +0.0404 to +0.1981, +0.197% to +0.893%, 21.057 / 20.965. WP2: 10 / 10 / 4, −0.564% to +0.543%, means 21.510 / 21.512; seed-1 21.504 / 21.482 / 21.609. PT start `lp`, budget 10.0, `use_frac` 1.0 | match |
| S4 | F66: A − A+α +9.488, +27.186, +0.120, +0.442, +2.001; s0.3 69%; s0.2 + s0.3 36.674 of 39.237 (93.5%) | `t2u_region4/trials_test.csv` | Identical; s0.3 69.3%, s0.2 + s0.3 93.5% | match |
| S5 | F59: TB:pt vs A 1/6, −0.314 (≈2.2 / ≈3.4 SE); 10/18 neutral; 9 of 10 equal to B; s0.5 r2 23.062 vs 22.750; F60: A+α 1/6, −0.487 (≈2.7 / ≈7.9); B+α 1/6, −0.338 | `wp10_schedule/trials_test.csv` | −0.3145 (SE 0.1417 / 0.0918 → 2.22 / 3.43); neutral at s0.1 r1–3, s0.2 r2–3, s0.4 r1/r3, s0.5 r1–3; 9 equal; 23.062 vs 22.750; A+α −0.4865 (0.1787 / 0.0612 → 2.72 / 7.95); B+α −0.3382 | match |
| S6 | F25, F26, §8 row 18: wins 36/36/37; 13.03 / 13.15 / 13.69%; R4 4.59 / 3.04 / 5.37; R5–7 30/30, 15.6 / 16.2 / 16.2; 13.0–17.7 per region; PT − CP-SAT −0.18, 18/39; window differs 30/34/33; plan coincides 6/9/6; per-trace mean 12.8–13.5% | `wp1_offline/results/wp1_table.csv` | 36/36/37; 13.03 / 13.15 / 13.69; 4.59 / 3.04 / 5.37; 15.57 / 16.19 / 16.18; region means 12.99–17.67; −0.184, 18; 30/34/33; 6/9/6; 12.82 / 12.90 / 13.48 | match |
| S7 | F52, F53: A+α 35.02 vs A 36.17, 5/6, +1.16 (0.09 / 0.75); vs B +1.35 (0.08 / 0.94); s0.5 4.76 of 6.927 (69%), other five +0.434; B+α 6/6 +1.70 / +1.89, SE_inst 1.19 / 1.40; F54: X1 38.09, vs A 3/6 −1.92, vs A+α 2/6 −3.07 | `wp9_region5/trials.csv` (stage = test, 90 rows) | +1.1546 (0.0938 / 0.7454); +1.3455 (0.0811 / 0.9433); 4.758, Σ 6.927, other five 0.434; B+α +1.6959 / +1.8868 (1.1944 / 1.3953), 6/6; X1 38.094, 3/6 −1.9195, 2/6 −3.0741 | match |
| S8 | F39, F40, F70 WP2 X1 row: X1 vs A +1.30 (0.25 / 0.64; 6/8), vs B +1.24 (0.26 / 0.51; 6/8), vs A+α +0.68 (5/8; 0.63), vs Ea-1.0:F1CPSAT +1.26 (0.47 / 0.61; 5/8; 2.07 / 2.7 SE) | `wp2_deployed/trials.csv` (widened re-runs merged as in Appendix D) | +1.301 (0.251 / 0.643), +1.244 (0.258 / 0.509), +0.678 (0.627), +1.263 (0.472 / 0.610 → 2.07 / 2.68) | match |
| S9 | F69: dev Region1_s0 A 26.97 → A+α 26.23, 3 retrains each; F64: A 0/6 on s0.1, 2/6 on s0.5 | `cls_table/trials_dev.csv`, `t1u_region2/trials_test.csv` | 26.97 (n = 3) → 26.23 (n = 3); A s0.1 0 of 6 rows matched, s0.5 2 of 6 | match |
| S10 | F100: the Region5_s0 dev solves "have no deployed PT-vs-CP-SAT row of their own"; F100 / FINAL_REPORT: Region5_s0 objectives within 0.16–0.31%, Region1_s0 identical | `union/trials_dev.csv`; `union/labels/Region{5,1}_s0_F1{PT,CPSAT}_s{1,2,3}.json` | Union dev instances: Region1_s0, Region5_s0, Region6/7 s0–0.3. XA/XG-F1PT and -F1CPSAT have 3/3 matched on both Region5_s0 and Region1_s0. Region5_s0 PT − CP-SAT +0.170%, +0.155%, −0.309%; Region1_s0 0.000% on all 3 | 0.16–0.31% matches; **"no deployed row" is contradicted → R4-B1** |

## 6. Counts

- **`check_story.py` problems:** 0.
- **Findings audited in full:** 64 (P0 9/9, P1 45/45, P2/P3 10). Also audited: the header, abstract, legend, index, §8 (24 rows and the summary), Appendix B (all rows) and Appendix D (items 2–10).
- **Recomputed spot checks:** 10 (S1–S10). S1–S9 match; S10 confirms R4-B1.
- **Round-3 blocking items:** 6/6 fixed. Round-3 grill items 1 (F105) and 2 (day-1 losses) are present and their numbers check out (S1–S3). The new F100 wording written for R3-B4 introduced R4-B1.
- **Blocking problems: 1.**

  | Kind | Count | Items |
  |---|---|---|
  | Wrong number | 0 | — |
  | Unsupported or contradicted claim | 1 | R4-B1 (F100, P3) |
  | Wrong evidence tag | 0 | — |
  | Missing ref | 0 | — |

- **Non-blocking problems: 17** (R4-N1 to R4-N17). R4-N17 needs no action.

```
OPEN_FINDINGS=1
VALIDATOR_STATUS=FAIL
```
