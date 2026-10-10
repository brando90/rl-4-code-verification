# Experiment 13 review and phase-0 checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/CKPT_e13.md>

**TLDR:** One Astra/ultra review is reconciled; the executable phase-0 handoff reuses verified source/strict-control receipts. This checkpoint records a publishable plan phase, not experiment completion.

Created: 10-09-2026. Last updated: 10-09-2026 22:50:40 PDT
Status: RUNNING — adapter landed; sealed equality reproduction is executing; training remains gated.

Original base/input HEAD: `be43d3a8fcd9a1df5b77058be516821f3a7629d0`. Current coordination/publication owner: recovery master `deploy_16e6b761a004445db113437e27f45456`. The prior Terra/high implementation worker exited 0; its native thread `01a1241d-1151-7ed0-85ba-72f9e93c9e7d` is retained. The ordinary audit owns computation; publication uses an isolated integration checkout so active source bytes remain unchanged. Historical plan reviewer: `gpt-6-astra` / `ultra`, session `01a123fd-3adf-7133-b95c-cf293feed08d`, full access/approval never verified in native turn metadata.

Read `REVIEW.md`, `REVIEW_RESULT.json`, `PHASE0_READY.json`, `results.md` and `RUNBOOK.md`. Original request/hashes are immutable. Reviewed bytes/diff: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/review_input`. Primitive controls and manifest: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls`; all 20,520 source hashes match. The original 14/15 fixture result and the separate printed-error expectation reconciliation are retained. No duplicate source reads or model/training jobs are needed for handoff.

Completed deterministic checks: 23 contract tests; full suite 226 passed / 21 conditional integration skips; source pin/hash checks; 15 actual Lean fixture executions with source-bound reconciliation. Before merge: rerun checks on the rebased exact head, inspect staged diff/secret patterns and verify merged state.

Rebase plan recorded BEFORE rebase: backup branch `recovery/rl4cv13-reviewed-before-rebase`; old merge base `be43d3a8fcd9a1df5b77058be516821f3a7629d0`; freshly fetched main `8600731c977612b54c62ce11377942d4bda6bdd8`. Commit this checkpoint with the completed phase, then create the backup at that tip. Compare range-diff and every owned path after rebase; preserve any concurrent experiment-12 milestone changes. Final receipt records the verified and merged revisions.

Current resource state: no device allocation. 260–350 A100 hours remains an estimate. Existing SNAP authorization is sufficient within available resources; scientific gates and real allocation remain prerequisites. `09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` stays failed/zero updates. `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` keeps its exhausted probe allowance. No edits to `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` or its environment.

Historical plan handoff command (already completed; do not rerun as recovery):

```bash
env -u PYTHONPATH /lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/.venv/bin/python /lfs/skampere1/0/brando9/recovery_rl4cv13/repo/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/phase0_resume.py --controls /lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls
```

The declaration adapter and opaque equality audit have now been implemented. Continue the existing admitted process; do not duplicate it. L1 admits reproduction before requiring it for G0/G1. Training remains blocked until its separate LP/L2 sequence, coverage controls, measured resources and valid devices pass. Root sends deduplicated recovery notifications. Primitive watcher had no reboot persistence or automatic account failover.

## 10-09-2026 opaque-audit execution

Parser-backed adapter change 11 landed at `7014bae8229266c643da8bf192e0a2b3cb8329d5`. The sealed base manifest is complete at 21,504/21,504 cells (`06fcbcda…`); it binds the three scored inputs and split manifest without disclosing a row, label, factor or example. `L1_audit_v1` is retained, while append-only `L1_audit_v2` (`c1bcff67…`) and F0/F1 successors bind the corrected frozen vacuity import before the first successful historical measurement. The named `codex-rl4cv13-opaque-reproduction` CPU-only session and `codex-rl4cv13-opaque-watch` watchdog are live with one-cell heartbeats. At checkpoint, only sanitized progress is public; G0/G1, fitting and training remain unadmitted.

## Verified landing

LANDED ef1c612d73f8c7b231ea94dd3baa0a14d21c282b https://github.com/brando90/rl-4-code-verification/pull/10 10-09-2026 21:34:22 PDT

Verified branch head `7ecc28ddafe0a473463d81e3dd16aed784ed3fc3`; GitHub reports MERGED. Rebase range-diff retained the one patch unchanged; owned-path diff against merged main is empty. Post-rebase `make test`: 226 passed, 21 conditional skips; `git diff --check` and the phase-0 handoff verifier passed. Root owns notifications and the next phase after receipt; this phase does not complete the experiment.

## Current opaque-audit implementation publication — 10-09-2026 22:50:40 PDT

Full repository `make test` completed with 233 passed, 24 skipped, exit 0 (193.78 seconds); log `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_phase0/master_full_test.log`. The skips are reported as skips, not checks passed. Prior 30 source-bound Lean controls remain separate. Three new integrity tests reject replacement sources, duplicate cells and incomplete denominators. The audit adds strict source/model/task/sample joins and retains initial integrity rejection and zero-cell vacuity-import failure before append-only v2. No model calls or accelerators.

Current public completeness: 101/21,504 at 2026-10-10T05:50:39+00:00; equality PENDING. Named scientific session `codex-rl4cv13-opaque-reproduction`, launcher PID2883852/start11172407, Python child2883861/start11172408; skampere1 boot83765e57-f5f3-4202-b7b4-18f1eb506043. Authoritative observer `codex-rl4cv13-audit-root-observer-v2`, PID2961961/start11207134, ten deterministic fixtures passed. Observer binds process starts, source/lock/manifest hashes and full denominator; DONE requires complete PASS plus terminal exit0 and both processes exited. The earlier legacy observer is not authoritative. Automatic account failover and reboot persistence are absent.

The v2 lock has a conflicting duplicate program hash; `locks/L1_audit_v2_metadata_erratum.json` records the exact conflict after execution started. Original lock/forecast bytes stay unchanged; the frozen adapter hash matches actual measured code. No claim of universally consistent prospective metadata. The complete diagnostic receipt requirement remains for later factor measurement: this equality audit stores private scalars but does not persist complete probe evidence. It cannot independently admit factor fitting or training. No sealed examples, labels or outcomes were read to make this implementation diagnosis.

Exact continuation: read the sanitized `receipts/rl4cv13_audit.json` and observer state under the recovery work directory. Keep current process/lock IDs; preserve FAIL rather than retrying until PASS. Only a complete successful historical equality audit allows consideration of the separate source-bound train/validation measurements and original G0/G1 gates; those are not admitted by this publication. No device lease is claimed.

Pre-rebase publication plan: owned branch `recovery/rl4cv13-opaque-audit-10-09`; backup `backup-rl4cv13-opaque-audit-10-09`; old base `7014bae8229266c643da8bf192e0a2b3cb8329d5`; fetched main `39f41e6a268ac84e8c39025c475d59a41099beb8`. Preserve concurrent experiment12 documentation. Rebase only isolated integration checkout, compare range-diff and exact owned-path bytes, then repeat deterministic checks before guarded publication.

Integration refresh 10-09-2026 22:55:43 PDT: main advanced with experiment12 documentation only. Before second rebase, backup `backup-rl4cv13-opaque-audit-2256`; old merge base `39f41e6b` (full value 39f41e6a268ac84e8c39025c475d59a41099beb8); fetched main `e5c2b4002c03199e2508aeefd9e16c59e47e268d`. The first rebased full suite passed233/24, exit0 in190.93seconds. Preserve all21ownedpaths exactly across this second integration.
