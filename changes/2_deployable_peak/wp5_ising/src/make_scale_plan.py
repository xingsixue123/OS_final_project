"""scaling plan (WP5 step 4): REAL instances of increasing size -> scale_plan.json
  day-1 parts and full traces of Regions 4-7 samples 0-0.3 (WP1 builds), and unions of 2 / 4 disjoint 0.1% samples of
  the same trace (= real 0.2% / 0.4% samples) to go beyond the largest single 0.1% instance.
  mfsb (32 agents x 500 steps) and pt (16 replicas, 5 s) everywhere; the dense package (32 agents x 100 steps on day-1,
  50 steps on larger ones; RLIMIT_AS 64 GB) on every day-1 part, one full trace per region and the unions."""
import json, os
P2 = "/home/sxing/project/OS_final_project/changes/2_deployable_peak"
I = lambda k: os.path.join(P2, "wp1_offline", "inst", f"full_{k}.npz")
keys = [f"{r}_s{s}" for r in ("Region4", "Region5", "Region6", "Region7") for s in ("0", "0.1", "0.2", "0.3")]
keys = [k for k in keys if os.path.exists(I(k))]
plan = []
for k in keys:
    for part in ("day1", "full"):
        plan.append(dict(inst=I(k), part=part, solver="mfsb", agents=32, steps=500))
        plan.append(dict(inst=I(k), part=part, solver="pt", agents=16, moves=20000, pt_secs=5.0))
    plan.append(dict(inst=I(k), part="day1", solver="dense", agents=32, steps=100, mem_cap_gb=64))
for k in ("Region4_s0.3", "Region5_s0", "Region6_s0", "Region7_s0"):
    if os.path.exists(I(k)):
        plan.append(dict(inst=I(k), part="full", solver="dense", agents=32, steps=50, mem_cap_gb=64, timeout=3000))
unions = [["Region7_s0", "Region7_s0.1"], ["Region7_s0", "Region7_s0.1", "Region7_s0.2", "Region7_s0.3"],
          ["Region5_s0", "Region5_s0.1", "Region5_s0.2", "Region5_s0.3"]]
for u in unions:
    if all(os.path.exists(I(k)) for k in u):
        p = ",".join(I(k) for k in u)
        plan.append(dict(inst=p, part="union", solver="mfsb", agents=32, steps=500))
        plan.append(dict(inst=p, part="union", solver="pt", agents=16, moves=20000, pt_secs=5.0))
        plan.append(dict(inst=p, part="union", solver="dense", agents=32, steps=50, mem_cap_gb=64, timeout=3000))
json.dump(plan, open(os.path.join(P2, "wp5_ising", "scale_plan.json"), "w"), indent=1)
print(len(plan), "runs")
