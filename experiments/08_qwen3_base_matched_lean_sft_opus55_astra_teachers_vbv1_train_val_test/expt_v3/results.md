# Matched replay versus expansion continuation results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results.md>

**TLDR:** Phase A: DONE; Phase B: RUNNING. 8,640/17,280 validation cells known. [Execution events and verified training progress](results/runtime_progress.md).

**Status:** RUNNING. **Last updated:** 10-16-2026 03:50 PDT.

Expansion 8B training and both exports are fully verified; its half checkpoint has 1,080 exact generated cells and CPU scoring is active. Full-checkpoint generation and matched replay controllers are running; 14B awaits eight eligible devices. Generated coverage: 9,720/17,280. [Checked execution evidence](results/recovery02_E8_completion.json).

Known validation cells: **8640/17,280**; 8640 belong to complete rungs. [Every missing/failed cell](results/coverage) remains in the declared denominator; no paid model calls.

| System | Known / declared | Extracted | Capped | Mixed /135 | Gates | Pass rate [95% interval] |
|---|---:|---:|---:|---:|---|---|
| v3_R_1p7b_f0p5 | 1,080/1,080 | 955 | 125 | 20 | FAIL | 0.0370 [0.0204, 0.0565] |
| v3_R_1p7b_f1p0 | 1,080/1,080 | 946 | 134 | 27 | FAIL | 0.0602 [0.0380, 0.0861] |
| v3_R_4b_f0p5 | 1,080/1,080 | 1006 | 74 | 31 | PASS | 0.0833 [0.0537, 0.1167] |
| v3_R_4b_f1p0 | 1,080/1,080 | 970 | 110 | 40 | FAIL | 0.1222 [0.0833, 0.1639] |
| v3_R_8b_f0p5 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_R_8b_f1p0 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_R_14b_f0p5 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_R_14b_f1p0 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_E_1p7b_f0p5 | 1,080/1,080 | 936 | 144 | 18 | FAIL | 0.0491 [0.0250, 0.0769] |
| v3_E_1p7b_f1p0 | 1,080/1,080 | 959 | 121 | 19 | FAIL | 0.0509 [0.0278, 0.0769] |
| v3_E_4b_f0p5 | 1,080/1,080 | 953 | 127 | 35 | FAIL | 0.1157 [0.0769, 0.1583] |
| v3_E_4b_f1p0 | 1,080/1,080 | 981 | 98 | 36 | PASS | 0.1417 [0.0972, 0.1907] |
| v3_E_8b_f0p5 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_E_8b_f1p0 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_E_14b_f0p5 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_E_14b_f1p0 | 0/1,080 | — | — | — | INCOMPLETE | — |

Gates are protocol-defined: ≥972 extracted, ≤108 capped, ≥7 mixed tasks, with every input known. Intervals resample 135 tasks with all eight attempts, 10,000 draws, seed 0; p-val=n/a. Training-seed variation is unmeasured. Mixed-share Wilson intervals, failure taxonomy, diversity and paired comparisons are in [the full summary](results/validation_summary_v3.json) and [per-cell/per-task tables](results/ladder).

Primary four-size decision: `{"f0p5": {"status": "INCOMPLETE", "selected": null}, "f1p0": {"status": "INCOMPLETE", "selected": null}}`.

Three-size sensitivity (4B/8B/14B): `{"f0p5": {"status": "INCOMPLETE", "selected": null}, "f1p0": {"status": "INCOMPLETE", "selected": null}}`.

Hosted Smooth Conjunctive Score for Code verification judging remains deferred at $0 spend. Namespace escaping is a separate diagnostic and never changes primary scores; [diagnostic tables](results/namespace_diagnostic). The test split remains unopened.

Frozen forecast assessment: [prediction and measured outcome](results/forecast_assessment_v3.json). Incomplete outcomes have no hit/miss verdict. The report retains the original earliest-selected-winner interpretation alongside earliest common checkpoint within each condition; both are disclosed if they disagree.

Execution and recovery events: [runtime ledger](results/runtime_progress.md).


| Size and fraction | Expansion minus replay success rate [95% interval] |
|---|---:|
| 1p7b_f0p5 | 0.0120 [-0.0037, 0.0296] |
| 1p7b_f1p0 | -0.0093 [-0.0259, 0.0074] |
| 4b_f0p5 | 0.0324 [0.0111, 0.0546] |
| 4b_f1p0 | 0.0194 [-0.0019, 0.0426] |

**TLDR-end:** [rl4cv: matched replay versus expansion] 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3 validation coverage is 8640/17,280; incomplete comparisons remain unresolved.
