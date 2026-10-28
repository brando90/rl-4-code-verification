# Experiment 25 (checkpoint reuse): should the ρ–H predictive law reuse training checkpoints, scaling-law style?

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/25_checkpoint_reuse_for_rho_h_law/README.md>

**TLDR:** Brando's question (10-28-2026): scaling-law work reuses checkpoints of one run; should the ρ–H law do the same instead of separate runs? The plan answers yes for the budget axis, prefix extrapolation and rolling ρ, H, and no for replacing separate runs per scale × environment × seed. This folder holds Stage 0: free CPU analyses of existing data (0a inventory, 0b prefix extrapolation on the toy, 0c SFT rungs versus fresh runs, 0d power) and the audit of public checkpoints (0e: Marin Delphi, laion post-training repos, Open Athena Snowball). Protocol is frozen in [PROTOCOL.md](PROTOCOL.md); live numbers are in [results.md](results.md). Night 6 (CPU toy, dense versus independent) and the Lean RL pilot are separate steps.

Plan (Google Doc, v5 after three QA rounds): <https://docs.google.com/document/d/1aGlvbsZsEDLz9FG3BozUsT1O1J9lsR6GS9VzEr85Lfw/edit>

## Hypothesis and decision criterion
See the plan §4 and §5. This folder tests R2 (prefix extrapolation, P2) and R4 (SFT rungs as start policies, P4) retrospectively on committed data, and audits R5 (public checkpoints, P6 to P9). Outcome labels (ADOPT, ADOPT FOR DENSE CHECKPOINTS ONLY, NO ADVANTAGE, WRONG DOMAIN) need Stage 1 and 2 and are not issued here.

## Structure
- `PROTOCOL.md`: frozen first. `results.md`: 0a to 0e. `expt_v1/`: code (`stage0.py`), `cc.md`, `results/`, `audit_0e/`.
- Tests: `tests/test_e25_stage0.py`, run by `make test`.

## Status log (newest first)
- 10-28-2026 (Stage 0 status): analyses 0a to 0e are done (results.md). The completion-mode generator in `expt_v2/` passed the 0e smoke on a free skampere1 GPU; Q1 (Delphi 3.4B, 9.7B replicas) is in progress, Q3 (P8) and the final results.md rewrite are pending; Q4 and Q2(c) are blocked by licence terms.
- 10-28-2026: folder created; PROTOCOL.md was committed before any 0b, 0c or R5 outcome was read and was pushed together with the results (not before them). Addenda A and A.1 (R5 environments, exemplars, smoke bar) were committed before any R5 generation.
- `expt_v6/` (Night 6, from another agent) is separate work and not part of this Stage 0 result.
