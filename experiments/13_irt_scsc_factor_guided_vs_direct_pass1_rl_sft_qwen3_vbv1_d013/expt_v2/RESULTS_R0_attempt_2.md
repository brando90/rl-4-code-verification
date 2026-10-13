# R0 attempt 2: complete authored fixture acceptance

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_R0_attempt_2.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 passes its second authored fixture attempt under Amendment A1: all 30 source cases matched, and the required full repository suite passed. The train-only R1 diagnostic is now admitted.

Created: 10-13-2026 12:57 PDT
Status: **PASS** (development attempt 2 of at most 5).

| Check | Measured / declared | Requirement |
|---|---:|---|
| Full fixture expectations | 30 / 30 | Every case matches |
| Historical strict value and status | 30 / 30 | Independent frozen oracle |
| Complete component measurements | 30 / 30 | No missing outputs |
| Required repository suite | 283 passed, 23 skipped, 0 failed | `E13_REQUIRE_LEAN_INTEGRATION=1 make test` |
| Required legacy Lean integration | 7 / 7 executed | Cannot skip |
| Attempt-1 frozen files retained | 50 / 50 checked | Byte-identical (excludes live checkpoint/results) |
| Original version-1 files retained | 42 / 42 | Byte-identical |

These are deterministic full-set counts from one attempt, not population estimates; confidence intervals and p-values are not applicable (p-val=n/a). Required-suite duration was 168.61 seconds. All 29 earlier source cases were retained; two fixture sources were corrected with advance justification, and one initialized-error-printing regression was added.

## Corrections and observed evidence

- **Long messages:** a literal 5,000-character string replaces the unavailable constructor. Both information messages contain **5,001 characters**, at command indices 2 and 4. The 60-character error is attached to the intervening theorem at index 3. Clean commands are **4/5** and proved theorems **1/2**, strict **0**.
- **Streams:** the original `#eval IO.eprintln` marker is retained as a **22-character information message**. A separately scoped command with `stderrAsMessages false` retains **25 raw standard-error characters**. The separate probe control captures exact raw standard-output and standard-error markers. Clean commands are **4/4**, proved theorems **1/1**, strict **1**.
- **Unresolved theorem:** with initializer execution enabled before header import, both error messages are retained (63 and 86 characters). The unresolved theorem remains in the denominator: proved **0/1**, clean commands **1/2**, strict **0**.
- **Regression:** explicitly enabling Mathlib's binder-predicate printing option produces the expected `n < 0` error without crashing, and the later valid theorem is measured. Clean commands **3/4**, proved theorems **1/2**, strict **0**.

The fixes and their independent justifications were committed before the rerun: long-message `3fbcb96`, stream handling `7ed9e85`, initialized imports and exception retention `76d85b4`. The implementation was compiled before freezing. Header import failures remain Lean diagnostics; parsed command exceptions and diagnostic-rendering exceptions are retained without discarding the obligation list. No historical oracle behavior changed.

## Provenance and next admission

- [Attempt-specific lock](R0_attempt_2/lock.json), digest `67f005f9b146704ec5007be748d6a30bc01239d0f0af826d3aec489799872759`; [execution binding](R0_attempt_2/execution_lock.json).
- Full result digest `d3085ce762c905fdd66e77bbdfa0078a68ce49bf259bf96033d99b28b06bc459`; [results and raw-evidence hash inventory](R0_attempt_2/result.json); [authored source copies](R0_attempt_2/fixtures/).
- Raw evidence remains privately under `/lfs/skampere1/0/brando9/rl4cv_e13v2/R0_attempt_2`. Serial execution used a 64-gibibyte virtual-address ceiling.
- [Attempt 1](RESULTS_R0_terminal.md) remains **FAIL, 26/29**. It was not rewritten or erased. A1, committed before this rerun, changes development acceptance only. No retry is allowed from L1v2 onward.
- The fenced watchdog is re-armed as `e13v2_a1`; prior notification and attempt records are preserved.
- No historical train, validation or test source had been executed when this report was produced. R1 is the next admitted step; its full 300-rejected plus 100-measured train-only sample must be frozen before execution.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2's second fixture attempt passed 30/30 and admits the train-only diagnostic; this is measurement acceptance, not a reinforcement-learning outcome.
**Snapshot:** 30/30 full matches; 30/30 oracle matches; 30/30 component measurements; 283 tests passed; 0 historical cells executed.
