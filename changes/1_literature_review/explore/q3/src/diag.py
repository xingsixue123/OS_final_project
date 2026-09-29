"""Dev-only diagnostics: offline (OPT) admission decisions simulated under the DEPLOYED prefetch variant.

  diag.py <Region> <name>   name in {base_fullml, hx_R2}
  base_fullml : Baleen's peak-blind order on full-trace episodes at the deployed EA (common/work a0_fullml dump)
  hx_R2       : harness_eval's peak-aware R2 offline decisions (EA_opt, read-only)
The deployed prefetch variant: Region6 All on Partial Hit; Region7 ML-Range on ML-When with harness_eval's R0
deployed (Baleen-trained) prefetch models. --ap opt cutoff converged to 35.599 +-1%. cwd = common/work.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.environ["X_ROOT"], "common", "src"))
import xc  # noqa: E402

W = os.path.join(xc.COMMON, "work")
POOL = ThreadPoolExecutor(max_workers=6)


def main():
    region, name = sys.argv[1], sys.argv[2]
    H = xc.HARNESS
    if name == "base_fullml":
        out = xc.parse_train_outputs(os.path.join(W, "logs", "a0", f"a0_fullml_{region}_s0", "train.log"))
        dec, ana = out["thresholds"][0], out["analysis"][0]
        hint = 29.0
    else:
        exp = f"o11_{region}_R2"
        out = xc.parse_train_outputs(os.path.join(H, "work", "logs", "o11", exp, "train.log"))
        dec = os.path.relpath(os.path.join(H, "work", out["thresholds"][0]), W)
        ana = os.path.relpath(os.path.join(H, "work", out["analysis"][0]), W)
        hint = 27.0 if region == "Region6" else 30.0
    if region == "Region6":
        pf = ["--prefetch-when", "partial", "--prefetch-range", "acctime-all"]
    else:
        tl = open(os.path.join(H, "work", "logs", "dep", "dep_Region7_R0_rep1", "train.log")).read().splitlines()
        mp = [l.split(" ")[1] for l in tl if l.startswith("model_prefetch_offset_start ") and l.endswith("M")][0]
        mp = os.path.relpath(os.path.join(H, "work", mp.replace("_prefetch_offset_start.model", "_prefetch_{k}.model")), W)
        pf = ["--prefetch-when", "predict", "--prefetch-range", "acctime-episode-predict", "--prefetch-when-threshold",
              "0.5", "--prefetcher-model-path", mp]
    tag = f"diag_{region}_{name}"
    base = ["--trace", xc.trace_path(region, 0.0), "--offline-ap", "--ap", "opt", "--ap-threshold", "30",
            "--size_gb", "366.475", "-o", f"runs/diag/{tag}", "--batch-size", "16", "--log-interval", "600",
            "--ep-analysis", ana, "--offline-ap-decisions", dec, "--job-id", tag, "--eviction-policy", "LRU"] + pf
    tried, best = xc.converge_loop(W, tag, base, [hint - 2, hint, hint + 2], POOL,
                                   os.path.join(W, "logs", "diag", tag), f"runs/diag/{tag}/converge", 2.0,
                                   increasing=True, lo_bound=0.0, hi_bound=1e6, max_rounds=5)
    m = xc.metrics(best["result_file"])
    ws = xc.window_series(best["result_file"])
    US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100
    sel = {w: round(float(ws["used"][w] * US), 2) for w in [712, 152, 816, 646, 660, 613, 282]}
    row = dict(region=region, name=name, threshold=best["threshold"], **{k: v for k, v in m.items()}, windows=sel)
    print(json.dumps(row, default=float), flush=True)
    xc.append_jsonl(os.path.join(xc.Q3, "results", "diag.jsonl"), row)


if __name__ == "__main__":
    main()
