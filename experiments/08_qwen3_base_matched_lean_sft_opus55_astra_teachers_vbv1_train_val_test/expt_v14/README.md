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
- `results/`: measured host and dataset preparation receipts.

## Status

10-19-2026: preparation complete. Both GPU controls passed. Prepared 217 Mathlib and 512 DeepSeek candidates; three fixed Mathlib source/kernel controls passed. The prospective full 729-candidate formal validation batch is now running on SNAP with eight CPU workers; exact original source/context checks and freezing are complete. All candidates remain outside training pending admission gates. Dynamic SNAP-to-GX10 fallback currently needs the Mac's Brev route; the primary cluster workflow can continue independently. See [measured results](results.md).
