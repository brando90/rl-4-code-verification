# Fixed reference success and specification comparison

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/METRICS.md>

**TLDR:** Use explicit binary outcomes for pass@1 and retain SCSC as the official aggregate. Proving reference obligations about a candidate is more directly useful than demanding exact equality of specification text.

## What pass@1 means here

Pass@1 is the probability that one sampled attempt passes a specified acceptance predicate, estimated by the average binary success across declared tasks (or samples per task, with task-level uncertainty). It is not intrinsically “passes tests”: the predicate must be named. The code-generation literature uses functional correctness under fixed tests; see [Chen et al.](https://arxiv.org/abs/2107.03374). A continuous geometric mean of fractional components is not ordinary pass@1. The geometric mean of three binary indicators equals their conjunction, so a binary definition is possible, but redundant continuous scores should not be relabelled pass@1.

Define the attempt as either the initial single response or one entire fixed-budget repair policy. Report `initial-pass@1` and `policy-success@budget` distinctly: a multi-call repair policy is not a one-call sample.

## Candidate auxiliary endpoints

| Endpoint | Binary success | Scope and limitations |
|---|---|---|
| `reference_tests_pass` | Candidate implementation passes every fixed reference test in a compatible, frozen interface | Finite tests cannot certify all behaviors; require a nonempty test suite |
| `reference_obligations_proved` | Every fixed reference obligation about the candidate implementation has an allowed-axiom proof certificate | Proof search is incomplete; distinguish disproved, search-exhausted, adapter-unavailable and infrastructure-missing |
| `reference_verified_success` | Both conditions above hold | Primary proposed independent acceptance predicate; retain its two components and applicability |
| `spec_refinement_proved` | Candidate specification conjunction implies the reference conjunction under an explicit abstraction relation and common domain | Secondary; include preconditions, non-vacuity and the actual implementation linkage |
| `spec_equivalence_proved` | Both implication directions have accepted certificates | Optional stricter diagnostic; stronger valid specifications need not be equivalent |

These are auxiliary endpoints, not replacement VeriBench aggregates. No geometric mean of them is introduced. If only tests are reliably measurable, label the result `reference_tests_pass`, freeze that fallback prospectively and narrow the claim to tested behavior. Do not omit the third quantity after observing a disappointing correlation. Report infeasibility and both any original and revised analysis plans.

## Reference replay without circularity

For each task define a frozen callable interface or a semantics-preserving adapter from the reference representation to the candidate. References remain evaluator-only. Instantiate the fixed reference statements with the candidate implementation. Neither running the original reference proof about the original function, nor importing its proved theorem unchanged, verifies the candidate.

Two endpoints must stay separate: (a) properties certified by the **submitted** artifact after a mechanical adapter, and (b) properties an **external prover** establishes using extra search. The latter tests certifiability under that evaluator's budget and capacity, not the submitted model's proof skill. Match prover budget across policies and report proof certificates, attempt counts, time and unknowns.

A representation adapter must not smuggle in the reference implementation, add assumptions equivalent to the goal, or silently restrict inputs. Freeze adapters using screened external tasks before the final test; record required conversions and failed applicability by benchmark/split. Do not train a repair controller on observed test adapters.

## Cross-file equivalence is possible but conditional

Different files are not inherently the obstacle. Load modules under distinct namespaces and state a bridge theorem in a third module. The hard parts are different types, representations, preconditions, signatures, dependent types and abstraction relations. Syntactic equality, definitional equality, logical equivalence and implementation equivalence are different tests.

Let `R(x, f(x))` be the conjunction of reference postconditions and `A(x, f(x))` the candidate's. After aligning domains, proving `A → R` addresses reference coverage; `R → A` tests whether the candidate adds constraints. Equality requires both. Handle precondition implication explicitly: a stronger candidate precondition can make an apparently strong postcondition vacuous. A conjunction over an empty requirement set is not evidence of useful correctness.

A failed bounded proof search is `unknown`, never “not equivalent.” A checked counterexample may establish a specific mismatch. Report directional success, applicability and resource exhaustion separately; keep all tasks in the full denominator. Report certification yield as a lower bound only for proofs whose transitive axioms meet the strict policy.

## Proof and evaluation integrity

- Trust only transitive theorem dependencies within `{propext, Classical.choice, Quot.sound}`. `sorry`, `admit`, user axioms and `native_decide` dependencies fail the policy, even through helpers.
- Empty tests or theorems cannot earn reference success. Check the manifest has real requirements before evaluation.
- Pin Lean, Mathlib, reference bytes, adapter, scorer, judge, prompt, model/revision, container and policy. Keep each result joined to candidate SHA-256 (cryptographic content hash), not only a task name.
- Reference outcomes are hidden from the solver; an evaluation judge may see references, but feedback must not leak their text or exact hidden counterexamples.
- Use the validated formal specification coverage judge; gate reward on compilation and non-vacuity. An ungated coverage score on invalid text is diagnostic only.
- Existing historical replay uses fields called `tc_kernel` and `kernel_validated`; those names do not override its published trust warning. Do not join its deprecated judge to modern SCSC as if they were one instrument.

## Analysis once suitable data exists

Use within-model, within-panel, within-condition comparisons. Report Pearson correlation, Spearman rank correlation and Kendall rank correlation separately with task-cluster bootstrap 95% intervals; constant vectors yield undefined values. Do not pool model means and mistake capability differences for within-model validity. Do not test correlation against zero as the substantive result.

Compare predictive performance of compiler status, aggregate SCSC, and the full factor vector using an externally fit mapping to reference success. Freeze the mapping on non-VeriBench validation data. Use held-out Brier score or log loss, calibration and discrimination; raw SCSC is not a probability estimate. When interpreting mapped probability levels, report mean absolute error, both means and bias = prediction minus binary reference outcome (positive is optimistic). Include sample counts, base rates, missingness and censoring.

A low correlation need not invalidate VeriBench: SCSC measures additional proof/specification quality beyond tested functional behavior. Inspect matched pairs with equal test success and different proof/coverage outcomes. A high correlation does not show useful diagnosis; only the controlled intervention tests that claim.
