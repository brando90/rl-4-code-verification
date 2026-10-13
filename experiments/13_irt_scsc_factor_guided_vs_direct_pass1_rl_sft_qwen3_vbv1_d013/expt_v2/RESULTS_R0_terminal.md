# Version 2 authored fixture gate: terminal failure

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_R0_terminal.md>

**TLDR:** The authored fixture gate (R0) for `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 failed: 26 of 29 new fixture cases matched all frozen expectations. Under PLAN § 4, downstream measurement stops; this is an engineering admission failure, not evidence about reinforcement-learning efficacy.

Created: 10-13-2026 12:10 PDT
Last updated: 10-13-2026 12:10 PDT
Status: **STOPPED AT R0 — FAIL**, no gate retries.

## Complete accounting and decision

| Check | Observed | Frozen requirement / interpretation |
|---|---:|---|
| New authored source fixtures | 26 / 29 fully matched | Every fixture must match; FAIL |
| Historical oracle value **and status** | 29 / 29 matched | Source-specific frozen readbacks preserved in these cases |
| Complete component measurements | 28 / 29 | One frontend failure stays unmeasured, not zero |
| Inherited experiment-13 contract/integration tests | 30 / 30 passed | Included in the required full suite |
| Full required repository suite | 283 passed, 23 skipped, 0 failed | `E13_REQUIRE_LEAN_INTEGRATION=1 make test`; all seven legacy Lean cases executed |
| Watchdog self-tests | 6 / 6 passed | Fake mail, owned kill session, concurrent recovery, orphan adoption, durable attempts, no deterministic retry |
| Historical reproduction | 0 / 38,784 | Not admitted or executed |
| Train diagnostic | 0 / target 400 | Not admitted or executed |

These are exhaustive deterministic fixture/test counts from one formal run, not population estimates: confidence intervals and statistical tests are not applicable; p-val=n/a. No extra repetitions were added. The 23 conditional suite skips concern other prerequisites; absence of the seven required Lean integration prerequisites would have raised under the required flag.

## Three retained failures

| Fixture | Frozen expectation | Actual evidence | Meaning |
|---|---|---|---|
| `error_beyond_4000` | Clean commands 4/5; proved theorems 1/2; strict 0 | Clean commands **2/5**; proved theorems **1/2**; strict **0**. Two `unknown constant 'String.ofList'` errors surround the intended failed proof | Authoring error: `String.ofList` is unavailable in pinned Lean 4.22.0. No 5,000-character message was produced. The required long-log property remains unvalidated |
| `stderr_capture` | Strict 1; clean commands 3/3; proved theorems 1/1; marker in per-command standard error | All scalar expectations matched. `e13v2-stderr-evidence` is present in the command's **information message**; its raw standard-error field is empty | The channel assertion did not account for Lean's `#eval` message capture. The text was retained, but the frozen assertion failed |
| `unresolved_type` | Strict 0; clean commands 1/2; proved theorems 0/1 | Oracle strict **0**, status **scored**. Frontend exit **1**, no component JSON: `cannot evaluate [init] declaration 'Mathlib.pp.mathlib.binderPredicates' in the same module` | Actual probe failure on this unresolved-obligation case. Complete diagnostics and the obligation denominator were not delivered; the whole component measurement stays missing |

The long-log fixture and stderr assertion were authored incorrectly for this runtime. The unresolved-theorem failure is separately material: the new probe cannot yet satisfy its every-output contract. No expectation, source, implementation hash, or result was changed to convert a failure into acceptance. No fixture was rerun after the freeze.

## What did work

The failed-proof-then-valid-theorem case preserved **1/2** proved theorems and **2/3** clean commands. The vacuity case preserved **2 raw historical screen hits** separately from **1 distinct vacuous theorem**. Valid capped source remained strict **1**. Printed error-looking text retained historical kernel-probe rejection at strict **0**. Unknown historical status remained **None / unmeasured** while components were computed. Both multiple-block extraction controls used the pinned selector and matched.

The oracle calls the frozen scorer and the source-specific readback independently of the components. The Lean frontend traverses unchanged source commands; private records retain messages, command spans, final-environment theorem dependencies, and captured standard output/error. These are candidate implementation properties observed on authored cases, not admission for historical cells.

## Chronology, provenance and limits

- Initial owner/results records were pushed at `c49d4ba` before authored development measurements; watchdog publication is `b508c9e`.
- Fixture freeze: [R0 lock](locks/R0.json), SHA-256 (Secure Hash Algorithm, 256 bits) `e2041b3ca1f4fca5a226c8cc28b1d544698ea5ea5968d27d8a09ea5f5a092a49`. [Execution binding](locks/R0_execution.json) records the serial process and 64-gibibyte address-space ceiling.
- Full fixture result digest: `6d87f6a616fdac0c229b63df5ec36b474d87086d452a0c08565899a0a26991d0`. [Machine-readable results and raw-evidence hashes](results/R0_result.json); [authored source copies](fixtures/).
- Private raw evidence: `/lfs/skampere1/0/brando9/rl4cv_e13v2/r0/`. Published copies are byte-identical; source paths in the original lock remain unchanged.
- All **42 original version 1 files** remain byte-identical. Three frozen scorer file hashes and extraction revision `c11b99badfa386fd26810b208eef1eb8dc9f6806` were verified; Lean is 4.22.0.
- Required-suite startup initially failed before collection because the isolated environment lacked `pygments`; dependencies were installed privately and the suite then ran. That startup failure is retained at `required_integration_make_test.log`. Scientific fixture attempts were neither reset nor repeated.
- No historical train, validation or test source was executed in version 2. The train allowlist was not created. No measurement lock for historical cells, forecasts, model fit, rollout, graphics-processor job, provider call, or reinforcement-learning update was run.
- Unexecuted train-diagnostic preparation is preserved privately under `$WR/state/unexecuted_r1_preparation/`; it is not an accepted implementation.

The binding transition is **stop downstream measurement and publish**. The current version does not proceed to the train diagnostic, historical lock/reproduction, usefulness gate, prediction phase, or training phase. The parent experiment retains its existing live dependency: unresolved measurement admission blocks its planned matched reinforcement-learning comparison.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 stopped at its authored fixture gate with 26/29 matches and one missing component measurement; the reinforcement-learning hypothesis remains untested.
**Snapshot:** 26/29 fixture matches; 29/29 oracle value/status matches; 28/29 component measurements; 0/38,784 historical cells; 0 gate retries.
