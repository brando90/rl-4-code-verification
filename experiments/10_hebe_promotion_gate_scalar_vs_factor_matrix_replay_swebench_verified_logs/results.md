# Experiment 10 results: promotion-policy replay on SWE-bench Verified factor matrices

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/results.md>

**TLDR:** No real-data statistic has been computed yet. Protocol revision 2 applies the GPT-6 Astra (effort ultra) review, and the analysis code passes 8 unit tests plus synthetic signal, null and coverage checks. A replacement Claude Fable 5.1 review is pending before the lock.

**Status:** LOCK CANDIDATE (10-09-2026).

**Last updated:** 10-09-2026.

| Stage | State | Evidence |
|---|---|---|
| Design and protocol revision 1 | DONE | commit `769ade0` |
| GPT-6 Astra (effort ultra) design review | DONE (15 findings, all addressed in revision 2) | [reviews/design_review_gpt6_astra_ultra_10-09-2026.md](reviews/design_review_gpt6_astra_ultra_10-09-2026.md) |
| Claude Fable 5.1 design review | ATTEMPT 1 DIED (out of usage credits on the personal account, 10:18 PDT, no file written); attempt 2 on another account pending | — |
| Protocol revision 2 | DONE | [PROTOCOL.md](PROTOCOL.md) |
| Analysis code and unit tests | DONE (8/8 pass) | `expt_v1/analyze_e10.py`, `tests/test_e10_replay.py` |
| Synthetic checks | DONE | `expt_v1/results/synthetic/` |
| Lock and frozen forecast | NOT STARTED | — |
| Phase A replay on real data | NOT STARTED | — |
| Phase B (real AlphaHebe records) | WAITING on the AlphaHebe team's export | — |

## Synthetic checks before the lock (no real data)

Data comes from `expt_v1/synthetic_e10.py`: 164 systems × 424 tasks, 20 splits × 100 draws.

- **Signal set:** systems differ in ability and in a propensity to break PASS_TO_PASS tests.
- **Null set:** no system-specific breakage.

| Check | Signal | Null | Consequence for the protocol |
|---|---:|---:|---|
| H2(a) partial Spearman (3 binary covariates) | 0.096 [0.059, 0.130] | 0.112 [0.056, 0.148] | Positive even under the null: factor values also sharpen the ability estimate, so H2 is descriptive, not a mechanism test |
| H2 with marginal factor means | 0.052 [0.008, 0.087] | 0.037 [0.007, 0.081] | Same caveat |
| Unstratified "fewest regressions" (S3) versus "largest gain" (S0+), HPR | 0.304 versus 0.260 | 0.305 versus 0.266 | Ranking by risk alone confounds gain size, so primary policies are stratified by validation net gain |
| Stratified R0 − R3 HPR (factor versus scalar at equal gain) | +0.015 [−0.008, +0.034] | +0.014 [−0.012, +0.036] | Small effects; intervals are wide at this size |

**Bootstrap coverage** (`coverage_check.json`): 400-system population, 100 samples of 60 systems, 200 tasks, 10 splits, 200 draws. The nominal 95% dyadic-bootstrap intervals covered the population value in 100% (H1 HPR), 100% (R0 − R2), 100% (R2 − R3), 99% (R0 − R3) and 99% (H2) of replications. The intervals are conservative in this simulation, partly because 60 of 400 systems are sampled without replacement. This is a sanity check, not a proof of calibration.

## Deviations and open questions

- **10-09-2026, review worktree removal:** removing the GPT-6 reviewer's worktree with `--force` discarded its checkpoint file (`CKPT_codex-rl4cv-e10-e11-design-review.md`) and an edit it had made to that worktree's copy of this ledger. The review file itself had been copied first and is unchanged.
