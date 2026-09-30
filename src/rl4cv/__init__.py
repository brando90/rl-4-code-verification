"""rl4cv: measure RL environments for code verification before RL and predict their held-out utility.

Modules:
    experience     usable signal density rho and effective coverage H from probe groups
    utility_model  the compact environment-utility model (Eq. 7), leave-one-scale-out metrics
    forecast       prospective forecast freezing with SHA-256 hashes
    cells          policy-relative 2x2 environment construction (group signal x admission/cost)
    rewards        reward channels computed from VeriBench-style per-response scores
    veribench      adapters for VeriBench tasks, generation, extraction and scoring
"""

__version__ = "0.1.0"
