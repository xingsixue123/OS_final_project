"""Our own entry module (SCOPE.md §1): register PolicyPeakBaleen into policies.__dict__, then call the
UNMODIFIED BCacheSim.episodic_analysis.train.main() with the usual arguments.

  cd H/work && bwrap ... $BALEEN_PY -B -m launch_train <train.py args> --policy PolicyPeakBaleen
Policy configuration is passed via the env var HE_POLICY_CONFIG (json file); nothing else is patched.
"""
import peakbaleen_policy
from BCacheSim.episodic_analysis import train

if __name__ == "__main__":
    peakbaleen_policy.register()
    train.main()
