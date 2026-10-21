# CKPT e20: IRT ability-matched prompt selection for GRPO (Azalia's test, IRT version)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_e20.md>

**TLDR:** Resume record for experiment 20. Dispatcher: Claude Code session local_268be283 (Mac); worker: tmux `codex-rl4cv-e20-irt-prompt-selection` on skampere1 (Codex gpt-6-astra, ultra, personal profile, full access).

Created: 10-21-2026 11:18 PDT
Last updated: 10-21-2026 14:19 PDT

## Goal
- Finish the failed-gate closure of 20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013; no new phases.
## What ran
- Adopted Phase 0a 48841018_[0-3] and smoke 48857034; two earlier smoke failures 48845232/48855196. Sole repository writer Codex gpt-6-astra/ultra, full access; predecessor fenced.
- Takeover commit eaa6ef96 pushed; operational corrections and observed gate evidence verified locally.
## Results
- Smoke completed 2/2 updates, exit 3:0 at 14:09:11 PDT; max mismatch 22,654/864,717 = 2.61982% >1%. 17/256 strict, 6/32 active groups, 0/256 unresolved.
- Calibration 2,816/4,312 saved, unscored; allocated Phase 0 5.1033 GPU-h/10; final smoke 0.5900/15 including both earlier failures. API $0. IRT treatment effect not measured.
- make test: 1,415 passed, 17 skipped, 6 subtests; 3 warnings. Google experiment log updated and read back.
## Stuck / blocked
- STOPPED at trainer log-probability gate. Existing adopted jobs must finish naturally under the no-cancellation instruction. No new scoring, IRT fit, pilot/main/evaluation or retry.
## Next steps
- [p 10/10] Monitor `/tmp/e20_live_monitor.log` and `/tmp/e20_live_monitor/latest.json`; owned local monitor `/tmp/e20_monitor.py` polls every 300 s, exits when adopted jobs terminal. Do not duplicate monitor or Slurm polls.
- [p 10/10] On terminal state fetch final raw-generation manifest and smoke receipts; record actual allocation, final docs/plots, PR into main (do not merge), Google final bullet, E20_FINISHED.txt with result commit, and RUN DONE mails.
- Verification worktree `/lfs/skampere1/0/brando9/.worktrees/rl4cv-e20-checks` holds copied operational fixes; preserve/compare before cleanup. Remove after final verification.
## Brando to-do
- None for this closure. A future backend-repair experiment requires a new prospective run; do not weaken this failed gate.

## Log
- 10-21-2026 11:18 PDT -- folder claimed on main; runbook written; dispatching the worker.
- 10-21-2026 11:38 PDT -- dispatch receipt logged (deploy_ed87a5b1900b45d2af6e22c1707cc31e, cc profile, watch-e20); worker checkpoint CKPT_cc-rl4cv-e20-irt-prompt-selection.md created; README dispatch line corrected.
- 10-21-2026 12:40 PDT -- worker change: Claude Fable 5.1 (personal account) -> Codex gpt-6-astra ultra (personal ~/.codex), reason: Claude personal weekly allowance reserved; implementation-only role, no measured model or protocol change. Handoff state: branch e20-irt-prompt-selection pushed; Sherlock jobs 48841018 (Phase 0a, running/pending), 48845232 (trainer smoke, pending) left running; worker checkpoint holds the exact next commands.
- 10-21-2026 13:44 PDT -- Codex start: deploy_50715cf54e614ecf914f0f7da4aae03c, gpt-6-astra ultra, personal ~/.codex; full access verified in process arguments, predecessor fenced. Implementation-only role; no measured model, judge, dataset or protocol change. Live-state discrepancy (newer smoke) recorded in the Codex checkpoint.
- 10-21-2026 13:55 PDT -- Codex takeover verification passed (make test: 1,391 passed, 41 skipped, 6 subtests); calibration 1,792/4,312 rows, trainer smoke 48857034 scoring. Current command and receipts are in the Codex checkpoint.
- 10-21-2026 14:05 PDT -- Adopted smoke update 1 violates the frozen log-probability gate: (21,721 out-of-tolerance + 167 outside-support) / 842,189 tokens = 2.59894%, above 1%. The implementation takes the maximum over smoke updates, so the gate cannot recover on update 2. No pilot/main/evaluation admission. Calibration is 2,304/4,312 generated rows; existing jobs are being reconciled at the stop boundary.
- 10-21-2026 14:09 PDT -- Gate evidence and 128 smoke rollout records preserved; full verification PASS (1,415 passed, 17 skipped, 6 subtests). Google experiment log readback verified. Adopted jobs drain naturally; local 300-second monitor active.
- 10-21-2026 14:13 PDT -- Gate evidence and operational fixes pushed in b0ef925e; draft PR https://github.com/brando90/rl-4-code-verification/pull/20 opened and mergeable. Artifact-only closure collector passed denominator/missing-cell/duplicate fixtures; no scoring or new jobs.
- 10-21-2026 14:14 PDT -- Smoke 48857034 finished both updates and failed the gate (exit 3:0, max 2.61982% versus 1%); final smoke allocation including two infrastructure failures is 0.5900 GPU-h. 256 rollout records and native final check downloaded with SHA-256 verification. Calibration 2,688/4,312 saved; only calibration remains running.
- 10-21-2026 14:19 PDT -- Calibration progress: 2,816/4,312 generations, 0/4 chunks complete, 4 adopted jobs active; Phase 0 allocated 5.1033/10 GPU-h as of 10-21-2026 14:18:15 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:19 PDT -- Closure collector and final smoke artifacts verified: make test PASS (1,415 passed, 17 skipped, 6 subtests, 295.48 s). Smoke DONE email delivered (Gmail 1a16051be5758f1a); Google final smoke bullet readback verified.
