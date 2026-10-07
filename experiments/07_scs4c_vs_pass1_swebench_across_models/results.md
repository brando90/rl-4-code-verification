# Experiment 07 results — SCS4C versus pass@1 on SWE-bench across models

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/results.md>

**TLDR:** Phase A (SCS4C-T, the tests-only smooth conjunctive score for code, versus pass@1 across every public SWE-bench Verified submission, zero model calls) is locked for SNAP execution. The master reported dispatch, but no launch receipt is recorded here; every hypothesis remains unmeasured in this record.

**Status:** DISPATCH REPORTED; EXECUTION UNVERIFIED (10-07-2026)

**Last updated:** 10-07-2026 (local light review; no new experimental outcomes read)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| A — definition, protocol, frozen forecast | DONE (10-07-2026) | [PROTOCOL.md](PROTOCOL.md), `expt_v1/forecasts/` |
| A — fetch public reports (about 180 systems × 500 tasks) | NOT STARTED | — |
| A — analysis (H1, H1b, H2, H3) | NOT STARTED | — |
| B — full SCS4C on SWE-Bench Pro Verified | DESIGNED, not admitted | [README.md](README.md#phases) |
| C — SCS4C as an RL reward | DESIGNED, not admitted | [README.md](README.md#phases) |

## Results

Unmeasured. The worker fills this section from `expt_v1/results/analysis_e07.json`: inclusion and cohort counts, H1 to H3 with all three correlations and their intervals, the frozen predictions beside the outcomes, validity checks and the per-system table.

## Deviations and open questions

- **10-07-2026, implementation corrections before local outcome analysis:** report parsing now distinguishes absent test evidence from explicit empty lists; nonfinite statistics remain undefined; the analyzer enforces the locked consistency/coverage checks, preserves known aggregate resolutions in the declared-denominator diagnostic, reports both cohorts and all cell receipts, and reports bootstrap/split denominators. Fetching validates pinned input provenance and protects against partial prediction downloads. Record the actual reviewed code commit used by the worker, since it differs from the protocol's original code pin.
- Frozen predictions, thresholds and `expt_v1/forecasts/` are unchanged. Protocol edits only clarify the already disclosed pre-lock exposure, the declared-denominator diagnostic, and the worker's sensitivity responsibility.
- The GitHub adapter, base-model sensitivity and human-readable hypothesis verdicts remain explicit worker deliverables; no real phase A result was computed during this review.
- The claimed dispatch lacks a committed launch receipt. Verify the named worker/session on the host and record the exact revision, process and first completed action before reporting RUNNING.
- The common cohort can be empty even when every system passes the frozen 95% inclusion rule; split sizes can also exceed it. These states are reported unavailable without altering the locked inclusion or hypothesis thresholds.


## Local light-review receipt — 10-07-2026

- **Scope:** original base `7b3ad352088753b3cce27063d662b37b0c2ecabc` through `94c95efdfaaca2956fb4d406cfe1c689132022a6` and owned working-tree corrections; no commit or push. Other sessions' paths were not edited.
- **Reviewer:** Codex, launched as `gpt-6-astra` with `model_reasoning_effort=ultra` and `--dangerously-bypass-approvals-and-sandbox` (verified process flags); one review round, with bounded read-only source lookups. Builder recorded as Claude Code / Opus 5.5 in the protocol; builder effort unverified. Classification: scoring/scientific integrity and funding rules; no benchmark reference edits.
- **Verification:** `make test` passed after every code edit; final suite 71 passed, 2 skipped. The skips require an available VeriBench experiment-103 checkout. Synthetic regressions cover parser gaps, constant/nonfinite correlations, all-undefined splits, zero/underpowered/empty-common cohorts, inconsistent reports, manifest membership, input pins, interrupted downloads and complete cell receipts. No real phase A outcomes were read for this review.
- **Integrity:** `git diff --check` passed; no broken local Markdown paths found; all three frozen forecast files match `94c95ef` byte for byte and `verify_forecast` returned true. Protocol prediction and threshold rows are unchanged.
- **Structural finding (minor):** `analyze_e07.py:main` remains 77 lines with input validation, orchestration and status assembly. Output writing and shared report parsing are separated; a broader refactor was deferred to keep this correction focused. No dead code or material duplication requiring removal was identified.
- **Verdict:** FIXED. Required log adapters, model sensitivity, dispatch receipt and real-data reporting remain explicitly assigned to the worker; this receipt does not claim completion of the experiment.
