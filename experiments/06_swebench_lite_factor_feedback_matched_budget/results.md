# SWE bench Lite feedback experiment progress

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/results.md>

**TLDR:** Version 3 is blocked before official admission after exhausting its three coordinator launches: 0/16 official controls, 0/8 diagnostic-author calls and 0/56 solver cells completed. Historical version-2 validation remains 1/8 usable diagnostic structures and 2/8 valid control pairs, below both 6/8 gates. No repair effect is measured.

**Status:** VERSION 3 BLOCKED BEFORE ADMISSION; COORDINATOR ATTEMPT BUDGET EXHAUSTED
**Last updated:** 10-08-2026; execution and cleanup verified through 20:05 PDT

## Current version 3

The [published blocked receipt](expt_v3/results/supervision_blocked_10-08-2026.json), commit `c53c0e2`, supersedes the earlier implementation-in-progress status. The `skampere2` coordinator exited at 19:34 PDT with `error_max_turns` after reaching its configured 90-turn limit. All three launches are spent; no fourth coordinator was started. The original deadline remains 10-09-2026 10:50 PDT, and neither time nor resource budgets were reset.

Five real smoke executions ran outside official admission. Four had no effective processor or memory bounds; the fifth verified four processors/eight gibibytes but failed its storage observation. All retain private evidence and remain excluded from the official-control denominator. Official progress is **0/16 controls, 0/8 author calls and 0/56 solver cells**; the 6/8-pair validity gate was not measured. No Vals-funded Valkyrie response route was admitted.

Fresh checks on the preserved remote revision found 113 repository tests passed and 11 skipped, while the version-3 suite had 146 passed and two failed under Python 3.12. The clean backend environment also lacks dependencies. Complete version-budget accounting, bounded image pulls, owned-storage coverage, source/environment verification and the executable freeze remain unresolved. The earlier [review reconciliation](expt_v3/results/implementation_review.json) covers its recorded implementation snapshot, not the subsequent unfinished backend. Twenty-three pending files were archived privately. With no surviving scientific job, the experiment06 observer and its single tagged cron entry were removed at 20:05 PDT; other experiments were untouched. See [version-3 results](expt_v3/results.md) and the [checkpoint](expt_v3/CKPT_e06_v3.md) for evidence and preservation paths. All version-2 evidence below remains historical and unchanged.

## Historical version 1 and 2 closeout (10-06-2026)

| Stage | State | Evidence |
|---|---|---|
| Benchmark/source selection | DONE | Official source note and exact candidate pins |
| Preparation and paired analysis | DONE | Deterministic tools implemented; parent integration tests passed (35 passed, none skipped) |
| Cluster runtime | VERIFIED PREFLIGHT | Docker 28.1.1, local scratch available; shared storage threshold failure isolated from large writes |
| Eight selected task IDs | DONE | 23-row legacy `dev` export; public manifest SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`; 56 declared solver cells |
| Version 1 evaluator compatibility | FAILED PRE-ADMISSION | Pinned harness needs `image`, `eval_script`, `eval_type`, and `log_parser`; all are absent from the legacy rows; `make_test_spec` raised `KeyError: 'image'` |
| Version 2 evaluator compatibility | DONE | Historical harness `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` created a test specification for all 8 selected rows in the clean evaluator environment |
| Public diagnostic-author feasibility | FAILED ADMISSION GATE | 8/8 bounded author calls; 1/8 structural bundles vs prospective 6/8 threshold. The recovered validator chronology is unverified, so this is not a prospective-validator success claim. |
| Official endpoint controls | FAILED CONTROL GATE | 14/16 reports, but 5/16 interpretable endpoints and 11/16 null; 2/8 valid gold/unchanged-base pairs versus 6/8 required. Seven cells aborted on imports, two have fixture errors pending environment validation, and two exhausted retries. See [audited controls](expt_v2/results/official_evaluator_controls.md). |
| 56-cell repair comparison | NOT ADMITTED | 0/56 solver cells measured; all remain explicit missing cells, not failures or zero scores |
| Official final-condition scoring | NOT ADMITTED | 0/24 final condition cells measured; all remain explicit missing cells, not unresolved issues |
| Later test panel and training | NOT STARTED | Separate prospective protocols required |

Both bounded default-Codex coordinator attempts ended at the cluster account usage limit before dataset export or measured calls. Two Claude replacement attempts did not execute the requested preparation. The now-finished Vals Codex profile is separately authenticated through ChatGPT; it exported the pinned data and froze the panel without a solver call. No credits were purchased.

The diagnostic rejection audit is published in `expt_v2/results/diagnostic_rejection_audit.md`: the frozen ledger remains SHA-256 `8e9511af9c0ef7c6b1d76f8d51cbdc6256e28d696ba974ec28d12b6e7f45e6ff`, with 1/8 structural acceptance. It distinguishes fence/transport and character-allowlist defects from behavioral quality; generated checks were not executed. The exact parser was recovered after author calls and had no frozen implementation hash in the admission record, so the claimed prospective-validator status is corrected to unverified/late.

The parent checked execution logs as well as grader reports. Import failures and ambiguous fixture failures are null even when the official grader emits `resolved=false`. Raw flags and evidence hashes remain in the [16-cell audit](expt_v2/results/official_evaluator_controls.json); original input/control JSON files (26) were unchanged by the audit. The prior report-only summary at commit `3056662` overstated interpretable outcomes. This correction is post hoc and preserves every selected task and the original grader.

Container limits of four processors/eight gibibytes and a 1,800-second test timeout were observed. Outer build-time and new-storage ceilings were not enforced; recorded wrapper duration of 2,275.874 seconds is not complete processor accounting. These are fixed engineering checks, so confidence intervals and hypothesis tests are not applicable.

No resolution-rate improvement, cost advantage or training result has been measured. All 56 solver cells and 24 final-condition cells remain missing. Both reserved Vals coordinator attempts have ended; no replacement or additional model call is admitted. The worker's cluster `make test` invocation failed because `python` was absent from its command path; the parent subsequently passed the repository suite locally with the available VeriBench checkout (35 passed, none skipped). Raw evaluator material remains in private remote storage.

The [version 3 proposal](expt_v3/README.md) was authorized on 10-08-2026, but its existing coordinator allocation is now exhausted before admission. Preserve its declared eight diagnostic-author and conditional 56 solver cells as unmeasured; this proposal is not a new execution allowance. The proposed 24-task test panel and training remain separate and unapproved.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Version 3 is blocked before admission, with all official controls and response cells unmeasured; the historical version-2 failed gates remain unchanged.
