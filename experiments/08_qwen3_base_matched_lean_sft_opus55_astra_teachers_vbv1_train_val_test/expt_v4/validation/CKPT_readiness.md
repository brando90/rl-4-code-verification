# Sherlock validation and existing SFT readiness checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/validation/CKPT_readiness.md>

**TLDR:** Broader SFT already has useful measured RL signal; latest completed1.7B is120/1080successes but fails format gates. Sherlock replica validation has an active separate execution owner; do not duplicate it.

Created: 10-19-2026 12:17 PDT
Last updated: 10-19-2026 12:17 PDT

## Goal
- Reconcile existing SFT evidence, then finish the authorized two-seed/Base validation comparison if not already completed by the active owner; keep test sealed, publish and email once done.
## What ran
- Independent recomputation of6existing1080-cell validation tables;5targeted tests pass. Read-only Sherlock inspection via sherlockctl; no new generation/training submitted.
- Canonical repo `/Users/brandomiranda/rl-4-code-verification`; owned detached checkout `/Users/brandomiranda/.worktrees/rl4cv/sherlock-validation` (Codex cleanup owner).
## Results
- Current-corpus checkpoint:120/1080successes;24/135mixed;16/135in2–6band;971extracted,110capped. Useful signal, frozen gates FAIL,25%target unmet.
- Sherlock48502119cancelled;48505048replacement smoke queued;48504619weight hashes PASS; scorer48483971controls30/30plus40/40PASS. Model readiness unknown.
## Stuck / blocked
- Active foreign execution owner updates v4_validation scripts; preserve it and inspect next jobs/logs before any submission. Local full suite has Linux/proc and missing-dependency failures; Linux verification being prepared. Google companion previously403.
## Next steps
- Read results.md and current main receipts first; prioritize already-running newer SFT and avoid redundant work. Use `sherlockctl exec 'squeue --me'` no more often than60s, then inspect48505048/fulljobs/logs. No empty-queue success claim.
- If full3model comparison proceeds:135validation tasks×8×3=3240cells, frozenV6prompts,seed91,T0.6,p0.95,k20,12288cap,thinkingon,im_endstop; oneGPUatonce,8h/model maximum; preserve completed cells and record exact source/runtime/model hashes before admissions.
- Reuse verified grading at `$SCRATCH/rl4cv_sherlock/grading`; reconcile allcells, compute readiness.py and paired task-bootstrap comparisons. Do not infer results from training loss or hashes.
- Publish owned exactdiff after required tests; update Google if access works; send unique validation DONE email with all4requiredBCCs only after terminal outcome. OldtrainingDONE1a15267ee2fc1c9a is unrelated; never resend.
## Brando to-do
- None for evidence audit or cluster work.

## Log
- 10-19-2026 12:17 PDT — Recomputed existing results and corrected scope: SFT signal already measured; Sherlock replication is separate. Preserved active owner's replacement smoke job and prepared complete-cohort readiness analysis.
