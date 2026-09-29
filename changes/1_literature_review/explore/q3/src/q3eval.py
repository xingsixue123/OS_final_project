"""Q3 verdict per PROTOCOL.md (held-out only):
  (1) Against Baleen: config mean P100 < Baleen online mean P100 on >= 4 of 6 held-out instances.
  (2) Average margin: mean_i (Baleen_i - config_i) > 2 SE of the difference.
      Primary SE (as harness_eval): retrain noise, SE = sqrt(sum_i (s_c,i^2/n_c,i + s_b,i^2/n_b,i)) / 6.
      Also reported: instance-level SE = sd_i(diff_i)/sqrt(6) (between-instance variation), and the one-sided
      paired t over instances.
  (3) Against the baselines: mean_i config_i < mean_i RejectX_i and < mean_i CoinFlip_i.
All retrains are used; only matched-WR rows count (unmatched rows are reported and excluded, per PROTOCOL rule 4).
  q3eval.py [--stage heldout] [--configs A B C]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

X = os.environ.get("X_ROOT", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
HELDOUT = [f"{r}_s{s}" for r in ["Region7", "Region6"] for s in ["0.1", "0.2", "0.3"]]


def evaluate(trials, base, cfg, instances=HELDOUT):
    rows = []
    for inst in instances:
        t = trials[(trials.config == cfg) & (trials.instance == inst)]
        tm = t[t.matched]
        b = base[(base.instance == inst) & (base.method == "Baleen") & base.matched]
        rx = base[(base.instance == inst) & (base.method == "RejectX") & base.matched]
        cf = base[(base.instance == inst) & (base.method == "CoinFlip") & base.matched]
        r = dict(instance=inst, n=len(tm), n_unmatched=len(t) - len(tm), p100=tm.p100.mean(),
                 sd=tm.p100.std(ddof=1) if len(tm) > 1 else np.nan, per_rep=", ".join(f"{v:.2f}" for v in tm.p100),
                 baleen=b.p100.mean(), baleen_sd=b.p100.std(ddof=1) if len(b) > 1 else np.nan, n_baleen=len(b),
                 rejectx=rx.p100.mean(), coinflip=cf.p100.mean())
        r["diff"] = r["baleen"] - r["p100"]
        rows.append(r)
    d = pd.DataFrame(rows)
    ok = d.dropna(subset=["p100", "baleen"])
    k = len(ok)
    wins = int((ok.p100 < ok.baleen).sum())
    mean_imp = float(ok["diff"].mean()) if k else np.nan
    var = ((ok.sd.fillna(0) ** 2) / ok.n.clip(lower=1) + (ok.baleen_sd.fillna(0) ** 2) / ok.n_baleen.clip(lower=1)).sum()
    se_retrain = float(np.sqrt(var)) / max(k, 1)
    se_inst = float(ok["diff"].std(ddof=1) / np.sqrt(k)) if k > 1 else np.nan
    crit1 = wins >= 4
    crit2 = mean_imp > 2 * se_retrain
    crit3 = bool(ok.p100.mean() < ok.rejectx.mean() and ok.p100.mean() < ok.coinflip.mean())
    summ = dict(config=cfg, instances=k, wins_vs_baleen=wins, mean_improvement=mean_imp, se_retrain=se_retrain,
                se_instance=se_inst, t_instance=mean_imp / se_inst if se_inst and se_inst > 0 else np.nan,
                mean_p100=float(ok.p100.mean()), mean_baleen=float(ok.baleen.mean()),
                mean_rejectx=float(ok.rejectx.mean()), mean_coinflip=float(ok.coinflip.mean()),
                crit1_4of6=crit1, crit2_margin_2se=crit2, crit3_below_rejectx_coinflip=crit3,
                crit2_instance_se=bool(mean_imp > 2 * se_inst) if se_inst == se_inst else None,
                Q3_pass=bool(crit1 and crit2 and crit3 and k == 6))
    return d, summ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="heldout")
    ap.add_argument("--configs", nargs="*")
    o = ap.parse_args()
    trials = pd.read_csv(os.path.join(X, "q3", "trials.csv"))
    trials = trials[trials.stage == o.stage]
    base = pd.read_csv(os.path.join(X, "common", "baselines.csv"))
    base["matched"] = base["matched"].astype(bool)
    trials["matched"] = trials["matched"].astype(bool)
    cfgs = o.configs or list(dict.fromkeys(trials.config))
    out = []
    pd.set_option("display.width", 250)
    for c in cfgs:
        d, s = evaluate(trials, base, c)
        print(f"\n=== {c}\n" + d.round(3).to_string(index=False))
        print(json.dumps(s, indent=1, default=float))
        out.append(s)
    pd.DataFrame(out).to_csv(os.path.join(X, "q3", "results", f"q3eval_{o.stage}.csv"), index=False)
    # markdown for RESULTS.md
    md = []
    for c in cfgs:
        d, s = evaluate(trials, base, c)
        md.append(f"\n**{c}** (held-out, 3 retrains per instance; P100 util %, matched WR only)\n")
        md.append("| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | "
                  "RejectX | CoinFlip | win vs Baleen |")
        md.append("|" + "---|" * 9)
        for _, r in d.iterrows():
            md.append(f"| {r.instance} | {r.n}/{r.n + r.n_unmatched} | {r.p100:.2f} +- {r.sd:.2f} | {r.per_rep} | "
                      f"{r.baleen:.2f} +- {r.baleen_sd:.2f} | {r['diff']:+.2f} | {r.rejectx:.2f} | {r.coinflip:.2f} | "
                      f"{'yes' if r.p100 < r.baleen else 'no'} |")
        md.append(f"\nCriteria: wins {s['wins_vs_baleen']}/6 (need >= 4) -> {'PASS' if s['crit1_4of6'] else 'FAIL'}; "
                  f"mean improvement {s['mean_improvement']:+.3f} vs 2 SE = {2 * s['se_retrain']:.3f} (retrain SE; "
                  f"instance-level 2 SE = {2 * s['se_instance']:.3f}) -> {'PASS' if s['crit2_margin_2se'] else 'FAIL'}; "
                  f"mean P100 {s['mean_p100']:.2f} vs RejectX {s['mean_rejectx']:.2f} / CoinFlip {s['mean_coinflip']:.2f} -> "
                  f"{'PASS' if s['crit3_below_rejectx_coinflip'] else 'FAIL'}. **Q3 for {c}: {'YES' if s['Q3_pass'] else 'NO'}**")
    open(os.path.join(X, "q3", "results", f"q3eval_{o.stage}.md"), "w").write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
