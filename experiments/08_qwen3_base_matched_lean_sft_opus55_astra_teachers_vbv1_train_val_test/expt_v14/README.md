# Failure-guided Lean curriculum and unattended host preparation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/README.md

**TLDR:** Prepare the GX10 as an optional GPU fallback and prepare pinned public-source candidates for specific training gaps. This experiment does not launch model calls or training; those are coordinated by versions 12 and 13.

## Scope and authorization

The user authorized parallel training, proof cleanup, reasonable data and training changes, and asked for unattended access checks on 10-19-2026. Prior authorization covers GX10 package installation and CPU proof checks. The primary cluster has available A100 GPUs, so the GX10 is a fallback. API generation uses Terra workers and a shared $300 initial allocation, with a second $300 only if needed (hard maximum $600); this experiment does not spend from that ledger.

## Admission

Candidates remain outside training until pinned Lean/kernel checks, exact target preservation, automation inventory, actual FILE extraction/Qwen template checks, deduplication, and protected overlap screens succeed. Protect all 357 VeriBench V1 validation/test tasks (Python plus gold Lean: 714 references) and 50 fresh diagnostic Python tasks. Validation error categories can guide generic curriculum choices; their task statements, outputs, and proposed solutions never go to teachers. The benchmark test split stays closed.

## Files

- `PROTOCOL.md`: failure-category decision rules and source admission.
- `prepare_candidates.py`: deterministic, no-model candidate preparation for pinned Mathlib modules and DeepSeek-Prover-V1 rows.
- `gpu_control.py`: bounded disposable GB10 GPU/backward control, with no model downloads or training.
- `qwen_gpu_control.py`: a tiny random Qwen3 attention/backward/optimizer control, without pretrained model downloads or experiment training.
- `check_source_controls.py`: three fixed Nat/Int/List original-module checks with the frozen kernel inspector.
- `aggregate_existing_failures.py`: generic category counts from existing diagnostic receipts, without exporting protected task contents.
- `AMENDMENT_bulk_validation.md`: prospective full 729-candidate CPU validation extension.
- `bulk_validate.py` and `watch_bulk.py`: frozen source/context verification, eight-worker kernel checks and ordinary completion/death watch.
- `sync_bulk.py`: collect compact JSON receipts and the full declared-row CSV locally, without changing Git.
- `AMENDMENT_training_admission.md` and `admit_verified.py`: admit the complete 688-pass cohort through safe comment insertion, actual format/token checks, protected screens and global deduplication against version 12's frozen current pool.
- `publish_admission.py` and `sync_admission.py`: publish the stable, hash-checked latest-admission pointer and collect compact receipts.
- `results/`: measured host and dataset preparation receipts.

## Status

10-19-2026: complete. Both GPU controls passed. All 729 prepared files received formal checks; 688 passed. The full 688-pass admission cohort yielded **678 ready auxiliary proof exercises: 209 Mathlib and 469 DeepSeek**, with deterministic comments, actual format/token gates, zero protected-screen hits and global deduplication against all 10,940 frozen version 12 current rows. Ten candidates remain excluded with recorded reasons. Use `/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/latest_admission.json`, which points to final `admission_v2/training.jsonl`; version 1 is preserved and superseded. No model calls or training were launched in this experiment. Dynamic SNAP-to-GX10 fallback currently needs the Mac's Brev route. See [measured results](results.md).
