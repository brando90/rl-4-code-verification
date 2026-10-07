# Checkpoint — experiment 01 FSC repeat fix (median of 3)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01_fsc_median3.md>

**TLDR:** Resume record for completing experiment 01's locked FSC judge design (repeats 2 and 3, median of 3) without overwriting repeat-1 evidence.

**Created:** 10-07-2026 16:48 PDT
**Last updated:** 10-07-2026 16:49 PDT (worker)

- **Task:** `expt_v1/cc_fsc_median3_fix.md`. Requested by Brando, 10-07-2026: "fix the 01 FSC repeat deviation".
- **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `cc-rl4cv-master-argon-qa-e02-lethan-e01-fsc`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv. **Worker:** Claude Code `claude-fable-5-1` / effort `high` via `/lfs/skampere1/0/brando9/bin/clauded_tok` (full access) on `skampere1`, tmux `rl4cv-e01-fsc-median3-worker`.
- **Status file:** `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_fsc_median3`.
- **Spend:** $106.37 of $400 before this fix; estimate about +$204.
- **Next command (worker):** runbook § 1.

## Log
- **10-07-2026 16:49 PDT — worker launch receipt.** Client Claude Code via `/lfs/skampere1/0/brando9/bin/clauded_tok`; host `skampere1`; model `claude-fable-5-1`; effort `high`; permission mode `--dangerously-skip-permissions`; tmux session `rl4cv-e01-fsc-median3-worker`; checkout `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification` on `main` (pulled `--ff-only`, clean before start). Status file set to `RUNNING`. Step: runbook § 1 done, starting § 2 (build repeat packs, zero model calls).
