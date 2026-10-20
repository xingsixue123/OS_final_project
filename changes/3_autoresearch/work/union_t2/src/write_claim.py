"""AR: write result/GOOD_RESULT_CLAIM.json (contract §5) ONLY if <test dir>/results_test/evaluation.json says
good_result = true. The deterministic validator (code/validate.py) recomputes everything from the raw rows.

  python3 src/write_claim.py --test-dir ../t1u_region2
"""
import argparse
import json
import os
import re

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.normpath(os.path.join(H, "..", ".."))                     # changes/3_autoresearch
REPO = os.path.normpath(os.path.join(ROOT, "..", ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-dir", required=True)
    o = ap.parse_args()
    td = os.path.normpath(os.path.join(os.getcwd(), o.test_dir))
    ev = json.load(open(os.path.join(td, "results_test", "evaluation.json")))
    if not ev.get("good_result"):
        print("evaluation.json: good_result is not true -> no claim written")
        return
    go = open(os.path.join(td, "TEST_GO")).read()
    commit = re.search(r"\b([0-9a-f]{7,40})\b", go).group(1)
    arms = ev["arms"]
    lab = arms["Y"].split("-")[1]
    claim = dict(
        config=f"{arms['Y']}: union admission (Baleen's model A OR an F1 peak-label model X, kappa = theta_X*/theta_A* "
               f"from the training day{', X gated to load >= day-1 q75' if arms['Y'].startswith('XG') else ''}), "
               "alpha = -1 load-adaptive threshold, overlay v5 (SCOPE amendment 1.2d)",
        ising_component=f"labels of the second admission model: the F1 min-max day-1 peak episode-selection QUBO "
                        f"(phase-1/WP2 formulation) solved by parallel tempering ({lab})",
        classical_control_arm=arms["control"],
        test_dir=os.path.relpath(td, REPO),
        protocol_commit=commit,
        trials_csv=os.path.relpath(os.path.join(td, "trials_test.csv"), REPO),
        arm_names=arms,
        static_baselines_csv=os.path.relpath(os.path.join(td, "results_test", "static_baselines.csv"), REPO))
    out = os.path.join(ROOT, "result", "GOOD_RESULT_CLAIM.json")
    json.dump(claim, open(out, "w"), indent=1)
    print("claim written:", out)
    print(json.dumps(claim, indent=1))


if __name__ == "__main__":
    main()
