# Sherlock training live results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/results.md>

**TLDR:** Seed 20260830 completed all 658 updates and exported its checkpoint. Seed 20260831 is now training; 1/2 trajectories are complete and final persistent archive verification is pending.

**Status:** RUNNING — job 48378536 COMPLETED 0:0; job 48378539 training on sh04-01n01; 1/2 trajectories complete.
**Last updated:** 10-18-2026 16:37 PDT

| Phase | State | Observed evidence |
|---|---|---|
| Sherlock access | DONE | Authenticated OnDemand shell on sh03-ln02 as brando9; sanmi scheduler association; zero existing user jobs at initial check |
| Input transfer | DONE | Original training corpus retrieved from SNAP; exact SHA-256 verified |
| Token and runtime admission | PASS | Job 48377554 completed 0:0; all 1,315 examples / 5,752,936 loss tokens match; maximum sequence 16,112 |
| Seed 20260830 | COMPLETE | Job 48378536 COMPLETED 0:0 on H100 80 GB; 658/658 updates, 1,315/1,315 examples, 5,752,936/5,752,936 loss tokens; 658/658 finite step records with nonzero gradients |
| Seed 20260831 | RUNNING | Job 48378539 on H100 80 GB; observed 25/658 updates, 50/1,315 examples, 224,456/5,752,936 loss tokens; progress age 1.1 seconds |
| Persistent archive | PENDING | Collector 48378541 waits for seed 20260831; root-level terminal/archive receipts not yet present |
| Held-out evaluation | NOT PART OF THIS RUN | Validation not measured; test unopened |

The first completed training result is available: [result receipt](results/20260830/result.json), [all 658 steps](results/20260830/steps.csv), [12-file export hash manifest](results/20260830/weights_manifest.json), and [collection verification](results/20260830/collection_verification.json). All three collected files match remote SHA-256 values exactly. The final-step training loss was 0.170871; this is a descriptive value for the last training batch, not a held-out accuracy estimate. Training-loop elapsed time was 3,703.60 seconds; total GPU allocation was 01:04:20 (1.072 GPU-hours), including startup and export. Peak allocated device memory was 57.66 GiB. The full two-seed protocol still declares 2,630 example exposures and 11,505,872 assistant loss tokens within eight GPU-hours.

Collaborator update: The first Sherlock replication finished all 658 updates and exported its checkpoint; the second is now training. I’ve preserved the full first trajectory and exact hashes, while held-out accuracy and final archive verification remain pending.

**TLDR-end:** [rl4cv: Sherlock training] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` has one complete H100 trajectory and a second in progress; final persistent checkpoint verification remains pending.

Completion collector job 48378541 follows every terminal scheduler outcome, including failure/cancellation, and is configured to retain hashed checkpoints under `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`. A 15-minute chat monitor checks progress and errors. The monitor requires this Mac/app and browser authentication; Slurm jobs and terminal collection survive browser closure. [Google companion](https://docs.google.com/document/d/1S1FgSRRSzVmh4bF8XBtaNnYupBeaHsrjmP0dLwwL1eM/edit).

Verification: [full Linux log](results/make-test-linux.txt), 1,382 tests plus six subtests passed, three skipped; three new terminal-state controls passed. The exact corpus/token admission and source hashes are in [prepare_receipt.json](results/prepare_receipt.json).

First execution evidence: [initial receipt](results/initial_training_receipt.json) records four completed updates and exact runtime/input identity; [later visual receipt](results/sherlock_training.png) shows continuing execution. Peak allocated device memory at update 24 was 47.85 GiB; the completed first run reached 57.66 GiB. These are descriptive execution measurements, not held-out performance estimates.

Latest scheduler and freshness evidence: [monitor receipt](results/first_seed_completion_monitor.json). No death, timeout, cancellation or stale-progress condition was observed. The completion email is reserved for the verified terminal outcome of both runs and the persistent archive.
