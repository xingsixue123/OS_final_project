"""G1 part (iii): model-file replay (see g1_replay.py). For each dev trace, the frozen training's dump is retrained
twice with the frozen code and twice with the overlay code (each under the shared train lock); all model files are
compared byte-for-byte.  -> results/g1_replay.json

  source wp0_overlay/env.sh && cd wp0_overlay && taskset -c 8-23 $BALEEN_PY -B src/g1b.py
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tacommon as T  # noqa: E402

OUT = os.path.join(T.RESULTS, "g1", "replay")
LOGS = os.path.join(T.A, "logs", "g1", "replay")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    res = {}
    for region in ("Region7", "Region6"):
        dump = os.path.join(T.RESULTS, "g1", "dumps", f"g1_{region}_trainF")
        while not os.path.exists(os.path.join(T.RESULTS, "g1", f"train_g1_{region}_trainF.json")):
            time.sleep(10)  # written by g1.py once that training (and its dump) is complete
        runs = {}
        for code, k in (("frozen", 1), ("overlay", 1), ("frozen", 2), ("overlay", 2)):
            tag = f"{region}_{code}{k}"
            out = os.path.join(OUT, tag)
            if not os.path.exists(os.path.join(out, "prefetch_pred_net_pf_st.model")):
                with T.TrainLock():
                    rc, _ = T.run_logged(["../src/g1_replay.py", dump, out], os.path.join(LOGS, f"{tag}.log"),
                                         code=code)
                assert rc == 0, tag
            runs[tag] = {f: sha(os.path.join(out, f)) for f in sorted(os.listdir(out))}
        ref = runs[f"{region}_frozen1"]
        res[region] = dict(n_models=len(ref),
                           identical_to_frozen1={t: {f: h == ref[f] for f, h in r.items()} for t, r in runs.items()},
                           all_identical=all(r == ref for r in runs.values()))
        print(region, "all model files identical across frozen x2 / overlay x2:", res[region]["all_identical"], flush=True)
    json.dump(res, open(os.path.join(T.RESULTS, "g1_replay.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
