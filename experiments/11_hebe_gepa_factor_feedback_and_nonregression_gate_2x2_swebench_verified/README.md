# Experiment 11: AlphaHebe self-improvement with per-item factor feedback and a non-regression promotion gate (2×2) on SWE-bench Verified

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md>

**TLDR:** This is the live version of the 10-08-2026 meeting's idea. AlphaHebe optimizes an AlphaDiana agent harness on SWE-bench Verified, crossing two changes in a 2×2 design:

- **Feedback:** the optimizer sees per-task factor vectors (patch gate, FAIL_TO_PASS fraction, PASS_TO_PASS fraction) instead of one score per task.
- **Promotion:** edits are accepted only if they do not regress items, instead of on any scalar improvement.

The outcome is the held-out test pass@1 and the regressions of the final promoted harness. The experiment is designed, not run, and **blocked**. It needs read access to AlphaDiana-dev and AlphaApollo-v3-dev, three AlphaHebe/AlphaDiana changes tracked as issues, GPU (D-101) or Valkyrie (D-108) approval, and [experiment 10](../10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md)'s verdict to fix the gate arm.

Created: 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando. Owners:

- **Brando:** design, analysis, this repository.
- **AlphaHebe / AlphaDiana team:** the integration issues on [`AndrewZhou924/AlphaHebe-dev`](https://github.com/AndrewZhou924/AlphaHebe-dev/issues).

## Origin

- [10-08-2026 meeting](../meetings/oct_7_2026/oct_7_2026.md) and its [whiteboard](../meetings/oct_7_2026/self_improving_with_factored_decomposed_smooth_metric_meeting_pic.md). The loop is Diana measures S_t → Hebe proposes an edit δ_t to the model, harness or prompts → the edited agent A_{t+1} is measured again. Two problems were raised:
  1. localizing an error to the model or the harness;
  2. regressions on previously solved tasks.

  Brando's proposal: give the improver the task × factor matrix, and accept only edits that do not regress.
- Brando, 10-09-2026: "see if the SCSC type factorized matrix per item can guide alpha-hebe diana apollo system to self improve."

## What AlphaHebe does today (AlphaHebe-dev@f89294e)

| Hook | Today | Change tested here |
|---|---|---|
| Optimizer feedback: `integrations/diana/search_feedback.py::TrainingFeedback` | `{per_task: mean score, traces}` | Add an allowlisted per-task `factors` vector, with no test names, test contents or gold patch |
| Promotion: `control/promotion.py::gate_decision` | Promote iff `candidate.score > incumbent.score` on the promotion envelope | Non-regression gate: the scalar improvement must hold **and** per-item regressions (binary, or factor mass, per experiment 10) stay within a fixed bound |
| Evidence: `evidence/execution.py::ExecutionEvidence` | `score`, per-record `rewards` and `successes` | Per-record factor vectors kept on the private side for the promotion gate |
| Diana SWE-bench scorer (AlphaDiana-dev, not readable yet) | `resolved` per task (to be verified) | Emit `patch_applied`, FAIL_TO_PASS passed/total and PASS_TO_PASS passed/total per record |

## Goal, hypotheses and decision criterion

The design is a 2×2 crossing of **feedback** {per-task scalar (A·0), per-task factor vector (A·1)} with **gate** {scalar strict (A0·), non-regression (A1·)}. The arms are:

- A00: the current AlphaHebe;
- A10: factor feedback only;
- A01: non-regression gate only;
- A11: both.

Everything else is fixed: the artifact (the harness system prompt, optimized by AlphaHebe's GEPA workflow), the solver model and harness, the reflection model, the search and promotion budgets, and the task splits.

| ID | Question | Prediction (to freeze in PROTOCOL) |
|---|---|---|
| H1 | Does factor feedback raise held-out test pass@1 of the final artifact (A10 versus A00)? | Δ ≥ +2 points, task-bootstrap interval excluding 0 |
| H2 | Does the non-regression gate reduce held-out test losses (tasks the baseline solved that the final artifact fails) without lowering pass@1 (A01 versus A00)? | Losses −30% or more, pass@1 Δ ≥ −1 point |
| H3 | Are the two additive (A11 versus A10 and A01)? | Reported |

**What follows:**

- **Positive:** make factor feedback and the gate AlphaHebe defaults upstream, then repeat on VeriBench V1 with SCSC factors under the D-013 split (train for search, validation for promotion, test once).
- **Null:** report it. Per-item factors then do not guide prompt-level self-improvement at this scale, and model-level edits (CoDaPO, GRPO) are tested separately.

## Design sketch (finalized in PROTOCOL.md after the technical gates)

- **Tasks:** a fixed, repository-stratified split of the 500 SWE-bench Verified tasks into search (50), promotion (50) and test (200), with the rest unused. The seed and manifest are published before any run.
  - The test split is evaluated once per final artifact, plus the baseline.
  - The 07/10 analyses used public logs, not these runs.
- **Solver:** one open-weight model behind a fixed AlphaDiana harness (OpenCode or ZeroClaw), served by vLLM on SNAP (D-101). The exact Hugging Face revision is pinned at admission.
  - **Reflection/proposer:** AlphaHebe's improver model (Qwen3.6 30B A3B on the whiteboard) self-hosted, or a Valkyrie model (D-108).
  - **Keys:** no provider keys in `.env` (agents-config Hard Rule 9).
- **Budget:** per run, a fixed number of GEPA trials and a fixed token budget, identical across arms; 3 seeds per arm, so 12 runs. The size is set from the technical-gate pilot's measured cost, then approved by Brando.
- **Analysis:** task-level paired comparisons of each final artifact against the baseline on the test split. Intervals use a task bootstrap, with seeds as replicates. Every declared cell has a receipt; infrastructure retries rerun the identical cell.

## Technical gates (all must pass before admission)

| Gate | Check |
|---|---|
| T0 | `brando90` can read AlphaDiana-dev and AlphaApollo-v3-dev; AlphaHebe installs with the pinned submodule (`alphadiana@3bdbb66`) and passes its own test suite |
| T1 | The AlphaDiana SWE-bench Verified run on 5 tasks emits per-record factor fields. Controls: gold patch → resolved and all factors 1 (5/5); empty patch → gate 0 (5/5) |
| T2 | Leakage audit: the factor projection to the optimizer contains no test identifiers, test source, gold patch or ground truth |
| T3 | The pluggable promotion gate reproduces experiment 10's G0, G2 and G3 decisions on synthetic evidence (unit tests) |
| T4 | The solver and proposer are served by vLLM with immutable revisions recorded; no provider key is read; Valkyrie only under D-108 |
| T5 | Dry run: 2 GEPA trials end to end on 5 search + 5 promotion tasks; records replay with `alphahebe.integrations.diana.replay` |
| T6 | Measured per-episode cost → full manifest estimate → Brando's GPU/Valkyrie approval |

## Integration issues (assigned to the AlphaHebe / AlphaDiana team)

These are filed on `AndrewZhou924/AlphaHebe-dev`; links go in [results.md](results.md) once created.

1. AlphaDiana SWE-bench scorer: emit per-record factor fields (T1).
2. AlphaHebe `TrainingFeedback`: an optional allowlisted per-task `factors` projection plus a configuration switch for the ablation (T2).
3. AlphaHebe promotion: a pluggable gate (`scalar_strict` default, `binary_non_regression`, `factor_non_regression`) with recorded per-item reasons (T3).
4. Export per-task incumbent/candidate records from existing GEPA and Meta-Harness runs, for experiment 10 phase B (zero new model calls).
5. Document an OpenAI-compatible self-hosted endpoint path with an immutable model version for these runs (T4).

## Structure

| Path | Content |
|---|---|
| `PROTOCOL.md` | Written after T0–T5 and experiment 10's verdict; locked before T6 approval |
| [results.md](results.md) | Live ledger: gate status, issue links, receipts |
| `expt_v1/` | Runbooks, manifests and results, once admitted |

## Dependencies

- Experiment 10 (gate arm choice).
- `AndrewZhou924/AlphaHebe-dev` (pin `f89294e`), AlphaDiana-dev (pin `3bdbb66`, access pending), AlphaApollo-v3-dev (optional training backend, access pending).
- SNAP GPUs (D-101) and/or Valkyrie (D-108).
- Related work: [AlphaApollo, AlphaDiana and Hebe](../../docs/related_work/README.md).

## Status

BLOCKED (10-09-2026): T0 access pending; issues 1–3 open; no approval requested yet for GPUs or Valkyrie.
