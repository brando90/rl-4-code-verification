# Official evaluator control reconciliation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/results/official_evaluator_controls.md>

**TLDR:** There are 14/16 official reports, but only 5/16 controls have interpretable endpoint values after checking execution logs. The other 11/16 remain null. Only 2/8 tasks have the required resolved gold and unresolved unchanged-base controls, below the frozen 6/8 engineering gate. No repair comparison ran.

This corrects the earlier report-only summary: import and test-fixture errors appear in execution logs even when the grader emits `resolved=false` and test-status maps. Raw grader flags are retained separately from endpoint values. Fixture failures remain conservatively null pending environment validation. This audit is post hoc; it is not a new prospective experiment or a change to grading, reference patches, tests, or task selection.

The [machine-readable audit](official_evaluator_controls.json) contains all 16 cells, evidence hashes and safe test-group counts. Raw patches, tests, test identifiers and logs remain in private evaluator storage. Harness: `f7bbbb2ccdf479001d6467c9e34af59e44a840f9`; panel: `552c8bde40bc102b2145607e79cdffaeff45ad50e30011cafaf311890a819e7d`; audit script: `192dfc12db5f1e30d925ce7168c6e813a505aef1e44d64772f0d1fc9e9822be5`.

The empty adapter leaves the base tree unchanged and alters only empty-patch selection and absent patch application in a separately hashed harness copy. Official test/grading bytes remain unchanged. Two marker-file variants are excluded and consume their existing retry allowances; original filtered empty wrappers remain unmeasured. Earlier wrapper invocations that failed before creating receipts also count against retries; attempt labels alone do not establish remaining allowance.

Recorded wrapper duration across retained receipts is 2275.874 seconds, including excluded attempts. Four processors/eight gibibytes per evaluation container and the 1,800-second test-execution timeout were observed. There was no enforced outer build timeout or 120-gibibyte new-storage ceiling. Elapsed time multiplied by four is an allocation estimate, not measured processor use; setup/build and pre-receipt failure accounting is incomplete. No claim of complete resource-gate enforcement is made.

These are fixed engineering controls, not sampled model-performance estimates; confidence intervals and hypothesis tests are not applicable. Missing and infrastructure-invalid cells stay in the declared denominators.

| Task | Gold endpoint | Exact empty endpoint | Valid control pair |
|---|---|---|---|
| `sqlfluff__sqlfluff-1763` | resolved | NULL — retry_exhausted | no |
| `pvlib__pvlib-python-1606` | NULL — import_failure_before_test_completion (raw resolved=false) | NULL — retry_exhausted | no |
| `sqlfluff__sqlfluff-2419` | resolved | unresolved | yes |
| `marshmallow-code__marshmallow-1343` | resolved | unresolved | yes |
| `pvlib__pvlib-python-1707` | NULL — import_failure_before_test_completion (raw resolved=false) | NULL — import_failure_before_test_completion (raw resolved=false) | no |
| `pvlib__pvlib-python-1154` | NULL — import_failure_before_test_completion (raw resolved=false) | NULL — import_failure_before_test_completion (raw resolved=false) | no |
| `pvlib__pvlib-python-1072` | NULL — import_failure_before_test_completion (raw resolved=false) | NULL — import_failure_before_test_completion (raw resolved=false) | no |
| `pydicom__pydicom-1139` | NULL — fixture_failure_requires_environment_validation (raw resolved=false) | NULL — fixture_failure_requires_environment_validation (raw resolved=false) | no |

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] The evaluator-control gate fails; raw unresolved flags caused by infrastructure are not evidence of model failure. A separately frozen environment/check protocol and new explicit call budget are required for continuation.
