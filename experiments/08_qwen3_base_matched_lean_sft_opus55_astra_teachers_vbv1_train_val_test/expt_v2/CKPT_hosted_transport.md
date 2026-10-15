# Experiment 08 version 2 hosted transport checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_hosted_transport.md> (intended; coordinator owns publication)
**TLDR:** Assigned launcher migration committed and deterministic verification recorded; Linux and live checks remain coordinator-owned.
Created: 10-14-2026 17:49 PDT
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
- 10-14-2026 17:49 PDT -- Implementation fbce4bf complete; targeted tests pass, Linux/live checks and publication remain coordinator-owned.
- 10-14-2026 17:49 PDT -- Final checkpoint publication metadata prepared; no execution or result changes.
