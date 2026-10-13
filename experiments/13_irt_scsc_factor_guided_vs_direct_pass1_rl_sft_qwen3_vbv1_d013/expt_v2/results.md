# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 passed R0 attempt 2 under Amendment A1: 30/30 fixtures matched, with complete components and historical oracle value/status. R1 attempt 1 also passed 400/400 train cells with matching historical oracle values and statuses.

Last updated: 10-13-2026 13:05 PDT
Status: **RUNNING — R0 and R1 accepted; preparing L1v2.**

| Stage | Status | Measured / declared |
|---|---|---|
| R0 attempt 1 | FAIL, retained | 26/29 matches; 28/29 complete components |
| R0 attempt 2 | PASS | 30/30 matches, oracle values/statuses, and complete components |
| Required suite for attempt 2 | PASS | 283 passed, 23 skipped; all seven required Lean cases ran |
| R1 attempt 1 | PASS | 400/400 measured and oracle-equal; zero untyped inconsistencies |
| L1v2 | NOT FROZEN | No validation/test factors computed |
| R2 | NOT ADMITTED | 0/38,784 unique available historical cells |
| G0 | NOT ADMITTED | 0/135 validation tasks |
| Phases 1 and 2 | NOT ADMITTED | No fitting or reinforcement learning |

[R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 50 preserved version-2 files remain byte-identical. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. No retries from L1v2 onward.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2's fixture acceptance passed 30/30 on attempt 2; the train-only diagnostic passed 400/400; L1v2 is next.
**Snapshot:** R0_attempt_2 PASS; 30/30 fixtures; 283 tests passed; R1 400/400 PASS; R2 0/38,784.
