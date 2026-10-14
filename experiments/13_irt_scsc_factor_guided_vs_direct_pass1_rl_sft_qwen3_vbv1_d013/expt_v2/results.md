# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** G0 is admitted under Amendment A3. The fresh owner verified the 217-cell exclusion manifest and re-armed the watchdog additively. The separate bounds wrapper, tests and lock are prepared; no G0 statistic is computed before their publication. Original R2 FAIL under A2 remains unchanged.

Last updated: 10-14-2026 14:03 PDT
Status: **G0 FREEZE IN PROGRESS; no G0 statistic computed.** [Admission](R2_A3_ADMISSION_10-14-2026.md) · [Verified exclusion counts and prospective bounds method](reproduction/README_G0_A3.md).

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
| G0 | NOT RUN; wrapper/tests/lock prepared for publication | 0/135 validation tasks; 217 exclusions verified |
| Phases 1 and 2 | NOT RUN; later gates pending | No fitting or reinforcement learning |

Fresh-owner setup: `codex-rl4cv-e13v2-owner-g0` is the sole active writer; the previous owner remains idle. Seven prior cron entries were preserved byte-for-byte and two watchdog entries added. Six watchdog self-tests passed. Exclusions are 13 train + 204 validation, with no test IDs; all four public class-(c) cells are excluded. No historical cell was rerun. Required full suite passed: 433 passed, 23 skipped, 0 failed in 260.05 seconds; Lean integration required. G0 uses existing data and central processors, with zero model-call spend or graphics processor hours.

[Read-only diagnosis](RESULTS_R2_diagnosis.md) · [Adopted A3 and owner recommendation](AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md). **Admission recorded** 10-14-2026 14:25 PDT under A3 rule 3(ii–iii) ([record](R2_A3_ADMISSION_10-14-2026.md)). Next, the fresh owner verifies the manifest and freezes the wrapper before G0. All 49 exceptions plus 168 existing typed ordinary limits are listed privately: 217/33,456 excluded, 33,239 retained measured/equal. No class (b) defect is demonstrated; its repair/re-measurement set is empty. Opaque unresolved reasons are `RuntimeError` for 2/2; no sealed details opened, public PASS stands. Required integration suite after synchronizing main `d3c2777`: 382 passed, 23 skipped, 0 failed in 164.19 seconds. The second synchronization to `69ae5be` added independent experiment-15 tests: 14/14 passed in 47.06 seconds. This is diagnosis only; no G0 or cell rerun occurred.

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 47 preserved attempt-1 evidence/configuration files remain byte-identical. The 50-file snapshot also includes PLAN and the runbook, explicitly superseded by master Amendment A2, and the separately owned live master checkpoint. Frozen fixture measurements and measurement code remain unchanged. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [R2 report](RESULTS_R2.md) and [A2 public result](R2_A2/public_result.json) retain both original and effective counts and hashes. Original ordinary reproduction finished untouched. Separate route processes retried all 46 ordinary and two opaque untyped cells exactly once with unchanged measurement code, sources, environment and limits. All 48 retries completed; no attempt 3 occurred. The ordinary route fails oracle equality and its unresolved ceiling. Both routes pass component consistency and have zero integrity defects. Opaque measured equality is PASS; its unresolved count is allowed. All per-cell ordinary diagnostics remain private and all test evidence sealed.

A2's unresolved tolerance was selected after the original opaque public observation, as disclosed in its amendment. The first A2 launch failed before any cell retry due to Linux page-rounding the requested memory cap by 2,048 bytes. A separate [justified, frozen preflight launcher](reproduction/README_A2_resource_preflight.md) was published at `90089e2` before corrected launch; the original A2 and measurement files remain unchanged. Required integration suite before launch: 333 passed, 23 unrelated skips. The final publication verification is recorded in the checkpoint. No terminal notification is sent, following the latest master instruction.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. Later gates retain the no-retry rule. A2 authorized the completed untyped-cell retries; adopted A3 now governs exception classification and exclusion/bounds admission without changing the original A2 result.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 is preparing the admitted G0 bounds run; the exclusion set is verified and wrapper publication must precede measurement.
**Snapshot:** Exclusions 217 = train 13 + validation 204; watchdog tests 6/6; G0 not run; freeze ready; required suite 433 passed / 23 skipped.
