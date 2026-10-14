# Matched replay versus cached data expansion

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/README.md>

**TLDR:** Prepare the next supervised fine-tuning comparison using existing teacher outputs: replay the original corpus versus expand it, with matched additional loss tokens at four Qwen3 Base sizes. Existing-data analysis and a candidate manifest are complete; corpus admission and the training protocol remain unfinished, and no version-3 model run has launched.

**Status:** PREPARING — existing-data audit complete; prospective protocol not frozen.
**Owners:** Lethan (`@lethan3`), 1.7B/8B and MBPP conversion; Rakshit (`@rakshit-kaushik`), 4B/14B and shared cached-data assembly. B denotes billion model parameters; MBPP means Mostly Basic Python Problems.

## Question and decision

Does additional exposure to the original training set suffice for a reliable reinforcement-learning warm start, or does an expanded corpus help at the same loss-token budget? The proposed design and exact division of work are in the [10-13-2026 meeting plan](../../meetings/oct_13_2026/PLAN.md). A target Smooth Conjunctive Score for Code verification of 0.25 is a separate performance milestone from binary success probability and mixed-success learning signal.

The first comparison uses the four step-658 starting checkpoints and two conditions, original-data replay and screened expansion. The proposed additional budget is 5,752,936 loss tokens per condition and size, with validation at half and full budget. Freeze corpus contents, optimizer/scheduler continuation, token accounting, validation manifests and the plan’s decision criterion in a new `PROTOCOL.md` before production training. Existing versions remain frozen.

## Work already done

- [RESULTS_continuation_audit.md](RESULTS_continuation_audit.md): matched validation counts, uncertainty and interpretation.
- [results/continuation_audit.json](results/continuation_audit.json): measurements, source hashes and explicit missing corpus-admission result.
- [results/cached_train_candidates.csv](results/cached_train_candidates.csv): 685 train-only teacher-response candidates, including response hashes and host paths.
- [prepare_continuation.py](prepare_continuation.py): deterministic regeneration from committed existing metadata and validation outcomes; no model calls.

From the repository root with the project Python environment:

```bash
python experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/prepare_continuation.py
python -m pytest -q tests/test_sft_continuation_audit.py
```

The selected corpus has 1,315 examples from 476 train tasks. The capped candidates add zero new source tasks before deduplication; the separate MBPP source has 587 pairs across 455 tasks before conversion and joint screening. These are inventories, not promised training gains or an admitted 2,587-example corpus.

## Next execution boundary

**[p 9/10] Admit existing data first**, because this can expand the training pool without new teacher generation. On the execution host, verify the manifest’s response hashes; jointly normalize/deduplicate all candidate Lean and source-task groups; preserve verified Lean exactly; freeze an extraction-compatible MBPP assistant encoding; rerun full-text leakage, tokenizer-prefix, loss-mask and 16,384-token checks. Record exclusions and counts rather than repairing rejected source examples silently. This preparation does not require test outcome inspection.

**[p 8/10] Freeze and run the controlled comparison**, because training before token/recipe agreement would lose the cross-size comparison. Record exact starting weight/optimizer hashes, manifests, framework versions, compute estimates based on current throughput, device allocation and progress owner. Reset the extra-phase learning rate explicitly rather than inheriting the original schedule’s terminal zero. Resolve exact budget boundaries and log optimizer steps and processed tokens; these may differ by data condition even when loss tokens match. Use the existing project execution, funding and complete-cell rules. Preserve version-2 evidence and its terminal recovery contract. The owner closed that attempt PARTIAL at 17:49 PDT because the Vals-managed route was unavailable; 0/5,328 new outputs persisted. Corpus preparation can proceed, but any newly judged evaluation needs a working validated route.

The cheapest sufficient preparation is this metadata audit plus on-host corpus admission; new teacher generation is not a prerequisite. Training evidence will determine whether replay, expansion or neither meets the declared goal. Keep the full set of failed/missing cells and report one-seed limits.
