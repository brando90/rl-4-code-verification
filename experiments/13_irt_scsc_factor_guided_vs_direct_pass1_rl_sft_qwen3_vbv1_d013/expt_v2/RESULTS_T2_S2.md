# Experiment 13 v2-S2 T2: attempt 2 running; attempt 1 INCOMPLETE-INFRA

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_T2_S2.md>

**TLDR:** Attempt 2 has generated and scored the complete 256-response train cohort: 255 measured, one deterministic timeout, all cleanup verified. The controller reserved an idle device for its single update. Attempt 1 remains INCOMPLETE-INFRA; T1 remains PASS and no T2 verdict exists.

T2 attempt 2 scoring closure (10-15-2026 19:00 PDT): **256/256 receipts, 255 measured and one deterministic timeout**, cleanup verified for every cell ([receipt](phase2/T2_A4_attempt2_scoring.json)). The missing result remains masked; no response was repeated or replaced. Processor cost is 1.137382396 hours and elapsed scoring time 1582.049700 seconds. The same controller reserved idle skampere1 device 0 for its single update ([reservation snapshot](phase2/T2_A4_attempt2_update_launch.json)); no completed update or gate verdict exists at this snapshot. Source code is unchanged since required Lean integration passed 1,174 tests with 3 skipped and direct exit 0 ([receipt](phase2/T2_A4_attempt2_publication_test.json)).

T2 attempt 2 generation closure (10-15-2026 18:38 PDT): **256/256 responses** retained, 1,292,105 output tokens; device cleanup verified and lease released after 0.494777962 device-hours ([receipt](phase2/T2_A4_attempt2_generation.json)). The same controller is running the frozen official scorer. No optimizer update, T2 admission statistic or held-out measurement exists at this snapshot. Attempt 1 remains INCOMPLETE-INFRA, with its outputs excluded and all earlier costs retained. Required Lean integration: **1,174 passed, 3 skipped, zero failures in 504.84 seconds**, direct exit 0 ([receipt](phase2/T2_A4_attempt2_publication_test.json)).

T2 attempt 2 launch (10-15-2026 18:03 PDT): published repair `9b55f35` and admission `5b02bd9` preceded the fresh device-1 claim. Actual non-probe engine, provenance metadata and Ray socket checks PASS; complete numbered attempt 2 is admitted and its 256-response train generation is running ([receipt](phase2/T2_A4_attempt2_launch.json)). Controller PID 3497257 is watchdog-registered. Attempt 1 remains INCOMPLETE-INFRA, with 0.601555353 device-hours charged and its outputs excluded. No optimizer update or T2 statistic exists at this snapshot. Required integration passed 1,174 tests with 3 skipped, direct exit 0; this publication changes only status and copied launch evidence.

T2 A4 admission freeze (10-15-2026 17:57 PDT): [admission lock](locks/T2_A4.json), hash `169d4c62e7e68e1f9456216a2a8b71f1cce951080c12aa05d0a5fe14546ac2aa`, binds tested repair/LP revision `9b55f35`, regression PASS and failed-attempt revision `0266ac5`. All 4,685 successor bindings verify; seven infrastructure changes/additions are enumerated, with 4,678 prior hashes and the scientific signature/allocation unchanged. Required integration already passed 1,174 tests with 3 skipped and direct exit 0; this publication only binds references and records status. Complete attempt 2 may proceed after publication and a fresh non-probe engine preflight.

T2 attempt 1 infrastructure closure (10-15-2026 17:44 PDT): **INCOMPLETE-INFRA**, missing `provenance` in the generated update configuration raised `KeyError` before the update function was called. All 256 train responses and scoring receipts remain retained (255 measured, one timeout), with **zero optimizer updates and admission statistics**. All four T2 reservations are released and cleanup verified; cumulative **0.601555353/10.0 device-hours**. [Failure evidence](phase2/T2_A6_attempt1_result.json), [resource receipts](phase2/T2_A6_attempt1_resources.json). Under A4, publish the metadata-only fix, reproducing regression, preflight and successor lock before complete numbered attempt 2; failed-attempt outputs never enter its statistics. The current unchanged implementation passed 1,157 tests with 3 skipped, direct exit 0.

T2 scoring closure (10-15-2026 17:39 PDT): 256/256 receipts accounted, 255 measured and one deterministic timeout; zero retries and unresolved cleanups ([receipt](phase2/T2_A6_scoring.json)). The timeout stays missing, with its group masked. The original controller reserved idle skampere1 device 1 for the one update. No completed update or T2 verdict exists at this snapshot. The unchanged current code passed required integration with 1,157 passed, 3 skipped, direct exit 0 ([receipt](phase2/selected_coverage_analysis_publication_test.json)).

T2 attempt 1 admission (10-15-2026 16:44 PDT): the additive wait recovery was published at `fd7edca` before claiming device 2. The unchanged non-probe engine preflight passed, one numbered attempt was admitted, and controller PID 554111 is executing the fixed 256-response train generation under the watchdog ([launch receipt](phase2/T2_A6_launch.json)). No optimizer update or gate statistic exists. The earlier device collision remains charged at 0.015054962 device-hours; the 8.0/10.0-hour limits are unchanged. The just-completed required integration suite passed 1,133 tests with 3 skipped, direct exit 0; this publication copies launch evidence and updates documentation only.

The following table preserves the earlier pre-admission collision snapshot.

| Observation | Saved value |
|---|---:|
| Numbered T2 attempts admitted | 0 |
| Train responses generated | 0/256 |
| Optimizer updates | 0/1 |
| Admission statistics computed | 0 |
| Closed health reservations | 1 |
| Device-hours charged | 0.01505496150917477 |
| T2 per-attempt / cumulative caps | 8.0 / 10.0 hours |

[The collision receipt](phase2/T2_preflight_collision.json) retains exact error and evidence hashes. Cleanup is verified and the reservation released. No other owner's process was used or stopped. Parameter change and generator-refit probability agreement are **unmeasured**; this record is not T2 FAIL, PASS or an efficacy result. No confidence interval or hypothesis test applies to a device-wait event (`p-val=n/a`).

[The reconciliation method](phase2/T2_PREFLIGHT_WAIT.md) and [additive lock](locks/T2_PREFLIGHT_WAIT_A6_S2.json) preserve the failed launch, charge its cost and permit fresh idle-device polls. The unchanged actual engine preflight must pass before T2 attempt 1 is admitted. T2's complete 256-response train probe, one update and refit then follow the published LP at `d5961c9`, with prior T1 PASS published at `0439f49`. No completed gate is repeated.

Required Lean integration: **1,133 passed, 3 skipped, zero failures in 601.42 seconds**, direct exit 0 ([receipt](phase2/T2_preflight_wait_publication_test.json)). The wait poller is launched only after this freeze is pushed.
