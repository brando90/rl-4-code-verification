# Experiment 13 version 2 terminal process cleanup

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/operations/README.md>

**TLDR:** Under PLAN section 7's run-bound cleanup rule, stop registered Lean descendants only after their cell worker has exited and written a terminal receipt. This operational action neither changes a measurement nor retries a cell.

During full historical reproduction, seven exited workers had fourteen registered Lean descendants remaining after subprocess timeouts. The frozen coordinators waited for their groups to drain, while repeated liveness scans increased contention on the shared recovery lock. These children no longer served an active measurement: each worker had already written its source-bound terminal receipt.

The owner ran the accompanying helper on 10-13-2026. It checks the dead worker identity, frozen source binding, terminal receipt, and every descendant's recorded process identifier, start ticks, boot identifier and process group. It refuses cleanup without a terminal receipt, or when an unregistered process is present. It rechecks under the shared recovery lock, then signals individual verified processes through process-identifier file descriptors. Healthy workers and children whose measurement has not finished are preserved. No source-specific test result or component is emitted.

The first cleanup stopped fourteen descendants from seven completed workers using termination signals; no forced kill was needed. The existing measurement receipts were collected without alteration, and the attempt ledger still recorded zero retries. A subsequent run found zero eligible children and sent zero signals; both coordinators stayed alive. Full reproduction remained pending at 9,121 of 38,784 receipts. These are operational counts, not scorer-equality or hypothesis results.

The helper is post-lock operational tooling. All 51 scientific lock bindings remain byte-identical. It does not alter probe/oracle code, source bytes, sampling, resource ceilings, factors, labels, gate thresholds or attempts. This is cleanup authorized by PLAN section 7, not a repaired scoring run or a gate retry. Private audit records preserve receipt hashes and process identities under `$WR/state/R2_terminal_child_cleanup_*.json`; public records expose only operational counts. The owner invokes it periodically while supervising the unchanged reproduction.
