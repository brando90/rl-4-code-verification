# CKPT e20: IRT ability-matched prompt selection for GRPO (Azalia's test, IRT version)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_e20.md>

**TLDR:** Resume record for experiment 20. Dispatcher: Claude Code session local_268be283 (Mac); worker: tmux `cc-rl4cv-e20-irt-prompt-selection` on skampere1 (Claude Code claude-fable-5-1, max, personal profile, full access).

Created: 10-21-2026 11:18 PDT
Last updated: 10-21-2026 11:38 PDT

## Goal
- Does IRT-online prompt selection (C) raise validation strict pass@1 over uniform (A), a pass-rate filter (S) and DAPO (E) at matched rollouts, and how does it interact with a smooth reward (B, D)?

## What ran
- 10-21-2026 11:38 PDT: worker running (deployment `deploy_ed87a5b1900b45d2af6e22c1707cc31e`, Claude Code claude-fable-5-1 at max effort, profile cc = the `clauded` wrapper with the personal `~/.claude` config, bypass permissions on). Host watch: tmux `watch-e20` on skampere1 runs agents-config `watch_worker.sh` on the session and writes `/lfs/skampere1/0/brando9/e20_watch/STATE.txt`; 75 minutes idle without `expt_v1/results/E20_FINISHED.txt` counts as a stall. Dispatcher record: main 9d555e67, experiment 19 `CKPT_irt_lane.md`. Worker resume record: [CKPT_cc-rl4cv-e20-irt-prompt-selection.md](CKPT_cc-rl4cv-e20-irt-prompt-selection.md) (canonical from now on; this file is updated at phase boundaries).
- 10-21-2026 11:18 PDT: folder claimed on main with runbook `expt_v1/cc.md` (Brando's 10-20 design, revised with Sang Truong's textbook and lectures and experiment 19's results); worker dispatch next.

## Results
- none yet

## Stuck / blocked
- nothing

## Next steps
1. Worker: setup, then Phase 0a (539 train tasks x 8 on Sherlock via `sherlockctl`), Phase 0b IRT fit, gate G0 (runbook section 6).

## Brando to-do
- none

## Log
- 10-21-2026 11:18 PDT -- folder claimed on main; runbook written; dispatching the worker.
- 10-21-2026 11:38 PDT -- dispatch receipt logged (deploy_ed87a5b1900b45d2af6e22c1707cc31e, cc profile, watch-e20); worker checkpoint CKPT_cc-rl4cv-e20-irt-prompt-selection.md created; README dispatch line corrected.
