# Checkpoint — experiment 02A v3 (Lean warm-start data from Valkyrie teachers)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/CKPT_e02a_v3.md>

**TLDR:** Resume record for the 02A v3 worker: what is done, what runs where, and the exact next command.

**Created:** 10-07-2026 15:42 PDT
**Last updated:** 10-07-2026 16:00 PDT (worker)

- **Task:** build screened MBPP tasks in VeriBench layout, one single-call Lean file per task from each of three Valkyrie teachers, keep kernel-verified files, publish the verdict (README, PROTOCOL).
- **Owner:** Ethan Li (@lethan3), issue #6. **Master:** Claude Code (Opus 5.5) on Brando's laptop, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv. **Worker:** Claude Code `claude-fable-5-1` / effort `high` via `/lfs/skampere1/0/brando9/bin/clauded_tok` (full access) on `skampere1`, tmux `rl4cv-e02a-v3-worker` (launch receipt below once verified).
- **Why this worker model:** integrity-critical engineering (rewrite, screens, frozen-scorer adapter, Valkyrie service) before a ~2,900-call run; Fable 5.1 at high rather than max to conserve the shared allowance (Hard Rule 8).
- **Host:** `skampere1`; work root `/lfs/skampere1/0/brando9/rl4cv_e02a_v3`; own clone `$WORK/rl-4-code-verification` on `main` (D-012: pull before push, push each step); status file `$WORK/STATUS_e02a_v3`.
- **Done (master):** design, PROTOCOL (not locked), runbook `cc.md`, issue #6, one Codex light-QA round (see Log).
- **Next command (worker):** `cc.md` § 1 (source build, rewrite, screens; zero model calls).
- **Status file:** `RUNNING` written to `/lfs/skampere1/0/brando9/rl4cv_e02a_v3/STATUS_e02a_v3`.
- **Not ours on this host (never touch):** tmux `rl4cv-e01-qwen-vbv1-baseline`, `rl4cv-e01-zero-diag-A`, `rl4cv-e01-zero-diag-B`, `rl4cv-e05-worker`; experiment 01/05/07 work roots and ports.

## Log
- **10-07-2026 15:57 PDT — light QA (Brando-requested), one round:** Codex `gpt-6-astra`, reasoning `ultra`, codex-cli 0.161.0, read-only, on the issue #6 body, D-012 and this design. Verdict FAIL: 0 critical, 5 major, 2 minor. Builder fixed all 7: (1) task stem `task_<id>` so the frozen scorer's mapping gate passes, checked on every task; (2) re-send only cells positively unserved, at most two model requests per cell including the agent's internal re-send; (3) generated Lean screened against VeriBench and held-out panels before the SFT set; (4) single-call teachers recorded as an exception to D-108's vendor-agent rule, gated on Brando's recorded approval before any model call; (5) observed yield, measured-cell Wilson interval and missing-outcome bounds, UNRESOLVED verdict when bounds straddle a threshold; (6) D-012 wording for clones / detached worktrees; (7) issue #6 now scopes the proposals to the larger 02B design. Recorded verdict: FIXED; no automatic re-review (Hard Rule 3).
- **10-07-2026 16:00 PDT — worker launch receipt:** client Claude Code via `/lfs/skampere1/0/brando9/bin/clauded_tok`, host `skampere1`, model `claude-fable-5-1`, effort `high`, permission mode `--dangerously-skip-permissions`, tmux session `rl4cv-e02a-v3-worker`, checkout `/lfs/skampere1/0/brando9/rl4cv_e02a_v3/rl-4-code-verification` on `main`. Read INDEX_RULES, repository CLAUDE.md, README, PROTOCOL, this checkpoint and `cc.md`. Host note: the AFS home is unreadable from this session, so git uses the LFS SSH key through `core.sshCommand` in this clone (no secret in the repository). D-108 exception for single-call teachers: not yet in `docs/DECISIONS.md` at launch; zero-call steps proceed first (cc.md § 1–3), the gate is checked at § 4.3.
