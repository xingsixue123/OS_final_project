"""Track B entry module (SCOPE.md §1): register PolicyQ2 into policies.__dict__, then call the UNMODIFIED
BCacheSim.episodic_analysis.train.main() with the usual arguments (+ --policy PolicyQ2). Config via Q2_POLICY_CONFIG."""
import q2policy
from BCacheSim.episodic_analysis import train

if __name__ == "__main__":
    q2policy.register()
    train.main()
