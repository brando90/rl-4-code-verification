# V20 validation recovery checkpoint

**Doc link:** [live results](results.md)

**TLDR:** Training pass is complete. Validation generation is waiting for an empty A100 after the SciPy import fix.

Created: 10-19-2026 1:15 PDT
Last updated: 10-19-2026 1:22 PDT

## Goal
- Score all 1,080 frozen validation cells from the completed fresh-base checkpoint. Keep the test split sealed.
## What ran
- Remote result receipt: 1,784/1,784 updates, 3,568 rows, 2,948,296 loss tokens, peak 43.79 GiB, exit preserved. Generation died importing system SciPy against NumPy 2.3.5.
- Installed SciPy 1.16.3 into the brando9 generation environment. vLLM now imports. No optimizer reset.
## Results
- Validation scores unmeasured, 0/1,080. Recovery home `/lfs/skampere1/0/brando9/rl4cv_v20_validation_recovery`.
## Stuck / blocked
- eth127 corpus directory is not writable by brando9. All eight A100s were busy at launch, so generation waits for an empty card in {1, 0, 5}.
## Next steps
- The tmux session `rl4cv-v20-validation-recovery` launches the frozen vLLM command on the first empty allowed A100, then verifies 1,080 unique cells.
## Brando to-do
- None.

## Log
- 10-19-2026 1:15 PDT — Confirmed training COMPLETE and generation import failure. Installed SciPy 1.16.3 and started the empty-GPU validation waiter.
- 10-19-2026 1:22 PDT — GPU 1 attempt failed on system PyOpenSSL. Installed PyOpenSSL 26.4.0 in the generation environment and restarted the waiter. One failure counts toward a cap of three.
