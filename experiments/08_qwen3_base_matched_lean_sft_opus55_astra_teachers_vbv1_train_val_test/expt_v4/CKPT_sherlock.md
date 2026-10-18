# Sherlock training checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/CKPT_sherlock.md>

**TLDR:** Seed 20260830 completed all 658 updates and exported its checkpoint; seed 20260831 is now training. One of two trajectories is complete; persistent archive verification remains pending.

Created: 10-18-2026 14:57 PDT
Last updated: 10-18-2026 16:37 PDT

## Goal
- Complete `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` on Sherlock, with two full 658-update runs.
## What ran
- OnDemand shell access verified; source corpus downloaded and hash-verified; protocol and launcher prepared.
- Canonical local project: `/Users/brandomiranda/rl-4-code-verification`; owned temporary checkout `/Users/brandomiranda/.worktrees/rl4cv/sherlock-training` removed after publication; canonical ignored corpus retained and hash-verified.
## Results
- 1/2 trajectories completed. Seed 20260830: 658/658 updates, 1,315/1,315 examples, 5,752,936/5,752,936 loss tokens; all 658 step records finite with nonzero gradients. Slurm COMPLETED 0:0 in 01:04:20; 57.66 GiB peak. Result, full table and 12-file export manifest collected with exact remote hashes in `results/20260830/`. Final persistent archive is not yet verified.
- Seed 20260831 verified at 25/658 updates, 50/1,315 examples, 224,456/5,752,936 loss tokens, finite loss and nonzero gradients. Zero provider spend. Validation unmeasured; test unopened.
## Stuck / blocked
- None. Job 48378536 completed; job 48378539 is running on sh04-01n01. Collector 48378541 waits for the remaining terminal scheduler outcome.
## Next steps
- [p 10/10] Monitor both full trajectories and retain checkpoint/export verification. Both GPU holds were released after protocol commit `c54240b` reached main. Do not rerun submit.sh; jobs already exist.
- Inspect `sacct -j 48377554,48378536,48378539,48378541 --format=JobID,State,ExitCode` and `runs/*/progress.json` under `/scratch/users/brando9/rl4cv_sherlock/expt_v4`.
- Monitor: app heartbeat `monitor-sherlock-training`, every 15 minutes; no-model scheduler afterany collector 48378541 and four-hour training limits. Final archive path `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`.
- Collect `results_bundle.tar.gz`, verify root-level `terminal_receipt.json` and `archive_manifest.json` (not under `results/`), publish the second table, update Google companion (results.md link), send deduplicated DONE and stop monitor. START email ID 1a15110b6da2f189. No DONE sent as of this check.
- OnDemand file links render JSON/CSV directly; read their visible `pre` text. Browser CSV newline normalization requires restoring CRLF and matching the remote SHA-256 before accepting the transfer. Direct tar download did not return a local file in this session; no successful download receipt exists. The remote convenience bundle `../seed0_metadata.tar.gz` has SHA-256 `289c8c4b14eeead95a76041688d5edd24d95789625fb52fdc6d26fadee0d465f`.
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
- 10-18-2026 16:37 PDT — Seed 20260830 completed 0:0 at 16:30:35 PDT and all 658 records were collected and checksum-verified. Seed 20260831 started on sh04-01n01 and reached 25 updates; progress age 1.1 seconds, no inspected log failure markers. Root-level terminal/archive receipts absent as expected while collector waits. Google companion updated; monitor remains active.
