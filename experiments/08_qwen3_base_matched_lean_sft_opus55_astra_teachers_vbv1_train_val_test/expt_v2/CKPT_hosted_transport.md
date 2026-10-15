# Experiment 08 version 2 hosted transport checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_hosted_transport.md>
**TLDR:** Hosted launchers passed the full Linux suite and isolated live deployment/run checks; scientific holds remain intact.
Created: 10-14-2026 17:49 PDT
Last updated: 10-14-2026 18:12 PDT

## Goal
- Complete the RUNBOOK_rl4cv.md implementation while preserving scientific holds/results.
## What ran
- Worker codex-rl4cv-hosted-migration; deployment deploy_74603054ec944e1188f162fc14c97b7a; implementation fbce4bfa979383508548ef636f13531780cfa046 on base 6251b77.
- Runtime: unrestricted filesystem/approval never; useful source inspection verified. Runbook model/effort: gpt-6.1-sol/high; parent verifies actual launch.
## Results
- Targeted tests 41/41 pass; transport regressions 14/14 pass. Compilation, all three help commands and diff checks exit 0.
- Final macOS make test: 572 passed, 13 failed, 14 skipped; make exit 2. All 13 failures reproduce on unchanged base (Linux /proc required).
- Coordinator: Linux make test 590 passed/5 skipped, exit0; isolated hosted deployment and run46dee95d FINISHED1/1; start/status/results/output passed; zero model calls. No experimental result/reference edits.
## Stuck / blocked
- No transport blocker. Scientific-study holds remain independent of migration. Live evidence is in docs/valkyrie_hosted_transport.md.
## Next steps
- Coordinator publishes verified source and removes owned checkouts; no study admission is requested.
## Brando to-do
- None.

## Log
- 10-14-2026 17:49 PDT -- Implementation fbce4bf complete; targeted tests pass, Linux/live checks and publication remain coordinator-owned.
- 10-14-2026 17:49 PDT -- Final checkpoint publication metadata prepared; no execution or result changes.

- 10-14-2026 18:12 PDT -- Coordinator verified full Linux suite and actual hosted launcher roundtrip; rebase preserved all tested source bytes over concurrent result commits. Owned test service/tunnel stopped, port free, two test registrations/secrets removed;13existingservices preserved.
