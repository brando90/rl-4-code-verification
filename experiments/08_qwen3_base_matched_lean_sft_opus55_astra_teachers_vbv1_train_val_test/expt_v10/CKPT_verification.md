# Workbook verification continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v10/CKPT_verification.md

**TLDR:** Check all remaining retained Workbook proof candidates and preserve every failed cell.

Created: 10-19-2026 05:17 PDT. Last updated: 10-19-2026 05:43 PDT.
## Goal
- Current-toolchain kernel checks for 10,995 retained Workbook candidates; audit the 74 unresolved cases.
## What ran
- Remote: `rl4cv-workbook-verify-v10` on skampere1,48slots; `rl4cv-gx10-verify-v10` onGX10,16slots. Native controls passed.
- Local orchestration: `rl4cv-gx10-receipt-relay-v10` and `rl4cv-v10-progress-publish`; both jobs finish independently if relay stops.
## Results
- RUNNING, 10-19-2026 05:43 PDT. Cluster: 7,090/10,995 checked, 6,370 PASS with48slots. GX10: 1,162/1,600 checked, 376 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
## Stuck / blocked
- None for execution. Other source ingestion and final training-pool assembly remain pending; no new training.
## Next steps
- Inspect remote `lean_corpus_v10/progress.json` on skampere1 and `~/workspace/rl4cv-gx10/verification-v10/lean_corpus_v10/progress.json` onGX10.
- Canonical: `/Users/lethan3/Documents/veribench-projects/rl-4-code-verification/`; owned temporary checkout: `/Users/lethan3/Documents/veribench-projects/.worktrees/rl4cv-lean-verify-10-19-2026/`.
- Root coordinator owns the live publisher checkout; preserve it until both remote runs finish and final receipts are published/mirrored, then remove it under the checkout-cleanup rules.
- Finalize combined checked training data, protected screens and duplicate removal; retain all rejections/unresolved cases.
## Brando to-do
- None.
## Log
- 10-19-2026 05:17  -- Froze the remaining10,995proof cohort’s verification protocol and prepared48-slot ordinary-code executor, without model calls.
- 10-19-2026 05:23 PDT -- Confirmed48active compiler processes, collected live row receipts and74-case recovery outcomes, and launched native Lean/Mathlib setup on GX10.
- 10-19-2026 05:27 PDT -- RUNNING, 10-19-2026 05:27 PDT. Cluster: 2,403/10,995 checked, 2,114 PASS with48slots. GX10: 113/1,600 checked, 49 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:28 PDT -- Installed native Lean4.22.0/Mathlib79e94a0onGX10; import and three kernel controls passed,16CPU slots active in`rl4cv-gx10-verify-v10`. Combined64slot capacity; exact-source success relay and milestone publisher prepared.
- 10-19-2026 05:28 PDT -- RUNNING, 10-19-2026 05:28 PDT. Cluster: 2,794/10,995 checked, 2,478 PASS with48slots. GX10: 204/1,600 checked, 80 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:29 PDT -- Published5a6a187and9a671e4, verified64CPU slots across hosts, imported55then25exact-source GX10successes, and started receipt relay plus milestone publisher. Temporary checkout retained for that live publisher.
- 10-19-2026 05:29 PDT -- RUNNING, 10-19-2026 05:29 PDT. Cluster: 3,202/10,995 checked, 2,845 PASS with48slots. GX10: 273/1,600 checked, 104 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:31 PDT -- RUNNING, 10-19-2026 05:31 PDT. Cluster: 3,524/10,995 checked, 3,145 PASS with48slots. GX10: 342/1,600 checked, 124 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:32 PDT -- RUNNING, 10-19-2026 05:32 PDT. Cluster: 3,903/10,995 checked, 3,495 PASS with48slots. GX10: 433/1,600 checked, 152 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:33 PDT -- RUNNING, 10-19-2026 05:33 PDT. Cluster: 4,190/10,995 checked, 3,756 PASS with48slots. GX10: 501/1,600 checked, 176 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:34 PDT -- RUNNING, 10-19-2026 05:34 PDT. Cluster: 4,493/10,995 checked, 4,027 PASS with48slots. GX10: 571/1,600 checked, 196 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:35 PDT -- RUNNING, 10-19-2026 05:35 PDT. Cluster: 4,845/10,995 checked, 4,332 PASS with48slots. GX10: 643/1,600 checked, 213 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:36 PDT -- RUNNING, 10-19-2026 05:36 PDT. Cluster: 5,146/10,995 checked, 4,606 PASS with48slots. GX10: 712/1,600 checked, 235 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:37 PDT -- RUNNING, 10-19-2026 05:37 PDT. Cluster: 5,450/10,995 checked, 4,885 PASS with48slots. GX10: 802/1,600 checked, 266 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:38 PDT -- RUNNING, 10-19-2026 05:38 PDT. Cluster: 5,828/10,995 checked, 5,226 PASS with48slots. GX10: 870/1,600 checked, 284 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:39 PDT -- RUNNING, 10-19-2026 05:39 PDT. Cluster: 6,120/10,995 checked, 5,494 PASS with48slots. GX10: 942/1,600 checked, 307 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:41 PDT -- RUNNING, 10-19-2026 05:41 PDT. Cluster: 6,422/10,995 checked, 5,761 PASS with48slots. GX10: 1,013/1,600 checked, 328 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:42 PDT -- RUNNING, 10-19-2026 05:42 PDT. Cluster: 6,800/10,995 checked, 6,103 PASS with48slots. GX10: 1,096/1,600 checked, 352 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
- 10-19-2026 05:43 PDT -- RUNNING, 10-19-2026 05:43 PDT. Cluster: 7,090/10,995 checked, 6,370 PASS with48slots. GX10: 1,162/1,600 checked, 376 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.
