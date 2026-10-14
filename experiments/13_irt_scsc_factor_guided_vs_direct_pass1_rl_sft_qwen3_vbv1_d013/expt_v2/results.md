# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** Experiment 13 version 2 stops at a final measured LP-1 FAIL under A4. Attempt 2 completed 8/8 responses and 40,035 generated tokens; its 99th-percentile log-probability error 0.124769325 exceeds the frozen 0.10 ceiling. Other criteria pass. A4 forbids attempt 3 after statistics; cleanup passed, both leases are released, and no downstream run is admitted. G0 remains PASS.

Last updated: 10-14-2026 16:42 PDT
Status: **STOPPED: final measured LP-1 FAIL under A4; attempt 3 not admitted.** [LP-1 failure and evidence](RESULTS_LP1.md) · [G0 PASS and exact bounds](RESULTS_G0.md).

Closeout verified: report and final G1 method published at `77558aa`; the A4 watchdog recorded exactly one stopped notification as **sent** to `brando.science@gmail.com`. Its receipt shows zero live experiment children, both leases released and all twelve cron lines preserved. [Completion receipt](LP1_A4/completion.json).

## Final LP-1 result — 10-14-2026 16:38 PDT

[Attempt-2 report](RESULTS_LP1.md) and [evidence receipt](LP1_A4/attempt2_result.json). Published fix/lock `957efca` preceded a passing real engine preflight and all probe work. All 8/8 responses and 40,035 generated tokens were measured: unsupported 0/40,035 (required 0), median absolute log-probability error 0.0003027766943 (maximum 0.01), 99th percentile 0.1247693252563 (maximum 0.10, FAIL), importance truncation 0/40,035 (maximum 0.01). These fixed-probe technical statistics have no inferential interval or hypothesis test (p-val=n/a).

The lease lasted 362.776132 seconds (0.100771148 device-hours), including the non-probe preflight; cumulative usage is 0.115364424/0.6 device-hours. Four cleanup checks passed without signals; no marked process remains and both leases are RELEASED. The private launch plan is retired; all twelve cron lines remain unchanged. The ignored Ray destructor error happened after the probability receipts and does not reclassify this measured FAIL as infrastructure incompleteness.

A4 rule 5 makes a measured verdict final. No attempt 3, anchor generation, calibration, G1/H2 evaluation or Phase 2 is admitted. The final G1 driver and executable method lock were prepared before any fit and are published with this result; their LP-1 prerequisite prevents execution. All actual-data fits remain zero. The A4 watchdog notification was sent after verified publication.

Final preparation/result publication verification: **552 passed, 23 skipped, zero failures in 243.53 seconds**, direct exit 0 with Lean integration required. Seven focused G1 driver checks cover frozen publication/input refusal, phase chronology and retained partial-fit receipts. The final [G1 method lock](locks/G1_A3.json) and [driver](phase1/g1_driver.py) are complete; no actual-data fit ran. [Test receipt](phase1/G1_A3_publication_test.json).

## Earlier A4 preparation (historical)

## Current A4 continuation — 10-14-2026 16:22 PDT

The master adopted [A4](AMENDMENT_A4_technical_gate_infrastructure_attempts_10-14-2026.md) after observing attempt 1. Its original records and historical stopped notice remain intact. [Attempt-2 preparation](phase1/LP1_A4.md) fixes the reproducible launcher defect and adds a claimed-device engine preflight. The original no-retry stop below is superseded only as A4 specifies; scientific gates retain their no-retry rules. Next: publish successor lock/tests, arm attempt 2, then follow PLAN section 5 if admitted.

Publication verification (10-14-2026 16:28 PDT): required Lean integration suite exited 0, **545 passed, 23 skipped, zero failures in 239.73 seconds**. [Receipt](phase1/LP1_A4_publication_test.json). Successor lock binds 31 inputs, with four named replacements and 17 unchanged previous bindings; each of three runtime routes preserves 130 prior scientific/source bindings and verifies 133 total. Publish before arming.

Active execution: the published A4 lock passed the original-versus-successor scientific-configuration check before arming. A fresh census admitted skampere1 device 0. Real engine preflight passed with one non-probe token and numeric device index verified; attempt 2 is now recorded and generating. [Arming/preflight receipt](phase1/LP1_A4_armed.json). All twelve cron entries remain installed; the old stopped receipt is historical, and the A4 watchdog monitors this continuation.

## Historical result before A4

| Stage | Status | Measured / declared |
|---|---|---|
| R0 attempt 1 | FAIL, retained | 26/29 matches; 28/29 complete components |
| R0 attempt 2 | PASS | 30/30 matches, oracle values/statuses, and complete components |
| Required suite for attempt 2 | PASS | 283 passed, 23 skipped; all seven required Lean cases ran |
| R1 attempt 1 | PASS | 400/400 measured and oracle-equal; zero untyped inconsistencies |
| L1v2 | FROZEN | 51 verified bindings; F0v2 0.50, F1v2 0.85; zero validation/test factors at freeze |
| R2 | FAIL under A2 | 38,784/38,784 accounted; 38,562 measured; 175 typed limits; 47 unresolved; 48 one-time retries |
| A3 diagnosis | COMPLETE; rule 3(i) satisfied | 49/49 classified; all four unequal cells (c) |
| A3 admission | G0 ADMITTED (master, 10-14-2026) | 217/33,456 ordinary cells excluded; 33,239 kept; worst-case completions for every G0/G1 statistic |
| G0 | PASS, exact worst-case bounds | 4B 89–97/135 dense-only; AUC 0.670652174–0.904643963; 23 affected tasks |
| LP-1 | INCOMPLETE; technical startup failure | One attempt, 0/8 responses; 0 trainer evaluations; cleanup verified, lease released |
| Phase 1 | STOPPED at unmet LP-1 prerequisite | CPU preparation retained; anchors 0/17,248; actual fits 0 |
| Phase 2 | NOT RUN; not admitted | No reinforcement learning |

Fresh-owner setup: `codex-rl4cv-e13v2-owner-g0` is the sole active writer; the previous owner remains idle. Seven prior cron entries were preserved byte-for-byte and two watchdog entries added. Six watchdog self-tests passed. Exclusions are 13 train + 204 validation, with no test IDs; all four public class-(c) cells are excluded. No historical cell was rerun. Required full suite passed: 433 passed, 23 skipped, 0 failed in 260.05 seconds; Lean integration required. G0 uses existing data and central processors, with zero model-call spend or graphics processor hours. Result-publication suite also passed 433 tests with 23 skips in 233.01 seconds. The earlier device contention was a wait. At 15:30 PDT an idle device was claimed and the frozen LP-1 attempt failed at startup. The current stop is documented below; it is not caused by occupied devices.

[Read-only diagnosis](RESULTS_R2_diagnosis.md) · [Adopted A3 and owner recommendation](AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md). **Admission recorded** 10-14-2026 14:25 PDT under A3 rule 3(ii–iii) ([record](R2_A3_ADMISSION_10-14-2026.md)). The fresh owner verified the manifest and published wrapper/tests/lock at `a717d06` before G0. All 49 exceptions plus 168 existing typed ordinary limits are listed privately: 217/33,456 excluded, 33,239 retained measured/equal. No class (b) defect is demonstrated; its repair/re-measurement set is empty. Opaque unresolved reasons are `RuntimeError` for 2/2; no sealed details opened, public PASS stands. Required integration suite after synchronizing main `d3c2777`: 382 passed, 23 skipped, 0 failed in 164.19 seconds. The second synchronization to `69ae5be` added independent experiment-15 tests: 14/14 passed in 47.06 seconds. That earlier publication was diagnosis only; G0 is now reported above, with no cell rerun.

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 47 preserved attempt-1 evidence/configuration files remain byte-identical. The 50-file snapshot also includes PLAN and the runbook, explicitly superseded by master Amendment A2, and the separately owned live master checkpoint. Frozen fixture measurements and measurement code remain unchanged. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [R2 report](RESULTS_R2.md) and [A2 public result](R2_A2/public_result.json) retain both original and effective counts and hashes. Original ordinary reproduction finished untouched. Separate route processes retried all 46 ordinary and two opaque untyped cells exactly once with unchanged measurement code, sources, environment and limits. All 48 retries completed; no attempt 3 occurred. The ordinary route fails oracle equality and its unresolved ceiling. Both routes pass component consistency and have zero integrity defects. Opaque measured equality is PASS; its unresolved count is allowed. All per-cell ordinary diagnostics remain private and all test evidence sealed.

A2's unresolved tolerance was selected after the original opaque public observation, as disclosed in its amendment. The first A2 launch failed before any cell retry due to Linux page-rounding the requested memory cap by 2,048 bytes. A separate [justified, frozen preflight launcher](reproduction/README_A2_resource_preflight.md) was published at `90089e2` before corrected launch; the original A2 and measurement files remain unchanged. Required integration suite before launch: 333 passed, 23 unrelated skips. The final publication verification is recorded in the checkpoint. No terminal notification was sent at that earlier R2 closeout, following the master instruction then in force.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. Later gates retain the no-retry rule. A2 authorized the completed untyped-cell retries; adopted A3 now governs exception classification and exclusion/bounds admission without changing the original A2 result.

## Phase 1 CPU preparation — 10-14-2026 14:51 PDT

The generation runner, actual NeMo probability path, exclusive attempt ledgers, lease/dispatcher, missing-data nested forecasts and recovery/bounds controls are implemented. Forty-nine focused synthetic tests pass; full required publication verification passed 502 tests with 23 skips and zero failures in 230.51 seconds. Train-only prompt preparation covers 539 tasks, four batches of 4312 responses and an eight-response probe, with maximum prompt 7753/context 15945/output 8192 tokens. No model generation, actual-data fit, optimizer update or GPU lease has occurred.

Remote execution needs own deployments because the nodes do not mount skampere1 files. Environment copies to skampere2/3 are underway within a bounded 50 GiB preparation allowance per node. Mercury remains a permitted generation-only alternative subject to actual admission and bounded storage. Device contention is a wait, with preparation continuing; no completion or blocker email.

## LP-1 runtime and device-plan freeze — 10-14-2026 15:17 PDT

[Generation admission freeze](phase1/LP1_FREEZE.md) and [lock](locks/LP1.json) bind one eight-response probe, 8,192 new tokens per response, a 30-minute device cap and no optimizer updates or retries. All three skampere deployments passed 132 file bindings and eight package-version checks each, with zero model calls/device allocations. Own remote runtime/model copies are complete; at least 8 GiB local scratch is required at claim time. The existing fifteen-minute poller will invoke the dispatcher once its private plan names the verified published lock revision; all ten cron lines are retained.

The dispatcher checks published bytes, fresh device processes, canonical foreign leases and master reservations; it releases only after verified marked-process cleanup. Unknown cleanup retains the lease for adoption. Mercury generation-only routes remain allowed when admitted. Busy devices remain WAIT while anchor scoring and the final G1 input lock are completed. No actual-data fit or downstream gate has run.


Publication verification: `E13_REQUIRE_LEAN_INTEGRATION=1 make test` exited 0; **512 passed, 23 skipped, zero failed in 240.62 seconds**. Receipt: [LP1_publication_test.json](phase1/LP1_publication_test.json).

## Automatic LP-1 dispatch and remaining CPU preparation — 10-14-2026 15:29 PDT

LP-1 freeze `d831d0fe9eeff11487b7449530abf3f672b7d474` was pushed and verified on main before arming. The first dispatcher registered PID 3760150 with the watchdog and returned `WAIT_FOR_IDLE_UNRESERVED_DEVICE`; zero leases, device-hours or model calls. All ten cron lines are byte-identical to the post-poller backup. The watchdog confirms one live owner. [Arming receipt](phase1/LP1_armed.json).

The anchor scorer now uses frozen extraction, independent official strict scoring and separate declaration components, with one attempt per declared cell. It preserves capped successes and missing denominators, uses the measured R1 memory rule, 64 GiB per-worker limits and marked-process cleanup. Four focused checks passed, including a real capped-source Lean control. G1 input, alias-exclusion and fixed-forecast checks passed 41 synthetic tests; available M2 remains reported when the candidate or reward baseline is unavailable. Source features were prepared for 539 train and 135 validation tasks from 1,348 hash-bound Python/reference files; no test source opened and no actual-data fit. The [G1 draft](phase1/G1_BOUNDS_DRAFT.md) has updated source/input bindings, with its final execution driver and lock still required before fitting.

## LP-1 terminal result — 10-14-2026 15:36 PDT

[LP-1 report](RESULTS_LP1.md): one frozen attempt, 0/8 responses, zero generated tokens and optimizer updates. Installed vLLM 0.10.0 interpreted the launcher's device UUID as an integer during engine construction. Probability agreement is unmeasured; this is a launcher defect. The CPU preflight omitted this compatibility check. Cleanup passed and the lease was released after 52.535794 seconds (0.014593276 device-hours). Automatic launch is retired; the ten cron entries are preserved.

PLAN section 5's LP-1 prerequisite is unmet and section 4's no-retry rule applies. G0 remains PASS, but no anchors, calibration, G1/H2 or Phase 2 were run. The final G1 driver and executable lock were not completed; the retained draft is non-executable. The latest required suite passed 528 tests with 23 skips, zero failures in 247.80 seconds; [verification receipt](phase1/scoring_inputs_publication_test.json). No scientific failure is inferred from the unmeasured probability statistics. Report and retained preparation published at `50cf118`, verified on remote main. At 15:38 PDT the watchdog recorded exactly one stopped notification as sent to `brando.science@gmail.com`; zero live experiment children and zero active leases. [Completion receipt](LP1/completion.json).

**TLDR-end:** [rl4cv: Experiment 13 v2] LP-1 attempt 2 fails the frozen probability-tail criterion; the measured verdict is final under A4.
**Snapshot:** Responses 8/8; tokens 40,035; median error 0.000302777; p99 error 0.124769325 > 0.10; optimizer updates 0; cumulative device-hours 0.115364424; leases RELEASED.
