# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 completed full reproduction and A2's authorized retries. **R2 FAIL under A2**: 38,784/38,784 accounted; 4/33,243 ordinary measured oracle mismatches; 45/33,456 ordinary unresolved (maximum 33). Opaque equality PASS; 2/5,328 unresolved (maximum 5). G0 and later phases are not admitted; the reinforcement-learning hypothesis remains untested.

Last updated: 10-13-2026 21:21 PDT
Status: **R2 FAIL — downstream measurement not admitted under A2 rule 3 and PLAN § 4.**

| Stage | Status | Measured / declared |
|---|---|---|
| R0 attempt 1 | FAIL, retained | 26/29 matches; 28/29 complete components |
| R0 attempt 2 | PASS | 30/30 matches, oracle values/statuses, and complete components |
| Required suite for attempt 2 | PASS | 283 passed, 23 skipped; all seven required Lean cases ran |
| R1 attempt 1 | PASS | 400/400 measured and oracle-equal; zero untyped inconsistencies |
| L1v2 | FROZEN | 51 verified bindings; F0v2 0.50, F1v2 0.85; zero validation/test factors at freeze |
| R2 | FAIL under A2 | 38,784/38,784 accounted; 38,562 measured; 175 typed limits; 47 unresolved; 48 one-time retries |
| G0 | NOT ADMITTED | 0/135 validation tasks |
| Phases 1 and 2 | NOT ADMITTED | No fitting or reinforcement learning |

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 47 preserved attempt-1 evidence/configuration files remain byte-identical. The 50-file snapshot also includes PLAN and the runbook, explicitly superseded by master Amendment A2, and the separately owned live master checkpoint. Frozen fixture measurements and measurement code remain unchanged. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [R2 report](RESULTS_R2.md) and [A2 public result](R2_A2/public_result.json) retain both original and effective counts and hashes. Original ordinary reproduction finished untouched. Separate route processes retried all 46 ordinary and two opaque untyped cells exactly once with unchanged measurement code, sources, environment and limits. All 48 retries completed; no attempt 3 occurred. The ordinary route fails oracle equality and its unresolved ceiling. Both routes pass component consistency and have zero integrity defects. Opaque measured equality is PASS; its unresolved count is allowed. All per-cell ordinary diagnostics remain private and all test evidence sealed.

A2's unresolved tolerance was selected after the original opaque public observation, as disclosed in its amendment. The first A2 launch failed before any cell retry due to Linux page-rounding the requested memory cap by 2,048 bytes. A separate [justified, frozen preflight launcher](reproduction/README_A2_resource_preflight.md) was published at `90089e2` before corrected launch; the original A2 and measurement files remain unchanged. Required integration suite before launch: 333 passed, 23 unrelated skips. The final publication verification is recorded in the checkpoint. No terminal notification is sent, following the latest master instruction.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. Later gates retain the no-retry rule; A2 authorizes only the specified untyped-cell retries in R2.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 passed fixture and train diagnostics but fails full reproduction under A2; the reinforcement-learning comparison is not admitted.
**Snapshot:** R0 attempt 2 PASS 30/30; R1 PASS 400/400; R2 accounted 38,784/38,784; ordinary oracle mismatches 4/33243; opaque equality PASS; R2 FAIL; zero training updates.
