# SWE bench Lite feedback experiment progress

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/results.md>

**Status:** NEEDS ATTENTION: VERSION 2 PUBLIC-DIAGNOSTIC ADMISSION GATE FAILED; INDEPENDENT CONTROLS RECONCILED
**Last updated:** 10-06-2026 01:11 PDT

| Stage | State | Evidence |
|---|---|---|
| Benchmark/source selection | DONE | Official source note and exact candidate pins |
| Preparation and paired analysis | DONE | Deterministic tools implemented; test receipt pending integration |
| Cluster runtime | VERIFIED PREFLIGHT | Docker 28.1.1, local scratch available; shared storage threshold failure isolated from large writes |
| Eight selected task IDs | DONE | 23-row legacy `dev` export; public manifest SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`; 56 declared solver cells |
| Version 1 evaluator compatibility | FAILED PRE-ADMISSION | Pinned harness needs `image`, `eval_script`, `eval_type`, and `log_parser`; all are absent from the legacy rows; `make_test_spec` raised `KeyError: 'image'` |
| Version 2 evaluator compatibility | DONE | Historical harness `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` created a test specification for all 8 selected rows in the clean evaluator environment |
| Public diagnostic-author feasibility | FAILED ADMISSION GATE | 8/8 bounded author calls; 1/8 structural bundles vs prospective 6/8 threshold. The recovered validator chronology is unverified, so this is not a prospective-validator success claim. |
| Official endpoint controls | RECONCILED WITH LIMITS | 8/8 report-backed gold controls; 6/8 exact-empty-base adapter controls; 2/8 empty cells null after preserved filtered/marker attempts exhausted retry allowance. See `expt_v2/results/official_evaluator_controls.md`. |
| 56-cell repair comparison | NOT ADMITTED | 0/56 solver cells measured; all remain explicit missing cells, not failures or zero scores |
| Official final-condition scoring | NOT ADMITTED | 0/24 final condition cells measured; all remain explicit missing cells, not unresolved issues |
| Later test panel and training | NOT STARTED | Separate prospective protocols required |

Both bounded default-Codex coordinator attempts ended at the cluster account usage limit before dataset export or measured calls. Two Claude replacement attempts did not execute the requested preparation. The active Vals Codex profile is separately authenticated through ChatGPT; it exported the pinned data and froze the panel without a solver call. No credits were purchased.

The diagnostic rejection audit is published in `expt_v2/results/diagnostic_rejection_audit.md`: the frozen ledger remains SHA-256 `8e9511af9c0ef7c6b1d76f8d51cbdc6256e28d696ba974ec28d12b6e7f45e6ff`, with 1/8 structural acceptance. It distinguishes fence/transport and character-allowlist defects from behavioral quality; generated checks were not executed. The exact parser was recovered after author calls and had no frozen implementation hash in the admission record, so the claimed prospective-validator status is corrected to unverified/late.

The independent official controls establish that the evaluator can produce report-backed gold/empty differences on the compatible harness, subject to their documented two null baselines and outer resource-accounting limitations. They neither reopen the failed diagnostic gate nor measure a repair intervention. No resolution-rate improvement, cost advantage, training result, or official SWE-bench resolution rate has been measured. Solver cells remain 0/56 and final-condition scoring remains 0/24, all missing rather than zero. Current private receipts remain under `/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery`.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Independent controls and the diagnostic audit are published, but the 1/8 public-diagnostic gate remains failed and no repair comparison is admitted.
