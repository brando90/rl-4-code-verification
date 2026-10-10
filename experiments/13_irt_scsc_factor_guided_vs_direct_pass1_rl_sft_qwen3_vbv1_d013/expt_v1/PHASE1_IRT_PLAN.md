# Experiment 13 Phase 1: identifiable conditional item response models

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/PHASE1_IRT_PLAN.md>

**TLDR:** Use conditional hurdle probabilities to predict later strict outcomes without using their response factors. Fit training rewards separately on train-only anchors; exact scorer factors already determine strict success.

`../PROTOCOL.md` §4 is the binding model specification and gate. Implement it before L1 and hash the implementation/library/config.

Deliverables: grouped fold manifest; training-only preprocessing receipts; M0/M1/M2/M3/M3e predictions for identical outer-held-out cells; per-component risk-set counts; five fixed-start convergence/sensitivity results; simulation recovery; G1 report with bias, absolute error and intervals. Freeze candidate selection in inner folds; do not choose M3/M3e on outer performance. Do not estimate held-out policy ability or task residuals from their target labels. Base-model compute uses `log1p`, not log zero.

The conjunctive likelihood contains extraction/presence/vacuity, conditional compilation and conditional all-theorem honesty. Declaration fractions and all-proofs indicators are overlapping measurements; do not multiply their unconditional probabilities or double-count them in a likelihood. Observed candidate declaration counts are not an immutable rubric. Interpret component abilities only when recovery and prior-sensitivity checks support them.

Arm C requires a separate connected train anchor panel with at least three policies, fixed item parameters, identified scale and strictly positive normalized gradient weights. It optimizes a weighted partial reward, not `P(strict | all current factors)`. The latter is deterministic and would collapse back to strict. Current ability updates use only previous train rollouts; fixed weights apply throughout each prompt group.

The reference literature supports fitting item-response models, not identification from one policy or causal reinforcement-learning improvement here. See `SOURCE_EVIDENCE.json` for verified source links. The cited rubric paper uses a scalar rubric-quality model; it is not a validation of this conjunctive Lean reward. Record this distinction in any result.

G1, independent H2 and C's variance check all gate C; their failure leaves the eligible A/B/P comparison and the failed forecasts visible. No fitted validation parameters or reference text enter the train reward.
