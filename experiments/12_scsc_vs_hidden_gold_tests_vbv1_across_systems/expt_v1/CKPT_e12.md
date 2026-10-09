# Checkpoint — experiment 12 phase A (SCSC versus hidden gold-reference tests)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/CKPT_e12.md>

**TLDR:** Resume record for the experiment 12 phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-09-2026 14:36 PDT
**Last updated:** 10-09-2026 14:36 PDT (master)

- **Task:** `expt_v1/cc.md`. Brando, 10-09-2026: "Go" (measure hidden gold tests on existing outputs, zero model calls).
- **Owner:** Emily Xia (@emxia18), Ethan Li (@lethan3) advising; tracking issue: see Log. **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `oct9-cc-rl4cv-master`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv.
- **Worker:** Claude Code `claude-fable-5-1` / effort `high` via `/lfs/skampere1/0/brando9/bin/clauded_tok` (full access) on `skampere1`, tmux `oct9-cc-rl4cv-e12-hidden-gold-tests`. Why this model: integrity-critical adapter and control design with zero model calls; high, not max, to save the shared allowance.
- **Frozen forecast:** `expt_v1/forecasts/e12_phase_a_forecast.json`, SHA-256 `b29b71b7166b80df653220ddddec4b865a622ef9abc1fa42c6c1e559b067b0c5`, frozen 2026-10-09T21:35:33Z at git head `e851c02`.
- **Next command (worker):** `cc.md` § 1.

## Log
