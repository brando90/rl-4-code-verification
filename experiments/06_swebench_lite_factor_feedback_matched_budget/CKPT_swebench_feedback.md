# SWE-bench Lite feedback checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/CKPT_swebench_feedback.md>

**TLDR:** The Vals Codex recovery exported and validated the 23-row legacy development split and froze the version 1 eight-task public manifest. The version 1 evaluator pin is schema-incompatible, so version 2 prospectively tests one compatible historical harness before any model call.

Created: 10-05-2026 23:34 PDT
Last updated: 10-05-2026 23:51 PDT

- Run: `rl4cv-e06-swebench-validation-v1-10-05-2026`; coordinator: `codex-vals` / `gpt-5.6-terra` / high; runtime: `/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery`.
- Recovery accounting: two exhausted default-Codex coordinators, two non-executing Claude coordinators, then the first Vals-Codex coordinator. The earlier coordinators made no solver or diagnostic-author call; the Vals coordinator made the eight bounded diagnostic-author calls recorded below.
- Landed runtime inputs: pinned harness `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`; legacy dataset revision `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`; 23 rows; exported-row SHA-256 `4598a9f0195fe2d8d3ef83e5a2aad322cfcb3efb0a4b7abb559128a52adfb6df`; public manifest SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`.
- Gate: version 1 harness requires `image`, `eval_script`, `eval_type`, and `log_parser`, all absent from the 23 legacy rows; direct `make_test_spec` failed with `KeyError: 'image'`. Private receipt: `runtime_vals_recovery/evaluator_inputs/harness_schema_compatibility.json`, SHA-256 `8bae69fab301cd16b744319abc1ee65e12bf39a512d13703d5cb53e94d1240e9`.
- Version 2 result: `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` passed all eight `make_test_spec` compatibility checks. Public source checkouts are exact shallow bases with zero remotes; contexts are frozen at SHA-256 `51bf5613dd91e4bcd60d6d4cf44431398a6ef3510fd0a6907999ac799b1467eb`.
- Eight tool-free diagnostic-author calls completed using native `claude-sonnet-5` / medium receipts. The frozen check ledger SHA-256 is `8e9511af9c0ef7c6b1d76f8d51cbdc6256e28d696ba974ec28d12b6e7f45e6ff`: 1 valid bundle, 7 invalid bundles. This is below the predeclared 6/8 admission threshold.
- Terminal decision: do not run solver, gold, empty, or official final evaluation cells. Report 0/56 solver cells and 0/24 final-condition cells measured; they are missing, not scored zero. A future repair needs a separately frozen version and a new authorized call budget; do not reuse these author outputs as tuned checks.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Resume with the one version-2 compatibility test, then either freeze admission or retain a fully accounted-for evaluator blocker.
