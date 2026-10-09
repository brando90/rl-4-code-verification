# Experiment 10 results: promotion-policy replay on SWE-bench Verified factor matrices

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/results.md>

**TLDR:** No real-data statistic has been computed yet. Protocol revision 3 fixes all findings from two GPT-6 Astra (effort ultra) reviews. The analysis code passes 15 unit tests, including every reviewer counterexample, plus synthetic signal, null, coverage and full-pipeline checks. Claude Fable 5.1 was unavailable on all three Claude accounts.

**Status:** LOCK CANDIDATE (10-09-2026).

**Last updated:** 10-09-2026.

| Stage | State | Evidence |
|---|---|---|
| Design and protocol revision 1 | DONE | commit `769ade0` |
| GPT-6 Astra (effort ultra) design review of revision 1 | DONE (15 findings, applied in revision 2) | [reviews/design_review_gpt6_astra_ultra_10-09-2026.md](reviews/design_review_gpt6_astra_ultra_10-09-2026.md) |
| GPT-6 Astra (effort ultra) protocol-and-code review of revision 2 | DONE: 3 blocking, 5 major, 1 minor; all fixed in revision 3, with counterexamples as regression tests | [reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md](reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md) |
| Claude Fable 5.1 review | NOT AVAILABLE: personal account out of usage credits (attempt 1 died 10:18 PDT, no file); Stanford account "Usage credits are required for this model"; Vals account "individual spend limit" (preflight probes, 10-09-2026). No credits bought | — |
| Protocol revision 3 | DONE (lock candidate) | [PROTOCOL.md](PROTOCOL.md) |
| Analysis code and unit tests | DONE (15/15 pass) | `expt_v1/analyze_e10.py`, `tests/test_e10_replay.py` |
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

**Full-pipeline check (revision 3).** On the synthetic signal set, 40 splits × 1,000 draws with 8 worker processes (`signal_r3_40splits_1000draws.json`):

- **Cost:** 42.4 s wall time, 2.7 GB peak resident memory. The real run (1,000 splits) is estimated at about 18 minutes.
- **Matching:** matched rates R0 0.499 versus R3 0.499. Every family had full support (40/40 splits, 1,000/1,000 valid draws).
- **Undefined stays undefined:** the deployable zero-loss rule accepted no pair, so its conditional harmful promotion rate is reported as undefined, not 0.

## Deviations and open questions

- **10-09-2026, review worktree removal:** removing the GPT-6 reviewer's worktree with `--force` discarded its checkpoint file (`CKPT_codex-rl4cv-e10-e11-design-review.md`) and an edit it had made to that worktree's copy of this ledger. The review file itself had been copied first and is unchanged.
