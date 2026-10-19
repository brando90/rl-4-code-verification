# Public Lean corpus and tiny annotations: preparation results

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v8/results.md

**TLDR:** FIRST PASS FINISHED,10-19-2026 04:53PDT. All500tiny answers pass mechanical code-preservation, extractor, pinned chat-template and token checks. The100-worker Workbook pass produced12,822/12,823normalized commented candidates and1,457annotation flags; the missing assembly and the user's new explicit-proof preference are handled in version9. No new model training has started.

| Workstream | Declared | Complete |
|---|---:|---:|
| Source groups audited |4|4|
| Existing tiny answers annotated and mechanically verified |500|500|
| Workbook candidates annotated and normalized |12,823|12,822|
| New training runs |0|0|

## Tiny comments

All500files start with a2–4-line English solution/proof sketch and include comments around meaningful steps. All500retain identical original code and match prior accepted verification receipts (Lean compilation/allowed axioms and32Python differential cases each). Per the user's instruction, compilation was not repeated. All500pass the frozen extractor roundtrip and Qwen chat-template checks and remain below1000assistant tokens. The [per-item table](results/tiny_annotation_rows.csv) records hashes and token counts. No model assessment of explanation accuracy has been performed.

Annotated training JSONL: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v8/annotations/training.jsonl`, SHA256 `af2b68f683a2ab757108af87c4be398882f6b73f063eed015b0c8e9f7047d7f1`. The25Terra/high annotation sessions recorded6,708,473input tokens (5,847,077cached) and208,878output tokens: configured-rate estimate$5.40, not a provider invoice; cache-write surcharges unknown.

## Workbook comments

Pinned public source has140,214statements,12,823with proof candidates. Select proof index0per statement for comment-only augmentation; preserve the original candidate and its hash. All12,823pass the required exact/word5gram overlap screens against714VeriBench validation/test references plus50fresh diagnostic functions. These screens do not prove absence of semantic overlap.

Launch:100named remote workers `codex-rl4cv-workbook-000` through `codex-rl4cv-workbook-099`,64statements per batch,201batches. Actual model `gpt-5.6-terra`, medium reasoning, Codex CLI0.114.0, full access, the previously explicitly authorized lab credential. One initial attempt and at most one mechanical repair per batch;600seconds per attempt. No proof repair or new training is assigned. All100workers had live processes/started CLI turns and no reported API errors at the04:37observation; completion awaits actual outputs.

Runtime: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v8/workbook_annotations`. Watch: `rl4cv-workbook-comment-watch` on skampere1,15-second cadence, observes process death and output integrity, preserves the two-attempt bound, and renders normalized candidates when the batch pool terminates. Harmless dead-worker and exhausted-attempt controls passed with zero model calls. `progress.json`, `usage.json`, `completion.json` and per-batch receipts are the runtime evidence. No external notification messages are sent.

All201batches returned;198passed as whole batches and3exhausted their native repair allowance. Per-row recovery retained earliest valid annotations, yielding12,822normalized rows,1,457heuristic annotation issues, and12,821answers below1000assistant tokens. The missing row is `workbook_035658`. It is assigned to the version9changed-script annotation pool rather than resampling this frozen pass. See the [per-item table](results/workbook_annotation_rows.csv) and [version9reconciliation](../expt_v9/results.md). The baseline normalized-candidate JSONL SHA256 is `9efdfe14ecd232a1cf7d48448e4db71dd7269383ecc695a923b60e61daf984cf`.

The heuristic flags are not correctness verdicts. In particular, `exact?` can be a valid Lean search tactic; the next phase checks such cases and supplied alternatives with the pinned kernel inspector. Version8raw attempts and native failed statuses remain unchanged.

Public proof candidates remain **not admitted for training** until current Lean/kernel compatibility checks. Comment-only preservation certifies unchanged source; it does not establish that a supplied proof is correct. Annotators explicitly flag uncertain/flawed steps instead of repairing them. Comments and proof sketches are training targets, not private model reasoning transcripts.
