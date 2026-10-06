# Diagnostic rejection audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/results/diagnostic_rejection_audit.md>

**TLDR:** The frozen diagnostic ledger reproduces exactly as 1 structurally accepted bundle out of 8 author calls, below the prospective 6/8 admission criterion. This is a transport/schema/allowlist failure audit, not evidence that the authored checks ran, detected the issues, or established diagnostic quality.

## Immutable inputs and reproduction

The sealed private ledger is `/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery/public_solver/diagnostic_checks.json`, SHA-256 `8e9511af9c0ef7c6b1d76f8d51cbdc6256e28d696ba974ec28d12b6e7f45e6ff`. Re-running the recovered validator against the eight original receipt bytes created `diagnostic_checks_reproduced.json` with the identical hash. The exact recovered implementation is [diagnostic_validator_native.py](../scripts/diagnostic_validator_native.py); its non-executing synthetic parser tests are [test_diagnostic_validator_native.py](../scripts/test_diagnostic_validator_native.py) (3 passed with third-party test-plugin autoload disabled).

| Task | Receipt SHA-256 prefix | Request SHA-256 prefix | Native model / effort | List-basis cost | Structural result |
|---|---|---|---|---:|---|
| marshmallow-code__marshmallow-1343 | `e7a347f6e6fc` | `14e079e991de` | claude-sonnet-5 / medium | $0.1081984 | rejected: extra JSON material |
| pvlib__pvlib-python-1072 | `6e15317b038f` | `4c3934bd5af5` | claude-sonnet-5 / medium | $0.0798424 | rejected: allowlist filter |
| pvlib__pvlib-python-1154 | `5e64bccb83ca` | `2e994cc2564d` | claude-sonnet-5 / medium | $0.1543084 | rejected: extra JSON material |
| pvlib__pvlib-python-1606 | `0384ea1f4891` | `d3c8c29ef358` | claude-sonnet-5 / medium | $0.1052244 | rejected: allowlist filter |
| pvlib__pvlib-python-1707 | `488b1b019b09` | `e93ece940391` | claude-sonnet-5 / medium | $0.0889584 | rejected: allowlist filter |
| pydicom__pydicom-1139 | `5683438dfc56` | `ae6c7b459d00` | claude-sonnet-5 / medium | $0.0850964 | rejected: allowlist filter |
| sqlfluff__sqlfluff-1763 | `66ed9d3a3d1b` | `025a8c026c1f` | claude-sonnet-5 / medium | $0.0339114 | accepted structurally |
| sqlfluff__sqlfluff-2419 | `a8772c72d232` | `85f97fcb2de2` | claude-sonnet-5 / medium | $0.0569144 | rejected: allowlist filter |

Total recorded list-basis cost is $0.7124542. All eight client invocations returned normally; the seven rejections happened after response capture.

## What failed

The recovered validator permits only `python`, `python3`, `pytest`, and `py.test`; it rejects any command containing a semicolon, shell metacharacter, quote, backtick, dollar sign, or newline before tokenization. Two native outputs have otherwise parseable fenced JSON followed by additional material, so `json.loads` reports `Extra data`. Several generated `python -c` commands contain semicolons inside quoted code and are therefore rejected before shell parsing. These are schema/transport and character-allowlist defects, distinct from whether a command would be a useful behavioral assertion.

The accepted SQLFluff bundle is only command-shape accepted. Its issue commands are broad test invocations and some generated issue commands in rejected bundles merely print values; an exit status alone cannot distinguish correct from incorrect behavior in those cases. No generated command was run in this audit. Thus command acceptance neither proves execution nor issue detection.

The author prompt inherited the shared completion reminder that asks for a complete unified diff. That conflicting instruction is a plausible contributor to extra prose, but this audit does not infer an unmeasured counterfactual.

## Chronology correction and prospective plan

The admission record froze prose requirements and the 6/8 threshold before the author calls, but it contains no hash of this validator implementation. The exact implementation was recovered only from the first coordinator command log after those calls. Therefore the criterion was prospective, while the claimed prospective *validator implementation* status is unverified and must not be claimed.

A separately authorized next version would freeze a validator source hash and fixtures before calls; require a JSON-only transport schema without fences; parse command structure rather than banning safe syntax by raw characters; and require each issue check to encode a failing/passing exit-status oracle. It would need a new explicit author-call budget. No selected output was repaired, replaced, or used to relax the 6/8 gate.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] The diagnostic gate remains failed at 1/8, and the recovered audit identifies a late-unhashed validator plus transport/allowlist defects without claiming behavioral diagnostic validity.
