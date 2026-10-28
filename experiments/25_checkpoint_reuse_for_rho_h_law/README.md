# Experiment 25 (checkpoint reuse): should the ρ–H predictive law reuse training checkpoints, scaling-law style?

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/25_checkpoint_reuse_for_rho_h_law/README.md>

**TLDR:** Brando's question (10-28-2026): scaling-law work reuses checkpoints of one run; should the ρ–H law do the same instead of separate runs? The plan answers yes for the budget axis, prefix extrapolation and rolling ρ, H, and no for replacing separate runs per scale × environment × seed. This folder holds Stage 0: free CPU analyses of existing data (0a inventory, 0b prefix extrapolation on the toy, 0c SFT rungs versus fresh runs, 0d power) and the audit of public checkpoints (0e: Marin Delphi, laion post-training repos, Open Athena Snowball). Protocol is frozen in [PROTOCOL.md](PROTOCOL.md); live numbers are in [results.md](results.md). Night 6 (CPU toy, dense versus independent) and the Lean RL pilot are separate steps.

Plan (Google Doc, v5 after three QA rounds): <https://docs.google.com/document/d/1aGlvbsZsEDLz9FG3BozUsT1O1J9lsR6GS9VzEr85Lfw/edit>

## Hypothesis and decision criterion
See the plan §4 and §5. This folder tests R2 (prefix extrapolation, P2) and R4 (SFT rungs as start policies, P4) retrospectively on committed data, and audits R5 (public checkpoints, P6 to P9). Outcome labels (ADOPT, ADOPT FOR DENSE CHECKPOINTS ONLY, NO ADVANTAGE, WRONG DOMAIN) need Stage 1 and 2 and are not issued here.

## Structure
- `PROTOCOL.md`: frozen first. `results.md`: 0a to 0e, smoke, Q1, Q3. `expt_v1/`: Stage 0 code (`stage0.py`), `cc.md`, `results/`, `audit_0e/`. `expt_v2/`: completion-mode generator, Q1 scoring, P6 and Q3 scripts, results and raw samples.
- Tests: `tests/test_e25_stage0.py`, `tests/test_e25_completion.py`, `tests/test_e25_q3.py`, run by `make test`.

## Status log (newest first)
- 10-28-2026 (R5 status): smoke PASS; Q1 done at 3.4B and 9.7B (P6 NOT TESTABLE: 2 and 3 measurable environments, bar is 4); Q3 done as a worked example (P8: neither form beats a flat baseline); Q2(a) and Q2(b) not run (AT-1796); Q4 and Q2(c) blocked by license. Details and the verdict list: results.md.
- 10-28-2026 (Stage 0 status): analyses 0a to 0e are done (results.md); P2 HOLDS weakly, P4 EQUIVALENT.
- 10-28-2026: folder created; PROTOCOL.md was committed (locally) before any 0b, 0c or R5 outcome was read, and pushed together with the results, not before them. Addenda A and A.1 (R5 environments, exemplars, smoke bar) were committed before any R5 generation.
- `expt_v6/` (Night 6, from another agent) is separate work and not part of this Stage 0 result.
