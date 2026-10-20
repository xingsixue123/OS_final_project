"""AR mechanical dev step 2 (DEV_RULES R0-R2): wait for the retrain-1 screen of the candidates on DEV8, apply the
R0 screen gate, confirm at most 2 candidates (largest mean d): retrains 2-3 on DEV8 and 1-3 on Region1_s0/Region5_s0
for the candidate; then apply the finalist rule -> results/dev_finalist.json. The classical controls' confirmation
(report only; R0: controls are never candidates) is written to queue_dev2_controls.txt and run after the decision.

  source env.sh && setsid nohup src/sbx.sh src/chain_dev2.py > logs/chain_dev2.out 2>&1 &
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dev_eval as DE  # noqa: E402

H = DE.H
CANDS = {"UB:ptm": "UB:cdm", "CB:pt": "CB:cd", "CB:ptm": "CB:cdm", "CA:pt": "CA:cd", "CA:ptm": "CA:cdm"}
D8 = DE.DEV8
EXTRA = DE.EXTRA


def arm_of(name):
    return name.replace(":", "-")


def screen_done():
    t = pd.read_csv(os.path.join(H, "trials_dev.csv"))
    have = set(t.trial_key.astype(str))
    fails = t[t.trial_key.astype(str).str.contains("__FAILED_")].trial_key.str.split("__FAILED_").str[0]
    need = [f"{arm_of(c)}_baleen_{i}_r1" for c in CANDS for i in D8]
    return all(k in have or k in set(fails) for k in need)


def log(*a):
    print(f"[chain_dev2 {time.strftime('%F %T')}]", *a, flush=True)


def main():
    while not screen_done():
        time.sleep(60)
    t = DE.load()
    r1 = t[t.rep == 1]
    P = r1.pivot_table(index="inst", columns="cfg", values="p100", aggfunc="mean").reindex(D8)
    ref = np.minimum(P["A+a"], P["B+a"])
    res = []
    for c in CANDS:
        a = arm_of(c)
        if a not in P.columns or P[a].isna().any():
            res.append(dict(cand=c, complete=False, gate=False))
            continue
        d = ref - P[a]
        res.append(dict(cand=c, complete=True, mean_d=float(d.mean()), min_d=float(d.min()), wins=int((d > 0).sum()),
                        gate=bool(d.mean() > 0 and d.min() >= -2.0), mean_p100=float(P[a].mean())))
    res = sorted(res, key=lambda r: (-r.get("mean_d", -1e9), r["cand"]))
    passed = [r["cand"] for r in res if r["gate"]][:2]
    out = dict(screen=res, confirmed=passed, ref_min_alpha_mean=float(ref.mean()), ts=time.strftime("%F %T"))
    json.dump(out, open(os.path.join(H, "results", "dev_screen.json"), "w"), indent=1)
    log("screen:", json.dumps(res))
    log("confirmed:", passed)
    if not passed:
        json.dump(dict(FINALIST=None, reason="no candidate passed the R0 screen gate"),
                  open(os.path.join(H, "results", "dev_finalist.json"), "w"), indent=1)
        log("NO FINALIST (screen)")
        return
    q, qc = [], []
    for c in passed:                     # candidates first (finalist rule); controls (report only) afterwards
        q += [(c, i, r) for r in (1, 2, 3) for i in ("Region5_s0", "Region1_s0")]
        q += [(c, i, r) for r in (2, 3) for i in D8]
        x = CANDS[c]
        qc += [(x, i, r) for r in (2, 3) for i in D8] + [(x, i, r) for r in (1, 2, 3) for i in ("Region1_s0", "Region5_s0")]
    open(os.path.join(H, "queue_dev2_controls.txt"), "w").write(
        f"# control confirmation (report only; run after the finalist decision) {time.strftime('%F %T')}\n" +
        "\n".join(f"{a} {i} {r}" for a, i, r in qc) + "\n")
    qp = os.path.join(H, "queue_dev2.txt")
    open(qp, "w").write(f"# confirmation queue written by chain_dev2 {time.strftime('%F %T')}\n" +
                        "\n".join(f"{a} {i} {r}" for a, i, r in q) + "\n")
    log(f"confirmation queue: {len(q)} evaluations")
    rc = subprocess.call([sys.executable, "-B", os.path.join(H, "src", "cls.py"), "--mode", "dev", "--queue", qp, "-j", "14"])
    log("confirmation driver rc", rc)
    # the Region1_s0 / Region5_s0 references come from queue_dev1; wait until its driver has finished them
    while True:
        t = DE.load()
        n = t[t.inst.isin(EXTRA) & t.cfg.isin(["A", "B", "A+a", "B+a"])].groupby(["cfg", "inst"]).size()
        if len(n) == 8 and (n >= 3).all():
            break
        if subprocess.call(["pgrep", "-f", "queue_dev1"], stdout=subprocess.DEVNULL) != 0:
            log("queue_dev1 driver not running and Region1_s0/Region5_s0 references incomplete -> finalist on available instances")
            break
        time.sleep(120)
    fin = DE.final(DE.load(), [arm_of(c) for c in passed])
    q_ok = [r for r in fin if r.get("qualifies")]
    q_ok = sorted(q_ok, key=lambda r: (-min(r[f"{k}_mean"] for k in ("A", "B", "A+a" if "A+a_mean" in r else "B+a")), r["cfg"]))
    F = q_ok[0]["cfg"] if q_ok else None
    json.dump(dict(FINALIST=F, CONTROL=(CANDS[F.replace("-", ":", 1)].replace(":", "-") if F else None), rule=fin,
                   confirmed=passed, ts=time.strftime("%F %T")),
              open(os.path.join(H, "results", "dev_finalist.json"), "w"), indent=1, default=str)
    log("FINALIST:", F)


if __name__ == "__main__":
    main()
