"""Our own entry module (SCOPE.md §1), copied from harness_eval/src/launch_train.py: register PolicyPeakBaleen3 into
policies.__dict__, then call the UNMODIFIED BCacheSim.episodic_analysis.train.main() with the usual arguments.

  cd <work> && taskset -c 8-23 bwrap ... $BALEEN_PY -B -m launch_train <train.py args> --policy PolicyPeakBaleen3
Policy configuration is passed via the env var HE_POLICY_CONFIG (json file); nothing else is patched.
"""
import pb3_policy
from BCacheSim.episodic_analysis import train

if __name__ == "__main__":
    pb3_policy.register()
    train.main()
