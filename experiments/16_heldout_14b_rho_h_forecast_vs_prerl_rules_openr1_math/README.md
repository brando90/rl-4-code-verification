# Held-out 14B forecast versus pre-RL rules

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/16_heldout_14b_rho_h_forecast_vs_prerl_rules_openr1_math/README.md>

**TLDR:** Andrew Zhou's steer was that the ρ–H environment-utility law has to predict an experiment it was not fit on, and that the claim has to stay inside what that test shows. This experiment scores the paper's already-published 14B math forecast against rules that use only the pre-RL measurements. The law picks the same environment as "highest coverage" and does not beat it. A Lean forecast for a later unseen scale is frozen with its outcome still unmeasured.

## Why this experiment

Andrew Zhou, 10-18-2026, on the ICLR 2027 submission "Which Environments Should LLMs Learn From?":

- Scaling laws are no longer novel by themselves. Usefulness has to be the contribution.
- The result that would matter is a law that predicts the outcome of an experiment it has not seen. He thinks that is valuable for agentic reinforcement-learning post-training and for recursive self-improvement on particular environments.
- Reviewers may say the experiments are not solid enough. Check carefully and do not overclaim.

The Q&A doc already uses Q2 for a different question (what a state is). This experiment is the response to his steer. Doc: <https://docs.google.com/document/d/1KfC2G6E5xR_i5rI7QKN34qlnml3CszcHc6Kc4xKvkJc/edit>

## What was scored

The paper fit equation 7 on OpenR1-Math at 1.7B, 4B, and 8B, then predicted 14B before those outcomes were used in the fit. Those 14B outcomes are already in the paper and in `tests/test_utility_model.py`. This folder does not pretend to have sealed them again. It asks a narrower question: on that one published unseen scale, does the law choose a better environment than rules that look only at usable signal density (ρ) or effective coverage (H) measured before reinforcement learning?

## Verdict

**No allocation gain over highest H.** Equation 7 and "pick the cell with the highest H" both choose HL at 8, 16, and 24 million generated tokens. Allocation regret is 0.287 percentage points for both. Picking the highest ρ chooses HH and has regret 4.423 percentage points. A uniform choice has regret 2.717 percentage points. The law's full ordering of the four cells is more accurate than ranking by H alone (0.778 versus 0.611), but that extra accuracy is among the cells it does not select. Details: [results.md](results.md).

## What this does not show

It does not show that scaling laws are a new idea. It does not show that the law predicts agentic post-training or recursive self-improvement. It does not show a gain on Lean or on VeriBench. The panel is four environments and three budgets in one math setting. The Lean prediction is frozen and unmeasured: [forecasts/lean_02b_unseen_scale.json](forecasts/lean_02b_unseen_scale.json).
