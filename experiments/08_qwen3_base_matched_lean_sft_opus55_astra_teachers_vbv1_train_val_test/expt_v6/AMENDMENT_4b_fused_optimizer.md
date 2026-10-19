# 4B CPU fused AdamW continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/AMENDMENT_4b_fused_optimizer.md

**TLDR:** On 10-19-2026 the user authorized deployment of the faster CPU optimizer. Continue the existing 4B augmented trajectory from a complete checkpoint, restoring float32 master weights, Adam moments, learning-rate position and random-number states. Preserve both original 1.7B pipelines and the complete validation manifest.

## Prospective change

- Use PyTorch 2.7.1 CPU AdamW with `fused=True, foreach=False` after the handoff; the original kernel uses `fused=False`.
- The first intended boundary is update 100. If completed updates have already passed a boundary when it is fenced, wait for the next boundary. Retain the original checkpoint inode and the entire unfused metrics prefix.
- Restore the saved float32 master weights directly. Reconstructing them from rounded bfloat16 model parameters would lose optimizer precision and is forbidden by this continuation.
- Restore all Adam state, the consumed-token count and both CPU/CUDA random-number states. Continue the exact frozen batch schedule and token-based learning-rate function from the next update.
- Keep the same GPU 6, four CPU threads, bfloat16 model parameters, attention implementation, gradient checkpointing, loss masking, clipping, hyperparameters and final assistant-token budget. Expected GPU footprint remains approximately 39 GiB, with possible sequence-dependent peaks. End-to-end speed remains unmeasured before the handoff; both model computation and host/device transfers remain.
- The AdamW formula is unchanged. A different floating-point kernel may change rounding and future weights; do not describe the continuation as bitwise-equivalent to an uninterrupted unfused run.
- No validation outcome was inspected to choose this change. No additional evaluation cells or test-split evaluations are introduced.

## Verification and process handoff

1. Check CPU numerical agreement, full float32 optimizer save/restore and bfloat16 shadow updates. Exercise fencing a real disposable process at a complete checkpoint and resuming it after an invalid checkpoint is rejected.
2. At a complete production checkpoint, pause only the exact owned 4B trainer (PID, process start time, boot ID and owner verified). Inspect the saved state before terminating it. Resume the original process if inspection fails.
3. Retain the old trainer's receipt and log. Its original supervisor observes the deliberate termination as exit `-15`; record that mechanical failure as the planned migration, never as an unobserved success. The supervisor continues both original 1.7B pipelines.
4. Serialize the brief GPU gap with the existing allocation gates. Launch the successor in a named persistent session, verify exact state restoration and actual forward/backward/optimizer progress. Release allocation gates once its real GPU context is present.
5. The successor uses the original generation, materialization and scoring functions with their frozen settings. It waits for the original primary supervisor to exit before starting its eight CPU scoring jobs, preserving the global eight-job limit.
6. Reconcile the one expected original-supervisor failure explicitly; retain any unexpected failure. Publish full analysis only after all 24 scoring jobs have completed. Primary 1.7B analysis still runs independently.

## Durable records

The owned run root contains `fused_handoff/status.json`, retained checkpoint and unfused prefix, checkpoint inspection, original process/supervisor receipts, restored-state verification and numerical/process controls. `execution/4b_mixed/training_fused.json` records the new process. The old training receipt remains untouched. Live snapshots identify the effective training stage and the planned supersession.

The original 12-hour total training deadline is retained from the original 4B start, including the handoff. The old process-specific wall-clock guard is retired at the handoff; the successor enforces the remaining allowance. Frozen `experiment.py`, `run_jobs.py` and `PROTOCOL.md` remain unchanged.
