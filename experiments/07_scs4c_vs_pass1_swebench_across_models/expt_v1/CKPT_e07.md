# Checkpoint — experiment 07 phase A (SCS4C-T versus pass@1, SWE-bench Verified)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/CKPT_e07.md>

**TLDR:** Resume record for the phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-07-2026 15:26 PDT
**Last updated:** 10-07-2026 16:01 PDT (master, launch receipt)

- **Task:** fetch public SWE-bench Verified per-instance reports, compute SCS4C-T and pass@1 per system, run locked H1/H1b/H2/H3, publish, light QA (Codex gpt-6-astra ultra), land (Rule 46).
- **Owner:** Emily (@emxia18). **Master:** Claude Code (Opus 5.5) on Brando's laptop. **Intended worker:** Claude Code `claude-fable-5-1` / `max` on `skampere1`, tmux `rl4cv-e07-worker`. Dispatch was reported by the master, but no launch receipt is recorded; execution is unverified.
- **Host:** `skampere1`; work root `/lfs/skampere1/0/brando9/rl4cv_e07`; clone `$WORK/rl-4-code-verification`, use `main` in the isolated clone per the project rule; actual checkout state unverified; status file `$WORK/STATUS_e07`.
- **Done (master):** definition, README, PROTOCOL (locked), frozen forecast `forecasts/e07_phase_a_forecast.json` (sha256 `af0d4678…`), metric module `src/rl4cv/scs4c.py` with tests, fetch and analysis scripts (smoke-tested on synthetic data only).
- **Next action (worker/master):** verify the remote process/session and checkout revision, record the missing launch receipt, and use the reviewed `expt_v1/cc.md` § 1. Incorporate the local fixes before analyzing outcomes; do not claim a local review restarted or verified the remote run.

## Log

- **10-07-2026 15:53 PDT:** Local one-round review of `7b3ad352..94c95ef` plus working-tree fixes. Parsing, finite statistics, inclusion/cohort stop rules, bootstrap reporting, per-cell receipts and input provenance corrected; regression checks use synthetic data only. Frozen forecasts unchanged. GitHub adapters and model sensitivity remain worker deliverables. No commit, push or remote experiment performed by this review.
- **10-07-2026 16:01 PDT — launch receipt (master).** Host `skampere1`; tmux session `rl4cv-e07-worker`; client Claude Code via `/lfs/skampere1/0/brando9/bin/clauded_tok` (`claude --dangerously-skip-permissions`); model `claude-fable-5-1`, effort `max`; pid 2376770. Clone `/lfs/skampere1/0/brando9/rl4cv_e07/rl-4-code-verification` on `main` at `39b575e`; `STATUS_e07` = `RUNNING`. The master accepted Claude Code's folder-trust prompt for the new clone; first observed action: reading the experiment docs and code.
- **Preflight.** `snap_health.sh --node skampere1` (10-07-2026): job-relevant checks PASS; `disk.dfs` FAIL (100% used) is not on this job's path (all outputs on `/lfs`, 10 TiB free). `aws` CLI absent on the node; the brief installs it in the job venv.
- **Light QA (before dispatch).** Codex `gpt-6-astra`, effort `ultra`, one round, verdict FIXED (receipt in `results.md`). Reviewed commits `94c95ef`/`ef509f3` were published rebased onto `c2d11b3` as `5feb25b`/`39b575e` with identical content.
- **Master watch.** The laptop master polls `origin/main` for the `LANDED` line and the host's `STATUS_e07`.
