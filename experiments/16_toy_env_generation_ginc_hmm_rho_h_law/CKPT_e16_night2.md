# Checkpoint: 16_toy_env_generation_ginc_hmm_rho_h_law Night 2

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/CKPT_e16_night2.md>

**TLDR:** All 384 Night 2 budget cells are complete at $0; verdict TIE WITH BASELINES. Final verification passed; publication and completion notification are being finalized.

Created: 10-15-2026 20:23 PDT
Last updated: 10-15-2026 20:44 PDT

## Goal
- Test positive transfer and held-out-scale selection in `16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2`.
## What ran
- Owner: Codex in `codex-rl4cv-e16-night2`, skampere1; full filesystem access, approval never, nice 10. Dedicated requested checkout retained during execution.
- Clean branch `ub9/e16-toy-env-generation`; PR #15 remains the requested publication destination.
- Run-start email sent, Gmail message `1a142b7613b21a70`; CPU PyTorch 2.14.1 installed in local ignored `.venv`.
## Results
- 384/384 cells, 224 positive (58.33%); 79/128 final-budget trajectories positive. Verdict TIE WITH BASELINES.
- n4 law pick e08: +0.0375 [−0.3500,+0.4500] percentage points, p-val=0.500. Meaningful positive transfer unestablished.
- Coverage correlation 0.6731 [0.5826,0.7244]; entropy still correlated at n4. Exact definitions in protocol.
- 754 tests passed / 38 skipped; 11 focused tests passed; every raw utility and frozen hash independently verified. Zero training reruns; $0.
## Stuck / blocked
- Nothing. Completed CPU sessions exited 0. User-designated execution checkout retains ignored starting tensors; hashes and retrieval paths in result metadata.
## Next steps
- [p 8/10] Publish final results and metadata-only repair to `ub9/e16-toy-env-generation`, update PR #15, then send verified run-done email. No experiment work remains.
## Brando to-do
- None.

## Log
- 10-15-2026 20:23 PDT -- Night 2 started; exact four-token forward scorer, mixtures and KL implementation written; no reinforcement-learning outcomes observed.
- 10-15-2026 20:35 PDT -- 3/4 starting policies and 48/64 probes complete. Generator proposals frozen; protocol clarified to preserve the actual Night 1 coverage metric. Persistent full-matrix sweep launched waiting for the preflight gate.
- 10-15-2026 20:35 PDT -- Full deterministic suite passed (753 passed, 38 skipped); 10 focused tests and a synthetic 384-cell analysis integration check passed. Preparing first publication of implementation and prospective design.
- 10-15-2026 20:44 PDT -- Coverage gate passed; n1–n3 completed; n4 forecast frozen and n4 execution verified at nice 10. Detected and repaired metadata key collision without changing raw outcomes or retraining.
- 10-15-2026 20:44 PDT -- All 384 cells and final analysis completed; all hashes and target-score arithmetic verified, full tests 754 passed / 38 skipped. About 17.0 minutes from first pretraining to last trajectory; 6,553,600 RL-generated tokens, $0. Final publication pending.
