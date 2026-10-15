# Experiment 13 v2-S2 train-only hidden-test control freeze

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/HIDDEN_CONTROLS_S2.md>

**TLDR:** This prospective freeze admits one train-only check of the corrected experiment-12 hidden-test adapter. It uses 64 tasks from distinct train groups, 708 extracted tests and unchanged control thresholds. No benchmark-reference hidden-control outcome has been computed. The controls must pass before this route measures the independent train coverage audit.

Frozen 10-14-2026 by publication of [HIDDEN_CONTROLS_S2.json](../locks/HIDDEN_CONTROLS_S2.json). The corrected experiment-12 version-2 adapter, including its V2-A1 name-affinity and reference-veto correction, remains byte-for-byte unchanged at SHA-256 `da6fbe366b26e8518894ba5dd0d236de9e3f258f53e30c5181be08ebcfc7f430`. The original extractor, literal-fixture expansion, renaming and mutation helpers are imported read-only. No experiment-12 benchmark outcome or held-out gold source is used.

Selection uses the complete 539-task train allowlist and frozen train group identifiers. There are 529 tasks with extracted tests. Sort them by SHA-256 of `rl4cv-e13-s2-hidden-controls-1302261:` plus task identifier, retain the first task from each group, then take the first 64 groups. Selection uses source structure only. The 64 selected tasks contain 708 tests; private identifiers, sources and expected values remain on the host. The lock binds their complete private manifest and 926 implementation/input files. This is a new train-only route cohort, not experiment 12's original 50-task cohort. Sixty-four groups allow the unchanged minimum of 50 compiling mutants without requiring a compilable mutation in every selected task.

Run the following controls on every selected task, preserving all failures and missing measurements:

| Control | Construction | Admission criterion |
|---|---|---|
| C1 | Unchanged gold source against its own extracted tests | At least 98% of all 708 tests applicable and passing |
| C2 | Consistent implementation-symbol renaming in a private gold copy | At least 95% of C1 all-passing tasks recovered with every test passing |
| C3 | First compiling deterministic implementation mutant | At least 50 compiling mutants; at least 60% fail one or more evaluated hidden tests |
| C4 | Gold source of the next selected task, cyclically, from a different group | At least 95% rejected as unmapped or fail at least one evaluated test |

C3 removes example/theorem/lemma declarations from a private copy, then enumerates the original operator/literal mutations in source order, followed by its original string-literal and reachable-helper fallbacks. At most 40 candidate mutations per task are frozen. There are 585 candidate sources across 61 tasks; the other three remain in the denominator. Compilation alone chooses the first eligible mutant; a surviving hidden test never selects another candidate. A compilation timeout or other unresolved process result stops that task's mutant search. All compilation attempts and the first selected mutant's hidden outcome are retained. C4 bridge/type uncertainty is not counted as a rejection. These control counts record demonstrated criterion satisfaction, not imputed hidden outcomes.

The runtime preserves the corrected adapter's mapping priority, argument-only candidate-agreement probes and per-test `pass`, `fail`, `unmapped` and `type_unknown` statuses. For a compiling candidate, incomplete applicability makes all-tests-pass missing, while the measured-test fraction remains separately descriptive. A deterministic candidate compile failure is a hidden failure; resource limits and unresolved compilation remain missing. Tasks with no extracted tests are excluded consistently. Gold implementations are never copied into the candidate bridge, and expected test values never select a symbol mapping.

Execution uses eight central-processor workers at most, dynamic shared memory admission, one Lean thread per process, priority 10, a 64 GiB address-space cap and 600 seconds per Lean invocation. No accelerator, solver model or judge call is involved. Each task and runtime cell has a durable exclusive attempt receipt. A completed cell is never rerun; unfinished attempts require evidence reconciliation and have no automatic retry. One final control evaluation is admitted after every declared task finishes. Per-control missing/status counts accompany the verdict. Any control failure leaves this route unadmitted; it does not authorize changing the adapter, thresholds or cohort after observation.

This prepares one independent coverage route. The separately published hosted formal-specification judge controls have passed, but neither route replaces the train mutation audit, the fixed pilot monitor, strict scoring or the later selected-checkpoint test evaluation. Authored synthetic Lean fixtures test implementation behavior before the benchmark control run; they are not benchmark control results.

Publication verification: **722 passed, 3 skipped, zero failures in 350.22 seconds**, direct exit 0 for the required Lean integration suite ([receipt](hidden_controls_publication_test.json)).
