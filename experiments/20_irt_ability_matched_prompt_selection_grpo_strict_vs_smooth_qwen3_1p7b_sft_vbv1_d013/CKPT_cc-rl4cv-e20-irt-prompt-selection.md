# CKPT cc-rl4cv-e20-irt-prompt-selection: worker resume record for experiment 20 (IRT prompt selection for GRPO)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_cc-rl4cv-e20-irt-prompt-selection.md>

**TLDR:** Resume record of the Claude Code worker (tmux `cc-rl4cv-e20-irt-prompt-selection` on skampere1, deployment `deploy_ed87a5b1900b45d2af6e22c1707cc31e`, claude-fable-5-1 at max, profile cc, bypass permissions) that runs experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013 end to end. `CKPT_e20.md` is the dispatcher-facing checkpoint and points here.

Created: 10-21-2026 11:38 PDT
Last updated: 10-21-2026 11:54 PDT

## Goal
- Does IRT-online prompt selection (arm C) raise D-013 validation strict pass@1 over uniform (A), a pass-rate filter (S) and DAPO (E) at matched rollouts, and does a smooth reward (B, D) substitute for or add to it? Gated: Phase 0 calibration -> IRT fit + G0 -> smoke -> pilot -> main -> evaluation.

## What ran
- 10-21-2026 11:38 PDT: worker started; read runbook `expt_v1/cc.md`, agents-config rules (HR 1-11, TR 9, 19, 26, 37, 39, 42, 44, 46, 48, 51, 54, 57, 70, 71), repo CLAUDE.md, experiments/README.md, experiment 19 code/results, experiment 13 reward code, experiment 08 v4/v16 Sherlock pipeline. Installed `sherlockctl` (runner online, job service). Created venv `/lfs/skampere1/0/brando9/venvs/rl4cv_e20` (python 3.12.14, numpy 2.5.4, scipy 1.18.1, pytest 9.1.1, uutils). Branch `e20-irt-prompt-selection` from origin/main 63a0d3d0.

## Results
- Phase 0a: Sherlock array 48841018_[0-3] submitted 10-21-2026 11:54 PDT (4 chunks x ~1,078 cells); pack manifest PASS (adapter sha256 a129b20a…, train id list sha256 03c4167c… = committed split).
- none yet (Phase 0 not launched). Start-policy baseline from experiment 08 expt_v16 (Sherlock, v4 seed 20260831): validation strict pass@1 58/1080 = 5.37% [3.15, 8.06], pass@8 24/135; seed spread between the two v4 checkpoints 0.56 points.

## Stuck / blocked
- nothing. Sherlock gpu partition had 530 pending / 184 running jobs at 11:30 PDT (queue delay expected, not a blocker).

## Next steps
1. Watch array 48841018 (`sherlockctl exec 'squeue -j 48841018'`, >= 60 s apart); when a chunk finishes, verify `timing.json` cells = 8 x tasks.
2. Meanwhile: port the D-109 logged scorer + partial-credit adapter to `expt_v1/sherlock/`, write `irt_e20.py`, `samplers_e20.py`, tests; README design update.
3. After generation: submit the scoring array (normal partition), then Phase 0b IRT fit + gate G0 locally.

## Brando to-do
- none

## Log
- 10-21-2026 11:38 PDT -- worker started; dispatch receipt logged in CKPT_e20.md; README dispatch line fixed (profile cc); branch e20-irt-prompt-selection created from origin/main 63a0d3d0.
- 10-21-2026 11:54 PDT -- Phase 0a generation submitted: Sherlock array 48841018_[0-3]; RUN START email sent; PROTOCOL.md draft + results.md written.
