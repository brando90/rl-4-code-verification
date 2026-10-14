# Master checkpoint: 10-14-2026 ultracode progress round

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/CKPT_MASTER_oct14-cc-rl4cv-master-ultracode-progress.md>

**TLDR:** Brando asked (10-14-2026, about 12:40 PDT) for a multi-agent "ultracode" push to make progress on experiments and the 10-13 meeting notes while he is away 1-2 hours. The master (Claude Code, claude-fable-5-1, effort max, tmux `oct14-cc-rl4cv-master-ultracode-progress` on Brando's Mac) launched one Workflow run with six parallel workers, each independently checked. Zero model calls this round: the Vals Valkyrie route returns HTTP 403 since 10-13 03:27 PDT.

Created: 10-14-2026 12:56 PDT
Last updated: 10-14-2026 12:56 PDT

## Goal
- Land verifiable progress on main for: the 10-13-2026 meeting record and decisions; experiment 10 phase A (locked, never run); experiment 08 v3 corpus admission and failure taxonomy; experiment 13 v2 R2 diagnosis (via its idle owner on skampere1); a new experiment 15 (IRT forecast of RL-signal onset, idea-page Q2); experiment 12's corrected adapter (version 2 preparation).

## What ran
- 10-14-2026 ~12:50 PDT: Workflow `rl4cv-ultracode-progress-10-14` (run id `wf_ff4d2560-7f8`, in-process agents at Brando's explicit ultracode request; script under the session's `workflows/scripts/`). Stages: Work (6) -> Verify (6) -> Fix (only on blocking findings). Workers run in detached worktrees and push `HEAD:main` with explicit pathspecs; host jobs run on skampere1 in named tmux sessions (`rl4cv-e10-phase-a-10-14`, `rl4cv-e08v3-admission-10-14`, `rl4cv-e12v2-census-10-14`; experiment 13 reuses `codex-rl4cv-e13v2-owner`).
- Pre-launch: pulled origin/main to d5c97ec (reconciled the identical untracked transcript copy); read agents-config rules 8/42/44/48/51/57/67/69/70; read issue #68 and both weekly-notes docs (newest sections 10-14 Vals, 10-09 Stanford).

## Results
- none yet (workers in progress; see each experiment's CKPT and results.md as they land).

## Stuck / blocked
- Vals Valkyrie route: HTTP 403 "Managed AWS access is not available for this organization" since 10-13 03:27 PDT; Jaewon asked 10-14 03:43 PDT (issue #68 comment 6166535065). Blocks experiment 08 v2's matched test and all judged evaluation.
- Rakshit's SNAP access: IL Action ticket #149859 awaiting Prof. Koyejo (10-13 18:07 PDT). Brando's Slurm request: ticket #149865, unanswered since 10-13 12:27 PDT.
- make test on macOS has 4 pre-existing e13 v2 watchdog/A2 failures (Linux-only tests); workers treat that set as baseline.

## Next steps
- [p 10/10] When the workflow completes: read each worker's verified report, apply the experiments/README.md row updates, refresh this checkpoint, report to Brando with TLDR-end and Snapshot.
- [p 8/10] If any worker reports PARTIAL with a live host job: attach to the named tmux session on skampere1 and finish scoring/publication from its CKPT.
- [p 6/10] Clean up the Workflow worktrees once their commits are on origin/main (`git worktree list`; remove only worktrees whose HEAD is an ancestor of origin/main).

## Brando to-do
- Open PR #13 (plain-English status + cleanup proposal) is unmerged until you read it; say "archive" to execute its folder moves.
- Nudge Vals (Jaewon) on the 403 if you see him before he answers the email.

## Log
- 10-14-2026 12:56 PDT -- Workflow launched with six workers; checkpoint created.
