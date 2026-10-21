# CKPT e20: IRT ability-matched prompt selection for GRPO (Azalia's test, IRT version)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_e20.md>

**TLDR:** Resume record for experiment 20. Dispatcher: Claude Code session local_268be283 (Mac); worker: tmux `cc-rl4cv-e20-irt-prompt-selection` on skampere1 (Claude Code claude-fable-5-1, max, personal profile, full access).

Created: 10-21-2026 11:18 PDT
Last updated: 10-21-2026 11:18 PDT

## Goal
- Does IRT-online prompt selection (C) raise validation strict pass@1 over uniform (A), a pass-rate filter (S) and DAPO (E) at matched rollouts, and how does it interact with a smooth reward (B, D)?

## What ran
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
