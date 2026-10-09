# Experiment 11: AlphaHebe self-improvement with per-item factor feedback and a non-regression promotion gate (2×2) on SWE-bench Verified

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md>

**TLDR:** This is the live version of the 10-08-2026 meeting's idea. AlphaHebe optimizes an AlphaDiana agent harness on SWE-bench Verified in a 2×2 design:

- **Feedback:** per-task factor vectors (patch gate, FAIL_TO_PASS fraction, PASS_TO_PASS fraction) instead of one score per task.
- **Promotion:** accept an edit only if it does not regress items, instead of on any scalar improvement.

The outcome is the untouched-test pass@1 and the regressions of the final harness. The design is revised per the GPT-6 Astra (effort ultra) review. The experiment is **blocked**:

- read access to AlphaDiana-dev is pending;
- integration issues [#27–#30](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/26) are open;
- the model route is still unverified. Brando, 10-09-2026: "use valks for model calls".

Created 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando. Owners:

- **Brando:** design, analysis, this repository.
- **AlphaHebe / AlphaDiana team:** the integration issues on [`AndrewZhou924/AlphaHebe-dev#26`](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/26).

## Origin

- [10-08-2026 meeting](../meetings/oct_7_2026/oct_7_2026.md) and its [whiteboard](../meetings/oct_7_2026/self_improving_with_factored_decomposed_smooth_metric_meeting_pic.md). The loop is Diana measures S_t → Hebe proposes an edit δ_t to the model, harness or prompts → the edited agent A_{t+1} is measured again. Two problems were raised:
  1. localizing an error to the model or the harness;
  2. regressions on previously solved tasks.

  Brando's proposal: give the improver the task × factor matrix, and accept only edits that do not regress.
- Brando, 10-09-2026: "see if the SCSC type factorized matrix per item can guide alpha-hebe diana apollo system to self improve."

## What AlphaHebe does today (AlphaHebe-dev@f89294e)

| Hook | Today | Change tested here (issue) |
|---|---|---|
| Optimizer feedback: `integrations/diana/search_feedback.py::TrainingFeedback` | `{per_task: mean score, traces}` | Optional allowlisted per-task factor vector from training-envelope records only, behind a switch ([#28](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/28)) |
| Promotion: `control/promotion.py::gate_decision` | Promote iff `candidate.score > incumbent.score` | Pluggable non-regression gate on keyed per-item evidence ([#29](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/29)) |
| Evidence: `evidence/execution.py::ExecutionEvidence` | Flat `rewards`/`successes`, task keys discarded after validation | Immutable `(task_id, sample_index)` records with factor numerators and denominators, missingness and scorer/test-set identity (#29) |
| Diana SWE-bench scorer (AlphaDiana-dev, not readable yet) | `resolved` only; the public proxy discards the report's per-test status | `patch_applied`, FAIL_TO_PASS and PASS_TO_PASS passed/total per record; infrastructure errors stay missing ([#27](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/27)) |

## Goal, hypotheses and decision criterion

Arms are labeled A{feedback}{promotion}, so the first digit is feedback and the second is promotion:

| | Scalar strict promotion (…0) | Non-regression promotion (…1) |
|---|---|---|
| **Per-task scalar feedback (A0…)** | A00 (AlphaHebe today) | A01 |
| **Per-task factor feedback (A1…)** | A10 | A11 |

- **What is held fixed:** the artifact (the harness system prompt, optimized by AlphaHebe's GEPA workflow), the scalar fitness, the base prompt, traces, their ordering and truncation, the call ceilings, the outer-loop count, the candidate selection, the promotion opportunities and the stopping rule. Only the factor dictionary (feedback) or the gate (promotion) changes.
- **What feedback can change:** GEPA's workflow adapter gives the engine one aggregate example (`methods/gepa/workflow.py`). Per-task factors influence reflection; they do not create a per-task Pareto objective.
- **Promotion gate:** binary non-regression, provisional. A factor gate replaces it only if experiment 10's verdict recommends one and a fixed-bound threshold is calibrated separately.

| ID | Question | Prediction (to freeze in PROTOCOL) |
|---|---|---|
| H1 | Does factor feedback raise untouched-test pass@1 of the final artifact (A10 versus A00)? | Δ ≥ +2 points, interval excluding 0 |
| H2 | Does the non-regression gate cut untouched-test losses (baseline-solved tasks the final artifact fails) without lowering pass@1 (A01 versus A00)? | Losses −30% or more, pass@1 Δ ≥ −1 point |
| H3 | Interaction, A11 − A10 − A01 + A00 | Reported |

**What follows:**

- **Positive:** make factor feedback and the gate AlphaHebe defaults upstream, then repeat on VeriBench V1 with SCSC factors under decision D-013's 539/135/222 split.
- **Null or inconclusive:** report it. Three seeds are a pilot minimum, not a power guarantee, so an inconclusive verdict is pre-declared.

## Design (finalized in PROTOCOL.md after the technical gates)

- **Tasks:** a repository-stratified split of the 500 SWE-bench Verified tasks into 100 training (search), 100 validation (promotion) and 300 untouched test, grouping duplicate families.
  - Controls are confined to the training split. The manifests are frozen before any pilot outcome.
  - The test split is evaluated once per final artifact and for the baseline.
  - If promotion happens repeatedly during search, the validation data is reused adaptively, which is why the untouched test split decides.
  - SWE-bench Verified is public, so this is not a pristine unseen-task study.
- **Models and route (Brando, 10-09-2026: "use valks for model calls"):**
  - Model calls go through Vals Valkyrie (D-108). Gate T4 below must verify the route.
  - The harness being optimized is the object of study, so D-108's "vendor's strongest agent" rule cannot apply to the solver; this needs a recorded exception like D-014 before the protocol is frozen.
  - Open-weight solver weights that Valkyrie cannot serve fall back to self-hosted vLLM on SNAP (D-101).
  - Candidate solver: the team's #14 baseline target (Qwen3.6-35B-A3B on the Pi harness), so that their pipeline is reused. The base-model choice for VeriBench RL is a separate open question.
  - No provider keys in `.env`.
- **Budget:** identical across arms. 3 paired seeds per arm (12 runs) as a feasibility minimum. A synthetic power and precision calculation goes into the protocol.
  - Totals are recorded for solver, reflection and evaluation tokens, calls, retries, caching and wall time.
  - Replay re-executes services, so it counts against the budget.
- **Analysis:** report each seed. Paired task-level contrasts against the baseline use task-bootstrap intervals that condition on the realized optimizations, plus seed-level contrasts. Every declared cell has a receipt; infrastructure retries rerun the identical cell.

## Technical gates (each must pass before admission; the pilot is admitted separately from the full run)

| Gate | Check |
|---|---|
| T0 | `brando90` can read AlphaDiana-dev (requested from Andrew 10-09-2026). AlphaHebe installs with the pinned submodule (`alphadiana@3bdbb66`) in a clean environment and passes its suite. The actual container processor, memory, build-time and storage limits are verified. AlphaApollo-v3-dev is optional for this prompt path and does not block it |
| T1 | Per-record factor fields from issue #27, with controls kept as separate records: gold patch → resolved and factors 1; empty patch → gate 0 (counts null); unchanged base; malformed patch; partial fix; a regression; an infrastructure error, which stays missing and is never a scored zero. Native logs are inspected |
| T2 | Leakage audit of the **complete** optimizer-visible input (reflection prompt, traces, readable files, logs, replay payloads), using canary strings in hidden tests and a negative control. Only training-envelope aggregate feedback is permitted |
| T3 | Keyed evidence and gate controls from issue #29: shuffled, missing, duplicate, stale and mismatched records; equivalence of the default gate with today's rule; zero-acceptance cases |
| T4 | Model route verified. Valkyrie (or vLLM for open weights) is reachable from the containers for the solver and separately for reflection, with immutable model versions, the credential source and the payer recorded. An OpenAI-compatible address alone proves none of these |
| T5 | A frozen, authorized pilot: 2 GEPA trials end to end on 5 training and 5 validation tasks, with real resume and cleanup exercised and records replayed |
| T6 | Measured pilot cost → full manifest estimate → full-run approval. T6 cannot retroactively authorize T5 |

These gates answer the failures seen in experiments [06](../06_swebench_lite_factor_feedback_matched_budget/results.md) (evaluator controls) and [09](../09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/results.md) (backend mismatch): unit tests alone did not establish a working measured path.

## Structure

| Path | Content |
|---|---|
| `PROTOCOL.md` | Written after T0–T5 and experiment 10's verdict; locked before T6 |
| [results.md](results.md) | Live ledger: gate status, issue links, receipts |
| `expt_v1/` | Runbooks, manifests and results, once admitted |

## Dependencies

- Experiment 10's gate verdict.
- [`AndrewZhou924/AlphaHebe-dev`](https://github.com/AndrewZhou924/AlphaHebe-dev) (pin `f89294e`; issues #26–#30); AlphaDiana-dev (pin `3bdbb66`, access requested); AlphaApollo-v3-dev (optional).
- Valkyrie (D-108) and/or SNAP GPUs (D-101).
- Related work: [AlphaApollo, AlphaDiana and Hebe](../../docs/related_work/README.md). Design review: [GPT-6 Astra (effort ultra)](../10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/design_review_gpt6_astra_ultra_10-09-2026.md), findings 10–14.

## Status

BLOCKED (10-09-2026):

- T0: AlphaDiana-dev access requested from Andrew by email.
- Issues #27–#30 open and assigned.
- T4: the Valkyrie route is not yet verified.
