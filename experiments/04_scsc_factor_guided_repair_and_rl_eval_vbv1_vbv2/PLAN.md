# Controlled tests of diagnostic feedback and environment design

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/PLAN.md>

**TLDR:** The primary causal comparison is factor-aware versus scalar-only feedback from the same starting artifacts at equal total cost. Fixed-reference outcomes test whether any score gain survives an independent acceptance rule; training studies reuse the existing environment-scaling program.

## Scientific contribution and thesis fit

The thesis can argue that interpretable metrics are useful when their structure improves a decision. This program measures the value of revealing that structure. It does not need to claim SCSC merely predicts some “real” downstream benchmark. Smooth Conjunctive Score for Code verification (SCSC) remains an evaluation target, supplemented by fixed-reference checks that test what its improvement means.

Azalia's email names three applications. The causal study below directly addresses inference-time feedback; the environment and reward studies address the other two. The 09-05-2026 thesis deck already calls for a diagnostic-guided choice versus a meaningful aggregate-score baseline, with held-out outcomes. This proposal operationalizes that intention without claiming that Azalia specified every design choice.

## Phase 0 — Retained evidence and endpoint feasibility

The locked `expt_v1` audit inventories complete/missing factors, snapshot coverage of declared cells, and old adapter/replay records. It is retrospective. No new correctness correlation or training result can be inferred from this inventory.

Next, in a separately frozen `expt_v2`, validate reference-test and fixed-obligation checking on screened **non-VeriBench** validation tasks. Proposed size: 24 tasks selected by hash within source/representation strata before outcomes, with unmodified reference implementations as positive controls and implementation-only mutations as negative controls. These are harness controls, not proposed benchmark-reference edits. Do not manufacture new accepted gold labels: use pre-existing accepted references and deterministic witnessed violations. Reference fixes require the project's separate acceptance process.

Check wrappers, domain/precondition alignment, empty requirements, renamed namespaces, alternative representations, and transitive theorem axioms. Where existing wrappers fail, label adapter-unavailable. No universal accuracy claim follows from 24 tasks. Proposed engineering gate: all positive controls and all witnessed violations classified correctly on applicable cases; no forbidden-axiom acceptance; every abstention explained. Adapter applicability must be reported without dropping hard tasks. Choose a minimum useful applicability threshold after inspecting task schemas but **before** outcome measurement; 80% is an initial design target, not an established validity threshold.

Once the harness passes, run the frozen endpoint against all declared retained VeriBench artifacts that belong to the chosen original condition, keeping missing cells visible. Evaluator work may see held-out references; controller design/tuning may not. Existing reference exposure makes these analyses retrospective; later confirmatory evidence needs untouched tasks or a new independently frozen evaluation release.

## Phase 1 — Correlation and diagnostic validity

**Question:** what extra information do components provide about fixed-reference success beyond compilation and SCSC?

Use identical candidate artifacts for both instruments. Freeze candidate hashes, model revisions, score/judge policy, task definitions and missingness handling. Publish core 614, IndustrySet 282 and each version-2 condition separately. The current full-source version-2 pilot contains five projects; do not treat modules, theorems or multiple model outputs as independent projects.

Compare externally fitted predictors: compilation only; SCSC only; the three factors; factors plus fixed source/size descriptors. A factor model has more parameters, so use regularization and external validation, not test-set fit quality. Report predictive performance and task-cluster uncertainty, as described in METRICS.md. Inspect disagreements in both directions: high SCSC but failed fixed tests, and passed fixed tests but incomplete proofs/coverage. Record the provenance and number of manually inspected examples; illustrative cases do not estimate prevalence.

If one factor is constant or scores saturate/floor, report identifiability limits and use preselected harder/easier **external validation** tasks to develop the next policy. Do not quietly select VeriBench examples that make the correlation look stronger. A near-perfect correlation is not required: the metric may capture verification quality that pass@1 misses.

## Phase 2 — Fixed budget inference-time repair

**Primary hypothesis:** access to factor values enables a frozen controller to improve independently checked success, compared with scalar-only feedback, from the same initial artifact at the same total budget.

Develop and freeze controller prompts on contamination-screened external train/validation tasks. Final VeriBench is test-only. Benchmark evaluation with a frozen inference policy is allowed; changing that policy after reading test scores is not. Coverage feedback visible to the solver must be limited to the frozen information condition (numbers or approved generic categories), never hidden reference statements or gold counterexamples.

| Condition | Information delivered after each step | Role |
|---|---|---|
| Ordinary verifier feedback | Compiler and allowed proof-checker diagnostics | Strong practical baseline |
| Scalar feedback | Same diagnostics plus SCSC only | Main information control |
| Component feedback | Same diagnostics plus the three factor values and SCSC | Primary intervention; controller chooses its next edit |
| Shuffled component feedback | Same diagnostics and scalar; component vector reassigned within predeclared strata | Negative control for extra prompt length and feedback presence |
| Component-targeted instruction | Same real vector plus frozen test/proof/coverage-specific repair instruction | Secondary action-policy ablation |

The primary comparison is component versus scalar feedback. Distinguish numeric information from natural-language advice; otherwise improvement could be due to a better prompt rather than interpretability. The baseline must remain strong: aggregate feedback with full compiler diagnostics, equal generation opportunities and equal solver capacity.

For each task, start every condition from the **same saved initial artifact**. Randomize condition execution order and repair seeds, isolate contexts and file systems, and blind final evaluators to condition labels. Preserve the initial artifact hash. No condition sees another condition's output or hidden outcome. A simple controller attempts compilation repair first if needed, proof repair when coverage is adequate but proofs fail, and requirement repair when coverage is weak; exact thresholds and tie-breaking must be fitted externally and frozen, not guessed from VeriBench results.

**Proposed feasibility budget, not an admitted run:** 24 external validation tasks × 4 primary conditions × 2 repair steps = 192 solver calls; at an 8,192 output-token cap, at most 1,572,864 solver output tokens, plus input/judge/tool costs. The secondary targeted-instruction condition is deferred until the main comparison is stable. A proposed 100-task held-out pilot with two paired seeds would require 1,600 calls and at most 13,107,200 output tokens under the same settings. These are arithmetic upper bounds, not spend quotations or runtime measurements. The test manifest, actual model/effort, tool limits, verifier/judge calls, provider cost and full completion budget must be frozen before admission. Never call a 100-task pilot the full benchmark.

For the main comparison, compute all diagnostics for both scalar and component conditions but reveal only permitted fields; this isolates information at equal diagnostic cost. A separate practical-budget comparison can let the ordinary baseline spend its saved diagnostic cost on generation. Report generated tokens, input tokens, wall time, tool calls, prover time, judge cost and total authorized charges. Token matching alone is not cost matching when judging differs. No best-of-retries selection: the final submitted artifact follows the frozen policy.

**Outcomes:** official SCSC with all factors and denominators; fixed-reference test success; fixed-obligation certification yield; joint reference-verified success; number of newly invalidated requirements; cost per additional certified task. Resolve the historical aggregation mismatch identified in README before freezing a new score experiment. Primary effect is paired change in joint success for component minus scalar feedback; secondary score changes cannot substitute for that effect.

**Decision rule, proposed:** a 95% task-cluster interval whose lower bound exceeds zero supports benefit on the declared panel; a two-percentage-point absolute gain is an agent-suggested practical target, not a proven threshold. Compare that target with actual cost. Predeclare a paired randomization test against no benefit, and report its p-value; if adding comparisons, use a Holm correction for secondary confirmatory tests. Always report effect size and interval. With few projects or rare positives, report inconclusive results rather than a powered claim. Estimate precision from external data before locking final sample size. No optional stopping on significance.

Bootstrap whole tasks with all associated model/seed/condition observations kept together; evaluate training variability separately. A five-project version-2 panel is descriptive evidence with limited precision, not a population-wide significance claim. Preserve failures, unknown endpoints, interrupted generation and missing scores in the full manifest. Publish complete-case summaries as diagnostics plus explicit missingness bounds for binary success, never as the full-population estimate.

## Phase 3 — Environment design with Varun

Reuse `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics`, particularly its pool/probe and reward-channel phases. The new question is whether diagnosing the target skill profile helps choose the environment whose learning signal produces the right held-out improvement. All diagnostic profiles used for design come from screened external validation data; VeriBench final scores cannot choose the environment.

Environment axes should manipulate the required skill: implementation/testing, proving a fixed specification, constructing a sufficiently strong specification, and full verified-code tasks. Within each family, control task difficulty, source, prompt length, success rate, budget and model initialization as far as feasible. Otherwise “factor-aware” may just mean easier data. Include a uniform mixture, a simple fixed-family choice and the best externally validated scalar-only selection rule.

From the existing implementation, for group sample j of prompt i, leave-one-out advantage is reward minus the other samples' mean. Let admitted advantage mass be `m_i = sum_j admitted_ij * |a_ij|`.

- Usable signal density `rho = 10^6 * sum_i m_i / total_generated_tokens` measures available training signal per million tokens.
- Effective coverage `H = (sum_i m_i)^2 / (n * sum_i m_i^2)` measures how broadly that mass spans prompts; zero mass gives zero coverage.

This yields two different questions: rho/H predict **how much usable signal** an environment supplies; factor-specific outcomes test **which verification skill improves**. Add a directional target-alignment hypothesis only as a separately frozen extension; do not silently refit the existing law after seeing final test outcomes.

Multiplying rewards by a positive constant multiplies rho and leaves H unchanged under this implementation. Therefore freeze reward ranges/scales and report unnormalized and any prespecified normalized probes; higher rho alone cannot rank reward semantics. Random reward noise can produce advantage mass without useful learning. Use held-out improvement to test utility.

Use `rl4cv.forecast.freeze_forecast` before reading the outcome each forecast predicts. Refitting on small-scale external validation results is permitted only in the predeclared chronology. Preserve unsuccessful forecasts. The `rl-env-scaling` source pin is provisional pending verification of Varun's submission code/configs; no current scaling-law result is claimed from local placeholder documents.

## Phase 4 — Rewards and verifier reliability

Reuse the four channels already proposed in `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge`: kernel binary reward, proof-fraction reward, compile-gated formal specification coverage, and SCSC. Add component-targeted scheduling only after those baselines are stable. Identical training prompts, initialization, generated-action-token budgets and paired random seeds isolate reward differences.

Reinforcement learning (RL) can exploit mutable denominators by deleting hard theorems, adding trivial ones, weakening preconditions or inflating judged coverage on invalid code. Fixed-reference obligations, nonempty requirements, strict transitive proof checks and endpoint audits are required to detect these behaviors. Reward checks run on non-VeriBench training pools. If the full SCSC reward is zero almost everywhere, test decomposed tasks or warm starts already planned in the pool experiment; do not loosen the verifier.

The latest Stanford notes propose corrupting **training** verifier rewards and evaluating with a trusted held-out verifier. As a bounded later ablation, vary false-positive and false-negative rates independently while keeping final evaluation unchanged. The relation `observed success = true success*(1-FNR) + (1-true success)*FPR` is a measurement identity under the stated rates, not a prediction of learning dynamics. It helps separate reward quality from density. Keep this as a versioned extension, not a prerequisite for the first repair study.

## Thesis deliverables and claim limits

A thesis section can contain: (1) the distinction between aggregate validity and actionable diagnosis; (2) a table defining outcomes and their trust limits; (3) fixed-budget repair curves for scalar versus component information; (4) factor transition/failure-mode tables; (5) environment/reward selection results linked to rho/H forecasts; and (6) negative findings and contamination controls.

A positive repair result would support “the decomposition improved decisions under this budget and panel.” It would not prove universal interpretability, formal correctness of every generated program, or transfer to SWE-bench. A negative result can show that compiler feedback already supplies the useful information, that the judge is too noisy, or that the controller cannot act on the factor diagnosis. Separate those explanations with the ablations.

**Minimum coherent thesis contribution:** a validated auxiliary measurement plus a controlled repair comparison, even if the training extension is inconclusive. **Stronger contribution:** diagnosis-guided environment selection with a frozen successful held-out forecast and improved final verification. No manuscript, abstract or result claim is being changed at this planning stage.

## Milestones and stopping rules

| Milestone | Deliverable | Continue or redirect |
|---|---|---|
| Existing-artifact audit | Frozen inputs, full snapshot accounting, endpoint availability verdict | If endpoints absent, validate harness; do not compute a circular substitute |
| External harness validation | Accepted controls, per-case statuses and applicability | Repair interface/trust failures before measured comparisons |
| External controller validation | Frozen prompts, exact model/revisions, budget and cell manifest | If no usable signal, use existing warm-start/pool work |
| Held-out repair comparison | Full declared receipts, paired effects, factors and independent outcomes | If only SCSC rises, report restricted metric benefit or exploitation |
| Environment/reward comparison | Frozen forecasts, matched trajectories, independent final evaluation | Stop scaling a recipe if its validation evidence does not justify the cost |

Earliest cost-efficient route is the retained-artifact audit, then endpoint engineering, then feedback comparison. Training does not start merely because a document is complete. Existing authorization covers implementation and bounded useful work; new charges, scientific pins and budget ceilings remain binding. Use supported authenticated command-line interfaces for model work and do not author direct provider calls.
