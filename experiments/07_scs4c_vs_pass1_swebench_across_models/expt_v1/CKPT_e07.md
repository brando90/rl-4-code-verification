# Checkpoint — experiment 07 phase A (SCS4C-T versus pass@1, SWE-bench Verified)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/CKPT_e07.md>

**TLDR:** Resume record for the phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-07-2026 15:26 PDT
**Last updated:** 10-07-2026 15:53 PDT (local light review)

- **Task:** fetch public SWE-bench Verified per-instance reports, compute SCS4C-T and pass@1 per system, run locked H1/H1b/H2/H3, publish, light QA (Codex gpt-6-astra ultra), land (Rule 46).
- **Owner:** Emily (@emxia18). **Master:** Claude Code (Opus 5.5) on Brando's laptop. **Intended worker:** Claude Code `claude-fable-5-1` / `max` on `skampere1`, tmux `rl4cv-e07-worker`. Dispatch was reported by the master, but no launch receipt is recorded; execution is unverified.
- **Host:** `skampere1`; work root `/lfs/skampere1/0/brando9/rl4cv_e07`; clone `$WORK/rl-4-code-verification`, use `main` in the isolated clone per the project rule; actual checkout state unverified; status file `$WORK/STATUS_e07`.
- **Done (master):** definition, README, PROTOCOL (locked), frozen forecast `forecasts/e07_phase_a_forecast.json` (sha256 `af0d4678…`), metric module `src/rl4cv/scs4c.py` with tests, fetch and analysis scripts (smoke-tested on synthetic data only).
- **Next action (worker/master):** verify the remote process/session and checkout revision, record the missing launch receipt, and use the reviewed `expt_v1/cc.md` § 1. Incorporate the local fixes before analyzing outcomes; do not claim a local review restarted or verified the remote run.

## Log

- **10-07-2026 15:53 PDT:** Local one-round review of `7b3ad352..94c95ef` plus working-tree fixes. Parsing, finite statistics, inclusion/cohort stop rules, bootstrap reporting, per-cell receipts and input provenance corrected; regression checks use synthetic data only. Frozen forecasts unchanged. GitHub adapters and model sensitivity remain worker deliverables. No commit, push or remote experiment performed by this review.
