# Experiment 14 light QA: resolution of the findings

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/reviews/light_qa_resolution_10-12-2026.md>

**TLDR:** The single light QA round reviewed draft revision 1 at `1dad751`: Codex GPT-6 Astra, effort ultra, personal Codex account on `skampere1`, with verified full access. It returned `VERDICT: FAIL`: 2 critical, 4 major and 1 minor finding. The driver (Claude Code `claude-opus-5-5`, effort max, Vals profile) fixed all seven in the code and in protocol revision 2. Each fix has a regression test, and the reviewer's own counterexamples are among the tests. Per the light-QA convention there is no re-review.

**Review record:** [`light_qa_codex_gpt6_astra_ultra_10-12-2026.md`](light_qa_codex_gpt6_astra_ultra_10-12-2026.md), kept verbatim as provenance.

**Route:** two earlier launch attempts produced no review.

- The Vals Codex account (`~/.codex-vals`) hit its usage limit (until 10-17-2026 21:11) before reviewing.
- The Stanford account (`~/.codex-su`) came up read-only (`approval: on-request`, `sandbox: read-only`) despite the full-access flags, so it was stopped before any output.
- The completed review ran on the personal account (`~/.codex`). Review-only use of a personal subscription is allowed by the VeriBench rules; no measured call was made.

| # | Severity | Finding | Fix | Regression test (`tests/test_e14_irt.py`) |
|---|---|---|---|---|
| 1 | CRITICAL | A fixed 401-node grid on [−6, 6] with no numerical gate. In the reviewer's case, 41% of a posterior sat on the end node and the forecast moved 0.30 | Base grid 1,201 nodes on [−12, 12]; check grid 4,801 nodes on [−18, 18]. A fit is accepted only if the gradient bound also holds on the check grid. Gates: endpoint mass ≤ 1e-8 for every scored posterior, and check-grid rescoring change ≤ 1e-6 for every within-half fit and for the K-fold models (first 20 splits at n_A = 50). A failed gate makes the affected rule inconclusive | `test_review_finding1_support_counterexample_now_passes_the_gates` (the reviewer's all-zero panel and all-one target) |
| 2 | CRITICAL | A NaN gradient was counted as converged, and a finite failed fit could supply the decisive split | `max_abs` returns NaN for any non-finite input, so NaN never passes a tolerance. A failed within-half fit leaves its split undefined. P1 is inconclusive if more than 1% of fits fail or if the decision differs with failed splits at worst and best case. Combined Q1 rule frozen | `test_review_finding2_nan_gradient_is_a_failure`, `test_review_finding2_failed_split_cannot_decide_the_rank_rule` (the reviewer's 1,199/1/800 case) |
| 3 | MAJOR | Zero-SE pairs dropped, matched counts could differ, and undefined rates became 0 | A zero SE gives z = ±∞ or 0 by the sign of the gain. `top_n` keeps ±∞ and fills exact counts. Matched counts are asserted, and the comparison is reported unavailable on failure. Zero-promotion rates are `None` | `test_review_finding3_saturated_and_identical_pairs_and_exact_matching`, `test_zero_promotions_give_undefined_rates` |
| 4 | MAJOR | The sign-flip p-value was labelled as a zero-mean test | Level p-values now come from the same system bootstrap as the interval (null: zero mean; +1 corrected). The sign-flip test is kept as a diagnostic labelled with its symmetry null and never decides a rule | `test_review_finding4_level_p_value_targets_the_mean` |
| 5 | MAJOR | A Rasch STOP kept verdict-dependent outcomes and returned success | `run` raises `RaschCheckFailed` as soon as a size fails. `main` writes a failure receipt with no verdict or outcomes, marks every forecast outcome unavailable, and exits with code 2 | `test_review_finding5_stop_path_writes_receipt_without_outcomes` |
| 6 | MAJOR | The level-win attribution and the uncertainty scope were not rendered | The verdict text and the results tables state the attribution: linear-regression control beaten or not. The scope sentence is printed beside the primary results | `test_q1_attribution_text_follows_the_control` |
| 7 | MINOR | Synthetic `--boot` and sign-flip counts did not reach every call | Draw counts are passed explicitly, and test descriptions are built from the actual counts | `test_review_finding7_bootstrap_uses_the_requested_draws` |

**Verification:** `tests/test_e14_irt.py` passes 19 of 19 on the Mac; the full suite and the synthetic pipeline results are in `results.md`. No real-data IRT fit or Q1 statistic was computed before the lock.

```
VERDICT: FIXED
CRITICAL_ISSUES: 0 (2 found, 2 fixed)
MAJOR_ISSUES: 0 (4 found, 4 fixed)
FIXES_APPLIED: 7
STRUCTURAL: SKIP
SUMMARY: All seven light-QA findings on draft revision 1 are fixed in code and in protocol revision 2, each with a regression test that includes the reviewer's counterexamples; no re-review per the light-QA convention.
```
