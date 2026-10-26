# Existing validation signal audit checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v12/rl_signal_audit/CKPT_signal_audit.md>

**TLDR:** Local audit and Sherlock job 48510183 agree: the current-corpus checkpoint has nonzero validation reward signal.

Created: 10-19-2026 12:30 PDT
Last updated: 10-19-2026 12:56 PDT

## Goal
- Quantify reward signal in all 1,080 existing version-12 validation outputs without new generation or test access, then match that measurement on Sherlock.
## What ran
- Inherited chats 01a150f7 and 01a1559f. Local audit on the committed 1,080-cell table: 3 targeted tests passed. ρ 15.37 [9.37, 22.76], H 0.164 [0.107, 0.228], 24/135 mixed tasks, 191 nonzero admitted advantages.
- Prior bridge run 39309938703 failed before Slurm admission on the dev partition. Original remote directory preserved. Recovery directory created and fixed script uploaded without overwrite.
## Results
- Local and Sherlock job 48510183 agree: NONZERO_VALIDATION_RL_SIGNAL. ρ 15.37 [9.37, 22.76], H 0.164 [0.107, 0.228], 24/135 mixed, 191 nonzero admitted advantages. Exit 0:0 in 18s on sh02-01n56. Job 48509206 was the failed module-load attempt.
## Stuck / blocked
- None for this audit. The separate Sherlock two-seed validation cohort is still unmeasured and has another owner; do not launch a second copy.
## Next steps
- Publish this audit from a current main checkout. Leave the replica validation with its existing owner.
## Brando to-do
- None.

## Log
- 10-19-2026 12:30 PDT — Took over inherited audit, confirmed failed admission, fixed serialization and verified 20 tests; preparing bounded remote recovery.
- 10-19-2026 12:41 PDT — Recomputed locally (3 tests passed; nonzero signal) and submitted normal-partition job 48509206 once.
- 10-19-2026 12:48 PDT — Job 48509206 failed: NumPy missing inside the batch environment. Submitted one infrastructure retry, job 48510183, with an explicit interpreter and NumPy path.
- 10-19-2026 12:56 PDT — Job 48510183 completed 0:0 in 18s. Summary matched the local receipt on every compared field.
