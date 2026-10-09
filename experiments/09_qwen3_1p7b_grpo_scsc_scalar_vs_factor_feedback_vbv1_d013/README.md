# Qwen3 1.7B reinforcement learning with scalar versus factored smooth feedback

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/README.md>

**TLDR:** Authorized by Brando on 10-08-2026 for overnight execution. This exploratory three-arm study holds the model, optimizer and two-turn rollout contract fixed: a strict conjunctive binary reward versus the smooth geometric-mean reward, then the same smooth reward with its named factors disclosed. No improvement is measured yet.

## Goal and decision

Does partial-credit reward improve a model, and does disclosing the factor vector improve it further? The first contrast is B minus A; the second is C minus B. Preserve the task-by-factor matrix beside the strict desired outcome, including before/after values and regressions. This tests model-weight updates, with a common no-feedback held-out evaluation; the separate repair experiment tests inference-time actionability.

| Arm | Terminal training reward | First-turn feedback |
|---|---|---|
| A | 1 only if all three factors equal 1 | Smooth scalar, strict outcome bit, common compiler text |
| B | Same three factors' geometric mean | Identical to A |
| C | Same geometric mean as B | Same as B plus the three named factors |

Factors are implementation correctness via examples (`IC_tests`), fraction of kernel-accepted stated proofs (`IC_proofs`), and validated formal specification coverage (`FSC`). The only smooth aggregate is `(IC_tests * IC_proofs * FSC)^(1/3)`, with the repository's extraction/compile/vacuity gates. FSC requires the existing validated automated judge, not human labels. This is not a comparison of kernel-only binary reward with a newly added coverage objective.

## Inputs and boundaries

Use the completed full-schedule Qwen3 Base 1.7B supervised fine-tuning export from `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`, selected by its fixed final training step, not validation performance. This is a new exploratory initialization and is not a claim that the older study's cross-size readiness gate passed. The D-013 split remains train 539 / validation 135 / test 222; no validation/test text or references enter training or training-judge payloads. Earlier experiments with all-VeriBench holdout rules remain unchanged.

Use the already installed, verified NeMo RL runtime if its real two-turn/scoring integration passes controls. Do not substitute a different optimizer or silently relabel a local implementation as GRPO or CoDaPO. CoDaPO is a separate future optimizer factor, not this comparison.

## Execution and evidence

[Protocol](PROTOCOL.md), [remote runbook](expt_v1/cc.md), [live results](results.md), and [checkpoint](expt_v1/CKPT_e09.md). Experiment-specific code, source pins, configuration, manifests, tests and summaries live in `expt_v1/`. Raw responses and checkpoint weights stay in the recorded private cluster runtime.

A successful scientific outcome requires a positive paired held-out gain under the frozen analysis, with missingness and coverage/proof guards disclosed. Two seeds and a short overnight horizon are exploratory; a completed training run alone does not establish improvement. A failed differentiation/technical gate is reported with all planned trajectories unrun, not disguised as a negative learning result.

Status: AUTHORIZED; remote implementation and executable preflight pending.
