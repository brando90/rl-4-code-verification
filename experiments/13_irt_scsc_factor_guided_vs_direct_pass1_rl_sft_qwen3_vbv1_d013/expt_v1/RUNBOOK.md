# Experiment 13 executable phase-0 handoff

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/RUNBOOK.md>

**TLDR:** The single requested review is reconciled. Reuse the completed source inventory/authored controls, then implement the declaration adapter and sealed historical equality audit under the recorded locks; model fitting and training retain their gates.

Created: 10-09-2026. Last updated: 10-09-2026 21:23:50 PDT

## Owned paths and verification

Repository: `/lfs/skampere1/0/brando9/recovery_rl4cv13/repo`. Preparation branch: `recovery/rl4cv13-plans`. One writer transfers back to recovery master only after terminal receipt. Runtime files: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review`. Review: `REVIEW.md`; immutable original inputs: `../REVIEW_REQUEST.json` and the private `review_input/` snapshot. Exactly one acceptance reviewer was used (`gpt-6-astra` / `ultra`). Do not launch a second reviewer for deterministic reconciliation.

Private test environment: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/.venv`. It has its own NumPy, pytest and PyYAML; strip inherited `PYTHONPATH` to avoid the shared evaluator environment. Verification command:

```bash
cd /lfs/skampere1/0/brando9/recovery_rl4cv13/repo
env -u PYTHONPATH PATH=/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/.venv/bin:$PATH make test
git diff --check
```

## Admitted CPU preparation command

The following exact invocation is the completed/reusable preparation procedure. **Check `PHASE0_CONTROLS_RESULT.json` and the private receipt first; do not duplicate a successful run.** It is write-once; a necessary later repetition uses a new explicit output path, never overwrites locks or evidence.

```bash
cd /lfs/skampere1/0/brando9/recovery_rl4cv13/repo
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/.venv/bin/python /lfs/skampere1/0/brando9/recovery_rl4cv13/repo/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/phase0_prepare.py \
 --scorer-root /lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench_scorer \
 --lake-dir /lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src \
 --e08-root /lfs/skampere1/0/brando9/rl4cv_e08 \
 --e05-root /lfs/skampere1/0/brando9/rl4cv_e05 \
 --out /lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls
```

The named session is `codex-rl4cv13-phase0-controls`; its failure-aware watcher is `codex-rl4cv13-phase0-watch`, `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/watch_phase0.py`. It checks process/session completion, nonzero exit, death and 30-minute timeout every ten seconds. Result/progress paths are in `PHASE0_READY.json`. It does not survive reboot or perform automatic account failover. Master retains recovery ownership and its independent 30-second watch.

## Immediately dispatchable next unit

[p 10/10] Build the declaration adapter against the existing locked source manifest because that is the missing prerequisite for historical scorer equivalence. Read `PHASE0_CONTROL_PLAN.md`, implement command-span/theorem/axiom extraction in the owned experiment directory, and run its full counterexample fixture matrix. The completed primitive strict controls are an oracle check, not acceptance of an adapter that does not exist yet. No device allocation is required for this CPU unit.

Source manifest: `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls/validation_source_manifest.jsonl`. All 20,520 listed source hashes were checked; the 5,400 unavailable parent-ladder cells remain declared separately. Reuse these rows and raw source paths. For the full 21,504 base-cell equality control, retain the 3,240 overlap cache and implement a sealed opaque test audit before claiming full reproduction. Missing historical cells are not replaced or dropped.

Before any historical factor execution, freeze L1 and F0/F1 with `rl4cv.forecast.freeze_forecast`, binding adapter code, complete source manifest, folds/features/config and the reviewed G0/G1 thresholds. Run reproduction under L1; require its success only BEFORE G0/G1, so no circular dependency exists. An unimplemented command is not recorded as a run.

Then follow `../PROTOCOL.md`: G0 -> G1; resource/probability-admitted train anchors/H2; LP -> T1 -> T2/T3/T4 -> pilot T5 -> measured L2 -> main. The train-only mutation/coverage gate precedes B/C learning. A scientific failure is retained; no adaptive reward/seed expansion or account switch resets it.

## Residual blockers and preserved state

The declaration adapter and full sealed equality audit are not implemented/validated. No G0/G1/H2 outcome, fitted reward, rollout generation or optimizer update is claimed. No current allocation exists; the 260–350 A100-hour estimate is not a grant. A bounded probe lease/resource plan precedes T1, and a measured pilot projection precedes main. SNAP's explicit task preapproval applies; no additional human authorization gate is inserted.

`09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` remains failed with zero optimizer updates. `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` keeps its exhausted layout-probe allowance and independent owner. `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` keeps its environment and worker. Root handles notifications.
