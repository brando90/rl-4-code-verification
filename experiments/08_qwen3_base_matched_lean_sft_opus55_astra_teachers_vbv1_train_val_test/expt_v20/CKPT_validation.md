# V20 validation recovery checkpoint

**Doc link:** [live results](results.md)

**TLDR:** Training and validation are complete. Fresh-base scored 20/1080 (1.85%); V12 remains the stronger RL SFT start.

Created: 10-19-2026 1:15 PDT
Last updated: 10-20-2026 10:20 PDT

## Goal
- Score all 1,080 frozen validation cells from the completed fresh-base checkpoint. Keep the test split sealed.
## What ran
- Training: 1,784/1,784 updates, 3,568 rows, 2,948,296 loss tokens, peak 43.79 GiB.
- Validation: eth127 `v20_base_recovery3` wrote and scored all 1,080 cells under `corpus_training_v20/validation/v20_base/` (raw sha256 `f81b3e5e…93130955`).
- Parallel brando9 waiter at `/lfs/skampere1/0/brando9/rl4cv_v20_validation_recovery` failed three times: SciPy, PyOpenSSL, then CUDA 12.4 FlashInfer JIT (`--compress-mode`). Zero cells written there. `recover_validation.py` now forces CUDA 12.8 on PATH for any future retry.
## Results
- V20: 20/1080 successes (1.85%), CI [0.83%, 3.06%], 14 mixed tasks, target 25% not reached, test sealed.
- V12 reference: 120/1080 (11.11%), 24 mixed tasks; usable RL ρ/H already measured on that checkpoint.
## Stuck / blocked
- None for V20 measurement. Next scientific step is a stronger SFT than V12, or RL from V12—not further V20 generation.
## Next steps
- Treat V12 as the RL warm-start candidate.
- Optional: design the next SFT run to beat V12 validation success / mixed-task count under the same frozen eval.
## Brando to-do
- None.

## Log
- 10-19-2026 1:15 PDT — Confirmed training COMPLETE and generation import failure. Installed SciPy 1.16.3 and started the empty-GPU validation waiter.
- 10-19-2026 1:22 PDT — GPU 1 attempt failed on system PyOpenSSL. Installed PyOpenSSL 26.4.0 and restarted the waiter.
- 10-20-2026 10:05 PDT — Overnight brando9 waiter dead at failures=3; root cause CUDA 12.4 nvcc rejecting FlashInfer `--compress-mode`.
- 10-20-2026 10:20 PDT — Found eth127 recovery3 already complete: 1080/1080 scored, 20 successes. Published comparison vs V12; patched recovery CUDA path.
