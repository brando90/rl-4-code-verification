# Checkpoint: judge experiment 01's 11 proving G = 8 probe cells

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01_probe_judge.md>

**TLDR:** Live checkpoint for the worker that judges the 11 proving G = 8 probe cells (4 in `qwen3.5-9b_g8`, 7 in `qwen3-14b_g8`) with the locked FSC design (GPT-6 Sol high and Claude Opus 5.5 max, 3 repeats each, median of 3) on the `vb103_judge` Valkyrie route, then adds the probe's `scsc` and partial `fsc_compiled` channels. Runbook: `cc_judge_probe_proving_cells.md`.

- **Created:** 10-07-2026 19:55:37 PDT
- **Last updated:** 10-07-2026 19:55:37 PDT
- **Status file:** `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_probe_judge`

## Launch receipt

- **Client:** Claude Code via `clauded_tok`
- **Host:** skampere1 (SNAP)
- **Model:** `claude-fable-5-1`, effort high
- **Permission mode:** `--dangerously-skip-permissions`
- **tmux session:** `rl4cv-e01-probe-judge-worker`
- **Checkout:** `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification` on `main` at `4c1d6a2`
- **Task:** Brando (10-07-2026): "now judge the 11 proving G=8 probe cells".
- **Launched:** 10-07-2026 19:55:37 PDT; status file set to RUNNING.

## Log

- 10-07-2026 19:55:37 PDT — launched; reading INDEX_RULES, CLAUDE.md, PROTOCOL.md, results.md, REPORT.md and `judge_rl4cv_e01.py`.
