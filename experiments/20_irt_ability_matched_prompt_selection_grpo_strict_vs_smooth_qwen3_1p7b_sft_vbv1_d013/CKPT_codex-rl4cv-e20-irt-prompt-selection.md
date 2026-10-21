# CKPT Codex: experiment 20 IRT prompt selection for GRPO

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_codex-rl4cv-e20-irt-prompt-selection.md>

**TLDR:** Single-writer continuation of `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` under the unchanged runbook. Deployment `deploy_50715cf54e614ecf914f0f7da4aae03c`, Codex gpt-6-astra ultra, personal ~/.codex, skampere1.

Created: 10-21-2026 13:44 PDT
Last updated: 10-21-2026 13:55 PDT

## Goal
- Test whether IRT prompt selection improves held-out validation strict pass@1 at equal rollouts, within the runbook gates and 200 GPU-h/$0 API caps.
## What ran
- Adopted pushed branch `e20-irt-prompt-selection` at `e39d620abf44e4538f62f49f95027eb1da82ecf4`; clean tree; policy `217b6ee6775455ad3becb8e7971244d6ffce31ce` refreshed. Runbook and both predecessor checkpoints read in full.
- Runtime verified: Codex process 3183137, gpt-6-astra/ultra, `--dangerously-bypass-approvals-and-sandbox`; named tmux and `watch-e20` present; predecessor tmux absent. Sherlock runner online; remote brando9 on sh03-01n70.
- Live-state discrepancy: original smoke 48845232 FAILED (56 s); newer smoke 48857034 RUNNING (submission origin/logs being traced). All four Phase 0a tasks 48841018_[0-3] RUNNING. No duplicate launch.
## Results
- Calibration 1,792/4,312 generation rows at 13:54 PDT, scores pending. Smoke reached first-update CPU scoring; 0% H100 compute / 5,393 MiB during the observed scoring interval.
- No scientific outcome yet. Slurm allocation at 13:43 PDT: Phase 0 = 2.8033 GPU-h / 10; smoke = 0.2117 GPU-h at 13:46 PDT / pilot cap 15 (running allocation, both prior failures included). Main/evaluation 0; API $0.
## Stuck / blocked
- Nothing terminal; full verification PASS (1,391 passed, 41 skipped, 6 subtests); runtime source captured and hashed; submission session unresolved (before takeover). Local verification found a missing external scorer and a legacy test expecting ultimate-utils six parents above; verified in an isolated worktree at the compatible depth, without edits to other experiments.
## Next steps
- [p 10/10] Publish the verified takeover receipt, then monitor owned jobs at least 60 s apart. Exact: `sherlockctl exec 'tail -100 $SCRATCH/rl4cv_sherlock/e20/phase0/logs/e20_smoke_train_48857034.log'`.
- [p 9/10] On completed calibration: materialize, CPU score and partial-credit arrays, fetch committed per-cell table, then `/lfs/skampere1/0/brando9/venvs/rl4cv_e20/bin/python experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/analyze_phase0b_e20.py --workers 8 --two-skill` (CUDA_VISIBLE_DEVICES empty locally).
- Verification worktree: `/lfs/skampere1/0/brando9/.worktrees/rl4cv-e20-checks`, owned by this worker; same source revision, external pins restored, matches legacy relative-mail-dependency path. Remove after final verification.
## Brando to-do
- None.

## Log
- 10-21-2026 13:44 PDT -- Codex takeover verified against live Git, processes and Sherlock; adopted calibration; newer smoke differs from handoff and is under investigation. Native helper `/root/locate_experiment_log` (gpt-5.6-terra/medium) is locating the requested Google experiment log; root remains sole repository writer.
- 10-21-2026 13:49 PDT -- Reconciled two failed infrastructure attempts (48845232: missing SciPy, 56 s; 48855196: context limit, 109 s) and adopted 48857034 (A seed 0, 2 smoke updates, output train/runs/A_s0). Runtime source/launcher captured in expt_v1/results/receipts/runtime_takeover; only trainer code difference is context capacity 16384 -> 20480. Google log located: https://docs.google.com/document/d/1KKKabJJArClVmXcaxfTF5jxk8nF1oHmCH08d44jbqUg/edit .
- 10-21-2026 13:53 PDT -- Restored both frozen external dependencies (scorer 59059a2, prompt/judge code c11b99b) for deterministic tests; no other experiment edits. First full check stopped after exposing three environment/path failures (1,226 passed, 40 skipped); corrected-layout full check launched with CPU-only/thread-limited settings. Smoke START email accepted via uutils SMTP; inbox confirmed Phase 0a START already existed.
- 10-21-2026 13:55 PDT -- Calibration reached 1,792/4,312 saved rows; no scored outcome yet. Corrected smoke accounting to include previously unrecorded job 48855196: 0.2117 GPU-h through 13:46 PDT.
- 10-21-2026 13:55 PDT -- Full make test PASS in the verified compatible-layout worktree: 1,391 passed, 41 skipped, 6 subtests. Runtime source/launcher syntax checks and git diff --check passed. Takeover records ready to commit/push.
