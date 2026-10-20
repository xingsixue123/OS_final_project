"""AR union: pre-train the F1-label X models (labels.py + PolicyPeakBaleen4) for the given dev instances / retrains."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402
C.configure("dev")
C.LOGS = os.path.join(C.W, "logs")
sys.path.insert(0, C.WORK)
import union as U  # noqa: E402

for inst in sys.argv[1].split(","):
    assert inst in C.DEV and inst not in C.DEV8 and inst not in C.FORBIDDEN_DEV
    for lab in ("F1PT", "F1CPSAT"):
        for k in (1, 2, 3):
            r = U.x_model(U.B.spec(f"XA:{lab}", inst, k))
            print(inst, lab, k, r["key"], round(r.get("secs") or 0, 1), flush=True)
