# Experiment 13 v2-S2 anchor generation and scoring

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_ANCHORS_S2.md>

**TLDR:** The base anchor generation is complete: 4,312/4,312 responses on 539 train tasks, eight samples each. No cells are missing or retried. Base scoring is closed with 4,311 measured responses, zero strict successes and one unresolved parser error; half-schedule scoring is now closed with 4,303 measured and nine unavailable, and full-schedule batch 1 generation is complete with all 4,312 responses.

S1's measured generation-admission failure remains final (99th-percentile probability error 0.124769325 > 0.10). These anchors use the separately admitted S2 float16 condition; its one original-probe confirmation passed without changing the thresholds ([admission report](RESULTS_LP1_A5.md)).

Recorded: 10-15-2026 01:47 PDT. Condition: **v2-S2**, float16. Generation freeze `d4948f3e57af06fdff660f271a9602e0df3a092c` precedes every response; its bound files still match.

| Base generation accounting | Observed value |
|---|---:|
| Completed / declared responses | 4,312 / 4,312 |
| Missing; second-attempt cells | 0; 0 |
| Generated tokens | 9,324,934 |
| Prompt tokens | 15,515,768 |
| Minimum / maximum output tokens | 2 / 8,192 |
| Responses reaching the fixed token cap | 276 / 4,312 |
| Allocated device-hours, including all segment leases | 6.9587135382493335 |
| Released leases | 17 / 17 |
| Anchor scores; experiment optimizer updates | 0; 0 |

All segment cleanup receipts verify. The [immutable generation receipt](anchors_S2/base_generation.json) binds the frozen manifest, generation lock, private response inventory and closed terminal ledger by SHA-256. Raw responses and task identities remain private. This is complete generation accounting, not a scientific performance verdict; confidence intervals and p-values are not applicable to this fixed-manifest census. Token-cap completion does not establish strict correctness.

At this observation, half-schedule generation retains 3,328/4,312 responses and full-schedule batch 1 retains 2,368/4,312. Independent batch 2 remains unarmed until calibration, item parameters and forecast F2 are frozen and published. The preliminary PLAN runtime estimate is not a measurement: the actual base generation cost above will enter the later T4 resource projection.

Next, publish the base scoring-input lock before invoking the unchanged scorer. No score or actual-data fit has been computed. Required verification before this publication: **857 passed, 3 skipped, zero failures in 458.48 seconds**, direct exit 0, with Lean integration required ([receipt](phase2/evaluation_scoring_monitor_publication_test.json)).

Base scoring freeze (10-15-2026 01:56 PDT): [lock](locks/ANCHOR_SCORE_S2_base.json) binds all 4,312 base responses and 43 implementation/provenance dependencies, all bytes verified; SHA-256 `9c4107dada7005106169696b21c763ef074ab028219d0ca32beb201504e644a2`. The [generation report](anchors_S2/base_generation.json) is published at `608f20ca54e5b5675122b890f2a291daece5d195`. Required suite: **857 passed, 3 skipped, zero failures in 448.12 seconds**, direct exit 0 ([receipt](anchors_S2/base_scoring_lock_test.json)). The live cleanup preflight verified with zero signals. No base score has run; launch follows this publication under the existing watchdog, retaining processor timing. Half/full generation continues.

Base scoring launch (10-15-2026 01:59 PDT): published lock `b2556da71fc0750b373ce5091da44f5451082573` precedes the unchanged scorer. Process 623680 (birth tick 29324576), timed by process 623675, is registered as `score-base` under the existing watchdog. At this observation 285/4,312 durable cell results exist; cleanup verifies on 285/285. The full-panel verdict and processor cost remain pending ([launch receipt](anchors_S2/base_scoring_launch.json)). Half generation retains 3,424/4,312 and full batch 1 2,496/4,312. No actual fit, Phase 2 measurement or experiment optimizer update has run.

## Base scoring closed — 10-15-2026 02:35 PDT

The unchanged scorer accounts for **4,312/4,312** declared responses: **4,311 measured, one unresolved, zero measured strict successes**. Its terminal status is **INCOMPLETE**, with zero integrity defects, unresolved cleanup or retries. This is an accounted train calibration panel, not a failed admission gate. The single unresolved result is a deterministic parser `RuntimeError: invalid command span`; the frozen retry policy does not admit a retry for that error. Its task identity remains private and its outcome stays missing in the full calibration denominator and risk pattern.

The full-denominator strict-success mean has sharp completion bounds **[0, 0.00023191094619666049]**, or **[0%, 0.0231911%]**. The already-frozen grouped bootstrap uses 10,000 draws with seed 1302031 over 400 whole train task groups, retaining all eight responses per task. Across missing-value completions its 95% lower endpoint is [0, 0] and its upper endpoint is [0, 0.0007062146892655367]; the outer descriptive envelope is therefore **[0%, 0.0706215%]**. This bootstrap is conditional on this fixed model and its observed responses. With no observed successes its all-zero completion is degenerate; it is not a distribution-free population upper confidence bound. No held-out performance, model-fit uncertainty, repeated-training uncertainty or hypothesis-test claim is made (p-value not applicable).

The [terminal scoring receipt](anchors_S2/base_scoring.json) and [descriptive diagnostic](anchors_S2/base_strict_diagnostic.json) bind the private full ledger and frozen grouping/method. The [cost receipt](anchors_S2/base_scoring_cost.json) retains **14.387216666666665 processor-hours**, **1,545.45 elapsed seconds**, zero device-hours, 147,471,990 logical bytes and 382,500,864 allocated bytes in 80,353 owned scoring files. GNU time includes the process and waited-for descendants and records exit 0; its maximum resident set is 7,255,692 KiB, not a sum of simultaneous worker memory. Generation cost is reported separately above. Cleanup is verified for every accounted cell.

Half-schedule and full-schedule batch 1 continue generating. All three scored panels must be published before the one calibration execution, item freeze and F2 forecast; independent batch 2 remains unarmed. No fit or experiment optimizer update has run.

Closure-publication verification: **875 passed, 3 skipped, zero failures in 453.39 seconds**, direct exit 0 with Lean integration required ([receipt](phase2/monitor_runtime_coverage_publication_test.json)).

## Half-schedule generation closed — 10-15-2026 03:43 PDT

The v2-S2 half-schedule panel is **COMPLETE: 4,312/4,312** responses on all 539 train tasks, eight samples each, with zero missing or second-attempt cells. It generated **22,953,131 tokens**, with 15,515,768 prompt tokens. Output length ranges from 1 to 8,192 tokens; 1,114/4,312 responses reached the fixed cap. All **17/17 leases are released**, every segment cleanup verifies, and allocated generation cost is **9.079613708257675 device-hours**.

The [immutable half-generation receipt](anchors_S2/half_generation.json) binds the original `d4948f3` generation publication, unchanged generation-lock hash `9d35a9ed34c25046b19e73e50dad89fdb62babd37acb643a6364ad1f5554178f`, full manifest and private response inventory. These are fixed-manifest accounting counts; confidence intervals and p-values do not apply. Token-cap responses retain the unchanged oracle's scoring semantics. No half-panel strict score has been computed. Its scoring lock follows this generation publication, before the unchanged scorer runs. Full-schedule batch 1 continues; no actual calibration fit, independent batch 2 or experiment optimizer update has run.

Half-generation publication verification: **912 passed, 3 skipped, zero failures in 462.14 seconds**, direct exit 0 with Lean integration required ([receipt](phase2/monitor_driver_publication_test.json)). Full batch 1 retains 3,392/4,312 responses at 10-15-2026 03:50 PDT.

Half scoring freeze (10-15-2026 04:01 PDT): [lock](locks/ANCHOR_SCORE_S2_half.json) binds all 4,312 responses and 43 implementation/provenance files, verified byte for byte; SHA-256 `389cf914e339fe0320cda8ba84edeb3e6438513aeb6a62ca54c7bceeefe1ad4a`. The generation report is published at `82343ed681e910972471237061068d1d87d50191`. Required suite: **917 passed, 3 skipped, zero failures in 452.32 seconds**, direct exit 0 ([receipt](anchors_S2/half_scoring_lock_test.json)). No half score has run; the unchanged full-panel scorer launches after this freeze is published. Full batch 1 retains 3,488/4,312 responses.

Half scoring launch (10-15-2026 04:15 PDT): published scoring lock `7fba7c90b3beb63f5c17903608a703b7dc441514` precedes the one launch. Watchdog-registered scorer PID 1846736 has 1,778/4,312 durable cell receipts, with cleanup verified on 1,778; no result is inferred for unfinished cells. [Launch evidence](anchors_S2/half_scoring_launch.json). Required publication checks: 926 passed, 3 skipped, direct exit 0 in 611.93 seconds.

## Half scoring closed — 10-15-2026 04:58 PDT

The once-launched, unchanged scorer accounts for **4,312/4,312** declared train responses: **4,303 measured, nine unavailable, zero measured strict successes**. Terminal status is **INCOMPLETE**, with zero retries, integrity defects or unresolved cleanup. Eight cells reached the existing internal deterministic timeout and one had a frontend process failure; none qualifies for a retry. All nine remain missing in calibration and in the original denominator. Raw task identities and evidence stay private.

Sharp full-denominator strict-success mean bounds are **[0, 0.0020871985157699443]**, or **[0%, 0.208720%]**. The frozen 10,000-draw bootstrap (seed 1302031) resamples 400 whole train task groups with all eight responses per task retained. Across missing-value completions, the 95% lower endpoint ranges over [0, 0.0009074410163339383] and the upper endpoint over [0, 0.0035112359550561797]; the outer envelope is **[0%, 0.351124%]**, p-val=n/a (descriptive diagnostic, no null test). This is conditional on the fixed model and response panel, with no model-fit or repeated-training uncertainty; the all-zero observed bootstrap is not a distribution-free population upper confidence bound. This train-panel description is neither held-out performance nor an admission verdict.

The [terminal scoring receipt](anchors_S2/half_scoring.json), [grouped diagnostic](anchors_S2/half_strict_diagnostic.json) and [processor/storage receipt](anchors_S2/half_scoring_cost.json) retain hashes and full accounting. User plus system time is **16.653466666666667 processor-hours**; wall time is **2,926.64 seconds**, device time zero. Scoring retains 158,947,099 logical bytes and 390,475,776 allocated bytes over 78,316 files. Both timed controller processes exited normally; every cell cleanup verifies. Required publication suite: **956 passed, 3 skipped, zero failures in 448.86 seconds**, direct exit 0 ([receipt](phase2/audit_report_monitor_method_publication_test.json)). Full batch 1 retains 3,936/4,312 generated responses; no actual calibration fit has run.

## Full-schedule batch 1 generation closed — 10-15-2026 05:49 PDT

The v2-S2 panel is **COMPLETE: 4,312/4,312** responses across all 539 train tasks, eight samples each. Missing and second-attempt cells are both zero. Generation produced **24,760,842 tokens** plus 15,515,768 prompt tokens; output lengths span 1–8,192, with 1,410/4,312 responses reaching the fixed cap. All **18/18 leases are released**, every segment cleanup verifies, and allocated generation cost is **9.709927685658137 device-hours**. This includes the earlier no-response infrastructure interruption and its released lease; no completed response was repeated.

The [immutable full1 generation receipt](anchors_S2/full1_generation.json) binds the original `d4948f3` generation publication, unchanged lock `bba7314f0656b89632adf4a38a50311f5abaff982909956d8d8d605b8239a769`, manifest and private response inventory. These are full-manifest accounting counts; confidence intervals and p-values do not apply. No full1 score has run. The scoring-input lock must be tested and published before the unchanged scorer starts once. Calibration and F2 still follow all three published scored panels; independent full2 remains unarmed. Required publication checks: **981 passed, 3 skipped, zero failures in 457.14 seconds**, direct exit 0 with Lean integration required ([receipt](anchors_S2/full1_generation_publication_test.json)).
