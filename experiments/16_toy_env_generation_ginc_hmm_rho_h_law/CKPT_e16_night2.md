# Checkpoint: 16_toy_env_generation_ginc_hmm_rho_h_law Night 2

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/CKPT_e16_night2.md>

**TLDR:** Implementing and running the four-token CPU experiment under the requested $0 budget.

Created: 10-15-2026 20:23 PDT
Last updated: 10-15-2026 20:35 PDT

## Goal
- Test positive transfer and held-out-scale selection in `16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2`.
## What ran
- Owner: Codex in `codex-rl4cv-e16-night2`, skampere1; full filesystem access, approval never, nice 10. Dedicated requested checkout retained during execution.
- Clean branch `ub9/e16-toy-env-generation`; PR #15 remains the requested publication destination.
- Run-start email sent, Gmail message `1a142b7613b21a70`; CPU PyTorch 2.14.1 installed in local ignored `.venv`.
## Results
- 10 focused tests pass; All four starting policies trained; final n4 probes active. No reinforcement-learning outcomes.
## Stuck / blocked
- Nothing. System-Python full suite passes: 753 passed / 38 skipped. Initial managed-Python failures were environment-only; training environment unchanged.
## Next steps
- [p 8/10] Observe persistent sessions `rl4cv-e16-night2-cpu-preflight` and `rl4cv-e16-night2-cpu-sweep`. Sweep waits for pooled coverage gate, completes n1–n3, freezes n4 forecasts, runs n4 and analyzes; logs in `expt_v2/results/pilot_v3`. Publish after full tests pass.
## Brando to-do
- None.

## Log
- 10-15-2026 20:23 PDT -- Night 2 started; exact four-token forward scorer, mixtures and KL implementation written; no reinforcement-learning outcomes observed.
- 10-15-2026 20:35 PDT -- 3/4 starting policies and 48/64 probes complete. Generator proposals frozen; protocol clarified to preserve the actual Night 1 coverage metric. Persistent full-matrix sweep launched waiting for the preflight gate.
- 10-15-2026 20:35 PDT -- Full deterministic suite passed (753 passed, 38 skipped); 10 focused tests and a synthetic 384-cell analysis integration check passed. Preparing first publication of implementation and prospective design.
