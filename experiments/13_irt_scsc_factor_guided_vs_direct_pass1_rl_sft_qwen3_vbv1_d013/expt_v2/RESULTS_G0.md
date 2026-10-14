# G0 under Amendment A3: PASS

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_G0.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 completed its one G0 run with verdict **PASS**. Phase 1 is admitted; its generation admission, anchors and fits remain pending.

Published result prepared: 10-14-2026 14:06 PDT. G0 asks whether the fixed partial-credit reward varies where strict reward does not, and whether earlier partial credit predicts later strict success. The primary stratum is Qwen3 4B (four billion parameters), on all 135 VeriBench V1 validation tasks with eight samples per task at each of the 50% and full supervised fine-tuning rungs. The 1.7B and 8B strata are secondary and do not gate.

## Full-manifest bounds and verdict

Dense-only means strict is constant across all eight full-rung samples while partial reward B varies. Area under the receiver operating characteristic curve (AUC) predicts any full-rung strict success using mean earlier B, conditioned on zero earlier strict successes. Thresholds are at least 21/135 dense-only tasks and AUC ≥ 0.65, from PROTOCOL §3 and PLAN §4. Admission requires both minima to clear the thresholds and AUC to be defined at every feasible completion. Either maximum below its threshold fails; otherwise the gate is INCONCLUSIVE. An incomplete primary stratum fails. Undefined AUC at every completion fails.

| Stratum | Tasks affected by exclusions | Excluded cells across two rungs | Dense-only minimum–maximum | AUC minimum–maximum | Membership/label configurations; method | Verdict |
|---|---:|---:|---:|---:|---|---|
| 4B | 23/135 | 34/2,160 | 89–97 / 135 | 0.670652174–0.904643963 | 221,184; exact | PASS |
| 1p7B | 21/135 | 38/2,160 | 103–111 / 135 | 0.671604938–0.937687688 | 196,608; exact | PASS |
| 8B | 23/135 | 38/2,160 | 90–100 / 135 | 0.557485525–0.909090909 | 31,104; exact | INCONCLUSIVE |

These ranges bound every feasible completion of excluded cells; they are not sampling confidence intervals. Strict is zero or one; B is one for strict successes and otherwise ranges over [0,1]. Retained cells stay unchanged. One-class possibilities and any outer-bound fallback are recorded separately in the machine-readable result. No point imputation replaces these bounds. The original full denominators remain intact.

**Transition:** Phase 1 is admitted; its generation admission, anchors and fits remain pending. No G1, independent-batch H2, training pilot, main training or Phase 2 test outcome is claimed by this report.

The primary minima are 89/135 = 0.659259 dense-only share and AUC 0.670652174, so both pass. The AUC minimum has conditional grouped-bootstrap 95% interval [0.524992589, 0.811120839]; this interval is not the frozen point-threshold decision rule. All three strata used exact enumeration; no outer-bound fallback was needed, and AUC is defined at every completion in all three. The secondary 8B range crosses 0.65 and is INCONCLUSIVE; it does not gate. The carried F0v2 forecast of 0.50 dense-only share underpredicts the entire primary completion range, 0.659259–0.718519; p-val=n/a. F1v2 remains untested.

## Conditional uncertainty at attaining completions

Every row below is the unchanged frozen `evaluate` output at a retained witness. Intervals are 95% percentile intervals from 10,000 paired task-group resamples of the complete cohort, conditioning on earlier zero successes after each resample; seed 1302051. They describe sampling uncertainty conditional on that completion, not uncertainty over missingness or fitted models. The p-value is not applicable (p-val=n/a): the preregistered decision uses point thresholds, with no hypothesis test. Counts of positive/eligible tasks and valid AUC bootstrap draws are shown explicitly.

| Stratum | Completion | Dense-only count; share [95% interval] | AUC [95% interval] | Later positive / earlier-zero subset | Valid AUC draws |
|---|---|---|---|---:|---:|
| 4B | dense_minimum | 89/135; 0.659259 [0.562500, 0.757576] | 0.725155280 [0.579971998, 0.852871148] | 21/113 | 10000/10,000 |
| 4B | dense_maximum | 97/135; 0.718519 [0.625000, 0.810606] | 0.883838384 [0.776323104, 0.973648853] | 14/113 | 10000/10,000 |
| 4B | auc_minimum | 90/135; 0.666667 [0.568345, 0.765152] | 0.670652174 [0.524992589, 0.811120839] | 20/112 | 10000/10,000 |
| 4B | auc_maximum | 94/135; 0.696296 [0.601351, 0.789474] | 0.904643963 [0.808520309, 0.979612202] | 17/112 | 10000/10,000 |
| 1p7B | dense_minimum | 103/135; 0.762963 [0.685714, 0.835821] | 0.754192872 [0.603362419, 0.891788075] | 18/124 | 10000/10,000 |
| 1p7B | dense_maximum | 111/135; 0.822222 [0.753623, 0.886364] | 0.930008045 [0.879309255, 0.973060345] | 11/124 | 10000/10,000 |
| 1p7B | auc_minimum | 106/135; 0.785185 [0.710145, 0.855072] | 0.671604938 [0.504640541, 0.838263791] | 15/123 | 10000/10,000 |
| 1p7B | auc_maximum | 110/135; 0.814815 [0.744521, 0.880007] | 0.937687688 [0.888989804, 0.977348712] | 12/123 | 10000/10,000 |
| 8B | dense_minimum | 90/135; 0.666667 [0.575758, 0.755906] | 0.636111111 [0.444360300, 0.809048795] | 16/106 | 10000/10,000 |
| 8B | dense_maximum | 100/135; 0.740741 [0.654405, 0.825397] | 0.874458874 [0.781250000, 0.952820915] | 7/106 | 9991/10,000 |
| 8B | auc_minimum | 94/135; 0.696296 [0.608696, 0.781955] | 0.557485525 [0.355100591, 0.753637949] | 13/106 | 10000/10,000 |
| 8B | auc_maximum | 96/135; 0.711111 [0.623188, 0.796875] | 0.909090909 [0.835344349, 0.965219133] | 11/106 | 10000/10,000 |

All displayed minima and maxima are attained, certified extrema; no outer-bound fallback was used.

## Chronology, exclusions and execution

The [wrapper, tests and lock](reproduction/README_G0_A3.md) were published to main at `a717d069d0e47864c9ce6b47be0f3a11afd4781c` and the remote revision verified before the first G0 computation. The wrapper checked all nine bindings and its published revision before parsing validation rows. It imported only the frozen evaluator; `g0.py` remains byte-identical and its `main` was never run. A canonical exclusive-create attempt receipt records exactly one invocation; no gate retry occurred.

All 217 ordinary exclusions were verified: 13 train and 204 validation, no test cells, with all four named class-(c) cells included. The [per-policy counts](reproduction/README_G0_A3.md#verified-exclusion-set) publish no cell identifiers. The equivalent compositions are 168 typed limits + 2 class (a) + 4 class (c) + 43 class (d), or manifest labels 167 typed + 3 class (a) + 4 class (c) + 43 class (d); the supplemental A2 timeout is counted once. All excluded receipts are discarded before inspecting their measurement fields. Other missing cells remain INCOMPLETE. No original R2 receipt, forecast or exclusion record changed. The original A2 FAIL and opaque equality PASS remain recorded; test per-cell data were not opened.

The fresh owner re-armed the watchdog with two additive cron lines, retaining all seven previous lines. Process/start/boot binding and six watchdog tests passed. No old-owner input, historical-cell remeasurement, model call, graphics processor allocation or training update occurred. The validated Valkyrie judge remains unavailable for later formal specification coverage, but it is not used by G0.

Runtime: 118.686 seconds; process exit 0. Required freeze suite: `E13_REQUIRE_LEAN_INTEGRATION=1 make test`, 433 passed, 23 skipped, zero failed in 260.05 seconds. The [result-publication check](G0_A3/publication_test.json) also passed: 433 tests, 23 skips, zero failures in 233.01 seconds, with required Lean integration.

## Artifacts

- [Full result](G0_A3/result.json), SHA-256 `3eb06ce45a33c9fb877e86e95a46416afa9b13cfa6deeedf255f2e40dbdbb93e`.
- [Execution receipt](G0_A3/execution.json).
- [G0 A3 lock](locks/G0_A3.json), SHA-256 `78978a55c32f0416ac8332ee1f6c5380476e83c34ca8eca5a8c7082ba125d967`.
- Private completed arrays: `$WR/G0_A3/completions_private.json`, SHA-256 `e9a93389b3db5b380ada17423ef0bfb4d016657dcb840b9a2cd1221842385086`; never published.
- Attempt receipt `$WR/G0_A3/attempt.json`; execution log `$WR/state/G0_A3_run.log`.

## Complete outputs from the frozen evaluator

### 4B: full frozen evaluator outputs

```json
{
  "dense_minimum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 89,
    "dense_only_share": 0.6592592592592592,
    "dense_only_interval_95": [
      0.5625,
      0.7575757575757576
    ],
    "zero_success_earlier_tasks": 113,
    "later_positive_in_subset": 21,
    "auc": 0.7251552795031055,
    "auc_interval_95": [
      0.5799719982078853,
      0.8528711484593837
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "dense_maximum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 97,
    "dense_only_share": 0.7185185185185186,
    "dense_only_interval_95": [
      0.625,
      0.8106060606060606
    ],
    "zero_success_earlier_tasks": 113,
    "later_positive_in_subset": 14,
    "auc": 0.8838383838383839,
    "auc_interval_95": [
      0.7763231043453127,
      0.9736488526570048
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "auc_minimum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 90,
    "dense_only_share": 0.6666666666666666,
    "dense_only_interval_95": [
      0.5683453237410072,
      0.7651515151515151
    ],
    "zero_success_earlier_tasks": 112,
    "later_positive_in_subset": 20,
    "auc": 0.6706521739130434,
    "auc_interval_95": [
      0.5249925889328063,
      0.8111208394775647
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "auc_maximum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 94,
    "dense_only_share": 0.6962962962962963,
    "dense_only_interval_95": [
      0.6013513513513513,
      0.7894736842105263
    ],
    "zero_success_earlier_tasks": 112,
    "later_positive_in_subset": 17,
    "auc": 0.9046439628482972,
    "auc_interval_95": [
      0.8085203089803854,
      0.9796122022185851
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  }
}
```

### 1p7B: full frozen evaluator outputs

```json
{
  "dense_minimum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 103,
    "dense_only_share": 0.762962962962963,
    "dense_only_interval_95": [
      0.6857142857142857,
      0.835820895522388
    ],
    "zero_success_earlier_tasks": 124,
    "later_positive_in_subset": 18,
    "auc": 0.7541928721174004,
    "auc_interval_95": [
      0.6033624188311688,
      0.8917880752606153
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "dense_maximum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 111,
    "dense_only_share": 0.8222222222222222,
    "dense_only_interval_95": [
      0.7536231884057971,
      0.8863636363636364
    ],
    "zero_success_earlier_tasks": 124,
    "later_positive_in_subset": 11,
    "auc": 0.9300080450522928,
    "auc_interval_95": [
      0.8793092549806008,
      0.9730603448275862
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "auc_minimum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 106,
    "dense_only_share": 0.7851851851851852,
    "dense_only_interval_95": [
      0.7101449275362319,
      0.855072463768116
    ],
    "zero_success_earlier_tasks": 123,
    "later_positive_in_subset": 15,
    "auc": 0.671604938271605,
    "auc_interval_95": [
      0.504640540968048,
      0.8382637909253605
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "auc_maximum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 110,
    "dense_only_share": 0.8148148148148148,
    "dense_only_interval_95": [
      0.7445214313155151,
      0.880007042253521
    ],
    "zero_success_earlier_tasks": 123,
    "later_positive_in_subset": 12,
    "auc": 0.9376876876876877,
    "auc_interval_95": [
      0.8889898043586808,
      0.9773487115847872
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  }
}
```

### 8B: full frozen evaluator outputs

```json
{
  "dense_minimum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 90,
    "dense_only_share": 0.6666666666666666,
    "dense_only_interval_95": [
      0.5757575757575758,
      0.7559055118110236
    ],
    "zero_success_earlier_tasks": 106,
    "later_positive_in_subset": 16,
    "auc": 0.6361111111111111,
    "auc_interval_95": [
      0.44436029955621303,
      0.8090487954580327
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "dense_maximum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 100,
    "dense_only_share": 0.7407407407407407,
    "dense_only_interval_95": [
      0.654404854046882,
      0.8253968253968254
    ],
    "zero_success_earlier_tasks": 106,
    "later_positive_in_subset": 7,
    "auc": 0.8744588744588745,
    "auc_interval_95": [
      0.78125,
      0.9528209154529044
    ],
    "auc_valid_bootstrap_draws": 9991,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "auc_minimum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 94,
    "dense_only_share": 0.6962962962962963,
    "dense_only_interval_95": [
      0.6086956521739131,
      0.7819548872180451
    ],
    "zero_success_earlier_tasks": 106,
    "later_positive_in_subset": 13,
    "auc": 0.5574855252274608,
    "auc_interval_95": [
      0.3551005913729128,
      0.7536379492600422
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  },
  "auc_maximum": {
    "tasks": 135,
    "samples_per_task": 8,
    "groups": 100,
    "dense_only": 96,
    "dense_only_share": 0.7111111111111111,
    "dense_only_interval_95": [
      0.6231884057971014,
      0.796875
    ],
    "zero_success_earlier_tasks": 106,
    "later_positive_in_subset": 11,
    "auc": 0.9090909090909091,
    "auc_interval_95": [
      0.8353443489948574,
      0.9652191327567191
    ],
    "auc_valid_bootstrap_draws": 10000,
    "bootstrap_draws": 10000,
    "bootstrap_seed": 1302051,
    "uncertainty": "paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes",
    "p_value": null,
    "test": "prespecified point thresholds; no hypothesis-test p-value"
  }
}
```

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 G0 completed once with PASS; Phase 1 is admitted; its generation admission, anchors and fits remain pending.
**Snapshot:** G0 PASS; three strata reported; 135 validation tasks per stratum; 217 ordinary exclusions enforced; zero model calls or training updates.
