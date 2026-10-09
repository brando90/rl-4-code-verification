# Version 3 environment validation and matched factor-feedback repair

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v3/PROTOCOL.md>

**TLDR:** Brando authorized the automatic work on 10-08-2026. Validate the unchanged eight-task panel using repaired public dependencies and strict diagnostic transport, then run the complete matched-budget repair comparison only if at least six of the same eight tasks pass both validity gates. This version preserves the earlier failures and changes neither reference patches nor official tests.

Created: 10-08-2026. Status: IMPLEMENTATION AND PREFLIGHT AUTHORIZED; EXECUTABLE FREEZE PENDING. No version-3 control, diagnostic-author or solver outcome exists at writing. The final source/environment manifest must be committed before its relevant stage starts. After that, changes are append-only deviations or a new version.

## Admission and scope

Authorization is Brando's 10-08-2026 instruction: “anything that doesn't need human judgements, do it excellently,” with optional light Claude Fable 5.1 Max review and experiment folders. The parent selected one such review for this implementation. Routine design and setup choices are delegated to the experiment owner; they are not pending human approvals. Unknown payer, exhausted resources and human-only account/administrator actions remain blockers.

This version admits public dependency preparation, all 16 new gold/empty controls, at most eight fresh diagnostic-author responses, and conditionally the complete 56-response repair declaration. The scientific model is `claude-sonnet-5`, medium effort, no fallback. All measured responses use Vals-funded Valkyrie and an eligible vendor-agent implementation whose actual tool isolation, model, effort, prompt delivery and output limits are verified. D-108 supersedes earlier subscription-route language. A working coordinator login is not funding evidence. No personal paid or subscription fallback; no new credits or agent-authored provider calls.

The review uses personal-subscription Claude `claude-fable-5-1`, maximum effort, for implementation review only. No teacher, judge, 24-task test confirmation, reinforcement learning or benchmark-reference edit is implicitly added to this eight-task version.

## Frozen scientific inputs

Reuse the exact public panel in `../expt_v1/results/panel_public.json`, SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`. Dataset `princeton-nlp/SWE-bench_Lite` revision `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`; native `dev` split is validation here. Harness commit `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` follows version 2, superseding the original root-protocol harness pin. Preserve exact task base commits and evaluator rows privately.

The tasks are `sqlfluff__sqlfluff-1763`, `pvlib__pvlib-python-1606`, `sqlfluff__sqlfluff-2419`, `marshmallow-code__marshmallow-1343`, `pvlib__pvlib-python-1707`, `pvlib__pvlib-python-1154`, `pvlib__pvlib-python-1072`, and `pydicom__pydicom-1139`. No replacement or exclusion changes the declared denominator eight. Earlier outcomes were inspected; this is an exploratory validation study, not an untouched test or retrospectively claimed preregistration.

## Stage 1: environment and official controls

Use public base installation metadata to repair package compatibility. Before official evaluation, record every install command, interpreter/package version, public source hash, immutable image identifier, and exact environment delta. Verify ordinary imports and public test collection. Do not edit source, gold patches, official tests, expected outcomes or grader/parser behavior. If an unmodified test is incompatible with the environment, repair the dependency environment or retain a null outcome.

Freeze the environment and reviewed empty-patch adapter before all 16 cells. The adapter may admit the literal empty prediction and skip only absent candidate-patch application. It may add container resource controls and capture but must preserve official test application, parser and grading bytes. Record base-tree hashes before/after empty application and hash all grading inputs.

Every cell has a unique version/task/kind/patch/attempt identity, original result, execution log, terminal receipt and output hashes. A gold-resolved/empty-unresolved pair is valid only when both endpoints were measured under a valid environment with matching identities and completed tests. Setup, import, collection, fixture ambiguity, timeout or missing report produces null, even if a grader emits false. A valid test failure is false. Continue across the full panel, including every failed cell. Require at least 6/8 valid pairs before author calls; this is the inherited engineering gate, not a statistical threshold.

## Stage 2: public diagnostics

Before author calls, commit exact prompt, transport validator, isolated runner, synthetic tests, public-only context projection, client contract and source hashes. The new prompt requests bare structured JSON only; a diff, code fence, duplicate key or extra response text is rejected without manual salvage. One response per task, at most eight, no response retry. A transport failure or invalid check remains recorded.

Check categories are syntax, regression and issue; each has a fixed nonempty membership with at most eight commands. Commands are structured argument vectors and never evaluated by a host shell. Python assertions execute only in an isolated public task container, with no network, credentials, evaluator material or inherited optimization. Containers use a pinned public-only image, fresh disposable public checkout, fixed working directory and bounded resources. Pytest plugin autoload is permitted only from a frozen entry-point inventory bound to that image and interpreter; no host package mounts or inherited plugin environment are allowed. Freeze and verify the exact delivered author-prompt bytes, including their declared metadata header. Explicit Docker routing is admitted separately; ambient routing credentials or environment never enter the task container. Preserve raw bytes, normalized command and source hashes; structural acceptance alone never means a usable check.

On unchanged public base, all declared syntax and regression checks must pass. Each issue check must fail via an actual assertion in its submitted source; printing failure text, import errors, exceptions from dependencies, missing receipts and timeouts do not qualify. Base reproduction is a limited operational check: it cannot establish that a deliberately false or semantically irrelevant assertion tests the intended issue. Record this limitation and retain later frozen gold-check behavior as a diagnostic only. Never revise authored checks using official outcomes.

Require at least six tasks in the intersection of valid control pairs and usable public diagnostics. Below 6/8, close the gate, publish the full failure ledger and preserve the unused solver allowance. No manual human judgments are needed or inferred.

## Stage 3: fixed repair comparison

Inherit the root protocol's scientific metrics, feedback payload definitions, matched caps, deterministic public source retrieval, order randomization, null conventions and paired analysis. Freeze the complete executable declaration before solver generation: eight shared initial patches plus three conditions × two repair responses × eight tasks = 56 responses. Conditions are ordinary public logs, scalar geometric mean, and scalar plus three components. Every condition starts from the same initial patch; each reply is a complete patch against the base. Reset state, compute and charge all diagnostics in every condition, and record actual costs alongside common caps. Inapplicable cells remain explicit missing cells.

Maximum input is 96,000 characters per call; maximum output is 8,192 tokens only if the route demonstrably enforces it. The route must supply a supported enforceable alternative and its precise meaning before freeze if this cap is unavailable. Total invocation wall limit is 300 seconds plus 30 seconds capture/teardown reserve. No hidden retries or model substitution. Freeze feedback templates and truncation, check definitions, schedules, initial patches and final patches before the corresponding downstream stage.

After all final patches are immutable, score eight shared initial and 24 final patches through the independent official endpoint. Never return official evaluator results to a solver. Primary contrast is component-vector minus scalar; secondary is vector minus ordinary logs. Report resolved/observed/declared counts, all missing reasons, complete-pair differences with 95% task-paired percentile bootstrap intervals (10,000 draws, seed 0), exact paired-swap tests under exchangeable condition labels, and worst/best difference bounds over all eight tasks. Eight tasks cannot establish broad superiority; single responses do not measure within-cell generation variability. Improving the public aggregate alone is not evidence of improved issue resolution.

## Resource envelope and recovery

No graphics processors. At most two containers, four processor cores and eight gibibytes per container. Across this version: at most 160 processor-hours, 18 elapsed hours from the first admitted setup/control execution (not from local code authoring), 120 gibibytes new owned Docker data and 120 gibibytes new owned scratch data. Maintain at least 100 gibibytes free at Docker root and one tebibyte at the actual scratch filesystem. Never prune shared resources or alter shared daemon permissions. The selected healthy host, resolved storage devices and start/deadline are frozen in the execution manifest before execution.

Enforce build as well as evaluation limits. Reserve worst-case CPU allocation, wall time, storage and capture/teardown before admission. Track pre-receipt failures. A killed wrapper does not prove its Docker descendants stopped; verify owned resources are gone or explicitly blocked before any next admission. After freeze, allow at most one identical infrastructure retry per deterministic cell within cumulative limits; never generate a fresh model sample as a retry. A source/environment change requires a separately recorded freeze and cannot be relabeled identical.

Use one named full-access remote owner in a dedicated checkout, an ordinary-code watchdog, immutable receipts and a concise checkpoint. Verify useful first action and watchdog recovery with a harmless fake failure. Preserve prior evidence and completed cells through reboot. Publish small verified steps directly to main as project rules require; raw evaluator data and credentials stay private. No collaborator messaging or email is authorized.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Version 3 authorizes automatic validation and a conditional complete repair comparison, while keeping model funding, executable freezes, validity gates and resource limits enforceable prerequisites.
