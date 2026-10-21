"""TLDR: Refuse measured stage execution until the uncertified-token importance correction is specified."""
from admission import OBJECTIVE_BLOCKER


class LocalEngine:
    """Explicit measured-adapter boundary; never substitute synthetic measurements.

    The stage controller and stub implement the full CPU sequence. The measured
    adapter remains unadmitted: its update cannot consume nullable generator
    probabilities under the frozen installed loss. Finishing the generation /
    scorer / checkpoint adapter is required after the master resolves that rule.
    """
    synthetic=False

    def __init__(self, work, admission):
        raise RuntimeError('Measured runner unavailable: '+OBJECTIVE_BLOCKER)
