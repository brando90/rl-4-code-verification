# Sherlock training live results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/results.md>

**TLDR:** Sherlock input admission passed for all 1,315 examples; two full training runs are held pending publication.

**Status:** PREPARING — jobs 48378536 and 48378539 are held; 0/2 training runs complete.
**Last updated:** 10-18-2026 15:19 PDT

| Phase | State | Observed evidence |
|---|---|---|
| Sherlock access | DONE | Authenticated OnDemand shell on sh03-ln02 as brando9; sanmi scheduler association; zero existing user jobs at initial check |
| Input transfer | DONE | Original training corpus retrieved from SNAP; exact SHA-256 verified |
| Token and runtime admission | PASS | Job 48377554 completed 0:0; all 1,315 examples / 5,752,936 loss tokens match; maximum sequence 16,112 |
| Seed 20260830 | HELD | Job 48378536; 0/658 optimizer updates |
| Seed 20260831 | HELD | Job 48378539; 0/658 optimizer updates |
| Held-out evaluation | NOT PART OF THIS RUN | Validation not measured; test unopened |

No training result is available. The protocol declares 2,630 example exposures and 11,505,872 assistant loss tokens across both runs, without changing the existing recovery jobs.

**TLDR-end:** [rl4cv: Sherlock training] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` has authenticated cluster access and verified source data; training has not started.

Completion collector job 48378541 follows every terminal scheduler outcome, including failure/cancellation, and retains hashed checkpoints under `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4`. A 15-minute chat monitor checks progress and errors. The monitor requires this Mac/app and browser authentication; Slurm jobs and terminal collection survive browser closure. [Google companion](https://docs.google.com/document/d/1S1FgSRRSzVmh4bF8XBtaNnYupBeaHsrjmP0dLwwL1eM/edit).
