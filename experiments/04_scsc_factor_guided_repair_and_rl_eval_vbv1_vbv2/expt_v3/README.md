# Execute the external factor feedback repair pilot

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v3/README.md>

**TLDR:** This version implements the first real external-data repair comparison after the independent checker passes its controls. It compares identical starting artifacts and solver budgets with ordinary verifier feedback, an aggregate score, or its components; no VeriBench task is used to develop the controller.

## Scope and execution order

The user authorized execution on 10-05-2026. The completed `expt_v1` audit stays frozen. The restricted synthetic controls in `expt_v2` test checker engineering only; they do not establish applicability to general Lean programs. This version must additionally validate the checker on existing external references before admitting repair calls.

1. Run all `expt_v2` controls on the pinned Lean 4.22 toolchain and retain every receipt.
2. Reuse the screened external source prepared by `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2`. Freeze a 24-task panel by source hash, before generated outcomes; preserve unsupported adapters in the denominator. Do not substitute authored toy examples for this panel.
3. Implement and validate mechanical callable-interface adapters, fixed reference tests, fixed reference obligations, and transitive-axiom inspection. Use existing accepted references and witnessed implementation mutations. A reference that does not compile or is untrusted is not silently fixed or relabeled.
4. Freeze the exact run protocol, task/cell manifest, prompts, model revision, judge route, cost limits and runtime hashes before inference. The bounds below are ceilings for the initial admission, not a fabricated completed protocol.
5. Execute the entire admitted panel, analyze paired outcomes, and publish execution counts separately from scientific outcomes.

### Source feasibility discovered before measurement

The inspected FVAPPS export has specifications and tests but no solved-Lean field: [official export schema](https://github.com/quinn-dougherty/fvapps/blob/6f2f56c29c4f7c2cb409e0fedf3430953404023e/src/benchmark/postprocessing/jsonl.py). Its `solve` stubs cannot serve as accepted positive controls. Keep its screened panel as candidates, with that limitation.

The execution worker should inspect existing [VERINA solved references](https://github.com/sunblaze-ucb/verina/tree/66b3ce5014edafb20cb26b87c681e7f31847249f) as an alternative source for this endpoint study. Two inspected files (`verina_basic_1`, `verina_basic_15`) contain implementation and proof bodies; this is source evidence only, not Lean 4.22 acceptance. The release uses Lean 4.18. Exclude HumanEval/VeriSoftBench-derived entries and known VeriBench source-lineage matches, then apply both text screens. Freeze 24 remaining tasks by hash before compilation or model outcomes; preserve all failures. Do not silently choose the first 24 that compile. If fewer than 24 eligible tasks exist, record the population and create a separately bounded smaller protocol before any measured calls. Never use overlapping VERINA tasks merely because formatting evades the textual threshold. Pin any environment-only compatibility change; changing a theorem, implementation or proof changes the reference and is outside this run's acceptance scope.

## First admission bounds

- Panel: 24 screened external validation tasks. Four conditions: ordinary verifier diagnostics; diagnostics plus scalar Smooth Conjunctive Score for Code verification (SCSC); diagnostics plus scalar and three factors; and a predeclared shuffled-component negative control.
- One initial response per task, shared across conditions; two repair steps per condition: 24 initial + 192 repair responses, at most 216 responses and 1,769,472 generated tokens with an 8,192-token cap. No extra score-selected retries.
- Prefer the already available post-trained Qwen3-4B for the repair pilot, pin its exact public model revision before measurement. This is distinct from the running Qwen3 Base feasibility evaluation and does not wait on it. A different solver must be a separately frozen condition.
- At most one idle A100 graphics processor, 6 graphics-processor hours, and 24 processor hours for this initial external pilot. Estimate roughly 0.5–3 hours inference plus compilation/judging; actual runtime remains unmeasured. Do not reserve a graphics processor during data preparation or judging. Inspect occupancy immediately before admission.
- Use the already authorized `vb103_judge` Valkyrie route and its exact validated six-call ensemble. At most 216 distinct scored artifacts, hence at most 1,296 ensemble member calls, with caching by immutable artifact/input hash. Record the gateway's actual admission/budget evidence; no new charges, automatic top-ups or direct provider clients. Unknown payer capacity is not unlimited capacity. If that route cannot admit the full bounded pilot, complete independent checker and pool work and report the specific missing capacity.
- Every condition incurs the same diagnostic computation; reveal only its designated fields. Count input/output tokens, prover seconds, judge calls and elapsed time. Equal output caps alone do not establish equal total cost. Report the matched-budget design and observed cost differences.

## Measurement decisions

The primary independent outcome is fixed-reference tests AND certified fixed reference obligations instantiated on the candidate implementation. Report reference-test success, submitted-certificate coverage and bounded evaluator proof-search yield separately. An unsuccessful search is unknown, not a proof of falsehood. Empty requirements never pass. References and exact hidden counterexamples are evaluator-only.

For official dataset reporting, freeze the geometric mean of dataset-level factor means on a common measured cohort, matching the current paper. Per-artifact SCSC is still the geometric mean of its three factors and is what a repair controller sees. The mean of per-artifact SCSC is a separately named diagnostic. Do not change old summary files or use different factor denominators inside an unlabeled aggregate; report missingness bounds and cohort sizes. This resolves the aggregation choice prospectively, without rewriting historical evidence.

The primary paired comparison is component feedback minus scalar feedback in joint fixed-reference success after step two. Report counts, 95% task-bootstrap intervals (10,000 draws, seed 0), a paired randomization test against no benefit, missingness bounds, all factors, and observed costs. A small external pilot informs feasibility and precision; it is not confirmatory evidence on VeriBench or proof of a general benefit. No policy tuning occurs on VeriBench.

The shuffled control must preserve scalar compatibility and compilation strata; if no nontrivial matching exists, declare it unavailable before calls rather than showing an obviously contradictory vector. Do not let this optional control block the three meaningful conditions; any resulting smaller manifest must be fixed before all pilot inference and its counts/budget reported.

## Continue or stop

All applicable accepted positives and witnessed negatives must be classified as expected, no forbidden transitive axioms may be accepted, and all abstentions must be explained. Minimum practical adapter applicability is 20/24 tasks, an engineering choice fixed before outcomes. If the gate fails, finish all 24 applicability receipts and fix the specific engineering issue in a new version; do not run the causal comparison through an invalid endpoint.

After a usable external pilot, freeze the final controller before the held-out VeriBench comparison described in `../PLAN.md`. The full held-out inference and large training campaign require their own concrete manifests and bounded resource plans; this version does not claim they have run.
