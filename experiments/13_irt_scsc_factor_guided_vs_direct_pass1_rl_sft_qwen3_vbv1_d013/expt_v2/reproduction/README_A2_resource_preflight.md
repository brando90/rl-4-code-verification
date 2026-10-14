# Experiment 13 version 2: A2 resource-preflight correction

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/reproduction/README_A2_resource_preflight.md>

**TLDR:** The first Amendment A2 launch stopped before reading route results or reserving any retry because its preflight compared the requested memory limit with the kernel's page-rounded limit. A separate launcher corrects that comparison while preserving the original A2 implementation, lock, worker, measurement code, inputs, retry ceiling and actual resource limits.

Recorded: 10-13-2026, after the original reproduction completed and before any A2 measurement attempt. The original public result was INCOMPLETE, with ordinary equality reported FAIL; that observation is retained. No test cell, value, factor or source was inspected to diagnose this launcher failure.

The original execution lock requests 1,044,624,427,008 bytes through systemd. The request is not divisible by the host's 4,096-byte page size. A dedicated, zero-measurement control with the exact same request observed `memory.max = 1,044,624,424,960`, the request rounded down by 2,048 bytes. The original launch receipt's `MemoryMax` is systemd's requested value, not the kernel file's effective value. The initial A2 verifier incorrectly required those two representations to be identical.

The failure occurred in `verify_bindings`, before manifest/results access and before coordinator registration or retry reservation. The ledger contained zero attempt-2 rows. The initial launch log, sanitized error and private traceback remain under the work root; they are not overwritten. This is an operational preflight failure, not a rerun of a measured gate or a new cell attempt.

`a2_resource_launcher.py` calls the unchanged original verifier. It handles only its exact resource-representation error, after all original file bindings and the scope identity have passed. It then requires the exact page-rounded frozen cap; neither a larger cap nor a smaller cap passes. A supplemental lock binds this launcher, its tests, this justification, the control receipt and the original A2 lock. Both locks remain append-only.

The new parent dispatches separate opaque and ordinary children through this launcher, retaining the original reconciliation function, worker command, attempt ledger, route isolation and admission computation. Recovery uses the original resume path because the failed preflight created empty route directories; no completed cell is rerun and no attempt 3 is permitted. Original A2 files and all first-attempt evidence remain unchanged. The new launch log has a distinct name.

Publish this justification, the correction, supplemental lock and passing required integration suite before the corrected launch. Report the preflight failure and correction alongside the eventual R2 decision. Amendment A2's tolerance and every scientific gate remain unchanged.
