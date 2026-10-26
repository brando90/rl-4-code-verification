# Experiment 13 v2-S2: owned-worker shutdown before generator health

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/T2_A4_HANDOFF_REPAIR.md>

**TLDR:** The CPU-offloaded checkpoint hash repair passed on the actual frozen model: 399/399 distributed tensors and 4,411,424,256 elements. The next health step encountered its just-shut-down owned Ray worker in the device census and failed reading that exiting process's environment. No third numbered attempt was admitted. This infrastructure successor waits for the owned worker's exit and removal from the census, preserving the existing device guard and every scientific setting.

The [published preflight failure](T2_A4_CPU_preflight_failure.json) retains the actual hash success, log, runtime configuration, cleanup, immutable failed-state snapshot and 0.052590086923705204 additional device-hours. All eight T2 leases are released; total T2 usage is 1.452067459291882 of 10.0 device-hours. Its original directory and artifacts remain in place. Attempts 1 and 2 remain INCOMPLETE-INFRA with no experiment optimizer update or gate statistic.

## Failure-class regression and repair

An exited but unreaped child on this host raises the exact `PermissionError` when its `/proc/<pid>/environ` is read. The regression reproduces this kernel behavior without mocking the environment read. A stale device-census entry then reproduces the unchanged guard's failure. The repaired handoff waits until the exact owned worker, identified by process ID and Linux birth ticks, has exited and its process ID is absent from the graphics-processing-unit (GPU) compute census. The test also checks that the original guard continues to reject a live foreign process.

The preflight obtains identities only through its own NeMo worker handles. Shutdown synchronization is read-only: it sends no signals and never suppresses a device-ownership error. It waits at most 60 seconds inside the unchanged 900-second health allocation. Process-ID reuse while still in the census fails closed. The original device guard runs after the wait; the sampler, model, dtype, optimizer, seeds, thresholds, scorer and allocation are byte-identical.

## Explicit pre-admission reconciliation

The [successor learning-pilot lock](../locks/LP_A6_S2_T2_A4_HANDOFF.json) retains the preceding hash repair and its evidence. The new controller requires the published failure, exact old state identity, verified cleanup, exactly two infrastructure-only numbered attempts, no third admission and no generated update response. Busy-device observations preserve that state and poll every 15 minutes. A fresh health reservation gets a unique `preflight_handoff_*` ledger key; its time is charged to prospective attempt 3 and the original cumulative allocation.

A successful fresh model/shutdown/generator preflight admits attempt 3 once, records the successor state and resumes the original gate driver. A failed or interrupted health launch cannot be replayed automatically. The original failed-state snapshot and every old cost remain hash-bound. No failed-attempt output enters a statistic. The third numbered gate attempt remains the final permitted attempt under A4.

Focused checks: **23 passed in 10.31 seconds**, direct exit 0, no devices or experiment model calls. Required Lean integration: **1,194 passed, 3 skipped, zero failures in 532.46 seconds**, direct exit 0 ([receipt](T2_A4_HANDOFF_full_test.json)).
