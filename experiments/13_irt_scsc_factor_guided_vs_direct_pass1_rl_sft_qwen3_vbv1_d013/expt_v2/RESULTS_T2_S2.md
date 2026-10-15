# Experiment 13 v2-S2 T2: attempt 1 admitted after the device wait

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_T2_S2.md>

**TLDR:** T1 is published PASS. T2 attempt 1 passed the actual non-probe preflight on idle device 2 and is generating its fixed train batch under the unchanged learning-pilot freeze. The previous device collision produced no probe response or statistic and remains charged; no T2 verdict exists yet.

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
