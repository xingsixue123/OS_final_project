"""print the classical solver (lp, milp, cpsat, ls) with the lowest deval mean objective at budget argv[1] (dev only)"""
import os, sys
import pandas as pd
AREA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = float(sys.argv[1])
t = pd.read_csv(os.path.join(AREA, "trials.csv"))
d = t[(t.phase == "deval") & (t.status == "ok") & (t.budget == b) & (t.solver.isin(["lp", "milp", "cpsat", "ls"]))]
print(d.groupby("solver").objective.mean().idxmin())
