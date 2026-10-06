# Factor feedback for real repository repair

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/README.md>

**TLDR:** Test whether exposing separate public diagnostics helps a model resolve real SWE-bench Lite issues at a fixed repair budget. The diagnostic geometric mean is a new proxy; the official issue-resolution outcome remains separate and hidden. This extension is authorized to proceed alongside the ongoing VeriBench experiments.

Created: 10-05-2026. Paper inclusion: UNDECIDED until results exist.

## Question and why it matters

Azalia's suggestion becomes a falsifiable intervention here: can a decomposed metric help choose a better next edit, rather than merely correlate with success? A model can preserve existing behavior while missing the requested behavior, or implement the requested behavior while introducing regressions. A single score can conceal that distinction. The experiment measures whether communicating the distinction helps on the benchmark's separate tests.

SWE-bench Lite supplies real repository issues with a reproducible official evaluator. Its eight-task validation pilot is small enough to test the complete measurement path. The decision to expand depends on measurement validity and feedback usefulness, not a statistically significant result from eight tasks. [Sources and alternatives](SOURCES_AND_DESIGN.md) compare SWE-bench Verified, Terminal-Bench 2.1 and LiveCodeBench. The initial implementation uses bounded code context and patch responses; it is not a leaderboard-equivalent unrestricted agent run.

## Method

1. Freeze eight validation tasks by identifier hash from the pinned 23-task validation population, named `dev` upstream. Preserve every selected task, including setup failures.
2. Build public checks solely from issue text and the base repository. Freeze checks and source context before generating candidate patches. Keep gold patches, official test patches and official test identifiers in a separate evaluator store.
3. Generate one initial patch per task. Fork the same patch into ordinary public test feedback, scalar-only diagnostic feedback, and scalar-plus-component feedback. Each receives two repair responses with the same model and limits.
4. Freeze every final patch before official scoring. Compare the fraction of resolved issues across paired conditions, with all missing results and costs reported.
5. Use validation to fix measurement defects. Freeze any changed procedure in a new version before touching the proposed 24-task test panel.

The three proposed components are execution viability, preservation of existing public tests, and passing independent issue-derived public checks. They measure observable behavior; they do not assert proof correctness or formal specification coverage. We do not rename them Smooth Conjunctive Score for Code verification (SCSC). The raw-log baseline is essential: a vector beating an information-poor scalar alone would not establish value beyond ordinary debugging.

## Connection to the thesis and environment scaling

The thesis claim would be that interpretable evaluation supports useful actions across settings. The VeriBench experiment tests that idea for verified artifacts; this experiment tests it for repository repairs against an independent outcome. Positive correlation is secondary evidence. The central result is the paired intervention under a declared budget.

After the feedback comparison, a separate prospective environment study can compare environments that expose binary public-test rewards, their geometric mean, or the component vector to a fixed controller. To connect this to Varun's work, measure usable signal density and effective coverage before training, freeze the forecast, then compare equal-compute training on screened external repositories. Keep SWE-bench test tasks and their derived checks out of training, tuning and checkpoint selection. Changes in feedback available to a fixed model are test-time scaling; model weight updates are reinforcement learning. This first version performs no training.

For Terminal-Bench, the corresponding future factors would be command/runtime viability, preservation of required artifacts or services, and task-specific behavioral checks. These must be defined per task family and validated against the official verifier. Do not claim that arbitrary terminal tasks share SWE-bench's factors. A new version or experiment must pin the then-current release, task resources and hidden verifier isolation.

## Structure and dependencies

```text
README.md                     rationale and research sequence
SOURCES_AND_DESIGN.md          official sources, pins and alternatives
PROTOCOL.md                   pilot design and admission conditions
results.md                    live progress and measured results
expt_v1/cc.md                  remote execution runbook
expt_v1/dispatch_manifest.json ownership, resource bounds and recovery
expt_v1/scripts/               deterministic preparation and analysis
expt_v1/results/               published manifests and result receipts
```

Dependencies are the pinned SWE-bench harness and dataset, isolated Docker execution, authenticated subscription command-line model access, and a verified public-only feedback path. No Qwen evaluation result is required. The existing experiment04 worker and Qwen worker retain their own checkouts and jobs.

| Stage | Status | Evidence |
|---|---|---|
| Target and source selection | Done | Official source note |
| Public/evaluator manifest separation | Implementing | Version1 scripts |
| Eight-task environment and reference controls | Pending remote execution | Full denominator must remain eight |
| Public diagnostic checks | Pending | Frozen before candidates |
| Three-condition repair comparison | Pending admission | 56 solver responses maximum |
| Proposed 24-task test confirmation | Planned | New frozen version after validation |
| Environment scaling or reinforcement learning | Planned | Separate forecast and training budget required |

See [live results](results.md), [protocol](PROTOCOL.md) and [execution prompt](expt_v1/cc.md).
