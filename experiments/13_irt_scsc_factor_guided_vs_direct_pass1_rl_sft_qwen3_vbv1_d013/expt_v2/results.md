# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** G0 PASS under A3: primary 4B dense-only bounds 89–97/135 (threshold 21), predictive AUC bounds 0.670652174–0.904643963 (threshold 0.65), exact across 221,184 configurations; 23 tasks affected by 34 excluded cells. Phase 1 is resource-blocked before generation admission; no training has run.

Last updated: 10-14-2026 14:16 PDT
Status: **G0 PASS; Phase 1 resource-blocked before LP-1.** [Resource evidence and continuation](phase1/README.md). [Full G0 bounds and evaluator outputs](RESULTS_G0.md) · [Verified exclusions and frozen method](reproduction/README_G0_A3.md).

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
| Phase 1 | RESOURCE BLOCK before generation admission | No usable current device route; zero anchors/fits; LP-1 unattempted |
| Phase 2 | NOT RUN; later gates pending | No reinforcement learning |

Fresh-owner setup: `codex-rl4cv-e13v2-owner-g0` is the sole active writer; the previous owner remains idle. Seven prior cron entries were preserved byte-for-byte and two watchdog entries added. Six watchdog self-tests passed. Exclusions are 13 train + 204 validation, with no test IDs; all four public class-(c) cells are excluded. No historical cell was rerun. Required full suite passed: 433 passed, 23 skipped, 0 failed in 260.05 seconds; Lean integration required. G0 uses existing data and central processors, with zero model-call spend or graphics processor hours. Result-publication suite also passed 433 tests with 23 skips in 233.01 seconds. Phase 1 device inventory currently finds all skampere1/2/3 accelerators occupied and Mercury1/2 disks below required headroom; no allocation or generation has begun. The scheduler account has zero associations and its non-submitting allocation test failed (exit 1, invalid account). This is a resource block, not a failed gate or completion; [continuation](phase1/README.md) records the unfinished LP-1 implementation and lock work.

[Read-only diagnosis](RESULTS_R2_diagnosis.md) · [Adopted A3 and owner recommendation](AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md). **Admission recorded** 10-14-2026 14:25 PDT under A3 rule 3(ii–iii) ([record](R2_A3_ADMISSION_10-14-2026.md)). The fresh owner verified the manifest and published wrapper/tests/lock at `a717d06` before G0. All 49 exceptions plus 168 existing typed ordinary limits are listed privately: 217/33,456 excluded, 33,239 retained measured/equal. No class (b) defect is demonstrated; its repair/re-measurement set is empty. Opaque unresolved reasons are `RuntimeError` for 2/2; no sealed details opened, public PASS stands. Required integration suite after synchronizing main `d3c2777`: 382 passed, 23 skipped, 0 failed in 164.19 seconds. The second synchronization to `69ae5be` added independent experiment-15 tests: 14/14 passed in 47.06 seconds. That earlier publication was diagnosis only; G0 is now reported above, with no cell rerun.

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 47 preserved attempt-1 evidence/configuration files remain byte-identical. The 50-file snapshot also includes PLAN and the runbook, explicitly superseded by master Amendment A2, and the separately owned live master checkpoint. Frozen fixture measurements and measurement code remain unchanged. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [R2 report](RESULTS_R2.md) and [A2 public result](R2_A2/public_result.json) retain both original and effective counts and hashes. Original ordinary reproduction finished untouched. Separate route processes retried all 46 ordinary and two opaque untyped cells exactly once with unchanged measurement code, sources, environment and limits. All 48 retries completed; no attempt 3 occurred. The ordinary route fails oracle equality and its unresolved ceiling. Both routes pass component consistency and have zero integrity defects. Opaque measured equality is PASS; its unresolved count is allowed. All per-cell ordinary diagnostics remain private and all test evidence sealed.

A2's unresolved tolerance was selected after the original opaque public observation, as disclosed in its amendment. The first A2 launch failed before any cell retry due to Linux page-rounding the requested memory cap by 2,048 bytes. A separate [justified, frozen preflight launcher](reproduction/README_A2_resource_preflight.md) was published at `90089e2` before corrected launch; the original A2 and measurement files remain unchanged. Required integration suite before launch: 333 passed, 23 unrelated skips. The final publication verification is recorded in the checkpoint. No terminal notification is sent, following the latest master instruction.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. Later gates retain the no-retry rule. A2 authorized the completed untyped-cell retries; adopted A3 now governs exception classification and exclusion/bounds admission without changing the original A2 result.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 G0 passes with exact completion bounds; Phase 1 is resource-blocked before generation admission.
**Snapshot:** 4B dense-only 89–97/135; AUC 0.670652174–0.904643963; 23 affected tasks; G0 one run; Phase 1 anchors 0/17,248.
