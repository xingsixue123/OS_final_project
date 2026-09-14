MERGED_DUPLICATES: 1

## Merges

1. **Syno: Structured Synthesis for Neural Operators** — `asplos-2026` row 21 folded into `asplos-2025` row 48.
   - Both rows carry the byte-identical title "Syno: Structured Synthesis for Neural Operators", the same DOI
     `10.1145/3676642.3736118` (asplos-2025 gave it as `https://doi.org/...`, asplos-2026 as the ACM DL page
     plus `https://dl.acm.org/doi/pdf/10.1145/3676642.3736118`), and the same repository
     `https://github.com/tsinghua-ideal/Syno`.
   - The asplos-2026 scout states the reason for the overlap explicitly: the paper "was published in ASPLOS 2025
     Volume 3 and presented at ASPLOS 2026". So it is one paper enumerated by two venue-year scouts, not two
     papers with similar titles.
   - Kept `shard = "asplos-2025"` (first occurrence in input order). The asplos-2026 scout's why-in-scope text
     is quoted inside the surviving row's `note`.

## Arithmetic

| stage | count |
|---|---|
| Included rows across the 49 input reports | 1249 |
| Rows folded into another row (duplicates) | 1 |
| Objects in `candidates.json` | 1248 |

1248 + 1 = 1249.

## Per-shard Included-row counts (as consumed)

| shard | rows | shard | rows | shard | rows |
|---|---|---|---|---|---|
| osdi-2023 | 17 | eurosys-2023 | 14 | vldb-2023 | 53 |
| osdi-2024 | 23 | eurosys-2024 | 18 | vldb-2024 | 69 |
| osdi-2025 | 23 | eurosys-2025 | 23 | vldb-2025 | 47 |
| osdi-2026 | 30 | eurosys-2026 | 45 | vldb-2026 | 68 |
| sosp-2023 | 10 | atc-2023 | 19 | sigmod-2023 | 37 |
| sosp-2024 | 17 | atc-2024 | 19 | sigmod-2024 | 61 |
| sosp-2025 | 18 | atc-2025 | 20 | sigmod-2025 | 93 |
| sosp-2026 | 27 | nsdi-2023 | 16 | sigmod-2026 | 82 |
| fast-2023 | 5 | nsdi-2024 | 14 | sigmetrics-2023 | 3 |
| fast-2024 | 9 | nsdi-2025 | 12 | sigmetrics-2024 | 7 |
| fast-2025 | 7 | nsdi-2026 | 20 | sigmetrics-2025 | 7 |
| fast-2026 | 13 | asplos-2023 | 28 | sigmetrics-2026 | 10 |
| mlsys-2023 | 23 | asplos-2024 | 31 | socc-2023 | 12 |
| mlsys-2024 | 15 | asplos-2025 | 50 | socc-2024 | 7 |
| mlsys-2025 | 24 | asplos-2026 | 30 (1 merged) | socc-2025 | 11 |
| mlsys-2026 | 41 | middleware-2023 | 4 | middleware-2024 | 9 |
| middleware-2025 | 8 | | | | |

Total = 1249.

## Clerical notes (no papers added, dropped or re-judged)

- **Input set.** Only the 49 report paths listed in the task were read. Three further reports exist on disk
  (`atc-2026`, `socc-2026`, `middleware-2026`) but are not in the input list, so their rows were **not**
  collected; including them would have broken the 1249 total.
- **`unknown` / blank links → `null`.** Applied to `pdf_url` and `repo_url` throughout (e.g. osdi-2025 Kamino,
  sosp-2024 E3, atc-2025 Toppings, nsdi-2026 DroidSpeak, socc-2025 "A Fast, Efficient, and Strongly-Consistent
  Object Store", middleware-2025 RUNE, and the many SIGMOD/VLDB rows whose scouts found no artifact).
- **Deep repo paths normalised to the repository root**, with the original deep link preserved verbatim in the
  `note` as a "Merge note". This affected 23 rows, including:
  `microsoft/nnfusion` (osdi-2023 Cocktailer, Welder), `jschwe/tokio-rs` (osdi-2023 BWoS),
  `microsoft/BitBLAS` (osdi-2024 Ladder), `TuftsNATLab/PCS` (osdi-2024 PCS),
  `microsoft/SparTA` (sosp-2023 PIT, mlsys-2023 nmSPARSE), `ml-energy/zeus` (sosp-2024 Perseus),
  `asprasad/treebeard` (sosp-2024 SilvanForge), `ssdohammer-sl/ceph` (atc-2023 TiDedup),
  `llm-db/llmstation` (atc-2025), `microsoft/Moonlit` (nsdi-2024 LitePred),
  `caoshiyi/artifacts` (asplos-2025 MoE-Lightning), `lynnliu030/artifact-eval` (mlsys-2025 LLM-SQL),
  `microsoft/MixLLM` (mlsys-2026 BatchLLM), `543202718/iotdb`, `szcompressor/SZ3`,
  `cornelldbgroup/skinnerdb`, `leanstore/leanstore` (×4 across vldb-2023 and sigmod-2025),
  `vmware/declarative-cluster-management`, `DBOS-project/apiary`, `HugoZHL/Hetu` (vldb-2024),
  `damslab/reproducibility` (vldb-2026 BWARE), `SymbioticLab/FedScale` (socc-2023 Auxo),
  `DataStates/artifacts` (middleware-2024 Deep Optimizer States).
- **Repo cell containing a non-repository URL.** osdi-2026 row 19 (SPADE) had the paper's own PDF URL in the
  Repo-link column; the repository the same scout named in prose
  (`https://github.com/umass-solar/adaptive-dag`) was used, and the discrepancy is recorded in the `note`.
- **Non-GitHub repositories kept as given**: Zenodo / DOI records (eurosys-2023 Groundhog and "With Great
  Freedom", eurosys-2024 Desiccant / TraceUpscaler / Carbon-Aware / Karousos, eurosys-2025 Eg-walker / CAPSys /
  TUNA, eurosys-2026 Monolithic Forwarding, sosp-2025 PrefillOnly, osdi-2026 Spain, asplos-2023 ×5,
  asplos-2024 GAIA, asplos-2025 DarwinGame, mlsys-2023 SIRIUS, vldb-2026 GPU Scalar Functions figshare),
  a GitLab URL (nsdi-2023 Hindsight, middleware-2025 K23), a self-hosted GitLab (fast-2026 RASK), an
  institutional project page (fast-2025 Liquid-State Drive), an `aka.ms` redirect (vldb-2026 LoadStar), an
  `anonymous.4open.science` link (vldb-2025 GraphCSR), and a GitHub **organisation** rather than a repository
  (atc-2025 "Identifying and Analyzing Pitfalls in GNN Systems" → `github.com/the-data-lab`, which is exactly
  what that scout recorded, with the ambiguity noted).
- **Same repo, different papers — deliberately NOT merged** (distinct titles and distinct contributions):
  `microsoft/nnfusion` (Cocktailer vs Welder), `microsoft/SparTA` (PIT vs nmSPARSE),
  `mirage-project/mirage` (osdi-2025 Mirage vs osdi-2026 MPK), `ml-energy/zeus` (nsdi-2023 Zeus vs
  sosp-2024 Perseus), `mit-han-lab/omniserve` (mlsys-2025 LServe vs QServe),
  `thustorage/PipeANN` (osdi-2025 PipeANN vs fast-2026 OdinANN),
  `cwida/FastLanes` (vldb-2023 compression layout vs vldb-2025 file format),
  `microsoft/vattention` (asplos-2025 vAttention vs POD-Attention),
  `microsoft/MixLLM` (mlsys-2026 BatchLLM vs MixLLM),
  `apache/systemds` (sigmod-2023 AWARE vs GIO), `UWASL/dedup-bench` (fast-2025 VectorCDC vs
  middleware-2024 SeqCDC), `microsoft/sarathi-serve` (osdi-2024 Sarathi-Serve vs asplos-2026 QoServe),
  `leanstore/leanstore` (four different LeanStore papers across vldb-2023 and sigmod-2025).
- **Similar but different titles kept separate**, e.g. sigmod-2024 "Grafite"/"InfiniFilter" family vs
  sigmod-2026 "Aeris"/"Zeno"/"Breadcrumb" filters; vldb-2024 "Aleph Filter: To Infinity in Constant Time" vs
  sigmod-2026 "Zeno Filter: To Infinity in Tiny Steps"; asplos-2025 "COMET (W4A4KV4 serving)" vs
  mlsys-2024 "COMET (Neural Cost Model Explanation)"; osdi-2025 "Mirage" vs eurosys-2026 "Maya";
  eurosys-2024 "Trinity (data store)" vs asplos-2026 "Trinity (tile-level equality saturation)";
  sigmod-2025 "Themis (GPU query engine)" vs nsdi-2026 "Themis (concurrency-bug fuzzing)";
  mlsys-2024 "Atom (quantization)" vs sigmod-2025 "Atom (KG query serving)".
- `note` fields reproduce each scout's why-in-scope / concerns text; only lossless transliteration was applied
  (smart dashes/quotes and backticks normalised for JSON, non-ASCII characters escaped).
- A scratch index of shard/title pairs used to check for cross-shard duplicates was left at
  `collect/.titles.txt`; it is not an output and can be deleted.
