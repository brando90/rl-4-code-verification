# Experiment 13 version 2 live results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 is building the authored-fixture probe. Historical cell measurements have not started.

**Status:** RUNNING — setup started 10-13-2026 11:44 PDT.
**Last updated:** 10-13-2026 11:58 PDT

| Stage | Status | Measured / declared |
|---|---|---|
| Owner and watchdog | DONE (monitoring; executor recovery pending) | 6 / 6 self-tests passed |
| R0 authored fixtures | IN PROGRESS | Development only; formal expectations not yet frozen |
| R1 train diagnostic | PENDING | 0 / target 400 (300 rejected, 100 measured) |
| L1v2 measurement lock | PENDING | No validation/test measurement admitted |
| R2 oracle reproduction | PENDING | 0 / 38,784 unique available cells |
| G0 usefulness gate | PENDING | 0 / 135 validation tasks |
| Phase 1 prediction and anchors | PENDING | Train anchor tasks: 539 per batch |
| Phase 2 matched reinforcement learning | PENDING | Three paired seeds; test 222 tasks × 16 samples per selected arm/seed |

Full historical manifest: 21,504 base cells plus 20,520 available ladder cells, with 3,240 shared cells counted once. The parent's 5,400 unavailable ladder cells remain separately declared. Split task counts are train 539, validation 135, test 222. Missing cells never become zero scores.

The historical strict oracle supplies both value and status; new components are separate measurements. Development uses train cells only. The measurement lock precedes validation/test factors, and test reproduction runs only in an opaque process. Version 1 evidence is preserved byte-for-byte.

Verification: `make test` passed 283 tests with 23 conditional skips; watchdog self-tests use fake mail and uniquely owned processes. These are deterministic operational counts, not scientific estimates (p-val=n/a). Automatic executor replacement is still pending.

[Owner checkpoint](CKPT_e13_v2_owner.md) · [Binding transition table](PLAN.md#transition-table)

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 monitoring passed six self-tests; the formal fixture gate has not run.
**Snapshot:** 0 / 38,784 reproduction cells measured; no validation/test factors computed.
