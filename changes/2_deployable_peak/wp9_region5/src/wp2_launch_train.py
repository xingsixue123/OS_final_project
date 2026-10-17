"""Entry module for WP2 trainings: register PolicyPeakBaleen4 (label files), then the overlay's unmodified train.main()
(cwd = wp2_deployed/work, BCacheSim -> the reviewed overlay). Stock Baleen arms (A/B) use the authors' policy."""
import pb4_policy
from BCacheSim.episodic_analysis import train

if __name__ == "__main__":
    pb4_policy.register()
    train.main()
