# WP9 instances (Region5, trace group 20230325, 0.1%), built 2026-10-16

**How they were built.** `src/prep.py dumps` (copied from `wp3_test`) ran the **unmodified** BCacheSim training driver (the frozen artifact `0_reproduce/baleen_code`, via `work_frozen/BCacheSim`) with phase-1's dump Policy `PolicyPeakBaleen3` (`src/pb3_policy.py`, registered by `src/launch_train.py`; both unchanged copies). Same method as `explore/common/src/a0.py` and WP3.

| file | built with | windows in the objective | used for |
|---|---|---|---|
| `day1_<key>.npz` | the authors' Fig 9 Baleen `TrainCommand` for that sample (`jobs.json`, ML-Range on Partial Hit, experiment `20230421_alltraces_pfalways`; EA of that row), `--train-models` removed, mode `dump` | all 145 day-1 windows | the F1PT label solves (`labels.py`) |
| `fullml_<key>.npz` | the full trace at the same deployed EA, Baleen order, mode `baleen` | windows after day 1 (skip 144) | threshold-seeding emulator and mechanism statistics only |

Samples: s0 (dry run only) and s0.1–s0.6 (test). **No instance exists for the reserve s0.7–s0.9.** Logs (full command on the first line): `logs/prep/prep_{day1,fullml}_<key>/train.log`. Hashes: `results/instances_sha256.csv`.

| file | episodes | GET accesses | active windows | B (chunks) | EA (s) | bytes | sha256 |
|---|---|---|---|---|---|---|---|
| `day1_Region5_s0.1.npz` | 10914 | 31863 | 145/145 | 24606 | 5990.059 | 640062 | `f26b83b56e64f9048d8183388cf37485c79f6131fe37e3bf35de6a700153b58e` |
| `day1_Region5_s0.2.npz` | 10176 | 30527 | 145/145 | 24607 | 5827.476 | 598065 | `6bf891b607792417ce1817f3ccf2905a79c75bee2b2101b102bce9015b1dd8a6` |
| `day1_Region5_s0.3.npz` | 10651 | 31865 | 145/145 | 24607 | 5925.074 | 627291 | `b718438fe3bfbc47caeab091f560d651b6ea4f428e84d7b121d72fa169f46727` |
| `day1_Region5_s0.4.npz` | 8295 | 29378 | 145/145 | 24611 | 6266.973 | 516873 | `7a31ded1ee86bf1f4d1dd8e193c1d8c90c043703ee23b1efe4436fc3309d8f3a` |
| `day1_Region5_s0.5.npz` | 10037 | 30923 | 145/145 | 24606 | 5999.002 | 597804 | `3d4d44db9e8a7ed7e08e04885c7c2861a4caa586b851334daf6b2bec91385aab` |
| `day1_Region5_s0.6.npz` | 10342 | 34155 | 145/145 | 24606 | 6056.686 | 628257 | `117bfd74853156ffc3d9ed4d3a13c9d1f5c53d2f74f06d93116d39db3aab86ad` |
| `day1_Region5_s0.npz` | 10355 | 30290 | 145/145 | 24607 | 5936.225 | 610995 | `361e4b0f999c27b6cc2d8216898f842761dce31eb339acd8a6d737e9dbd99674` |
| `fullml_Region5_s0.1.npz` | 69566 | 214927 | 853/997 | 170204 | 5990.059 | 3984063 | `8e4d75cbc5204bead0167592d5ba3ef2498e51c0170d779d6d5dbf15dad732eb` |
| `fullml_Region5_s0.2.npz` | 65910 | 216181 | 853/997 | 170207 | 5827.476 | 3839621 | `ea71a6fc7ab7770197a3859dcf975eb395cf03f145f0d642e33a6b456ddabc08` |
| `fullml_Region5_s0.3.npz` | 69066 | 215500 | 853/997 | 170212 | 5925.074 | 3959742 | `18de824ce46cdeee9f98c18cffd2004adf7b47cf34b2feb403f47e1ad64a3cb9` |
| `fullml_Region5_s0.4.npz` | 52599 | 220353 | 853/997 | 170213 | 6266.973 | 3293991 | `1b624a6e79dac061fc6a4658a6cbc66ffff6843f326b35ffcc3a0d0526dfbb82` |
| `fullml_Region5_s0.5.npz` | 65470 | 216237 | 853/997 | 170204 | 5999.002 | 3855032 | `864e837ab6151f5570b0f0833987ae7c15beb24a5305ec37b9d1617e14d84b16` |
| `fullml_Region5_s0.6.npz` | 67476 | 216054 | 853/997 | 170202 | 6056.686 | 3915514 | `04d76120d396167b885c588b41e3ea493dd78aa76bfa7747067f0740d5c4cd70` |
| `fullml_Region5_s0.npz` | 66598 | 215689 | 853/997 | 170217 | 5936.225 | 3888472 | `c50d764b13408e7962105b4592347fc655b16434e1d36827766f72521310fb17` |

**Label sets** (`labels/<key>_F1PT_s<seed>.npz`, statistics in `.json` and `results/labels_summary.csv`): 6 test instances × F1PT × seeds 1–6 = 36 sets, all solved (rc 0). Configuration frozen and identical to WP3: `explore/q2/plan_F1.json` solver `pt`, `cfg_by_budget["10"]`, LP start, 8 numba threads, single level f = 1.0, 10 s. Means per instance over the 6 seeds (day-1 objective, util %):

| instance | F1PT labels | Baleen labels | Jaccard vs Baleen | day-1 peak F1PT | day-1 peak Baleen | zero-value labels |
|---|---|---|---|---|---|---|
| Region5_s0.1 | 1197 | 1857 | 0.438 | 22.11 | 30.83 | 0 |
| Region5_s0.2 | 1183 | 1809 | 0.444 | 21.09 | 29.04 | 0 |
| Region5_s0.3 | 1123 | 1787 | 0.426 | 21.64 | 33.53 | 0 |
| Region5_s0.4 | 1236 | 1576 | 0.550 | 17.11 | 22.55 | 0 |
| Region5_s0.5 | 1133 | 1703 | 0.466 | 20.47 | 24.57 | 0 |
| Region5_s0.6 | 1275 | 1923 | 0.476 | 20.61 | 27.18 | 0 |
