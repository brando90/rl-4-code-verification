# SWE bench Lite feedback experiment progress

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/results.md>

**Status:** STOPPED PRE-SOLVER: VERSION 2 PUBLIC-DIAGNOSTIC ADMISSION GATE FAILED
**Last updated:** 10-05-2026 23:51 PDT

| Stage | State | Evidence |
|---|---|---|
| Benchmark/source selection | DONE | Official source note and exact candidate pins |
| Preparation and paired analysis | DONE | Deterministic tools implemented; test receipt pending integration |
| Cluster runtime | VERIFIED PREFLIGHT | Docker 28.1.1, local scratch available; shared storage threshold failure isolated from large writes |
| Eight selected task IDs | DONE | 23-row legacy `dev` export; public manifest SHA-256 `68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46`; 56 declared solver cells |
| Version 1 evaluator compatibility | FAILED PRE-ADMISSION | Pinned harness needs `image`, `eval_script`, `eval_type`, and `log_parser`; all are absent from the legacy rows; `make_test_spec` raised `KeyError: 'image'` |
| Version 2 evaluator compatibility | DONE | Historical harness `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` created a test specification for all 8 selected rows in the clean evaluator environment |
| Public diagnostic-author feasibility | FAILED ADMISSION GATE | 8/8 bounded tool-free author calls completed; only 1/8 generated bundles met the frozen safe-command validation, below the prospective 6/8 threshold |
| Official endpoint controls | NOT RUN | No solver comparison could be admitted after the public-diagnostic gate failed; 8 gold and 8 empty controls are unmeasured, not zero |
| 56-cell repair comparison | NOT ADMITTED | 0/56 solver cells measured; all remain explicit missing cells, not failures or zero scores |
| Official final-condition scoring | NOT ADMITTED | 0/24 final condition cells measured; all remain explicit missing cells, not unresolved issues |
| Later test panel and training | NOT STARTED | Separate prospective protocols required |

Both bounded default-Codex coordinator attempts ended at the cluster account usage limit before dataset export or measured calls. Two Claude replacement attempts did not execute the requested preparation. The active Vals Codex profile is separately authenticated through ChatGPT; it exported the pinned data and froze the panel without a solver call. No credits were purchased.

The new diagnostic geometric mean is a proxy. No resolution-rate improvement, cost advantage, training result, or official SWE-bench resolution rate has been measured. The prospective gate failed before solver admission: only one valid diagnostic bundle is insufficient to evaluate the declared three-condition matrix. Current runtime receipts live at `/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery`; historical recovery logs remain preserved. The experiment has no dependency on completion of Qwen's evaluation.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] The repository-repair extension is prepared for bounded remote execution; measured diagnostics and repair outcomes are pending.
