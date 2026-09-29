"""Verify that the per-access features dumped by pb3_policy (acc_meta, acc_dyn) equal, row by row, the frozen
admission trainer's own feature matrix (train_ap.GBAdmissionTrainer.prep() -> df_X), and that the dumped Baleen
labels equal its threshold_binary labels. Mirrors train.py main() up to the trainer's prep (no GBM is trained).

  cd q3/work && bwrap ... $BALEEN_PY -B verify_features.py <Region> <start> <EA> <out.json>   (under X/.train.lock)
"""
import json
import os
import sys

import numpy as np

import pb3_policy
from BCacheSim.episodic_analysis import policies, train_ap, train_prefetcher as tpf


def main():
    region, start, ea, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    pb3_policy.register()
    exp = f"verify_{region}_s{start:g}"
    inst = os.path.abspath(f"inst/{exp}.npz")
    cfgp = os.path.abspath(f"cfg/{exp}.json")
    os.makedirs(os.path.dirname(cfgp), exist_ok=True)
    json.dump({"mode": "dump", "name": exp, "target_wr": 35.599, "skip_windows": 0, "inst_path": inst}, open(cfgp, "w"))
    os.environ["HE_POLICY_CONFIG"] = cfgp
    tk = dict(region=region, sample_ratio=0.1, start=start, trace_group="20230325", only_gets=True,
              min_ts_from_start=0.0, max_ts_from_start=86400.0)
    pt = tpf.PrefetcherConfTrainer(trace_kwargs=tk, e_age_s=ea, wr_threshold=35.599)
    pol = policies.PolicyPeakBaleen3(exp=exp, trace_kwargs=tk, target_wrs=[34, 50, 100, 75, 20, 10, 60, 90, 30],
                                     target_cache_sizes=[366.47461], supplied_ea="physical",
                                     output_base_dir=f"runs/verify/{exp}", train_target_wr=35.599,
                                     train_models=["admit", "prefetch"], res_fn_kwargs={"workers": 8},
                                     rl_init_kwargs={"filter_": "prefetch"},
                                     suffix=f"/ws.20230325_{region}_{start:g}_0.1/fs_meta+block+chunk/accs_15")
    pol.get_filenames(ea)
    pol.get_all(ea)
    pol._prep_residencies([ea])
    tr = train_ap.GBAdmissionTrainer(policy=pol, prefetch_trainer=pt, labels=["threshold_binary"],
                                     feat_subset="meta+block+chunk", target_wr=35.599, acc_cutoff=15)
    tr.prep()
    z = np.load(inst)
    idents = {(str(k), float(t)): i for i, (k, t) in enumerate(zip(z["keys"], z["ts0"]))}
    start_ = z["acc_start"]
    cols = (["feat_metadata|op", "feat_metadata|ns", "feat_metadata|user", "feat_metadata_size|start",
             "feat_metadata_size|end", "feat_metadata_size|size"] + [f"feat_dynamic_b|{i}" for i in range(6)]
            + [f"feat_dynamic_c_combined|{i}" for i in range(6)])
    Xt = tr.df_X[cols].to_numpy()
    sorted_eps = {b: sorted(e, key=lambda x: x.ts_logical[0]) for b, e in tr.eps_by_block.items()}
    mine = np.zeros_like(Xt)
    lab_mine = np.zeros(len(Xt), bool)
    # Baleen labels in the dump: strict prefix of base_order within B
    s = z["s"]
    order = z["base_order"]
    cs = np.cumsum(s[order])
    xb = np.zeros(len(s), bool)
    xb[order[cs <= z["B"]]] = True
    n_bad_map = 0
    for r, row in enumerate(tr.rows):
        i, j, k = row["id"]
        ep = sorted_eps[row["block_id"]][j]
        e = idents.get((str(ep.key), float(ep.ts_physical[0])))
        if e is None:
            n_bad_map += 1
            continue
        p = start_[e] + k
        mine[r, :6] = z["acc_meta"][p]
        mine[r, 6:] = z["acc_dyn"][p]
        lab_mine[r] = xb[e]
    diff = np.abs(mine.astype(float) - Xt.astype(float))
    res = dict(region=region, start=start, ea=ea, n_rows=len(Xt), n_rows_dump=int(z["acc_row"].sum()),
               n_unmapped=n_bad_map, rows_all_equal=int((diff.max(1) == 0).sum()),
               max_abs_diff_per_col={c: float(d) for c, d in zip(cols, diff.max(0))},
               label_equal=int((lab_mine == tr.df_Y["threshold_binary"].to_numpy()).sum()),
               n_pos_trainer=int(tr.df_Y["threshold_binary"].sum()), n_pos_dump_rows=int(lab_mine.sum()))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
