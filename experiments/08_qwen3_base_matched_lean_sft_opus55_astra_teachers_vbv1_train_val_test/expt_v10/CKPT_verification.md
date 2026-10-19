# Workbook verification continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v10/CKPT_verification.md

**TLDR:** Check all remaining retained Workbook proof candidates and preserve every failed cell.

Created: 10-19-2026 05:17 PDT. Last updated: 10-19-2026 05:27 PDT.
## Goal
- Current-toolchain kernel checks for 10,995 retained Workbook candidates; audit the 74 unresolved cases.
## What ran
- `rl4cv-workbook-verify-v10`:48Lean slots on skampere1, actual controls passed.
- `rl4cv-workbook-unresolved-v10`:4slots, complete74/74; `rl4cv-gx10-lean-setup-v10` installing native environment.
## Results
- Snapshot 1087/10,995checked, 923PASS; unresolved recovery6PASS,68still excluded and retained.
## Stuck / blocked
- No setup blocker:GX10native import and frozen-inspector controls passed;16slots active,64total across hosts.
## Next steps
- SSH skampere1, inspect `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v10/progress.json` and `driver.log`.
- SSH cactushacks-gx10, inspect `~/workspace/rl4cv-gx10/verification-v10/lean_corpus_v10/progress.json` and `driver.log`; native16-worker shard is running.
- Reassemble comments/screens for6recoveries before admitting; publish final row accounting when the queue finishes.
## Brando to-do
- None.
## Log
- 10-19-2026 05:17  -- Froze the remaining10,995proof cohort’s verification protocol and prepared48-slot ordinary-code executor, without model calls.
- 10-19-2026 05:23 PDT -- Confirmed48active compiler processes, collected live row receipts and74-case recovery outcomes, and launched native Lean/Mathlib setup on GX10.
- 10-19-2026 05:27 PDT -- RUNNING, 10-19-2026 05:27 PDT. Cluster: 2,403/10,995 checked, 2,114 PASS with48slots. GX10: 113/1,600 checked, 49 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:28 PDT -- Installed native Lean4.22.0/Mathlib79e94a0onGX10; import and three kernel controls passed,16CPU slots active in`rl4cv-gx10-verify-v10`. Combined64slot capacity; exact-source success relay and milestone publisher prepared.
