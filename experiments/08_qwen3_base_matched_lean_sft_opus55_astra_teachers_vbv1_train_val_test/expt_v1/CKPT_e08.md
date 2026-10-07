# Experiment 08 checkpoint — matched Lean SFT warm start (master and SNAP worker)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/CKPT_e08.md>

**TLDR:** Resumable state of experiment 08. The master finished the zero-call steps (D-013 split, Base baselines, token-budget inputs, design, protocol, runbook); the SNAP worker starts at runbook § 1.

**Created:** 10-07-2026 16:35 PDT (master). **Last updated:** 10-07-2026 16:35 PDT (master).

## State

| Item | Value |
|---|---|
| Current step | Master: design committed; light QA (Codex, one round, requested by Brando) next; then dispatch |
| Master | Claude Code (Opus 5.5) on Brando's laptop; private worktree `~/vb_worktrees/rl4cv-sft-warmstart-1007` |
| Intended worker | Claude Code `claude-fable-5-1`, effort `high`, on `skampere1`, tmux `rl4cv-e08-worker`, clone `/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification` |
| Work root | `/lfs/skampere1/0/brando9/rl4cv_e08` (master scratch only so far: `master_scratch/`, token-budget runs) |
| Status file | `/lfs/skampere1/0/brando9/rl4cv_e08/STATUS_e08` (not created yet) |
| Lock 1 / lock 2 | not locked |
| Valkyrie runs | none |
| GPUs held | none |
| Services, ports, tunnels | none |

## Log

- **10-07-2026 16:35 PDT (master).**
  - Built the D-013 split with `python -m rl4cv.splits` on VeriBench `c11b99ba`: 896 tasks, 664 groups, 539 / 135 / 222, manifest SHA-256 `157ce781…`. `tests/test_splits.py` passes, including the reproduction test (`VERIBENCH_ROOT` = an archive of the pin).
  - Computed Base baselines on the splits from experiment 05's receipts.
  - Ran `estimate_token_budget.py gold|e103` on `skampere1`; read-only on experiment 103's private receipts.
  - Wrote README, PROTOCOL (locks 1 and 2 pending), runbook and `results.md`. Recorded D-013 and D-015 and updated the `CLAUDE.md` held-out rule.

## Next command (worker)

Runbook `expt_v1/cc.md` § 1 on `skampere1`.
