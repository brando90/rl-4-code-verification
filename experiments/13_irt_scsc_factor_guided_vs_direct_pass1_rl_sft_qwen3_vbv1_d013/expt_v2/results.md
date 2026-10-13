# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 passed R0 attempt 2 under Amendment A1: 30/30 fixtures matched, with complete components and historical oracle value/status. R1 attempt 1 also passed 400/400 train cells with matching historical oracle values and statuses.

Last updated: 10-13-2026 14:57 PDT
Status: **DOWNSTREAM BLOCKED — opaque reproduction INCOMPLETE; ordinary cohort still running to finish the declared report.**

| Stage | Status | Measured / declared |
|---|---|---|
| R0 attempt 1 | FAIL, retained | 26/29 matches; 28/29 complete components |
| R0 attempt 2 | PASS | 30/30 matches, oracle values/statuses, and complete components |
| Required suite for attempt 2 | PASS | 283 passed, 23 skipped; all seven required Lean cases ran |
| R1 attempt 1 | PASS | 400/400 measured and oracle-equal; zero untyped inconsistencies |
| L1v2 | FROZEN | 51 verified bindings; F0v2 0.50, F1v2 0.85; zero validation/test factors at freeze |
| R2 | Opaque route INCOMPLETE; ordinary route running | 11,414/38,784 receipts at 14:57; opaque 5,319 measured + 7 typed limits + 2 unresolved / 5,328 |
| G0 | NOT ADMITTED | 0/135 validation tasks |
| Phases 1 and 2 | NOT ADMITTED | No fitting or reinforcement learning |

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 49 preserved attempt-1 evidence/configuration files remain byte-identical. The original 50-file snapshot also included the separately owned live master checkpoint, which the master updated in `1e1a34a` before L1v2; it is not frozen attempt evidence. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [opaque public receipt](R2/opaque_public_receipt.json) exposes completeness and hashes only. No test discrepancy, factor, label or source has been inspected. Under PLAN section 4, its INCOMPLETE status blocks G0 and every later phase; the existing ordinary run continues only to complete the declared reproduction report. No retry or scientific fix is authorized after the lock. This is unresolved technical measurement, not evidence against the reward hypothesis.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. No retries from L1v2 onward.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2's fixture acceptance passed 30/30 on attempt 2; the train-only diagnostic passed 400/400; L1v2 is published and full reproduction is blocked by incomplete opaque measurement while the ordinary cohort finishes.
**Snapshot:** R0_attempt_2 PASS; 30/30 fixtures; 283 tests passed; R1 400/400 PASS; R2 opaque INCOMPLETE: 5,319 measured, 7 typed limits, 2 unresolved / 5,328; ordinary cohort running.
