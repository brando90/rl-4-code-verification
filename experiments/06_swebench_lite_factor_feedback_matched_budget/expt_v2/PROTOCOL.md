# Version 2 protocol for legacy SWE-bench Lite harness compatibility

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/PROTOCOL.md>

**TLDR:** Version 1 cannot evaluate the pinned legacy dataset because harness commit `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e` requires four evaluator fields absent from all 23 legacy `dev` rows. This separately frozen version preserves the legacy dataset and eight-task selection but substitutes a schema-compatible official harness only after a direct compatibility check; it does not admit any model generation yet.

## Frozen delta from version 1

This version inherits every solver budget, public/evaluator isolation requirement, timing limit, response limit, cell accounting rule, and analysis rule from [the version 1 protocol](../PROTOCOL.md), except the harness revision below. The upstream legacy dataset remains `princeton-nlp/SWE-bench_Lite` revision `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`, split `dev`, logically named validation; its 23-row export SHA-256 is recorded in the private runtime receipt. The deterministic eight-task panel remains bound by public manifest SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`.

The version 1 harness is retained as evidence, not replaced in place. Its `make_test_spec` call raised `KeyError: 'image'` because all 23 exported rows lack `image`, `eval_script`, `eval_type`, and `log_parser`. That result is a pre-admission evaluator incompatibility, not an official outcome.

## Version 2 evaluator pin and admission condition

The proposed replacement is `SWE-bench/SWE-bench` commit `f7bbbb2ccdf479001d6467c9e34af59e44a840f9`. It constructs task environments from the legacy row fields rather than requiring pre-materialized `image` and `eval_script` fields. Before any control, diagnostic-author, or solver call, the coordinator must:

1. fetch immutable bytes for this exact commit into evaluator-only storage;
2. install it in a job-owned environment with a recorded dependency inventory;
3. call its `make_test_spec` for each selected evaluator row and preserve a private receipt showing all eight succeed;
4. freeze a version-2 admission manifest with the exact image-build/evaluation commands, container limits, public context/check recipes, prompt templates, solver interface, and unique run identifier derivation; and
5. verify gold-patch and empty-patch endpoint controls before measured solver generation.

The replacement is valid only if the direct compatibility check succeeds and the official controls yield unambiguous reports. If it fails, no source/harness is changed again in this version; preserve the receipt and freeze a later version. The solver remains `claude-sonnet-5` at medium effort through the existing authenticated command-line subscription, with 56 solver responses and at most eight diagnostic-author responses. No prior or future official result may enter any solver prompt.

## Publication and status

This protocol starts with zero measured generation cells and 24 missing final condition cells. The version 1 panel manifest is an immutable input. Version 2 may publish only safe identifiers, hashes, commands, environment metadata, and summary receipts; legacy rows, reference patches, test patches, evaluator logs, and test identities remain private. `RESULTS_validation.md` may report a completed study only after all declared cells have terminal receipts and the exact paired analysis has run.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Version 2 prospectively changes only the incompatible evaluator harness and requires direct compatibility plus control evidence before any measured repair call.
