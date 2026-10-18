# Sherlock training checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/CKPT_sherlock.md>

**TLDR:** Seed 20260830 is training on an H100; seed 20260831 waits for successful completion. Both full results remain pending.

Created: 10-18-2026 14:57 PDT
Last updated: 10-18-2026 15:32 PDT

## Goal
- Complete `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` on Sherlock, with two full 658-update runs.
## What ran
- OnDemand shell access verified; source corpus downloaded and hash-verified; protocol and launcher prepared.
- Canonical local project: `/Users/brandomiranda/rl-4-code-verification`; owned temporary checkout `/Users/brandomiranda/.worktrees/rl4cv/sherlock-training` removed after publication; canonical ignored corpus retained and hash-verified.
## Results
- 0/2 completed; seed 0 verified at 24/658 updates, 48/1,315 examples, finite loss/nonzero gradients, 47.85 GiB peak so far. Zero provider spend. Test unopened.
## Stuck / blocked
- None. GPU job 48378536 running on sh04-01n01; seed 1 and collector depend on terminal scheduler outcomes.
## Next steps
- [p 10/10] Monitor both full trajectories and retain checkpoint/export verification. Both GPU holds were released after protocol commit `c54240b` reached main. Do not rerun submit.sh; jobs already exist.
- Inspect `sacct -j 48377554,48378536,48378539,48378541 --format=JobID,State,ExitCode` and `runs/*/progress.json` under `/scratch/users/brando9/rl4cv_sherlock/expt_v4`.
- Monitor: app heartbeat `monitor-sherlock-training`, every 15 minutes; no-model scheduler afterany collector 48378541 and four-hour training limits. Final archive path `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`.
- Collect `results_bundle.tar.gz`, verify terminal/archive receipts, publish tables, update Google companion (results.md link), send deduplicated DONE and stop monitor. START email ID 1a15110b6da2f189.
- Cleanup completed: owned local worktree/external clone and Linux test copy removed; full test log and input corpus retained in canonical project.
## Brando to-do
- None; native browser sign-in succeeded without command-line vault approval.

## Log
- 10-18-2026 14:57 PDT — Authenticated Sherlock, verified the original corpus hash, prepared two separate full-training replications; existing SNAP workers preserved.
- 10-18-2026 15:19 PDT — Uploaded and hashed package; replaced unstarted prep job 48377449 to correct Slurm submit directory; prep 48377554 running, GPU jobs 48378536/48378539 held, collector 48378541 queued. START mail delivered and 15-minute heartbeat created.
- 10-18-2026 15:23 PDT — Preparation 48377554 completed 0:0, all token hashes passed. Full Linux verification: 1,382 passed, three skipped, six subtests passed; three added terminal controls passed on Linux and macOS. Google companion created and link-viewer sharing verified.
- 10-18-2026 15:25 PDT — Published frozen protocol/source as c54240b, then released training jobs 48378536 and 48378539. Preparation passed. Preserved full Linux verification log and removed its owned isolated test copy.
- 10-18-2026 15:30 PDT — Verified real optimizer updates (16/658), H100 device, finite loss and nonzero gradients; peak memory 46.56 GiB so far. Seed 1 remains dependent. Saved initial receipt and visual evidence; canonical checkout current and temporary copies cleaned.
- 10-18-2026 15:31 PDT — Later launch sample reached 24/658 updates and 197,859 loss tokens; peak allocated device memory 47.85 GiB. Saved the partial step sample and readable screenshot provenance.
