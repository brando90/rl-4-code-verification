# Experiment 10 results: promotion-policy replay on SWE-bench Verified factor matrices

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/results.md>

**TLDR:** Phase A's primary replay is running on the real data (launched 10-14-2026 13:02 PDT on skampere1, zero model calls) under the LOCKED protocol revision 3 (commit `55d1c53`); no real-data statistic has been read yet. The matched-test-lists sensitivity is BLOCKED by the protocol's own shape stop rule (164 × 421 instead of the declared 164 × 420, because one declared drift task is outside the cohort) and needs an amendment or `expt_v2`. Protocol revision 3 fixes all findings from two GPT-6 Astra (effort ultra) reviews. The analysis code passes 15 unit tests, including every reviewer counterexample, plus synthetic signal, null, coverage and full-pipeline checks. Claude Fable 5.1 was unavailable on all three Claude accounts.

**Status:** LOCKED; PHASE A RUNNING (10-14-2026).

**Last updated:** 10-14-2026.

| Stage | State | Evidence |
|---|---|---|
| Design and protocol revision 1 | DONE | commit `769ade0` |
| GPT-6 Astra (effort ultra) design review of revision 1 | DONE (15 findings, applied in revision 2) | [reviews/design_review_gpt6_astra_ultra_10-09-2026.md](reviews/design_review_gpt6_astra_ultra_10-09-2026.md) |
| GPT-6 Astra (effort ultra) protocol-and-code review of revision 2 | DONE: 3 blocking, 5 major, 1 minor; all fixed in revision 3, with counterexamples as regression tests | [reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md](reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md) |
| Claude Fable 5.1 review | NOT AVAILABLE: personal account out of usage credits (attempt 1 died 10:18 PDT, no file); Stanford account "Usage credits are required for this model"; Vals account "individual spend limit" (preflight probes, 10-09-2026). No credits bought | — |
| Protocol revision 3 | DONE (locked) | [PROTOCOL.md](PROTOCOL.md) |
| Analysis code and unit tests | DONE (15/15 pass) | `expt_v1/analyze_e10.py`, `tests/test_e10_replay.py` |
| Synthetic checks | DONE | `expt_v1/results/synthetic/` |
| Lock and frozen forecast | DONE: commit `55d1c53` (10-09-2026 16:43 PDT); forecast `expt_v1/forecasts/e10_forecast.json`, SHA-256 `e4eccd8b84fa427fa9d5839980df6c08293f6a628f93cfc0c01f78cf2f163c23` (`verify_forecast` True on 10-14-2026); pins `analyze_e10.py` `a1278349…`, `tests/test_e10_replay.py` `dc1ba2e1…`, `per_cell_e07.jsonl.gz` `f064c395…`, drift list `e1d34185…` all re-verified | `expt_v1/forecasts/forecast_ledger.jsonl` |
| Phase A primary replay (`--sensitivity none`) | DONE (run): launched 10-14-2026 13:02 PDT on skampere1 (clone at `57c3bb6`, venv numpy 2.5.4, 15/15 tests pass there) in tmux `rl4cv-e10-phase-a-10-14`; 1,000 splits × 1,000 draws, 32 workers, one BLAS thread each; exit 0 at 13:04:56 PDT; output `e10_primary.json` SHA-256 `0005a03e455ae22a92edfee1d2632a4a3d1246ddfc8159d7c738b47f60ed20b1`. Scoring of the frozen predictions follows below | [`expt_v1/results/run_e10_primary.log`](expt_v1/results/run_e10_primary.log) |
| Phase A sensitivity (`--sensitivity matched_test_lists`) | BLOCKED under the lock: launched 13:02 PDT in tmux `rl4cv-e10-phase-a-sens-10-14`, exited after 1.4 s with the pinned stop rule `STOP: expected (164, 420), got (164, 421)`. Cause: of the 4 declared drift tasks, `django__django-10097` is not in the 424-task common cohort (0 `common_cohort` cells; the other 3 have 164 each), so the drop leaves 421 tasks. Needs a dated amendment or `expt_v2`, not a run under the old lock | [`expt_v1/results/run_e10_sensitivity_matched_test_lists.log`](expt_v1/results/run_e10_sensitivity_matched_test_lists.log) |
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

- **10-14-2026, matched-test-lists sensitivity blocked by its own stop rule.** PROTOCOL.md declares that dropping the 4 drift tasks gives 164 × 420 and that any other shape stops the analysis. On the real cohort the drop gives 164 × 421 because `django__django-10097` (1 drift cell) lies outside the 424-task common cohort; within the cohort the drift is 65 cells in 3 tasks. The pinned code stopped before computing any statistic (exit 1, 1.4 s). Re-admitting the sensitivity requires changing `EXPECTED_SHAPE` in `analyze_e10.py` or the protocol's declared drop, which is a dated amendment or a new `expt_v2` with its own lock; it was not done in this round. The primary analysis never reads the drift list and is unaffected. The check that found the cause read only cohort membership flags, no outcome.
- **10-09-2026, review worktree removal:** removing the GPT-6 reviewer's worktree with `--force` discarded its checkpoint file (`CKPT_codex-rl4cv-e10-e11-design-review.md`) and an edit it had made to that worktree's copy of this ledger. The review file itself had been copied first and is unchanged.
