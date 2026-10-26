# Elementary Python to Lean curriculum generation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v5/PROTOCOL.md

**TLDR:** Generate 500 short complete Lean training responses through 25 explicitly authorized Terra/high Codex workers, using centrally fixed Python tasks and cluster compilation. This prepares data and does not start training or change a frozen experiment.

## Authorization and purpose

The user explicitly requested the Vals OpenAI key, 25 Terra workers at high reasoning, 20 examples per topic, compilation, and warm-start formatting; approved this plan with “ok go.” Later instruction explicitly selects independent tmux processes. Existing corpus examples contain little sub-1000-token practice. This run prepares the requested focused curriculum; effectiveness remains an unmeasured hypothesis, to be tested in a separate training experiment.

## Frozen inputs and execution

- Source tasks: `manifest.jsonl`, 500 tasks across 25 topics, 20 each. `manifest.sha256` records the frozen bytes. Python functions, natural-input restrictions, signature order, and 32 deterministic Python test cases are coordinator-authored before generation.
- Four coordinator-authored style prototypes are supplementary examples, separate from the 500 requested outputs; preserve attribution if workers reuse one.
- Model: exact `gpt-5.6-terra`, reasoning effort `high`, official Codex CLI. No model or funding substitution.
- Funding: initially the user selected the saved Vals OpenAI key (`VAL1_OPENAI_API_KEY`). The first worker request was rejected by OpenAI because that project reached its enforced spend limit; no model output completed. The user then explicitly instructed “use the lab oai key,” authorizing `LAB_OPENAI_API_KEY` for this same 500-example batch. Execution now uses that named lab credential through the official Codex CLI. No administrator limits are changed. Credential values stay in private runtime storage and never enter prompts, results, or Git.
- Planning cost: approximately $20–$100, depending on internal reasoning and repair turns, using saved rates of $2/million input and $12/million output tokens. This is an estimate, not an invoice or claim about current account balance. Record usage returned by each CLI process. Fixed target is 500 examples, one worker per topic, at most two repair continuations per topic, each invocation with a finite 60-minute deadline; do not launch duplicate healthy workers.
- Execution: named tmux workers on skampere1, owned by eth127, isolated worker directories/worktrees. Shared utilities and the manifest are coordinator-owned. Compiler queue initially had four slots. After observing approximately 82 GB available memory and 4.8 GB peak resident memory per Lean process, new checker invocations allow eight shared slots, still with one Lean thread per invocation; the Lean 4.22.0 memory flag rejects max_memory after import, so use the finite compile timeout and bounded process count, 45-second compile timeout. Use existing Lean 4.22.0 binary and cached Mathlib build paths directly without running Lake dependency resolution against another owner's environment.

## Admission

Every accepted response must have fewer than 1000 Qwen3 assistant loss-span tokens, including the file envelope and template terminator. Preserve the pinned system prompt, addendum, extractor, tokenizer revision and assistant-only template semantics. Each file defines `Tiny.solution`, at least one general nonvacuous `spec_` theorem and two `test_` example theorems.

Actually compile under Lean 4.22.0, inspect the kernel axioms of every named theorem, and compare executable outputs against the fixed Python test cases. Only propext, Classical.choice and Quot.sound are allowed kernel axioms. No sorry, admit, declared axioms, native_decide, unsafe or partial implementations. No tactic or notation modifications that weaken the intended specification. Preserve Python integer, division, empty-list, zip-truncation and optional-value semantics.

Screen Python, Lean and assistant response text against protected validation/test Python and gold references with exact hashes and word-5-gram Jaccard >=0.7. Record all hits and exclude contaminated rows from the final admitted dataset. Deduplicate identical Python/Lean pairs and exact Lean outputs; report reused Python function families, report related-task families, and preserve all requested task IDs and unresolved failures in the manifest. A short theorem is not a substitute for functional correctness; differential testing and human-readable intent remain separate checks.

Workers may repair proof code and shorten exposition but cannot change fixed Python behavior or weaken obligations to pass. All compiler logs, API/client transcripts, failures and provenance belong outside the training response. Publish measured accepted/500 counts, unknowns and blockers. Completion requires 500 accepted examples or an explicit unresolved inventory; launching workers is not completion.

## Operational checker refinement

The first workers used separate Lean invocations for axiom inspection and differential evaluation. New checker invocations consolidate those commands into one Lean execution, preserving all checks and fixed test cases while avoiding a second Mathlib import. The consolidated checker passed the addition prototype with the same token span and all 32 cases. Existing healthy workers retain their loaded checker implementation. Global admission independently applies the pinned nonvacuity policy, frozen prompt hashes, and exact evaluated-file/extracted-response byte identity to all rows.
