"""The published 14B panel: equation 7 ties highest-H and beats highest-rho on regret."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments/16_heldout_14b_rho_h_forecast_vs_prerl_rules_openr1_math"))

from score_heldout_14b import score  # noqa: E402


def test_equation_7_ties_highest_h_and_beats_highest_rho():
    payload = score()
    rules = payload["rules"]
    assert abs(payload["rmse_percentage_points"] - 2.2912412573305936) < 1e-9
    assert rules["rho_H_equation_7"]["regret_percentage_points"] == rules["max_H"]["regret_percentage_points"]
    assert rules["rho_H_equation_7"]["choice_by_budget_million_tokens"] == rules["max_H"]["choice_by_budget_million_tokens"]
    assert rules["max_rho"]["regret_percentage_points"] > rules["rho_H_equation_7"]["regret_percentage_points"]
    assert payload["rank_permutation"]["at_least_as_extreme"] == 520
    assert payload["rank_permutation"]["total"] == 13824
