# Experiment 13 v2-S2 T2: final attempt 3 FAIL, unchanged weights

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_T2_S2.md>

**TLDR:** v2-S2 T2 final FAIL: one completed optimizer step left all 399 parameter tensors (4,411,424,256 elements) unchanged. All 256 train responses are retained; 255 scores are measured and one deterministic resource limit remains missing. The fixed 8-response refit passes (median absolute log-probability error 0.0000327482 <= 0.01). PLAN section 4 and A4 stop Phase 2 here; no T3–T5, audits, main learning or selected held-out evaluation is admitted. All 14 T2 leases are released; cumulative T2 use is 4.370285669/10.0 device-hours.


## Final measured result — closeout 10-16-2026 08:40 PDT

The single-update gate asks whether the frozen Qwen3-4B supervised fine-tuning warm start at `step_658` changes its parameter hash after one update and whether the exported generator agrees with the trainer. The [saved gate result](phase2/T2_A6_attempt3_result.json) is copied byte-for-byte; all ten gate-input bindings and all 4,706 learning-pilot lock bindings were checked, with no statistic recomputed ([binding verification](phase2/T2_A6_attempt3_binding_verification.json)).

| Observation | Final attempt 3 |
|---|---:|
| Train generation | 256/256 slots; 1,290,726 output tokens |
| Official scoring | 255/256 measured; 1 deterministic resource limit |
| Strict successes | 0/255 measured; missing outcome retained in 256 denominator |
| Usable groups / declared groups | 31/32 (one incomplete group masked) |
| Nonzero-advantage slots | 0; all measured advantages zero |
| Optimizer steps / nonzero-gradient updates | 1 / 0 |
| Parameter hash changes | 0; required change absent (**FAIL**) |
| Parameter tensors / elements | 399 / 4,411,424,256 |
| Refit responses / tokens | 8/8 / 44,844 |
| Refit median absolute log-probability error | 0.000032748153898864985 <= 0.01 (**PASS**) |
| Refit p99 absolute error (descriptive) | 0.017602388858795164 |
| Unsupported / importance-truncated refit tokens | 0/44,844 / 0/44,844 |
| Admitted attempt-3 device-hours | 2.918218210 / 8.0 cap |
| Separate unadmitted preflight device-hours | 0.052590087 (retained) |
| Cumulative T2 device-hours, all attempts and preflights | 4.370285669 / 10.0 cap |
| Released T2 leases / active experiment leases | 14/14 / 0 |

Before and after parameter SHA-256 are identical: `7fed40220b3d759cd49391bd311b15a5468137d3bf99dff425ac401c838c16ae`. The frozen technical path uses strict binary rewards (`technical_driver.cpu_scores` → `rollout_groups.assemble(technical=True)`); all 255 measured rewards were zero. The installed optimizer/scheduler advanced on the all-zero-advantage batch as frozen in PROTOCOL section 5; an optimizer call is not a nonzero-gradient update. The refit receipt's generic “no optimizer update” annotation describes its probability measurement, not the preceding completed update stage.

[Scoring summary](phase2/T2_A6_attempt3_scoring.json), [update summary](phase2/T2_A6_attempt3_update_summary.json), and [resource receipts](phase2/T2_A6_attempt3_resources.json) preserve the saved evidence without task identifiers or response manifests. Scoring cleanup verified for all 256 cells. The score stage used 1.221859386 accounted processor-hours and 1,622.197572 elapsed seconds. Resource receipts label their processor-accounting scope; detached service usage is not inferred. Attempts 1 and 2 and the unadmitted preflight remain unchanged and excluded from attempt-3 statistics, with all costs retained.

**Binding transition:** PROTOCOL section 6 requires a changed weight hash. PLAN section 4 says “T1–T4 fail → Stop Phase 2 at that gate; publish.” A4 makes every measured admission result final. Consequently T3, T4, the train mutation and independent coverage audits, T5, main learning, checkpoint selection and new held-out evaluations were not run. No fourth attempt, replacement batch, different reward or relaxed criterion is admitted. The requested comparison of reward conditions remains unmeasured; the failure does not establish that a factored reward is ineffective.

These are single-run deterministic admission observations. Confidence intervals and hypothesis tests are not applicable to hash equality or the fixed-probe gate (`p-val=n/a`); no population probability or efficacy claim is made. The 0/255 strict-success count is descriptive, with full-manifest success bounds [0, 1/256], not a substitute learning test.

The existing controller closed the result before this recovery; its saved result timestamp is 10-16-2026 00:06 PDT (07:06 UTC). Publication testing and the final notification receipt are recorded below. Earlier dated entries below are historical snapshots, not current state.

## Preserved attempt history

T2 attempt 2 infrastructure closure (10-15-2026 19:20 PDT): **INCOMPLETE-INFRA**, CPU-offloaded distributed-tensor state hashing requested an unsupported CPU collective while saving the before-update checkpoint. The full 256-response generation/scoring and trainer probability recomputation remain retained; **zero experiment optimizer updates and gate statistics** completed. The native saver's zero-learning-rate optimizer initialization is separately disclosed in the [failure evidence](phase2/T2_A6_attempt2_result.json). Cleanup is verified and all seven T2 leases are released; attempt 2 used **0.797922019** device-hours, cumulative **1.399477372/10.0** ([resources](phase2/T2_A6_attempt2_resources.json)). Under A4, repair the byte-preserving state-hash path, reproduce the defect in a regression, add a real checkpoint-state preflight, and publish the successor before complete attempt 3. Attempt 3 is the final permitted infrastructure attempt; all scientific settings and caps stay unchanged. The unchanged source last passed required integration with 1,174 passed, 3 skipped and direct exit 0.

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

T2 pre-admission shutdown handoff (10-15-2026 19:55 PDT): the published repair passed real-model hashing for **399/399 CPU-offloaded distributed tensors, 4,411,424,256 elements**, on the claimed idle device. The subsequent unchanged device guard encountered the shutting-down owned Ray worker and raised `PermissionError` reading its process environment, before generator engine construction. [Evidence](phase2/T2_A4_CPU_preflight_failure.json). Zero experiment responses, optimizer updates or admission statistics; **numbered attempt 3 was not admitted**. Cleanup verified, lease released, 0.052590087 additional device-hours charged; cumulative **1.452067459/10.0**. Preserve this preflight and publish a tested shutdown wait plus explicit pre-admission reconciliation. The device guard and scientific settings remain unchanged.

T2 reservation-observation reconciliation verified (10-15-2026 20:37 PDT): [method](phase2/T2_A4_OBSERVATION_RECONCILIATION.md) and [successor](locks/LP_A6_S2_T2_A4_OBSERVATION.json). One exact duplicate historical review in experiment 12 caused a no-claim wait; its path/hash are now bound while the original allocator, live foreign checks, allocation hash/caps and scientific settings remain unchanged. Nineteen focused checks and required integration **1,204 passed, 3 skipped, zero failures in 503.52 seconds**, direct exit 0. The sleeping controller was retired without children or active leases. Numbered attempts remain two; T2 usage is 1.452067459/10.0 device-hours. Publish admission, then resume fresh health and final attempt 3.

T2 final numbered attempt 3 admitted (10-15-2026 20:47 PDT): tested repair `2b9fb66` and admission `c107bbc` preceded fresh health. Actual model hashing **399/399 offloaded tensors**, owned-worker exit/census synchronization and non-probe generator/provenance/socket checks PASS. The original gate driver is generating the complete 256-response train cohort on skampere1 device 0, controller PID 49490 under the watchdog ([evidence](phase2/T2_A4_OBSERVATION_attempt3_launch.json)). Both failed numbered attempts and the earlier unadmitted preflight remain retained, with 1.452067459 device-hours already charged before this fresh health; none of their outputs enters the gate statistic. No optimizer update or verdict yet. This is the final permitted A4 numbered attempt; caps remain 8.0/10.0 hours. Required integration passed 1,204 tests with 3 skipped and direct exit 0; source is unchanged.

Final T2 attempt-3 launch publication verification (10-15-2026 20:52 PDT): the merged repository passed required Lean integration **1,220 tests, 3 skipped, zero failures in 523.44 seconds**, direct exit 0 ([receipt](phase2/T2_OBSERVATION_launch_publication_test.json)). The published infrastructure/runtime and scientific settings are unchanged. Fresh health and final numbered admission already succeeded; the saved launch snapshot binds the exact plan, controller, health evidence and retained costs. This publication computes no gate statistic and performs no retry.

T2 final attempt 3 generation closure (10-15-2026 21:19 PDT): **256/256 fresh train responses**, 1,290,726 output tokens, generation cleanup verified and lease released after 0.514747599 device-hours. [Evidence](phase2/T2_A4_CPU_attempt3_generation.json). The same controller is running the frozen official scorer. No completed optimizer update or T2 gate statistic exists at this snapshot. Both earlier failed numbered attempts and the separate unadmitted preflight remain retained and excluded from the final gate; every cost stays charged. No fourth numbered attempt is available. Runtime source is unchanged since required integration passed 1,220 tests with 3 skipped and direct exit 0 (subsequent isolated Experiment 08 test addition also passed).

T2 terminal publication verification (10-16-2026 08:53 PDT): required Lean integration **1,382 passed, 3 skipped, 6 subtests passed, zero failures in 517.38 seconds**, direct exit 0 ([test receipt](phase2/T2_A6_terminal_publication_test.json)). All 4,706 frozen bindings and ten gate inputs verify. The initial unconfigured-shell test failure was retained and resolved by restoring the prescribed environment and pinned dependency paths; no runtime/scientific source changed. The temporary test alias and added closeout cron line were removed; every prior cron line remains. The watchdog sent exactly one stopped-event email to brando.science@gmail.com, no CC ([closeout receipt](phase2/T2_A6_terminal_closeout.json)). The notice includes the credential-rotation action; no raw environment log or credential value is published. Final experiment state is STOPPED_AT_T2_FAIL; downstream measurement remains unadmitted.
