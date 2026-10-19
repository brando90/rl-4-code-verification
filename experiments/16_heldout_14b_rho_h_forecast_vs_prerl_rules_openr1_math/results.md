# Held-out 14B scores

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/16_heldout_14b_rho_h_forecast_vs_prerl_rules_openr1_math/results.md>

**TLDR:** On the paper's already-published 14B math scale, the ρ–H law chooses HL, the same environment as highest effective coverage. Regret is 0.287 percentage points either way. Highest usable signal density chooses HH and is worse. The Lean forecast is frozen and unmeasured.

**Status:** SCORED for the published 14B panel. **Lean forecast:** UNMEASURED. **Last updated:** 10-18-2026. **Spend:** $0.

The fit used 1.7B, 4B, and 8B. The scored panel is 14B, four environments, three budgets (8, 16, and 24 million generated tokens), 12 points, 18 environment pairs. Utilities are pass@1 change from the warm start, in percentage points. Machine-readable scores: [results/heldout_14b_scores.json](results/heldout_14b_scores.json).

| Rule | Environment chosen | Rank accuracy | Allocation regret (percentage points) |
|---|---|---:|---:|
| Equation 7, frozen ρ–H model | HL at all three budgets | 0.778 (14/18) | 0.287 |
| Highest H | HL at all three budgets | 0.611 | 0.287 |
| Fixed label HL | HL at all three budgets | 0.694 | 0.287 |
| Highest ρ | HH at all three budgets | 0.444 | 4.423 |
| Highest ρ×H | HH at all three budgets | 0.444 | 4.423 |
| Uniform choice | — | — | 2.717 |

Root mean squared error of equation 7 is 2.291 percentage points. The paper reports 2.29 and regret 0.288; the 0.001-point difference is the rounded Table 4 inputs.

The predicted order is HL, HH, LL, LH. Against the null that reassigns the four utilities inside each budget, 520 of 13,824 assignments match or beat the observed rank accuracy, so p-val=0.0376. The null is that enumeration. It is not a confidence interval for a new domain, and p-val is not against "correlation is zero."

**Verdict.** No allocation gain over highest H on this panel. The law's higher rank accuracy orders the environments it does not select. Highest ρ, which is the raw signal-density rule, selects the worse cell.

**Not shown.** Agentic post-training, recursive self-improvement, Lean, and VeriBench are unmeasured here. Scaling laws are not claimed to be a new idea.

The Lean rule is frozen at `forecasts/lean_02b_unseen_scale.json`, sha256 `36bdb2cc596625f69c2584a98e5c99701bb6bea6d8b63279f3b0bc62ecb388c2`, with no Lean outcome attached.

**TLDR-end:** [rl4cv: held-out 14B environment forecast] Equation 7 matches highest-H on the published 14B math panel and does not beat it; the Lean forecast remains unmeasured.
