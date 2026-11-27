"""Amended experiment 14 H2 replay comparison for a numpy other than the locked 2.2.6 pin.

The locked analyzer's exact equality is unchanged. This helper is the comparison a rerun
uses when the pin in requirements-locked-rerun-11-27-2026.txt cannot be installed.
"""
from __future__ import annotations

# Published replay in expt_v1/results/results_tables_e14.md, e07_h2_reproduction.
PUBLISHED = {
    "25": {"delta_median": -0.009360066473104778, "positive_splits": 391},
    "50": {"delta_median": -0.012138953190928725, "positive_splits": 92},
    "100": {"delta_median": -0.012941050463773973, "positive_splits": 7},
    "250": {"delta_median": -0.012669847666142708, "positive_splits": 0},
}
PINNED_NUMPY = "2.2.6"
PINNED_SCIPY = "1.16.3"
# Wider than the numpy 2.5.3 sixth-decimal drift (~1.2e-6 at n_A = 50) and tighter than 1e-4.
MEDIAN_ATOL = 5e-6


def replay_matches(replayed: dict, *, numpy_version: str, atol: float = MEDIAN_ATOL) -> dict:
    """Return whether each published H2 size matches, and which comparison was applied."""
    mode = "exact" if numpy_version == PINNED_NUMPY else "tolerance"
    rows = {}
    ok = True
    for key, published in PUBLISHED.items():
        got = replayed[key]
        splits_ok = int(got["positive_splits"]) == int(published["positive_splits"])
        if mode == "exact":
            median_ok = float(got["delta_median"]) == float(published["delta_median"])
        else:
            median_ok = abs(float(got["delta_median"]) - float(published["delta_median"])) <= atol
        rows[key] = {"median_ok": median_ok, "positive_splits_ok": splits_ok}
        ok = ok and median_ok and splits_ok
    return {"ok": ok, "mode": mode, "atol": 0.0 if mode == "exact" else atol, "sizes": rows}
