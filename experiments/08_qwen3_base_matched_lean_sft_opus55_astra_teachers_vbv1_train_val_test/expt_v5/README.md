# Elementary Python to Lean warm-start curriculum

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v5/README.md

**TLDR:** Completed: 500 short complete training examples from 25 elementary Python/math topics using Terra at high reasoning. Responses use the existing experiment 08 system prompt, addendum, file envelope, Qwen chat template and assistant-only loss span. This version records data preparation; subsequent training and the executable-example adaptation are tracked in [version 6](../expt_v6/results.md).

See [live results](results.md) and [protocol](PROTOCOL.md).

## Files

- `build_manifest.py`, `manifest.jsonl`, `manifest.sha256`: centrally authored Python tasks, explicit input domains and 32 fixed Python comparison cases per task.
- `prototypes/`: four supplementary coordinator-authored Lean examples illustrating concise, readable solutions. These are outside the 500-worker-output target.
- `check_example.py`: actual Lean compilation and kernel-axiom checks, Python/Lean differential checks, token cap, pinned output-extractor round trip and chat-template validation.
- `prepare_workers.py`, `worker_driver.py`, `supervise.py`: isolated topic worktrees and 25 named tmux processes, exact Terra/high settings, finite repairs, liveness and progress receipts.
- `verify_1p7_format.py`: direct check against the pinned Qwen3-1.7B-Base tokenizer, including exact token identity with the pinned 8B tokenizer.
- `finalize_dataset.py`: protected-reference screening, exact Lean deduplication, consolidated training JSONL and coverage/token summaries.
- `results/`: non-secret run receipts mirrored from the cluster.

Cluster runtime and generated artifacts live under `/lfs/skampere1/0/eth127/rl4cv_tiny_curriculum/`. Each worker owns `workers/<topic>/examples/<task_id>/`, containing the Lean solution, Python source, intent, training row and verification receipts. Operational transcripts remain outside training responses. Credentials are stored separately from the experiment directory and never included in Git or the dataset.

The training row's `messages` list contains the system prompt, task instruction plus the frozen addendum, and one assistant file response. The tokenizer inserts the empty thinking block and end-of-message terminator in the loss span. Every accepted complete assistant span is below 1000 Qwen tokens. The prompt receives no training loss.

Compilation uses existing Lean 4.22.0 and cached Mathlib on cluster CPUs, with initially four concurrent single-thread compiler processes; new checker invocations permit eight after measured memory admission. No GPU is allocated. The kernel axiom allowlist and intended Python behavior remain fixed; failures and missing examples remain visible until resolved.

Some topics deliberately revisit the same Python operation with different input domains or proof properties. Report these families and remove identical Lean outputs. Split future synthetic evaluations by operation family rather than randomly separating near-identical variants. No held-out evaluation result is claimed here.

## Completed dataset

All 500 examples are ready in [dataset/training.jsonl](dataset/training.jsonl) and [tiny_curriculum_500.tar.gz](tiny_curriculum_500.tar.gz). See [final results](results.md) for exact counts, token lengths, provenance, checks and the existing macOS-wide test limitations.
