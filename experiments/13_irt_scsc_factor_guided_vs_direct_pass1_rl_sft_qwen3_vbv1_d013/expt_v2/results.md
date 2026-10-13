# Experiment 13 version 2 live results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** Amendment A1 permits up to five development attempts; attempt 2 is now frozen. The following numbers describe attempt 1. `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 stopped at its authored fixture gate (R0): **26/29** cases matched, with **28/29** complete component measurements. Historical strict value and status matched on **29/29** authored cases; no historical cells or training were run.

**Status:** RUNNING under Amendment A1 — R0_attempt_2 frozen (30 authored fixtures); attempt-1 failure retained unchanged in its terminal report.
**Last updated:** 10-13-2026 12:52 PDT

[Full terminal report](RESULTS_R0_terminal.md) · [Machine-readable evidence](results/R0_result.json) · [Owner checkpoint](CKPT_e13_v2_owner.md)

| Stage | Status | Measured / declared |
|---|---|---|
| Owner and watchdog | DONE | 6 / 6 self-tests passed |
| R0 attempt 1 authored source fixtures | FAIL (retained) | 26 / 29 full matches; 28 / 29 component measurements |
| R0 attempt 2 | RUNNING | 30 declared; required full suite passed 283 tests with 23 skips |
| R0 historical oracle value/status | DONE | 29 / 29 matched authored expectations |
| R0 inherited contract and Lean integration cases | DONE | 30 / 30 passed |
| R1 train diagnostic | NOT ADMITTED | 0 / target 400 (300 rejected, 100 measured) |
| L1v2 historical measurement lock | NOT CREATED | No validation/test measurement admitted |
| R2 oracle reproduction | NOT ADMITTED | 0 / 38,784 unique available cells |
| G0 usefulness gate | NOT ADMITTED | 0 / 135 validation tasks |
| Phase 1 prediction and anchors | NOT ADMITTED | Train anchor tasks: 539 per batch |
| Phase 2 matched reinforcement learning | NOT ADMITTED | Three paired seeds planned; test 222 tasks × 16 samples per selected condition/seed |

Three failures remain exactly as recorded: the long-log fixture used unavailable `String.ofList` (clean commands 2/5, expected 4/5); the standard-error assertion missed text retained by Lean as an information message; and the unresolved-theorem probe exited 1 with a Mathlib initializer error, leaving its components unmeasured. The long-log fixture and channel assertion were authoring errors. None was repaired and rerun to convert this gate into acceptance.

Required verification: `E13_REQUIRE_LEAN_INTEGRATION=1 make test` passed **283**, skipped **23**, failed **0** in 164.72 seconds; all seven required legacy Lean cases ran. An earlier dependency failure occurred before test collection and is retained. These are exhaustive deterministic counts, not population estimates; confidence intervals/statistical tests do not apply, p-val=n/a.

Full historical denominator stays **38,784**: base **21,504** plus available ladder **20,520** minus **3,240** shared cells. The parent's **5,400** unavailable ladder cells remain separately declared. Split task counts remain train **539**, validation **135**, test **222**. Missing values never become zero scores.

All **42** original version 1 files remain byte-identical. No historical train, validation or test source was executed for version 2. No new historical forecast, model fit, rollout, provider call or reinforcement-learning update occurred. The stop is an engineering admission result, not evidence for or against the reinforcement-learning hypothesis. Gate retries: **0**.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 resumed under A1 with a separately frozen second fixture attempt; historical measurement awaits acceptance.
**Snapshot:** 26/29 fixture matches; 29/29 oracle matches; 28/29 component measurements; 0/38,784 historical cells; 0 retries.
