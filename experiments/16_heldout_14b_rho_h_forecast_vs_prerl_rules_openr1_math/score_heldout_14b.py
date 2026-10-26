#!/usr/bin/env python3
"""Score the paper's already-published 14B forecast against pre-RL environment rules.

The 14B utilities were public before this script. It does not create a new sealed
forecast of those utilities. The prospective Lean forecast is a separate frozen file.
"""
from __future__ import annotations

import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from rl4cv.forecast import freeze_forecast
from rl4cv.utility_model import (
    Observation,
    allocation_regret,
    feature_rule,
    fixed_label_rule,
    model_rule,
    pairwise_rank_accuracy,
    paper_frozen_14b_model,
    uniform_portfolio_regret,
)

# Paper Table 5, 14B row, and Table 4 panel A. Utilities are percentage points.
TABLE5_14B = {"HH": (29.13, 0.743), "HL": (18.63, 0.776), "LH": (5.24, 0.183), "LL": (2.94, 0.149)}
OBS14 = {
    8: {"HH": -0.23, "HL": 2.61, "LH": -1.16, "LL": 2.28},
    16: {"HH": -3.01, "HL": 2.92, "LH": -0.56, "LL": 3.78},
    24: {"HH": -0.11, "HL": 3.53, "LH": -2.76, "LL": -0.21},
}
ENVS = ("HH", "HL", "LH", "LL")
HERE = Path(__file__).resolve().parent


def observations() -> list[Observation]:
    return [
        Observation(14.0, env, float(budget), utility / 100, *TABLE5_14B[env])
        for budget, row in OBS14.items()
        for env, utility in row.items()
    ]


def permutation_rank_p(model, obs, observed_rank: float) -> dict:
    """Exact null: reassign the four utilities inside each budget; keep each cell's rho and H."""
    utilities = {(o.budget, o.env): o.utility for o in obs}
    budgets = sorted({o.budget for o in obs})
    at_least = 0
    total = 0
    for perms in itertools.product(itertools.permutations(ENVS), repeat=len(budgets)):
        shuffled = []
        for budget, perm in zip(budgets, perms):
            for env, source in zip(ENVS, perm):
                rho, coverage = TABLE5_14B[env]
                shuffled.append(Observation(14.0, env, budget, utilities[(budget, source)], rho, coverage))
        rank = pairwise_rank_accuracy(shuffled, [model.predict_obs(o) for o in shuffled])
        total += 1
        if rank + 1e-12 >= observed_rank:
            at_least += 1
    return {"at_least_as_extreme": at_least, "total": total, "p": at_least / total}


def score() -> dict:
    obs = observations()
    model = paper_frozen_14b_model()
    predictions = [model.predict_obs(o) for o in obs]
    utilities = np.array([o.utility for o in obs])
    rmse_pp = 100 * float(np.sqrt(np.mean((np.array(predictions) - utilities) ** 2)))
    rank = pairwise_rank_accuracy(obs, predictions)
    rules = {
        "rho_H_equation_7": model_rule(model),
        "fixed_HL": fixed_label_rule("HL"),
        "max_rho": feature_rule(lambda o: o.rho),
        "max_H": feature_rule(lambda o: o.H),
        "max_rho_times_H": feature_rule(lambda o: o.rho * o.H),
    }
    choices = {}
    groups = defaultdict(list)
    for item in obs:
        groups[item.budget].append(item)
    out_rules = {}
    for name, rule in rules.items():
        out_rules[name] = {
            "rank_accuracy": pairwise_rank_accuracy(obs, predictions if name == "rho_H_equation_7" else [
                {"max_rho": o.rho, "max_H": o.H, "max_rho_times_H": o.rho * o.H, "fixed_HL": 1.0 if o.env == "HL" else 0.0}[name]
                for o in obs
            ]),
            "regret_percentage_points": 100 * allocation_regret(obs, rule),
            "choice_by_budget_million_tokens": {str(budget): rule(group) for budget, group in sorted(groups.items())},
        }
        choices[name] = out_rules[name]["choice_by_budget_million_tokens"]
    return {
        "domain": "OpenR1-Math",
        "held_out_scale": "14B",
        "fit_scales": ["1.7B", "4B", "8B"],
        "n_environments": 4,
        "n_budgets": 3,
        "n_points": len(obs),
        "outcomes_already_published": True,
        "rmse_percentage_points": rmse_pp,
        "rank_accuracy": rank,
        "rank_pairs": 18,
        "uniform_regret_percentage_points": 100 * uniform_portfolio_regret(obs),
        "environment_order": sorted(ENVS, key=lambda env: -model.env_term(*TABLE5_14B[env])),
        "rules": out_rules,
        "choices": choices,
        "rank_permutation": permutation_rank_p(model, obs, rank),
        "permutation_null": "reassign the four observed utilities to the four cells inside each budget; rho and H stay with the cell",
        "api_spend_usd": 0,
    }


def main() -> None:
    payload = score()
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / "heldout_14b_scores.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    freeze_forecast(
        {
            "experiment": "16_heldout_14b_rho_h_forecast_vs_prerl_rules_openr1_math",
            "target": "Lean code-verification RL, experiment 02B, first unseen scale after a Lean fit",
            "status": "UNMEASURED",
            "rule": (
                "After rho and H are measured before RL, fit equation 7 on the earlier Lean scales only. "
                "Freeze that model before reading the later scale. The later scale is useful evidence only if "
                "its allocation regret is lower than max-H, max-rho, and a uniform choice. Matching max-H is not a gain."
            ),
            "not_claimed": [
                "scaling laws are novel",
                "agentic RL post-training",
                "recursive self-improvement",
                "a VeriBench test-split gain",
            ],
            "math_14b_study": "already published; scored separately; not this forecast",
        },
        HERE / "forecasts",
        "lean_02b_unseen_scale",
        outcomes_observed=False,
    )
    print(json.dumps({k: payload[k] for k in ("rmse_percentage_points", "rank_accuracy", "rank_permutation")}, indent=2))


if __name__ == "__main__":
    main()
