# Solver instances (common/inst/)

Built by Track A through the unmodified Baleen training driver with our launcher (`q3/src/launch_train.py` →
`PolicyPeakBaleen3` in `q3/src/pb3_policy.py`, mode `dump`/`baleen`, i.e. Baleen's own order; nothing is changed in
the harness). Format = harness_eval's instance format (consumed unchanged by `harness_eval/src/pbcore.Instance`,
i.e. `solve.py`), plus extra per-episode and per-access arrays. Builder: `common/src/a0.py` (commands in
`common/work/logs/a0/<exp>/train.log`, first line).

## Files

| file | mode | what | train args |
|---|---|---|---|
| `day1_<Region>_s<start>.npz` | deployed | day-1 episodes (labels for the GBMs) | the authors' Baleen `TrainCommand` for that sample (Fig 9 variant row; EA = that row's), `--train-models` removed (no GBMs needed to dump), `skip_windows=0` (all 145 day-1 windows active) |
| `full_<Region>_s<start>.npz` | offline | full-trace episodes (OPT decisions) | harness_eval's offline args ("OPT-Range on OPT-Ep-Start", `filter_=prefetch`) with the OPT's converged EA for that sample from the release CSV (`OPT AP` row), `--train-split-secs-end 1e9`, `skip_windows=144` (windows after day 1 active) |
| `fullml_<Region>_s<start>.npz` | helper | full trace at the deployed (ML) EA | used only to seed the WR-matching threshold search of deployed runs (and for dev analysis) |
| `hx_day1_<Region>_s0.npz`, `hx_full_<Region>_s0.npz` | dev | copies of harness_eval's `dep_<R>_R0_rep1.npz` / `dump_<R>_dump.npz` (read-only) | identical to our `day1_*_s0` / `full_*_s0` up to episode permutation (C, D, s, B checked) |

Instances: dev = `Region7_s0`, `Region6_s0`; held-out = `Region{7,6}_s{0.1,0.2,0.3}` (evaluation only).
EAs (s): day-1/fullml = Baleen row EA (R7 s0/0.1/0.2/0.3: 5653.153/5670.676/5726.042/5825.170; R6: 4669.873/4450.398/
4490.490/4222.270); full = OPT row EA (R7: 4442.942/4501.001/4615.013/4688.807; R6: 3848.741/3862.370/3796.137/3666.481).

## Keys (harness_eval format)
- `D_data, D_indices, D_indptr, D_shape`: CSR n×m, d(e,w) = DT (seconds) saved in 10-min window w if episode e is
  admitted (filter_=prefetch model: whole chunk range fetched at the first access; later accesses hit):
  d(e,w(a₁)) += st(1,c(a₁)) − st(1,N_e), d(e,w(a_k)) += st(1,c(a_k)) for k≥2; Σ_w d(e,w) == `rl.service_time_saved` (asserted).
- `C` (m): no-cache DT per window (== simulator `service_time_nocache` per window).
- `s` (n): `rl.chunks_written` (harness write units); `B`: largest chunk budget with WR < 35.599 (the label rule).
- `active` (m): windows in the objective (day-1: all; full: w ≥ 144).
- `base_order`, `base_score`: Baleen's order/score (`score_service_time_size_fixed`, argsort desc).
- `keys`, `ts0` (episode identity = (str(block key), first physical ts)), `ts_end`, `nchunks`, `ea`, `t0`, `duration`,
  `target_wr`, `upsample1`.
- Utilisation: util% = DT_seconds × 100/0.1/36/600 × 100 = DT × 4.6296 (per 10-min window).

## Extra keys (Track A)
- `chunk_lo`, `num_accesses`, `sts` (per episode), `trace_start_ts`, `trace_end_ts`.
- Per access (all GET accesses of all episodes; flat, episode-major; episode e's accesses are
  `acc_start[e]:acc_start[e+1]`): `acc_ep`, `acc_k` (index in episode), `acc_ts`, `acc_w` (window), `acc_nch`,
  `acc_c0` (first chunk id), `acc_meta` (n_acc×6 = `features.toList(with_size=True)`: op, namespace, user, offset,
  offset+size, size), `acc_dyn` (n_acc×12 = the admission trainer's block counts b0..b5 and combined chunk counts
  c0..c5, computed exactly as `train_ap.generate_data`; −1 where the trainer skips the row), `acc_row` (1 = a training
  row of the admission GBM, i.e. k < 15).
- Verified: on Region7 day 1, `acc_meta`/`acc_dyn` equal the frozen trainer's `df_X` on all 31,105 rows and the dumped
  Baleen labels equal its `threshold_binary` (`q3/results/verify_features_Region7_s0.json`).

## Loading
`harness_eval/src/pbcore.Instance(path)` works unchanged (extra keys are ignored); `q3/src/q3lib.Inst(path)` also
exposes the per-access arrays.
