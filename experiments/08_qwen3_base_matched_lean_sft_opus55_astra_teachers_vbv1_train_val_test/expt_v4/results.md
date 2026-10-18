# Sherlock training live results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/results.md>

**TLDR:** Real H100 training is progressing: seed 20260830 reached 24/658 updates; seed 20260831 is queued behind it. Input admission and deterministic checks passed.

**Status:** RUNNING — job 48378536 on sh04-01n01; job 48378539 waiting on its successful completion; 0/2 complete.
**Last updated:** 10-18-2026 15:32 PDT

| Phase | State | Observed evidence |
|---|---|---|
| Sherlock access | DONE | Authenticated OnDemand shell on sh03-ln02 as brando9; sanmi scheduler association; zero existing user jobs at initial check |
| Input transfer | DONE | Original training corpus retrieved from SNAP; exact SHA-256 verified |
| Token and runtime admission | PASS | Job 48377554 completed 0:0; all 1,315 examples / 5,752,936 loss tokens match; maximum sequence 16,112 |
| Seed 20260830 | RUNNING | Job 48378536 on H100 80 GB; 24/658 updates, 48/1,315 examples, 197,859/5,752,936 loss tokens; finite loss and nonzero gradients |
| Seed 20260831 | DEPENDENCY | Job 48378539; 0/658 optimizer updates |
| Held-out evaluation | NOT PART OF THIS RUN | Validation not measured; test unopened |

No completed training result is available. The protocol declares 2,630 example exposures and 11,505,872 assistant loss tokens across both runs, without changing the existing recovery jobs.

**TLDR-end:** [rl4cv: Sherlock training] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` has verified real H100 optimizer progress; both full trajectories and final checkpoints remain in progress.

Completion collector job 48378541 follows every terminal scheduler outcome, including failure/cancellation, and retains hashed checkpoints under `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`. A 15-minute chat monitor checks progress and errors. The monitor requires this Mac/app and browser authentication; Slurm jobs and terminal collection survive browser closure. [Google companion](https://docs.google.com/document/d/1S1FgSRRSzVmh4bF8XBtaNnYupBeaHsrjmP0dLwwL1eM/edit).

Verification: [full Linux log](results/make-test-linux.txt), 1,382 tests plus six subtests passed, three skipped; three new terminal-state controls passed. The exact corpus/token admission and source hashes are in [prepare_receipt.json](results/prepare_receipt.json).

First execution evidence: [initial receipt](results/initial_training_receipt.json) records four completed updates and exact runtime/input identity; [later visual receipt](results/sherlock_training.png) shows continuing execution. Peak allocated device memory at update 24 was 47.85 GiB; the full-run peak is not yet known. These are descriptive execution measurements, not held-out performance estimates.
