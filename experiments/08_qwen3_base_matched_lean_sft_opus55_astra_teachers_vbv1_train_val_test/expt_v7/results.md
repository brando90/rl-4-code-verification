# 1.7B seen-versus-fresh diagnostic results

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v7/results.md

**TLDR:** COMPLETE, 10-19-2026 04:03 PDT. The augmented Qwen3 1.7B checkpoint
passes all checks on 29/50 seen functions (58%) and 9/50 fresh functions (18%).
All 100 responses have the required declaration structure, extract successfully,
and contain fewer than 1000 generated tokens. Correct Lean remains the bottleneck.

## Full declared results

| Measure | Seen training functions, n=50 | Fresh compositions, n=50 |
|---|---:|---:|
| Measured / declared | 50/50 | 50/50 |
| Extracted, clean, short response | 50/50 | 50/50 |
| Required declarations and non-vacuity screen | 50/50 | 50/50 |
| Lean compiles | 29/50, 58% [44.2%, 70.6%] | 11/50, 22% [12.8%, 35.2%] |
| All named proofs pass kernel check | 29/50 | 11/50 |
| All 32 Python differential cases pass | 29/50 | 9/50 |
| **Complete success** | **29/50, 58% [44.2%, 70.6%]** | **9/50, 18% [9.8%, 30.8%]** |

Intervals are the prespecified 95% Wilson intervals over functions; shared topic
dependencies are not modeled. One checkpoint/training seed, one greedy response
per function; repeat variability is unavailable. p-val=n/a: this is a descriptive
diagnostic, with no prespecified hypothesis test or causal treatment comparison.
The fresh functions are new compositions of familiar primitives and can be harder.

Complete success combines clean extraction, response under 1000 tokens, required
anonymous example/specification/test declarations, compilation, honest named
proofs, non-vacuity screening, and behavioral agreement on all fixed cases.
Removing the formatting gates gives the same 29/50 and 9/50 results.

Sources: [all 100 rows](results/per_task.csv), [machine-readable outcomes](results/results.json),
[summary and component intervals](results/summary.json),
[compiler/proof receipts](results/kernel_reports.json), [artifact hashes](results/artifact_hashes.json).

## Failure analysis and interpretation

- 60/100 packages fail Lean compilation: 21 seen and 39 fresh. All have ordinary
  compiler exit code 1; none of these outcomes is a compiler timeout.
- All 40 compiling packages pass the named-theorem kernel check. Two fresh
  packages still disagree with Python: `fresh_list_membership_01` ignores the
  absolute-value mapping, and `fresh_safe_indexing_02` defaults each index
  separately instead of defaulting the entire pair. Both differential executions
  complete normally and return all 32 results.
- Compiler evidence includes unsolved goals, incorrect concrete claims rejected
  by `decide`, invalid `rfl` proofs, syntax/type errors, and invalid library use.
  Detailed messages for every task are in the compiler/proof receipts above.

The model reliably emits the requested short package structure on these tiny
prompts. It still fails 21 of the 50 exact seen prompts and transfers less often
to fresh combinations. These observations motivate targeting compilable Lean
idioms, proof construction, and composition; additional formatting examples alone
are poorly targeted to this diagnostic. A bounded training-data or exposure pilot
would be a separate experiment and has not been launched.

This does not establish universal Python/Lean equivalence or intended-specification
coverage: the behavioral check is finite, and the kernel checks the model's own
stated theorems. It is separate from the ongoing 135-task VeriBench V1 validation;
the 222-task benchmark test split is unopened. There is no before/after claim from
this diagnostic because the replay control was not run on these 100 prompts.

## Provenance and source separation

Exactly two seen and two fresh tasks per each of 25 topics were frozen before
inference. Seen system/user prompts match the consumed curriculum byte for byte.
The checkpoint identity is verified in [model identity](results/model_identity.json).
All five evaluator mutation controls pass: correct, wrong implementation, sorry
proof, missing example, and broken Lean. See [controls](results/controls.json).
All 100 generations finish, extract, and use 118–222 tokens; none is truncated.

Fresh functions have zero normalized-body matches and zero exact text matches
against the screened training pool. Four existing Python blocks could not be
parsed for the body check; their text was screened. Fourteen fresh functions
trigger the word-5-gram similarity screen because of shared syntax/primitives;
these are retained in [screening](results/screening.json). There are zero exact or
near protected-reference hits across 714 protected Python/Lean files. These
screens do not establish semantic-family independence.

## Execution and verification

The A100 is released after generation. Checking initially uses two CPU workers.
The [first resource amendment](AMENDMENT_cpu_admission.md) removes unnecessary
queue waiting at 30 completed records. Following the user's request for more
parallelism, the [second amendment](AMENDMENT_parallel12.md) increases concurrency
to twelve; all 66 completed records are preserved. Two interrupted checks are
archived and rechecked from identical responses. The remaining 34 finish in about
33 seconds. Scorer source, selection, cases, generations, and the original
checking deadline remain unchanged. [Transition](results/parallel_transition.json),
[continuation](results/parallel_continuation.json), and
[all stage receipts](results/stage_receipts.json) retain this history, including
intentional termination of the earlier worker stages. Final status: COMPLETE.

Repository `make test` passes on Linux: **1362 passed, 24 skipped, 6 subtests passed**.
The test environment supplies ripgrep and the historical relative ultimate-utils
layout. Inaccessible foreign experiment-13 fixtures are explicitly unavailable,
so their optional integrations skip. No tests or scoring gates are weakened.
See [test receipt](results/repository_tests.json) and
[full log](results/repository_tests_complete_layout.log).

Raw responses, extracted Lean, complete compiled probe evidence and interrupted
checks remain at `/lfs/skampere1/0/eth127/rl4cv_tiny_training/diagnostic_seen_fresh_v7/`.
Compact manifests, hashes, all per-task judgments and receipts are committed here.

**Copy-ready message:** I finished the 1.7B diagnostic: 29/50 exact seen functions
and 9/50 fresh compositions pass compilation, kernel proofs, and Python tests.
All 100 responses meet the short output format, so the main remaining issue is
correct Lean/proof construction and transfer to new compositions.
