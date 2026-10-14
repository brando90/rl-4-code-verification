# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** Version 2's read-only R2 diagnosis under adopted A3 is complete: 2/49 exceptions are class (a), 0/49 (b), 4/49 (c), and 43/49 (d). All four unequal ordinary cells are historical-record irreproducibility (c), satisfying A3's classification condition. The master must enforce exclusions and full-manifest bounds before G0. Original R2 FAIL under A2 remains unchanged; no new cell measurement, fitting or reinforcement learning ran.

Last updated: 10-14-2026 13:15 PDT
Status: **A3 diagnosis COMPLETE — classification condition satisfied; exclusion/bounds admission audit is next.**

| Stage | Status | Measured / declared |
|---|---|---|
| R0 attempt 1 | FAIL, retained | 26/29 matches; 28/29 complete components |
| R0 attempt 2 | PASS | 30/30 matches, oracle values/statuses, and complete components |
| Required suite for attempt 2 | PASS | 283 passed, 23 skipped; all seven required Lean cases ran |
| R1 attempt 1 | PASS | 400/400 measured and oracle-equal; zero untyped inconsistencies |
| L1v2 | FROZEN | 51 verified bindings; F0v2 0.50, F1v2 0.85; zero validation/test factors at freeze |
| R2 | FAIL under A2 | 38,784/38,784 accounted; 38,562 measured; 175 typed limits; 47 unresolved; 48 one-time retries |
| A3 diagnosis | COMPLETE; rule 3(i) satisfied | 49/49 classified; all four unequal cells (c) |
| G0 | NOT RUN; master exclusion/bounds audit pending | 0/135 validation tasks |
| Phases 1 and 2 | NOT RUN; later gates pending | No fitting or reinforcement learning |

[Read-only diagnosis](RESULTS_R2_diagnosis.md) · [Adopted A3 and owner recommendation](AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md). **Next:** master verifies exclusion and full-manifest worst-case bounds under A3 rule 3(ii–iii), then records admission. All 49 exceptions plus 168 existing typed ordinary limits are listed privately: 217/33,456 excluded, 33,239 retained measured/equal. No class (b) defect is demonstrated; its repair/re-measurement set is empty. Opaque unresolved reasons are `RuntimeError` for 2/2; no sealed details opened, public PASS stands. Required integration suite after synchronizing main `d3c2777`: 382 passed, 23 skipped, 0 failed in 164.19 seconds. The second synchronization to `69ae5be` added independent experiment-15 tests: 14/14 passed in 47.06 seconds. This is diagnosis only; no G0 or cell rerun occurred.

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 47 preserved attempt-1 evidence/configuration files remain byte-identical. The 50-file snapshot also includes PLAN and the runbook, explicitly superseded by master Amendment A2, and the separately owned live master checkpoint. Frozen fixture measurements and measurement code remain unchanged. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [R2 report](RESULTS_R2.md) and [A2 public result](R2_A2/public_result.json) retain both original and effective counts and hashes. Original ordinary reproduction finished untouched. Separate route processes retried all 46 ordinary and two opaque untyped cells exactly once with unchanged measurement code, sources, environment and limits. All 48 retries completed; no attempt 3 occurred. The ordinary route fails oracle equality and its unresolved ceiling. Both routes pass component consistency and have zero integrity defects. Opaque measured equality is PASS; its unresolved count is allowed. All per-cell ordinary diagnostics remain private and all test evidence sealed.

A2's unresolved tolerance was selected after the original opaque public observation, as disclosed in its amendment. The first A2 launch failed before any cell retry due to Linux page-rounding the requested memory cap by 2,048 bytes. A separate [justified, frozen preflight launcher](reproduction/README_A2_resource_preflight.md) was published at `90089e2` before corrected launch; the original A2 and measurement files remain unchanged. Required integration suite before launch: 333 passed, 23 unrelated skips. The final publication verification is recorded in the checkpoint. No terminal notification is sent, following the latest master instruction.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. Later gates retain the no-retry rule. A2 authorized the completed untyped-cell retries; adopted A3 now governs exception classification and exclusion/bounds admission without changing the original A2 result.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 completed the read-only R2 diagnosis under A3; all four unequal cells are class (c), and the master's exclusion/bounds admission audit is next.
**Snapshot:** A3 classes (a)/(b)/(c)/(d) = 2/0/4/43 of 49; original A2 FAIL preserved; no cell rerun; no G0; 382 tests passed, 23 skipped.
