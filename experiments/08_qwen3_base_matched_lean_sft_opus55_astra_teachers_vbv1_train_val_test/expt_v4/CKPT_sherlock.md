# Sherlock training checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/CKPT_sherlock.md>

**TLDR:** Input admission and tests passed; both training jobs released under the published protocol.

Created: 10-18-2026 14:57 PDT
Last updated: 10-18-2026 15:25 PDT

## Goal
- Complete `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` on Sherlock, with two full 658-update runs.
## What ran
- OnDemand shell access verified; source corpus downloaded and hash-verified; protocol and launcher prepared.
- Canonical local project: `/Users/brandomiranda/rl-4-code-verification`; owned temporary checkout: `/Users/brandomiranda/.worktrees/rl4cv/sherlock-training`; cleanup owner: this chat.
## Results
- 0/2 completed training runs. Zero provider spend. Test unopened.
## Stuck / blocked
- No human blocker; first training job awaits scheduler start.
## Next steps
- [p 10/10] Verify the first optimizer update, then monitor both full trajectories. Both GPU holds were released after protocol commit `c54240b` reached main. Do not rerun submit.sh; jobs already exist.
- Inspect `sacct -j 48377554,48378536,48378539,48378541 --format=JobID,State,ExitCode` and `runs/*/progress.json` under `/scratch/users/brando9/rl4cv_sherlock/expt_v4`.
- Monitor: app heartbeat `monitor-sherlock-training`, every 15 minutes; no-model scheduler afterany collector 48378541 and four-hour training limits. Final archive path `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`.
- Collect `results_bundle.tar.gz`, verify terminal/archive receipts, publish tables, update Google companion (results.md link), send deduplicated DONE and stop monitor. START email ID 1a15110b6da2f189.
- Cleanup owned local worktree and Linux test copy after publication; preserve test receipt/log.
## Brando to-do
- None; native browser sign-in succeeded without command-line vault approval.

## Log
- 10-18-2026 14:57 PDT — Authenticated Sherlock, verified the original corpus hash, prepared two separate full-training replications; existing SNAP workers preserved.
- 10-18-2026 15:19 PDT — Uploaded and hashed package; replaced unstarted prep job 48377449 to correct Slurm submit directory; prep 48377554 running, GPU jobs 48378536/48378539 held, collector 48378541 queued. START mail delivered and 15-minute heartbeat created.
- 10-18-2026 15:23 PDT — Preparation 48377554 completed 0:0, all token hashes passed. Full Linux verification: 1,382 passed, three skipped, six subtests passed; three added terminal controls passed on Linux and macOS. Google companion created and link-viewer sharing verified.
- 10-18-2026 15:25 PDT — Published frozen protocol/source as c54240b, then released training jobs 48378536 and 48378539. Preparation passed. Preserved full Linux verification log and removed its owned isolated test copy.
