# Checkpoint — experiment 07 phase A (SCS4C-T versus pass@1, SWE-bench Verified)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/CKPT_e07.md>

**TLDR:** Resume record for the phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-07-2026 15:26 PDT
**Last updated:** 10-07-2026 15:26 PDT (master)

- **Task:** fetch public SWE-bench Verified per-instance reports, compute SCS4C-T and pass@1 per system, run locked H1/H1b/H2/H3, publish, light QA (Codex gpt-6-astra ultra), land (Rule 46).
- **Owner:** Emily (@emxia18). **Master:** Claude Code (Opus 5.5) on Brando's laptop. **Worker:** Claude Code `claude-fable-5-1` / `max` on `skampere1`, tmux `rl4cv-e07-worker` (launch receipt below).
- **Host:** `skampere1`; work root `/lfs/skampere1/0/brando9/rl4cv_e07`; clone `$WORK/rl-4-code-verification`, branch `e07-scs4c-phase-a`; status file `$WORK/STATUS_e07`.
- **Done (master):** definition, README, PROTOCOL (locked), frozen forecast `forecasts/e07_phase_a_forecast.json` (sha256 `af0d4678…`), metric module `src/rl4cv/scs4c.py` with tests, fetch and analysis scripts (smoke-tested on synthetic data only).
- **Next command (worker):** `expt_v1/cc.md` § 1.

## Log
