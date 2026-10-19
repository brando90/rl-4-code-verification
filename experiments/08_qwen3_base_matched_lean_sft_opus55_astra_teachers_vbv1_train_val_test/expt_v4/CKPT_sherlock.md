# Sherlock training checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/CKPT_sherlock.md>

**TLDR:** COMPLETE: 2/2 fixed-seed trajectories, all 1,316 updates verified, 36 files hash-archived. Publication and notification closeout remain.

Created: 10-18-2026 14:57 PDT
Last updated: 10-18-2026 21:21 PDT

## Goal
- Complete `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` on Sherlock, with two full 658-update runs.
## What ran
- Preparation 48377554, training 48378536/48378539 and collector 48378541 all COMPLETED 0:0. No repeated trajectories.
- Canonical local project `/Users/brandomiranda/rl-4-code-verification`; completed temporary checkouts/test copies removed previously. Other owners preserved.
## Results
- Seeds 20260830 and 20260831 each: 658/658 updates, 1,315/1,315 examples, 5,752,936/5,752,936 loss tokens; all 1,316 records finite, gradients nonzero. Total GPU allocation 7,633 seconds = 2.1203/8 GPU-hours; $0 provider spend.
- Both 12-file exports and training states archived: 36 hash-verified files at `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`. Independent metadata, sizes/configuration and shard-header checks passed; no full-model reload. Tables and receipts in `results/`.
- Validation unmeasured; test unopened. Frozen input/model/source/order hashes unchanged. See `results.md` and `results/final_collection_verification.json`.
## Stuck / blocked
- Google companion write returned 403 for connected `brando@vals.ai`; grant Editor access or reconnect as owner. Browser control disabled in Work settings; existing authenticated SSH enabled collection. Private runner independently executed request 9192e85854f246e08cd66674e56e24c5 successfully; existing deployment preserved.
## Next steps
- Publish owned results and update the linked Google companion. Check saved/Gmail receipts before sending the single DONE email; START ID 1a15110b6da2f189, no DONE yet.
- Pause `monitor-sherlock-training` after verified closeout. Do not rerun submit.sh or either completed trajectory.
- Persistent terminal/archive receipts are inside `results_bundle.tar.gz`; bundle SHA-256 6d1eadbe6417b48f15bb54cf5d27b9be95da5acc5e0b940c999d15e118fe8da2 matches local/scratch/persistent copies.
## Brando to-do
- Restore Google companion edit access only; no training action needed.

## Log
- 10-18-2026 14:57 PDT — Authenticated Sherlock, verified the original corpus hash, prepared two separate full-training replications; existing SNAP workers preserved.
- 10-18-2026 15:19 PDT — Uploaded and hashed package; replaced unstarted prep job 48377449 to correct Slurm submit directory; prep 48377554 running, GPU jobs 48378536/48378539 held, collector 48378541 queued. START mail delivered and 15-minute heartbeat created.
- 10-18-2026 15:23 PDT — Preparation 48377554 completed 0:0, all token hashes passed. Full Linux verification: 1,382 passed, three skipped, six subtests passed; three added terminal controls passed on Linux and macOS. Google companion created and link-viewer sharing verified.
- 10-18-2026 15:25 PDT — Published frozen protocol/source as c54240b, then released training jobs 48378536 and 48378539. Preparation passed. Preserved full Linux verification log and removed its owned isolated test copy.
- 10-18-2026 15:30 PDT — Verified real optimizer updates (16/658), H100 device, finite loss and nonzero gradients; peak memory 46.56 GiB so far. Seed 1 remains dependent. Saved initial receipt and visual evidence; canonical checkout current and temporary copies cleaned.
- 10-18-2026 15:31 PDT — Later launch sample reached 24/658 updates and 197,859 loss tokens; peak allocated device memory 47.85 GiB. Saved the partial step sample and readable screenshot provenance.
- 10-18-2026 16:37 PDT — Seed 20260830 completed 0:0 at 16:30:35 PDT and all 658 records were collected and checksum-verified. Seed 20260831 started on sh04-01n01 and reached 25 updates; progress age 1.1 seconds, no inspected log failure markers. Root-level terminal/archive receipts absent as expected while collector waits. Google companion updated; monitor remains active.
- 10-18-2026 21:21 PDT — Verified all four terminal jobs, collected both complete trajectories, matched frozen hashes, validated configurations/shard structures and persistent archive (36 files; 30 independently rehashed metadata files). Existing private runner independently executed a command without Duo. Closeout publication/email/pause in progress.
