# Version 3 proposal: validate environments before factor-feedback repair

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v3/README.md>

**TLDR:** Prepare a new validation experiment that fixes the measurement path before testing whether decomposed feedback improves independent issue resolution. This is a draft proposal, not an admitted run: no further model calls, evaluator retries or training are authorized by this file. Preserve the version 2 failures and all eight selected tasks.

Created: 10-06-2026. Status: DRAFT, NOT FROZEN, NOT ADMITTED.

## Decision and scientific scope

[p 10/10] Repair evaluator environments and diagnostic transport first. Version 2 has only 2/8 valid official control pairs against its 6/8 engineering threshold, and 1/8 structurally accepted diagnostic bundles against its separate 6/8 threshold. Seven control cells aborted during imports, two have ambiguous fixture failures and two unchanged-base cells exhausted retries. These failures prevent a meaningful repair comparison. Details and immutable evidence hashes are in the [control audit](../expt_v2/results/official_evaluator_controls.md) and [diagnostic audit](../expt_v2/results/diagnostic_rejection_audit.md).

The question remains whether separate factors guide better edits at a matched budget and improve the hidden official endpoint. Increasing the geometric mean alone does not establish this claim. The factors are execution viability, preservation of public regression tests and public issue-check success; they are a coding proxy, not VeriBench's Smooth Conjunctive Score for Code verification (SCSC).

The eight-task panel is development/validation only. Its earlier outcomes have been inspected; neither environment repair nor a second validation pass is an untouched test result. Do not replace difficult tasks or claim this version was preregistered before the version 2 evidence. Later confirmation requires an independently frozen test panel.

## Stage 0: explicit admission and reproducible setup

Before any execution, freeze a new protocol and machine-readable manifest with:

- The unchanged eight-task public panel SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`, dataset revision `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`, harness commit `f7bbbb2ccdf479001d6467c9e34af59e44a840f9`, exact base commits and all original null cells.
- A separate runtime, fresh run identifiers including version/task/condition/patch hash, exact runner source hashes, dependency inventories and container image digests. No source, gold patch or official test may be edited. Any necessary harness/dependency change is an explicit prospective delta; grading/test bytes must remain identical.
- A verified authenticated subscription route, actual client/model/effort and enforceable tool/output/wall limits. Proposed scientific model remains `claude-sonnet-5` at medium effort. Never substitute from quota pressure after admission. No provider-key clients or new charges.
- A named full-access remote owner, one writer, an ordinary-code supervisor, completion and failure receipts, and a newly approved coordinator allowance. The old second/final Vals attempt has ended and supplies no automatic launch reserve.

## Stage 1: environment validity before model calls

Use a setup-only sandbox to establish compatible dependency versions from the pinned public repository's own installation metadata. Record exact package versions, image digests, install commands and changes. For the import-abort family, verify package imports and ordinary public test collection before official controls. For the fixture-error family, determine whether the installed test runner supports the public repository's fixture convention; the current attribution is provisional. Do not repair tests, change expected outcomes, or derive public check content from evaluator logs.

Freeze the resulting environment and empty-patch adapter before the new 16-cell gold/unchanged-base control panel. The adapter must preserve the exact base tree, admit a truly empty prediction, skip only absent candidate-patch application, and leave official test application/parser/grading bytes unchanged. No marker file. Record base-tree hashes before and after. Preserve the old two exhausted cells; new measurements belong only to the separately admitted version.

Require matching report identity, report/log hashes, observed test completion and a valid environment before interpreting a Boolean endpoint. Import/setup/collection failures, ambiguous fixture errors and absent reports remain null. A valid test failure remains false. Inspect all eight tasks, preserve every receipt, and require at least six valid gold-resolved/empty-unresolved pairs. If fewer than six pass, stop before author calls and publish the failure.

## Stage 2: prospectively freeze the public-check author and validator

Build a public-only author context from the same sealed base/issue projection. Do not use official changed-file lists, test identities or previous reference outcomes to author or select checks. Fresh tool-free invocations must have no evaluator files, inherited repository prompts, plugins, shell or network tools. Verify isolation on the actual client and retain the earlier period of permissive evaluator directory traversal as a caveat; permissions alone do not prove historical non-access.

Before author calls, commit exact prompt, transport schema, parser, synthetic test fixtures, command runner and hashes. Remove the inherited instruction requesting a unified diff from this check-author prompt. Use structured argument lists and explicit check identifiers with fixed regression/issue membership. Support quoted Python programs through argument parsing without shell evaluation; do not reject safe code merely because it contains a semicolon. Restrict execution using the sandbox and explicit allowed entry points, not a character filter alone. Reject ambiguous extra response material deterministically; never manually salvage selected responses.

Each issue check must contain an assertion whose exit status distinguishes a behavioral violation. Printing a value is insufficient. Each public regression check must pass on the unchanged public base; issue checks must reproduce the issue as an assertion failure, not an import/collection error. Declare nonempty denominators and freeze all check bytes before solver generation. Test transport and failure classification using authored synthetic fixtures before spending any author call.

Proposed budget: one fresh author response per task, at most eight total, with no model-response retries or replacement tasks. Invalid bundles stay invalid. Structural acceptance is recorded separately from public execution and behavioral validity. Require at least six tasks with both usable public diagnostics and valid official controls; a weaker aggregate count across disjoint task subsets does not pass. Do not alter authored checks after observing gold or official outcomes. Failures close the gate and preserve unused solver allowance.

## Stage 3: conditional full matched-budget comparison

Only after stages 0–2 pass, freeze the complete executable 56-response manifest: eight shared initial patches, three feedback conditions (ordinary logs, scalar, scalar plus components), two repair responses per condition/task. Preserve every declared cell, including inapplicable tasks as explicit missing outcomes. Reuse the same initial patch across conditions, reset repository/container state, charge all diagnostic computation to every condition and record actual costs alongside identical caps.

Keep the root protocol's metrics, missingness conventions, paired contrasts, task-level uncertainty analysis and feedback-space limits. Freeze all patches before official evaluation; score eight shared initial patches and 24 final patches under unique identities. Public diagnostics never receive official results. Report measured/declared/missing denominators, paired differences with 95% task-bootstrap intervals, exact paired-swap tests, and bounds over missing tasks. Eight tasks support an exploratory validation finding, not broad superiority.

## Proposed envelope requiring approval

Current additional allowance is **zero**. The proposal requests at most **8 new diagnostic-author responses plus 56 conditional solver responses**, through an existing subscription only. It requests a separate ceiling of 160 processor-hours, 18 elapsed hours, zero graphics processors, maximum two containers with four processors/eight gibibytes each, and maximum 120 gibibytes each of new Docker and scratch data. These are ceilings, not measured runtime forecasts. Unused version 2 allowance does not automatically transfer. No test-panel, training, judge, reference-generation or extra coordinator calls are included implicitly.

Implement and test outer build/cell/process-tree timeouts, the 1,800-second test timeout, cumulative container processor accounting, a run deadline and per-owned-resource storage accounting before any control. Preserve at least 100 gibibytes free at Docker root and one tebibyte scratch. Bound builds as well as evaluation containers. Never prune shared resources. Admit a cell only when its worst-case allocation plus capture/teardown reserve fits the remaining ceiling. Record pre-receipt failures and retries; at most one identical infrastructure retry per cell within this new envelope, never a fresh model sample. No retries from version 2 are relabeled as unused.

## After this version

[p 8/10] A 24-task test confirmation is conditional on valid measurement, not a positive eight-task effect, and needs its own frozen protocol and budget. Terminal-Bench remains a separate future study because its task families need different diagnostic definitions and environment controls. Neither expansion is currently admitted.

[p 7/10] Connect environment design to Varun's usable-signal-density/effective-coverage work only after a valid endpoint exists. Screen external training tasks, verify exact executable training code and model revisions, measure pretraining signal probes, obtain numeric law coefficients and freeze a forecast before reading training outcomes. No coefficient, throughput estimate or forecast may be invented. The current Lean [readiness manifest](../../02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/results/training_readiness_manifest_2026-10-06.json) remains not admitted.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] The next repair experiment has a concrete gated design and proposed ceilings; author, evaluator and repair execution require new explicit admission, and training remains outside this request.
