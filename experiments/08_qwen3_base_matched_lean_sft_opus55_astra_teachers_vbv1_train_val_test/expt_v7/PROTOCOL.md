# 1.7B seen-versus-fresh tiny-function diagnostic

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v7/PROTOCOL.md

**TLDR:** Evaluate the completed augmented 1.7B checkpoint on 50 exactly seen
training prompts and 50 fresh composition functions. This is an inference-only
diagnostic, separately labelled from the frozen benchmark evaluation.

## Question and decision

Can the checkpoint reproduce verified solutions to seen elementary functions,
and does that ability transfer to fresh combinations of the same primitives?
Low seen performance motivates investigating training/generation alignment;
high seen but lower fresh performance motivates more varied task training;
high performance on both makes larger-task composition the next uncertainty.
These are diagnostic interpretations, not causal claims or fixed pass-rate gates.

The fresh set uses familiar topics with new function bodies, not wholly unseen
mathematical domains. Novel compositions can be harder. Report this limitation
and each cohort separately; do not interpret their difference as a controlled
estimate of memorization. No 25–75% benchmark claim follows from this diagnostic.

## Immutable inputs

- Exactly 50 seen tasks: two per each of the 25 original curriculum topics,
  chosen before outcomes by ascending SHA-256 of `seen-fresh-v7:<task_id>`.
- Exactly 50 fresh tasks: two coordinator-authored compositions per topic,
  declared in `build_diagnostic.py` before inference. No provider model calls.
- The seen prompts must match the consumed corrected curriculum messages
  exactly. Use the same instruction builder, system prompt, single-turn addendum,
  namespace `Tiny`, required file marker, and Python argument order/types.
- Normalize Python function bodies, variable names and constants to reject
  syntactic family overlap with the 500 tiny tasks and parseable existing-pool
  Python functions. Preserve parse failures and word-5-gram near similarities.
  Exact/near protected validation/test reference hits block admission.
- Python is the behavioral oracle. Each task retains 32 fixed test inputs and
  expected outputs; seen cases are inherited unchanged, fresh cases combine
  boundaries and seeded small-domain samples. All fresh functions must exhibit
  at least two distinct expected outputs. Tests are hidden from the solver.
- Model: the exact v6 `onep7/runs/mixed/hf` export, verified against its recorded
  weights manifest before the first generation. No optimizer updates or repairs
  to evaluated model outputs.

## Cells and generation

Exactly 100 cells: one response per task, `sample_idx=0`, greedy decoding
(`temperature=0`, `top_p=1`, `top_k=-1`), seed 20261019, thinking on, stop at
`<|im_end|>`, maximum 4096 generated tokens, one vLLM engine, batch 100.
Greedy decoding is intentional for this diagnostic and differs from the main
benchmark's stochastic eight-attempt evaluation. The prompt's complete-response
limit remains below 1000 tokens; the larger generation ceiling lets us distinguish
an overlong complete answer from an interrupted answer. Save every raw completion,
prompt hash, finish reason and extracted file; no score-based retries.

Use the working cluster generation runtime (PyTorch 2.13.0 CUDA 13.0,
Transformers 5.18.0, vLLM 0.30.0), the pinned tokenizer, and identical source
extractor. The model receives instructions only, never gold Lean or hidden tests.

## Checks and primary outcome

Every declared cell survives into the results table. Check and report separately:

1. Clean completion, successful file extraction, and response under 1000 tokens.
2. Lean 4.22.0 compilation using the same cached Mathlib imports as v6.
3. Every named theorem checked by the unchanged pinned kernel-axiom checker;
   allow only `propext`, `Classical.choice`, and `Quot.sound`. Preserve errors,
   unresolved declarations, `sorry`, forbidden axioms and proof failures.
4. At least one anonymous executable `example`, one `spec_` theorem, two `test_`
   theorems, and the inherited non-vacuity screen.
5. Execute `Tiny.solution` on all 32 hidden Python cases, preserving exact JSON
   comparisons, compilation/interface errors, mismatches and timeouts.

Primary strict success requires all five. Also report compilation, kernel-proof
honesty, behavioral agreement, and their conjunction without the length/naming
style gates, so formatting failures remain distinguishable from capability.
Functional checks are finite: formal specification coverage and universal
Python/Lean equivalence are unmeasured. The kernel checker verifies the model's
stated theorems; it does not establish that those statements cover the intent.

Validate the checker first using a known correct package, a wrong implementation
with honest proofs, a `sorry` proof, a missing executable example, and broken
Lean. Preserve these control receipts. This is evaluator validation, not model QA.
Report 95% Wilson intervals for each 50-function proportion; one greedy response
per function, one training seed, no repeat-generation variability estimate.

## Execution, budgets, preservation

User authorization: `ok try 1` on 10-19-2026. D-101 authorizes self-hosted inference.
One idle 80 GB A100 (device 1 if still idle at admission), approximately 30–45 GB
inference allocation, compute-heavy generation; anticipated 5–15 minutes, exact
duration unknown. Recheck foreign processes and existing allocator gates, lease
the owned device until generation exits, and release it before CPU checking.
GPU generation wall-clock cap: 60 minutes for this 100-cell set. No new training,
checkpoint substitution, hosted calls or reading benchmark test instructions.

Use at most two diagnostic Lean workers, with 45-second per-compiler invocation
limits and a two-hour checking limit. Respect the existing v6 eight-worker budget:
admit a diagnostic compile only while no more than six original scorer jobs are
active; if all eight control scorers are active, wait. A check begun during the
transition can finish, creating at most two brief additional compiler processes;
record this operational overlap rather than change existing runs.

Run persistently in `rl4cv-tiny-seen-fresh`, retaining stage exit codes and process
identities. Every failure and missing cell remains explicit. Bounded identical
infrastructure recovery is separate from a correctness retry. Keep v6 runs and
their protocols unchanged. Colocate source, manifest, hashes, compact results and
receipts here; bulky raw generations and compiled probes live under the owned
cluster run's `diagnostic_seen_fresh_v7/`, with paths recorded in results.

Freeze this protocol, the 100-cell manifest, checks and input identities before
generation. Publish the compact, complete per-function table and a candid verdict.
