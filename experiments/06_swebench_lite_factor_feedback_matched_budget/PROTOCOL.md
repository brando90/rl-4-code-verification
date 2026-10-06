# Folder 06 protocol for factor feedback on SWE bench Lite

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/PROTOCOL.md>

**TLDR:** Compare ordinary public feedback, a diagnostic geometric mean, and its components on eight fixed validation tasks. The official resolution endpoint is evaluated only after final patches are frozen. This protocol authorizes preparation and a bounded pilot; exact executable prompts, check definitions and runtime pins must be committed in an admission manifest before model calls.

This file is written before this experiment's outcomes. Freeze executable details in `expt_v1/results/admission.json` before the first diagnostic-author or solver call. Changes after that point are append-only deviations in `REPORT.md`, or a separately frozen version. Never rewrite the protocol to fit results.

## Scientific question

Does exposing the component vector improve official issue resolution after two repair responses relative to exposing only its geometric mean? Does it improve upon ordinary public diagnostic logs? The primary contrast is vector minus scalar; vector minus ordinary is the practical secondary contrast. This validation pilot is exploratory and cannot establish a general benefit with eight tasks.

Continue to a separately frozen test experiment only if at least six of the eight selected tasks have valid official controls and usable public diagnostics, the public/evaluator isolation checks pass, and every admitted cell has accounted-for terminal evidence. Six of eight is an agent-selected engineering threshold, not a statistical threshold. A positive pilot effect is not required for expansion; a completely uninformative or invalid diagnostic warrants redesign. Retain all eight tasks and explain nonapplicability rather than selecting replacements.

## Locked parameters

- Dataset: `princeton-nlp/SWE-bench_Lite`, revision `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`; upstream split `dev`, called validation here. Population 23; select eight by ascending SHA-256 of `rl4cv-e06-v1:` plus instance identifier. No reference patch length, model success or test outcome enters selection.
- Harness: `SWE-bench/SWE-bench` commit `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`. Fetch immutable bytes and pin dependency versions and container digests before use. If the released schema or harness cannot run together, preserve the failure and freeze a new version before substituting a source or harness.
- Solver: proposed `claude-sonnet-5`, effort `medium`, authenticated subscription command-line interface (CLI), text-only tool-free calls. Record the actual returned model identifier and installed CLI version. No provider application programming interface (API) client code or provider keys. Entitlement and safe tool disabling must be verified before admission. A different measured model requires its own prospectively frozen manifest before any measured call; executor substitution never changes an admitted solver.
- One initial patch is shared across three conditions, then two repair responses for each condition: eight initial plus 48 repair responses, maximum 56 solver responses. Diagnostic-author budget: at most one call per selected task, maximum eight additional calls. Maximum 64 measured/preparation model calls; no implicit best-of sampling or score-triggered retries.
- Maximum input context per call: 96,000 characters; maximum output: 8,192 tokens if the client enforces that parameter. If no enforceable token parameter exists, freeze a supported output bound and its meaning before admission; do not claim prompt requests enforce token budgets. Each model invocation has a 300-second total wall limit, with a further 30 seconds reserved for capture and teardown. Preserve incomplete outputs and their native stop reason.
- Bounded context is retrieved from the base revision alone using a deterministic public-issue lexical retrieval rule. Freeze that rule, selected files and hashes once per task before candidate generation. Repairs receive the same base context and their own preceding patch. Return a complete unified diff against the base, not an incremental patch against a different arm.
- All conditions receive the same issue text, source context, public check definitions, previous patch, response cap and two steps. Ordinary receives normalized public check logs; scalar receives only the aggregate plus common operational failure information; vector receives that scalar and the three numeric components with denominators. Freeze payload templates and deterministic truncation; reserve identical maximum feedback space. This changes information content, not merely formatting. Do not infer equal actual cost from equal caps.
- Compute all public diagnostics in every condition. Charge their full cost to every condition. Order the six repair cells per task by a frozen identifier-hash permutation while respecting within-condition step order. Reset repository and container state between conditions.
- Official scoring covers the shared initial patches and 24 final patches after all final patches are immutable. Give every different patch/condition/step a distinct run identifier containing a prediction hash; cached harness results may otherwise be reused incorrectly.

## Locked metrics and analysis

Define execution viability V, public regression preservation R, and issue-check pass fraction B in [0,1], with frozen nonempty denominators. Freeze exact command-to-outcome parsers and check membership in the admission manifest. Execution viability must include patch applicability and declared syntax/import checks. The proposed aggregate is `(V * R * B) ** (1/3)`. Report the vector even when the aggregate is zero. If patch application fails, the compile-gated aggregate may be zero by the frozen convention, but unrun R and B remain null; do not invent test failures. If another required component is unavailable, the aggregate is null. No renormalization over available factors.

Public regression checks come from the base repository and must pass on the base. Choose them from public issue/repository context without reference changed-file lists or official test identifiers. Issue checks are authored from that same public view before candidates; record whether they expose the reported behavior on the base. A collection/import/environment error is not evidence that the issue was reproduced. Keep invalid checks and their reasons in the preparation record. Do not repair or select these checks against the gold patch or official outcomes. Diagnostic mismatch with the gold patch is an after-freeze validity finding, not permission to tune against it.

The independent endpoint is the pinned official harness `resolved` result, requiring its issue-resolution tests and preservation tests under the official parser. A generated patch that validly fails tests is false. Infrastructure failure, unavailable report or ambiguous parsing is null. Keep official reference/test patches, test identities, evaluator scripts and all evaluator logs outside solver prompts and accessible files. Gold-patch and empty-patch controls validate the evaluator without modifying reference artifacts.

Report each final condition's resolved count, observed denominator, missing count and declared denominator eight. Primary paired difference: vector minus scalar. Secondary: vector minus ordinary. Use a task-paired percentile bootstrap, 10,000 draws, seed 0, with 95% intervals and the exact paired-swap test under the null of exchangeable condition labels. Eight tasks give coarse, wide uncertainty. Report complete-pair results and worst/best difference bounds over all eight; missing is never zero. Keep per-task outcomes, execution validity, actual input/output/reasoning-token availability, elapsed time, diagnostic time and official evaluation time. Single generation per cell means within-cell generation variance is unmeasured. Correlations and calibration are secondary future analyses, not substitutes for this contrast.

## Scale verification

V, R and B are fractions already normalized to [0,1]. The official resolved value is Boolean or null. Do not divide either by a rating scale. The diagnostic geometric mean is not a calibrated probability, formal correctness score or VeriBench SCSC, and its increase is not itself the scientific outcome.

## Verified data schema

The selected legacy dataset includes `instance_id`, `repo`, `base_commit`, `problem_statement`, `patch`, `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS` and harness metadata. Verify field types after download. The solver projection permits exactly the first four fields. Preserve the original evaluator rows privately and publish only identifiers/hashes and allowed summary metadata. `prepare_panel.py` enforces the projection and freezes the full cell manifest. Native split `dev` maps explicitly to validation.

## Preconditions and resources

Execution is on `skampere1` local scratch in a dedicated checkout, with no graphics processor allocation. Docker server 28.1.1 was observed on 10-05-2026. The Docker root is on the node root filesystem, which had 266 gigabytes available; do not assume its capacity equals the 11-terabyte local-scratch headroom. Maximum two task containers, four processor cores and eight gibibytes memory each; maximum 120 gibibytes new Docker data, 120 gibibytes job scratch, 160 processor-hours and 18 elapsed hours including preparation and finalization. Retain at least 100 gibibytes free at the Docker root and one tebibyte local-scratch free. Never prune shared images/containers or alter the Docker daemon. Account for image layers shared with other jobs before cleanup; remove only uniquely owned, finished resources.

Use separate public and evaluator storage. For tool-free CLI calls, enforce no shell, file, network-search, plugin or connector tools, no inherited repository instructions, no resumed sessions and no evaluator material in prompt construction. Verify this on the actual client, rather than trusting a prompt. If that cannot be achieved, isolate the solver with an equivalent enforced public-only container and freeze the changed execution path before calls. Full-access execution applies to the coordinator; a measured solver's deliberately tool-free interface is an experimental treatment, not an approval wait.

## Estimated wall clock

Estimates are ceilings, not measured performance: model calls can use up to 5 hours 20 minutes in total; official controls/scoring up to eight hours combined with two evaluator workers; image/setup and public checks occupy the remaining admitted 18-hour envelope. Measure actual runtime on initial preparation and reserve finalization time before admission. Use per-command timeouts; never cut off a healthy admitted cell merely because a coordinator turn ends. If the full declaration cannot fit, freeze a smaller separately named version before model calls, keeping the original planned manifest and reason.

## Pass fail and abort rules

First complete source/schema isolation, official reference controls and public-check feasibility for all eight tasks. A passing control does not complete the pilot. Admit the full comparison only with at least six applicable tasks and the fixed executable manifest. Inapplicable tasks stay in the declared denominator with explicit missing receipts. Never replace them with easier tasks. The remaining valid cells follow the entire frozen procedure.

Pause new admissions on resource ceilings, exhausted subscription allowance, compromised public/evaluator separation, or unknown billing. Preserve healthy jobs and completed patches; finish deterministic capture/scoring when safe. Before the first measured call, harmless setup failures may be repaired and recorded. After admission, one identical deterministic infrastructure retry is permitted within cumulative limits; no fresh model sample is a retry. Any new measured continuation or model change needs a separately frozen condition.

## Identity and publication

Coordinator: this task's named remote worker and supervisor; owner Brando's existing repository `brando90/rl-4-code-verification`. No collaborator messaging, email or leaderboard submission is authorized. Commit only owned code, protocols, hashes and summaries to main after deterministic checks. Credentials and raw evaluator data never enter Git. Publish current `results.md` as stages finish.
