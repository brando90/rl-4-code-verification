# Matched replay versus expansion continuation results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results.md>

**TLDR:** Phase A: DONE; Phase B: RECOVERING. 12,960/17,280 validation cells known. Expansion 14B died at step 183 of 335 on 10-17-2026 22:03 PDT (CUDA out of memory) and is waiting for its eight devices before restarting from the step-658 weights. [Execution events and verified training progress](results/runtime_progress.md).

**Status:** RECOVERING. **Last updated:** 10-18-2026 10:30 PDT.

Known validation cells: **12960/17,280**; 12960 belong to complete rungs. [Every missing/failed cell](results/coverage) remains in the declared denominator; no paid model calls.

| System | Known / declared | Extracted | Capped | Mixed /135 | Gates | Pass rate [95% interval] |
|---|---:|---:|---:|---:|---|---|
| v3_R_1p7b_f0p5 | 1,080/1,080 | 955 | 125 | 20 | FAIL | 0.0370 [0.0204, 0.0565] |
| v3_R_1p7b_f1p0 | 1,080/1,080 | 946 | 134 | 27 | FAIL | 0.0602 [0.0380, 0.0861] |
| v3_R_4b_f0p5 | 1,080/1,080 | 1006 | 74 | 31 | PASS | 0.0833 [0.0537, 0.1167] |
| v3_R_4b_f1p0 | 1,080/1,080 | 970 | 110 | 40 | FAIL | 0.1222 [0.0833, 0.1639] |
| v3_R_8b_f0p5 | 1,080/1,080 | 1019 | 63 | 35 | PASS | 0.1074 [0.0713, 0.1481] |
| v3_R_8b_f1p0 | 1,080/1,080 | 1002 | 78 | 38 | PASS | 0.1519 [0.1065, 0.2009] |
| v3_R_14b_f0p5 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_R_14b_f1p0 | 0/1,080 | — | — | — | INCOMPLETE | — |
| v3_E_1p7b_f0p5 | 1,080/1,080 | 936 | 144 | 18 | FAIL | 0.0491 [0.0250, 0.0769] |
| v3_E_1p7b_f1p0 | 1,080/1,080 | 959 | 121 | 19 | FAIL | 0.0509 [0.0278, 0.0769] |
| v3_E_4b_f0p5 | 1,080/1,080 | 953 | 127 | 35 | FAIL | 0.1157 [0.0769, 0.1583] |
| v3_E_4b_f1p0 | 1,080/1,080 | 981 | 98 | 36 | PASS | 0.1417 [0.0972, 0.1907] |
| v3_E_8b_f0p5 | 1,080/1,080 | 960 | 119 | 29 | FAIL | 0.1065 [0.0676, 0.1500] |
| v3_E_8b_f1p0 | 1,080/1,080 | 1011 | 70 | 39 | PASS | 0.1556 [0.1093, 0.2056] |
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
| 8b_f0p5 | -0.0009 [-0.0269, 0.0250] |
| 8b_f1p0 | 0.0037 [-0.0194, 0.0259] |

Execution update (10-16-2026 07:08 PDT): [14B initialization timed out before any update; cleanup verified](results/E14_initialization_failure_recovery02.json). [Baseline cache preparation](results/model_cache_read_recovery02.json) repairs the cold read without changing scientific caps or the native timeout. Full suite1,362tests pass; validation remains12,960/17,280.

Execution update (10-16-2026 07:20 PDT): [Repaired 14B expansion](results/E14_repaired_admission_recovery02.json) has 0 token-verified updates; the original zero-update failure is preserved. Finalization now verifies and publishes every deterministic error receipt. All 1,368 tests pass; known validation cells remain 12,960/17,280.

Execution update (10-16-2026 07:30 PDT): [Expansion 14B model initialized; 0 updates verified](results/E14_repaired_admission_recovery02.json), totaling 0 loss tokens. Every observed token count matches the frozen schedule.

Execution update (10-16-2026 07:47 PDT): [Expansion 14B model initialized; 1 updates verified](results/E14_repaired_admission_recovery02.json), totaling 12,881 loss tokens. Every observed token count matches the frozen schedule.

Execution constraint (10-16-2026 08:00 PDT): **12,960/17,280 primary cells remain checked;4,320are missing.** Expansion14B has2token-matched updates. Its measured transport rate projects about283h remaining training against61.4h before the fixed deadline. Healthy training is preserved, with native completion checks prepared for explicit handoff. [Measurements, limitations and finite continuation](results/E14_two_step_operational_projection_recovery02.json).

Execution check (10-18-2026 10:30 PDT): expansion 14B is not running. The driver log reached step 183 of 335 and died during step 184 at 10-17-2026 22:03 PDT with `torch.OutOfMemoryError` on skampere3 (a foreign process held 130.69 GiB on that 178 GiB GPU). No `step_335` checkpoint exists, so the half segment has to start again from the step-658 weights. The phase B state was `NEEDS_RECOVERY` / `train_E_14b: FAILED`, and the multinode sequencer was blocked on that native failure. Brando approved the resume and the wall-clock extension on 10-18-2026. The recovery deadline moves from 10-18-2026 21:21 PDT to 11-01-2026 21:21 PDT. Token budgets, the eight-device layout and the test split are unchanged. A waiter relaunches the frozen multinode admission only when skampere1 GPUs 1–2, skampere2 GPUs 3 and 5, and skampere3 GPUs 2, 4, 5 and 7 are free. At the last published rate of about 770 seconds per step, the restarted half segment is about 72 hours and the full segment about 71 hours more (operational projection, p-val=n/a).

Execution check (10-17-2026 13:07 PDT): the same expansion-14B process is still the live job (`segment_to_step_335.log`, process started 10-16-2026 07:11 PDT). It has completed **139/335** optimizer steps on the half-budget segment, and step 140 was in progress. Over those 139 completed steps the mean step time is 759.5 seconds (minimum 479.67, maximum 1,342.85); the last 10 average 769.8 seconds. At that last-10 rate the remaining 196 steps to the half checkpoint are about 41.9 hours, and the following 332 steps to the full checkpoint are about 71 hours. Recent steps report about 1.6–2.1 TFLOPS and 0.01% model floating-point utilization, so the step time is communication, not a stalled GPU. No second 14B job was started. Validation remains 12,960/17,280. Replay 14B has not started. This rate is an operational projection from the observed steps, p-val=n/a, and it does not change the frozen forecast.

**TLDR-end:** [rl4cv: matched replay versus expansion] 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3 validation coverage is 12960/17,280; expansion 14B died at step 183/335 and waits for eight free devices before restarting.
