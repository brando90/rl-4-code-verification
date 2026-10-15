# RL4CV hosted Valkyrie launcher migration checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/CKPT_codex-rl4cv-hosted-migration.md> (intended; coordinator owns publication)
**TLDR:** Assigned launcher migration committed and deterministic verification recorded; Linux and live checks remain coordinator-owned.
Created: 10-14-2026 17:40 PDT
Last updated: 10-14-2026 17:49 PDT

## Goal
- Complete the RUNBOOK_rl4cv.md implementation while preserving scientific holds/results.
## What ran
- Worker codex-rl4cv-hosted-migration; deployment deploy_74603054ec944e1188f162fc14c97b7a; implementation fbce4bfa979383508548ef636f13531780cfa046 on base 6251b77.
- Runtime: unrestricted filesystem/approval never; useful source inspection verified. Runbook model/effort: gpt-6.1-sol/high; parent verifies actual launch.
## Results
- Targeted tests 41/41 pass; transport regressions 14/14 pass. Compilation, all three help commands and diff checks exit 0.
- Final macOS make test: 572 passed, 13 failed, 14 skipped; make exit 2. All 13 failures reproduce on unchanged base (Linux /proc required).
- No model/sandbox calls, no experimental result/reference edits, no shared runtime mutations or publication.
## Stuck / blocked
- Existing scientific holds remain. Coordinator owns Linux full-suite pass and isolated live verification; RESULT_rl4cv.md contains exact commands.
## Next steps
- [p 10/10] Coordinator: run `make test` on isolated Linux export of the implementation, then live checks in private RESULT_rl4cv.md.
- [p 9/10] Coordinator integrates/publishes only after required checks; retains then removes this checkout and its ignored pinned dependencies.
## Brando to-do
- None.

## Log
- 10-14-2026 17:40 PDT -- Read full runbook and applicable policy; began implementation in exclusive checkout.
- 10-14-2026 17:43 PDT -- Implemented transport, hosted registration and receipt fences; 11 regression tests pass; started full suite.
- 10-14-2026 17:45 PDT -- Transport regressions now 14 passed; full macOS suite exposes 13 Linux-specific failures; baseline comparison started.
- 10-14-2026 17:49 PDT -- Committed implementation fbce4bf; targeted checks pass and all 13 macOS failures reproduced at unchanged base; prepared coordinator handoff.
- 10-14-2026 17:49 PDT -- Final checkpoint publication metadata prepared; no execution or result changes.
