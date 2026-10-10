# Experiment 13 review and phase-0 checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/CKPT_e13.md>

**TLDR:** One Astra/ultra review is reconciled; the executable phase-0 handoff reuses verified source/strict-control receipts. This checkpoint records a publishable plan phase, not experiment completion.

Created: 10-09-2026. Last updated: 10-09-2026 21:26:30 PDT
Status: RUNNING — publication in progress; historical factor scoring and training gated.

Original base/input HEAD: `be43d3a8fcd9a1df5b77058be516821f3a7629d0`. Owner: `rl4cv13-review-10-09`, sole writer of `/lfs/skampere1/0/brando9/recovery_rl4cv13/repo` until terminal receipt. Branch: `recovery/rl4cv13-plans`. Actual reviewer: `gpt-6-astra` / `ultra`, session `01a123fd-3adf-7133-b95c-cf293feed08d`, full access/approval never verified in native turn metadata.

Read `REVIEW.md`, `REVIEW_RESULT.json`, `PHASE0_READY.json`, `results.md` and `RUNBOOK.md`. Original request/hashes are immutable. Reviewed bytes/diff: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/review_input`. Primitive controls and manifest: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls`; all 20,520 source hashes match. The original 14/15 fixture result and the separate printed-error expectation reconciliation are retained. No duplicate source reads or model/training jobs are needed for handoff.

Completed deterministic checks: 23 contract tests; full suite 226 passed / 21 conditional integration skips; source pin/hash checks; 15 actual Lean fixture executions with source-bound reconciliation. Before merge: rerun checks on the rebased exact head, inspect staged diff/secret patterns and verify merged state.

Rebase plan recorded BEFORE rebase: backup branch `recovery/rl4cv13-reviewed-before-rebase`; old merge base `be43d3a8fcd9a1df5b77058be516821f3a7629d0`; freshly fetched main `8600731c977612b54c62ce11377942d4bda6bdd8`. Commit this checkpoint with the completed phase, then create the backup at that tip. Compare range-diff and every owned path after rebase; preserve any concurrent experiment-12 milestone changes. Final receipt records the verified and merged revisions.

Current resource state: no device allocation. 260–350 A100 hours remains an estimate. Existing SNAP authorization is sufficient within available resources; scientific gates and real allocation remain prerequisites. `09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` stays failed/zero updates. `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` keeps its exhausted probe allowance. No edits to `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` or its environment.

Immediate next command after ownership transfer:

```bash
env -u PYTHONPATH /lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/.venv/bin/python /lfs/skampere1/0/brando9/recovery_rl4cv13/repo/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/phase0_resume.py --controls /lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls
```

Then implement the missing declaration adapter and sealed full historical equality audit, freeze L1/F0/F1, and execute admitted CPU work in a new named session/watch. L1 admits reproduction before requiring it for G0/G1. Training remains blocked until its separate LP/L2 sequence, coverage controls, measured resources and valid devices pass. Root sends deduplicated recovery notifications. Primitive watcher had no reboot persistence or automatic account failover.
