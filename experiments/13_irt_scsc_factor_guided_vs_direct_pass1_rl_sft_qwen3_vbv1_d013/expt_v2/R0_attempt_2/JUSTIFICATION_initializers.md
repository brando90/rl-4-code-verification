# Attempt 2: initialized imports and retained frontend failures

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R0_attempt_2/JUSTIFICATION_initializers.md>

**TLDR:** Enable Lean module initializer execution before processing the input header, retain imported environments, and record command/diagnostic exceptions without dropping the parsed theorem obligation.

Pinned Lean v4.22.0 source `Lean/ImportingFlag.lean:14–28` documents that import initializers are disabled by default and the frontend enables them at startup. It also requires imported compacted module regions to remain alive. Therefore the probe calls `enableInitializersExecution` before `processHeader`, using `leakEnv := true`. Each process imports one pinned module environment and uses synchronous elaboration; no library version or scientific oracle changes.

Attempt 1's unresolved-type source, expected strict 0, clean commands 1/2, examples 1 and proved theorems 0/1 are unchanged. The missing measurement came from formatting its error through Mathlib's initialized `pp.mathlib.binderPredicates` option.

The new `initialized_pretty_printing` fixture explicitly sets that option, then fails a universally quantified theorem with a natural-number inequality, followed by a valid theorem. Independent expectations: strict 0; clean commands 3/4 (example, option, valid theorem); examples 1; proved theorems 1/2. The error must include the inequality `n < 0`, and both theorem obligations remain. Mathlib's pinned `Mathlib/Util/PPOptions.lean:20` registers the option and its delaborators read it.

The command loop catches frontend input/output exceptions after parsing, records the exception on that command and marks it unclean, then continues from the retained parser state. Message-rendering exceptions become explicit diagnostic text with a rendering-error flag; they do not escape and discard the obligation list. Header import errors already become messages in Lean's `processHeaderCore`. Final-environment axiom collection and theorem counts stay separate from historical strict. Process loss and frozen resource limits remain infrastructure/resource classes, not fabricated scores.

The fixture runner retains all previous 29 cases, adds the regression case, strengthens long-message attribution checks and freezes the attempt-specific implementation hashes. Original attempt-1 paths are unchanged. Each development attempt has a separate ledger cell namespace; its per-cell infrastructure retry policy remains unchanged.
