# WP3 test instances (PROTOCOL_v2_H3 §7.3), built 2026-10-04

**How they were built.** `src/prep.py dumps` ran the **unmodified** BCacheSim training driver, i.e. the frozen artifact `0_reproduce/baleen_code`, through `work_frozen/BCacheSim`. It used phase-1's dump Policy `PolicyPeakBaleen3` (`src/pb3_policy.py`), registered by `src/launch_train.py`; both files are copied unchanged from `explore/q3/src`. This is exactly the method of `explore/common/src/a0.py`.

| file | built with | windows in the objective | used for |
|---|---|---|---|
| `day1_<key>.npz` | the authors' Fig 9 Baleen `TrainCommand` for that sample (`jobs.json`, EA of the Baleen row), `--train-models` removed (no GBMs), mode `dump` | all 145 day-1 windows (`skip_windows` = 0) | the label solves (`labels.py`) |
| `fullml_<key>.npz` | the full trace at the same deployed EA (`--train-split-secs-end 1e9`), Baleen order, mode `baleen` | windows after day 1 (`skip_windows` = 144) | the threshold-seeding emulator and the mechanism statistics only; no tuning |

Logs, with the full command on the first line: `logs/prep/prep_{day1,fullml}_<key>/train.log`. Machine-readable hashes: `results/instances_sha256.csv`.

| file | episodes | GET accesses | active windows | B (chunks) | EA (s) | bytes | sha256 |
|---|---|---|---|---|---|---|---|
| `day1_Region7_s0.4.npz` | 11735 | 38561 | 145/145 | 24612 | 5461.262 | 711152 | `a69c9aeb778a6b62e3104b6d961d33291820e1552808b639e263b1006b5a6729` |
| `fullml_Region7_s0.4.npz` | 79893 | 249300 | 853/997 | 170209 | 5461.262 | 4493259 | `36962b1b97478d4683b19d723ade95ead609a4ad9354646ff7541badab048cd2` |
| `day1_Region7_s0.5.npz` | 12063 | 35718 | 145/145 | 24607 | 6287.450 | 708079 | `9f75761cb138fd431ea9712cb112e712187d4de20b6cef115808b668b04615d8` |
| `fullml_Region7_s0.5.npz` | 81265 | 245345 | 853/997 | 170210 | 6287.450 | 4564891 | `66103e55795fe7e4dc6eb19c740e1c94655511f5d293da8bc2d70a3ede795d36` |
| `day1_Region7_s0.6.npz` | 11945 | 38478 | 145/145 | 24606 | 5716.396 | 714741 | `c24bb9c24420af6ec638f898e807dc768deff4e5f41ea44625f4800da155479a` |
| `fullml_Region7_s0.6.npz` | 81427 | 246933 | 853/997 | 170215 | 5716.396 | 4540915 | `8e73bae6095726aba93183e8a5a990366ab108b149dcdcb740d9a6689d6d2777` |
| `day1_Region6_s0.4.npz` | 8495 | 32854 | 145/145 | 24606 | 4325.542 | 608146 | `e55a760d55b017c3f89d90c9ea76179cc1b84d29201dc22f1e4a174fdba4fef3` |
| `fullml_Region6_s0.4.npz` | 59118 | 241832 | 853/997 | 170217 | 4325.542 | 4037405 | `664f9084338fe792a6077269bef7b7d13480965645c32199fdd71efcd62ab206` |
| `day1_Region6_s0.5.npz` | 8541 | 31696 | 145/145 | 24607 | 4250.464 | 597880 | `a1e354d5548d29de0e6872e22d04902f55cc5bd33377f63700dede861d4bb57c` |
| `fullml_Region6_s0.5.npz` | 59106 | 241531 | 853/997 | 170215 | 4250.464 | 4031678 | `b8580edf2b9c8d4bd7c69cf8d1a76deae7d3517a71f3e893cb0de1ff7c063def` |
| `day1_Region6_s0.6.npz` | 8057 | 29525 | 145/145 | 24606 | 4514.823 | 559798 | `590aada0784ba6b29d0b87e1df3a0763b714595941e487313b1f31d099fc231a` |
| `fullml_Region6_s0.6.npz` | 55264 | 242679 | 853/997 | 170201 | 4514.823 | 3870964 | `4a5c2c564011383a29a256f8b37fd5afc2247f7ecd7f2226535ec94436077626` |

**Label sets** (`labels/<key>_<design>_s<seed>.npz`; statistics in `.json` and `results/labels_summary.csv`): 6 instances × {F1PT, F1CPSAT} × seeds 1–6 = 72 sets. Configurations are frozen:
- **F1PT:** `explore/q2/plan_F1.json` solver `pt`, `cfg_by_budget["10"]`, start `lp`, 8 numba threads, single level f = 1.0, 10 s.
- **F1CPSAT:** solver `cpsat`, `cfg_by_budget["10"]`, 10 s.

The solver code is `src/labels.py`, copied from WP2 with only `INST` changed, plus the q2 modules in `src/q2lib`, copied unchanged.

Seed-1..6 means: F1PT day-1 label peak 21.06 vs Baleen 28.44 (Jaccard 0.46); F1CPSAT 20.97. Seeds 4–6 are used only for PROTOCOL §4 extra retrains.
