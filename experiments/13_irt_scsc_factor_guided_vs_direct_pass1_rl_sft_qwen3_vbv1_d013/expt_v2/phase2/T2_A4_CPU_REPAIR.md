# Experiment 13 v2-S2 T2: CPU-offloaded checkpoint hash repair under A4

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/T2_A4_CPU_REPAIR.md>

**TLDR:** T2 attempt 2 remains INCOMPLETE-INFRA. Its full generation, scoring, trainer probability recomputation and partial before-update checkpoint are retained; no experiment optimizer update or gate statistic completed. The successor changes only checkpoint hashing and its infrastructure preflight, preserving every scientific setting and resource cap. Complete attempt 3 is the final permitted attempt under A4.

## Reproduced defect and repair

The frozen trainer uses central-processing-unit (CPU) offloading on a one-rank CUDA device mesh. Calling `DTensor.full_tensor()` on its offloaded parameters requested a CPU collective from an NCCL-only process group and raised `RuntimeError: No backend type associated with device type cpu`. The native checkpoint files were saved before the digest failed. The native saver's zero-learning-rate Adam initialization was restored in the existing `finally` path; no experiment `policy.train` call occurred. [Attempt 2 evidence](T2_A6_attempt2_result.json) and [resources](T2_A6_attempt2_resources.json) remain final infrastructure records.

`worker_state.complete_tensor` reads the complete local tensor only when the mesh has exactly one rank and local/global shapes agree. Parameter and recursive optimizer digest serialization, tensor dtype, byte order and values are unchanged. Multi-rank tensors still use the full gather, and a mismatched local shape is rejected. No model, sampler, reward, optimizer, seed, threshold, token cap or allocation changes.

The installed Torch regression uses real CPU distributed tensors with row sharding, column sharding, replication and partial placement. It reproduces the exact observed error without mocking, using a real process group with no registered CPU backend. It additionally injects that error across the four placements, then checks the repaired parameter digest against an independently constructed legacy digest and checks nested optimizer hashes against ordinary full tensors. It also rejects shape mismatches and prevents multi-rank shard-only hashing. This CPU test does not claim to exercise CUDA/NCCL transport.

Before numbered attempt 3, the new bound preflight must construct the actual frozen NeMo trainer on an exclusively leased idle device, verify real CPU-offloaded single-rank tensors, compute complete parameter and optimizer digests, and close its Ray cluster. The existing non-probe vLLM engine health check then runs on that same claimed device. Both checks precede admission, use no experiment prompt and perform no optimizer update. The existing 900-second health cap remains unchanged.

## Verification and chronology

Focused installed regression, native checkpoint replay/export and provenance checks: **21 passed in 14.30 seconds**, direct exit 0, no device claims. Required Lean integration: **1,175 passed, 3 skipped, zero failures in 527.88 seconds**, direct exit 0 ([receipt](T2_A4_CPU_full_test.json)).

The [successor learning-pilot lock](../locks/LP_A6_S2_T2_A4_CPU.json) retains the previous lock and every unchanged binding at its previous hash. The separately published A4 admission lock will name the published repair revision, regression receipt, failed-attempt record and each changed binding before complete attempt 3. Neither failed attempt's outputs enter attempt 3 statistics. Both earlier costs remain charged: **1.3994773723681768 of 10.0 device-hours** cumulative; the per-attempt limit stays **8.0 device-hours**, at most three numbered attempts.
