# SWE-bench Lite feedback checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/CKPT_swebench_feedback.md>

**TLDR:** Attempt 2/2 completed the deterministic continuation: recovered the diagnostic rejection mechanism, reconciled all 24 authored Lean controls, and ran the eligible official evaluator controls. The repair admission remains failed and closed.

Created: 10-05-2026 23:34 PDT
Last updated: 10-06-2026 01:38 PDT

- Run: `rl4cv-e06-swebench-validation-v1-10-05-2026`; coordinator: `codex-vals` / `gpt-5.6-terra` / high; runtime: `/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery`.
- Recovery accounting: two exhausted default-Codex coordinators, two non-executing Claude coordinators, then the first Vals-Codex coordinator. The earlier coordinators made no solver or diagnostic-author call; the Vals coordinator made the eight bounded diagnostic-author calls recorded below.
- Landed runtime inputs: pinned harness `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`; legacy dataset revision `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`; 23 rows; exported-row SHA-256 `4598a9f0195fe2d8d3ef83e5a2aad322cfcb3efb0a4b7abb559128a52adfb6df`; public manifest SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`.
- Gate: version 1 harness requires `image`, `eval_script`, `eval_type`, and `log_parser`, all absent from the 23 legacy rows; direct `make_test_spec` failed with `KeyError: 'image'`. Private receipt: `runtime_vals_recovery/evaluator_inputs/harness_schema_compatibility.json`, SHA-256 `8bae69fab301cd16b744319abc1ee65e12bf39a512d13703d5cb53e94d1240e9`.
- Version 2 result: `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` passed all eight `make_test_spec` compatibility checks. Public source checkouts are exact shallow bases with zero remotes; contexts are frozen at SHA-256 `51bf5613dd91e4bcd60d6d4cf44431398a6ef3510fd0a6907999ac799b1467eb`.
- Eight tool-free diagnostic-author calls completed using native `claude-sonnet-5` / medium receipts. The frozen check ledger SHA-256 is `8e9511af9c0ef7c6b1d76f8d51cbdc6256e28d696ba974ec28d12b6e7f45e6ff`: 1 valid bundle, 7 invalid bundles. This is below the predeclared 6/8 admission threshold.
- Diagnostic audit: the native command-log validator was recovered and reproduced the frozen ledger exactly. JSON-fence transport, quote/semicolon allowlist rejection, and non-discriminating print-only assertions explain the structural failures. The admission prose lacked a frozen validator implementation hash, so prospective-validator status is unverified/late. No generated check was run and no author call was added.
- Independent controls: experiment04's immutable-row reconciliation is 24/24 measured and matching; its external applicability remains 0/24 versus the unchanged 20/24 engineering gate. The parent log-aware correction is 14/16 reports, 5/16 interpretable endpoints and 11/16 null (seven import aborts, two ambiguous fixture failures, two exhausted retries). Only 2/8 tasks have valid control pairs versus the frozen 6/8 criterion; raw `resolved=false` flags from execution failures are not issue outcomes. It records verified 4 CPU/8 GiB containers and 1800-second test timeout, while retaining the outer build-time/new-storage accounting limitation.
- Terminal decision: do not run solver or official final scoring. Report 0/56 solver cells and 0/24 final-condition cells measured; they are missing, not scored zero. The [version 3 proposal](expt_v3/README.md) specifies environment/validator repair and requests a new author-call/resource envelope. Training is not part of that proposal. Do not reuse these author outputs as tuned checks.

- Parent audit verified all 26 original input/control JSON files unchanged. Audit JSON SHA-256: `cf28d5fd89cc200edbb196b59fa62eab796e3e64a6d94cdf7e61bc17500ffbd3`. Worker attempt2 ended; no further automatic coordinator launch remains. Parent verification supersedes its report-only completion summary without altering that receipt.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Deterministic controls are reconciled, but the failed public-diagnostic gate preserves a non-admitted, unmeasured repair comparison.
