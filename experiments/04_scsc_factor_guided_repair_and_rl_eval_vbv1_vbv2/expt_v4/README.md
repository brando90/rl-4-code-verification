# Draft generic Lean adapter for independent reference outcomes

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v4/README.md>

**TLDR:** Develop an evaluator that can connect general Lean candidate programs to fixed external requirements without exposing reference solutions or weakening proof trust. Version 3 remains failed at 0/24 supported tasks. This is a draft engineering plan, not an admitted experiment; its new model-call budget is zero.

Created: 10-06-2026. Status: DRAFT / NOT_ADMITTED. No external measurement, repair or training is launched by this document.

## Decision and existing evidence

The consequential uncertainty is whether a mechanical adapter can preserve both the candidate's meaning and the identity of independent requirements across arbitrary Lean interfaces. The [version-3 result](../expt_v3/results.md) shows that the existing natural-number-to-natural-number candidate language cannot answer that question for the frozen external panel. Passing [24 authored controls](../expt_v2/endpoint_validation/results_2026-10-06T0734Z_reconciliation.json) validates only the restricted checker.

The first implementation should support a clearly declared subset of pure Lean declarations. Unsupported signatures stay unsupported. It must not attempt arbitrary specification equivalence or treat failed proof search as a counterexample. The existing 24-task external panel remains a development/validation record after its outcomes were inspected; it cannot be relabeled an untouched confirmation set.

## Mechanical adapter contract

1. **Declaration lookup and identity.** Use Lean's parsed and elaborated declarations to record the implementation name, fully qualified namespace, declaration type, universe parameters, explicit and implicit arguments, type-class arguments, and source hash. Avoid regular-expression replacement of arbitrary Lean source. Freeze the expected interface from public task metadata before inspecting a generated candidate.
2. **Namespaces and dependencies.** Compile candidate and evaluator modules in separate namespaces and workspaces. Record imports and dependency hashes, reject collisions with evaluator names, and prevent candidates from importing the reference implementation, reference proofs, evaluator files or private requirements. Required public data types may be shared through a separately hashed interface module that contains no reference implementation.
3. **Type and interface mapping.** Generate an explicit wrapper only when Lean can verify a meaning-preserving mapping between the candidate interface and the fixed public interface. Preserve argument order, preconditions, outputs and dependent types. Reject unsupported polymorphism, recursion interfaces, state or effects with a reason; do not replace an unsupported task with an easier one.
4. **Fixed requirements.** Keep reference tests and theorem statements in evaluator storage. Bind the mapped candidate into the fixed requirement harness without editing those requirements or importing a solved reference as a candidate dependency. Hash every candidate, interface mapping and requirement identifier. A wrapper that changes the intended domain is not a valid adapter.
5. **Proof trust and non-vacuity.** Inspect transitive kernel axioms for every claimed proved theorem under the pinned scorer; only `propext`, `Classical.choice` and `Quot.sound` are allowed. Reject `sorry`, `admit`, declared axioms and forbidden native-decision trust. Check satisfiable preconditions and witnessed inputs where the supported task family permits it; empty domains, contradictory assumptions and unestablished non-vacuity remain explicit failures or unknowns. Compilation alone is insufficient.
6. **Outcome accounting.** Separate candidate compilation failure, valid behavioral failure, valid proved obligation, unsupported mapping, reference failure and evaluator infrastructure failure. Unknown, unsupported or infrastructure-invalid endpoints remain null in the declared denominator. A zero score must correspond to a valid evaluated failure, never a missing measurement.

## Cheapest checks before external measurement

Use authored deterministic fixtures to cover overloaded names, nested namespaces, implicit arguments, multiple public types, helper dependencies, type mismatch, namespace collision, unsupported interfaces, an honest proof, transitive `sorryAx`, and a vacuous precondition. Verify that changing a candidate can change the evaluated outcome while all requirement hashes stay fixed. Verify that reference source and private requirement bytes cannot enter candidate inputs or accessible files. These checks test an implementation; they are not evidence of feedback efficacy.

A later remote validation must freeze the complete source and cell manifest, adapter/scorer/toolchain/dependency hashes, per-command and total resource limits, output paths, missing-cell reasons and one-writer recovery rules before compiling its declared external set. Positive controls use unchanged accepted references; negative controls are separately hashed, witnessed mutations in evaluator storage, never edits to benchmark references. The previous 20/24 applicability criterion is retained as the proposed minimum, but this draft does not freeze or launch a new panel. Record the final criterion and its engineering rationale before new outcomes.

## Accepted reference and lineage gates

The solved-reference alternative is not yet an accepted pool: only 6/24 inspected original reference theorems were kernel-honest under the pinned environment; 16/24 used forbidden trust and 2/24 were unknown after compilation failure. An adapter alone cannot make those references accepted.

Inventory existing solved sources with exact repository and dataset revisions, licenses, original task lineage and immutable reference hashes. Exclude HumanEval-derived tasks, VeriSoftBench-derived tasks when VeriBench version 2 is a target, and other known shared-source lineage with VeriBench. Apply both normalized exact-hash and word-five-gram screens against the pinned protected corpus. Textual non-overlap does not override known lineage overlap.

Freeze the full eligible candidate population and a hash-selected validation panel before acceptance outcomes; retain compile and trust failures rather than taking the first tasks that pass. Every accepted reference needs pinned Lean compilation, allowed-axiom and non-vacuity evidence. Existing candidate partitions of 141 train / 24 validation / 24 test remain candidate-only. If an original reference needs changing, stop that route and use a separately authorized reference-acceptance process; this version grants no permission to edit references.

## Budget and later admission

- New author, solver, judge, reference-generation and training calls admitted: **0**. No graphics processors are allocated. The earlier continuation's exhausted attempts and resource use are not reset.
- Current scope is a reviewable design. Any external validation run needs a separate, prospectively recorded execution budget and complete manifest; no commands here implicitly launch it.
- Repair needs accepted references, a validated independent endpoint, frozen feedback/aggregation rules, exact solver and judge pins, a fresh call/resource admission and full missing-cell accounting. The earlier 192 repair cells remain unmeasured.
- Training additionally requires the [experiment02 readiness dependencies](../../02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/results/training_readiness_manifest_2026-10-06.json): verified executable Lean training code/configuration, immutable model revision, measured pre-training probes and throughput, and a numeric forecast frozen before any outcome it predicts. No forecast is invented to satisfy a gate.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] The generic-adapter draft specifies the next independent-outcome engineering work while preserving failed applicability evidence and a zero new model-call budget.
**Snapshot:**
```text
version=expt_v4; status=DRAFT_NOT_ADMITTED
existing_authored_controls=24/24 matching
existing_external_applicability=0/24; prior_gate=20/24
accepted_external_pool=not_established
new_model_call_budget=0; graphics_processors_allocated=0
training=NOT_ADMITTED; forecast=NOT_FROZEN
```
