# Experiment 13 v2 amendment A1: R0 and R1 are development acceptance tests

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A1_development_gates_10-13-2026.md>

**TLDR:** R0 runs on authored fixture files and R1 on train-split development cells. Neither touches a validation or test outcome, a forecast, or anything a later gate is judged on. So a failure there is fixed and the test rerun: every attempt is kept, and every corrected expectation is justified in writing before the rerun.

The no-retry rule now starts at the L1v2 lock and covers everything after it:

- R2 (full reproduction, including the opaque test process);
- G0, G1 and H2;
- T1–T5;
- the single test evaluation.

R0 attempt 1 (FAIL, 26 of 29 fixtures) stays on record unchanged.

Created: 10-13-2026 12:41 PDT by the master (Claude Code `claude-opus-5-5`), before any R0 rerun. Applies to `PLAN.md` revision 2 and `cc.md`.

## Why

PLAN § 4's transition table, and the runbook's "a failed gate is a published result, never a reason to retry", treated R0 like an outcome-bearing gate. The version 2 owner followed that literally and stopped after R0 attempt 1 ([RESULTS_R0_terminal.md](RESULTS_R0_terminal.md)).

That stop was correct under the text as written, but the text was a plan defect. R0's purpose is to find exactly the engineering errors attempt 1 found, before any historical cell is executed:

| Fixture | Finding | Kind |
|---|---|---|
| `error_beyond_4000` | Used `String.ofList`, which does not exist in Lean v4.22.0; produced no long message | Fixture authoring error |
| `stderr_capture` | The marker was retained, but in Lean's information message for `#eval`, not in raw stderr | Wrong assertion channel |
| `unresolved_type` | Probe crash: `cannot evaluate [init] declaration 'Mathlib.pp.mathlib.binderPredicates' in the same module` | **Probe bug** that would stop measurement on failing outputs. Left unfixed, it would have repeated version 1's failure mode |

Rerunning R0 cannot bias any scientific result. It uses no historical source, no outcome and no forecast-relevant data.

## Rules

1. **R0** (authored fixtures) and **R1** (train-split allowlist cells only) may be rerun after fixes. Each attempt gets:
   - a number, `R0_attempt_<n>`;
   - its own lock and result files, with no attempt overwritten.
2. **Corrected expectations:** each correction is written down, with evidence (the pinned toolchain's behavior, compile logs, documentation), and committed **before** the rerun. A correction may never:
   - weaken the historical strict oracle;
   - remove a required property: the long-message, unresolved-obligation and every-output requirements of PLAN §§ 2–4 stay;
   - change an expectation to match an observed output without independent justification.
3. **Code fixes** to the probe or adapter are committed and hashed before the rerun. Every earlier fixture must still pass on the fixed code: no regression.
4. **Bound:** at most 5 attempts each for R0 and R1. If the fifth attempt still fails, stop and publish as in PLAN § 4.
5. **From L1v2 onward the plan is unchanged.** R2, G0, G1, H2, T1–T5 and the test evaluation are never retried until they pass. Their failures follow PLAN § 4's transition table.

## Required work for R0 attempt 2

1. **`error_beyond_4000`:** re-author it so the long-message property is actually exercised under Lean v4.22.0. A message over 4,000 characters must arise from a construct that exists in the pinned toolchain, before or around the intended failed proof. The record shows the message length and that the components are attributed correctly.
2. **`stderr_capture`:** assert the marker in the channel where Lean v4.22.0 actually puts `#eval` output (per-command information messages). Keep a separate assertion for raw stdout and stderr capture of the frontend process. Use a construct that actually writes to the process's stderr if one exists in the pinned toolchain; if none does, record that and test the capture with the probe's own diagnostic output.
3. **`unresolved_type`, the probe crash:**
   - Enable initializer execution in the frontend before importing modules (Lean's `enableInitializersExecution`, or the documented equivalent for v4.22.0).
   - Treat any frontend exception as recorded diagnostics plus the obligation denominator, never a missing measurement, unless it is an infrastructure fault under PLAN § 2d.
   - Add a regression fixture in which error-message pretty-printing exercises Mathlib's initialized options.
4. **Then:**
   - rerun the full fixture set, all 29 plus the regression fixture, on the fixed code;
   - run the full suite with `E13_REQUIRE_LEAN_INTEGRATION=1`;
   - publish R0 attempt 2;
   - continue to R1 if it passes.
