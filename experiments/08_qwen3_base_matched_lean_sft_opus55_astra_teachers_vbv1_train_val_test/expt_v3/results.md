# Cached data continuation preparation status

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results.md>

**Status:** PREPARING. **Last updated:** 10-13-2026 17:53 PDT.

| Phase | State | Evidence |
|---|---|---|
| Existing validation analysis | DONE | 4 sizes ×135 tasks ×8 known samples; [report](RESULTS_continuation_audit.md) |
| Cached train candidate inventory | DONE | 685 candidates /360 already-covered train tasks; [manifest](results/cached_train_candidates.csv) |
| Earlier external pool inventory | DONE | 587 pairs /455 tasks before conversion and joint screening |
| Source availability and hashes | DONE | 685/685 cached responses and 587/587 earlier Lean files verified; [receipt](results/host_data_verification.json) |
| Corpus conversion and admission | PENDING | No accepted expansion count yet |
| Prospective training protocol | DRAFT DESIGN | [Meeting plan](../../meetings/oct_13_2026/PLAN.md); not frozen |
| Deterministic verification | DONE | 323 tests passed, 24 skipped on Linux; [receipt](results/verification.json) |
| New training and evaluation | NOT LAUNCHED | Version 2 closed PARTIAL (17:49 PDT), with 0/5,328 new outputs; Vals route restoration required |

The audit is deterministic reuse of existing data, not a new model experiment. Tests and publication are recorded in [CKPT_continuation.md](CKPT_continuation.md). Raw training data remain on the execution host.

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test] The next matched training study has a data-reuse inventory and owner-specific plan; gains from more data or exposure are unmeasured.
