# Protocol: held-out 14B comparison and the unmeasured Lean forecast

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/16_heldout_14b_rho_h_forecast_vs_prerl_rules_openr1_math/PROTOCOL.md>

**TLDR:** The 14B math outcomes were already published, so this protocol scores them against pre-RL rules and does not call that score a new sealed forecast. The Lean forecast is sealed before any Lean reinforcement-learning outcome exists, and it counts only if a later scale beats highest-H, highest-ρ, and a uniform choice.

## Already-published 14B comparison

- Source: paper Table 5, 14B row, and Table 4 panel A, as copied in `tests/test_utility_model.py`.
- Predictor: `paper_frozen_14b_model()`, the equation-7 coefficients fit on 1.7B, 4B, and 8B.
- Rules declared for the comparison: highest ρ, highest H, highest ρ×H, the fixed label HL, and a uniform choice.
- Allocation gain requires a strictly lower regret than highest H, highest ρ, and the uniform choice. A tie with highest H is not a gain.
- Rank accuracy uses every pair of environments inside each budget, with half credit for a tie. The null reassigns the four observed utilities inside each budget and keeps ρ and H on the cell. All 24³ assignments are counted. That null does not cover seed noise, table rounding, or another domain.
- No model calls and no GPUs.

## Unmeasured Lean forecast

`forecasts/lean_02b_unseen_scale.json` is frozen with `outcomes_observed=False`. It names the rule for experiment 02B's first unseen scale. It does not state a numeric Lean utility. Scoring it before ρ and H are measured before reinforcement learning, and before the later scale is run, is out of scope.
