# Frozen engineering protocol for endpoint controls

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v2/endpoint_validation/PROTOCOL.md>

**TLDR:** Freeze and run all authored endpoint controls before using this checker in a repair comparison. This protocol covers engineering validation only; the measured repair protocol belongs to the parent coordinator.

## Locked setup before Lean execution

The manifest, driver, candidate files, pinned verifier and this protocol form the frozen setup. Preserve their cryptographic content hashes and original bytes in the run receipt. The current manifest declares three tasks and eight variants per task; no cell may be removed because it fails. Reference expressions, finite tests and universal obligations are evaluator-owned and do not depend on the submitted specification.

The tasks are authored solely for validation and have no imported benchmark material. They must not become an evaluation benchmark or a trained controller's task pool under this protocol. Cross-family benchmark-reference acceptance and dataset contamination screening would be separate requirements if that scope changes.

Hypothesis: a correct implementation with a valid full certificate passes all three control endpoints; a buggy implementation fails fixed tests and the exact obligation through a checked witness; a weak/vacuous valid submitted certificate cannot bypass those fixed requirements; dishonest certificates fail transitive-axiom inspection even when the implementation is correct. Correct implementations with dishonest certificates can pass evaluator certifiability independently.

Decision criterion: every declared cell matches `expected.tests`, `expected.submitted` and `expected.evaluator`, with all source and dependency pin checks satisfied. A mismatch prompts an engineering repair followed by a new receipt directory preserving the earlier run. Changing objective, callable representation, reference requirements or search budget requires a versioned protocol amendment before execution. Never rewrite a measured receipt or call a failure a success through expectation edits.

## Fixed budgets and measurement

No model calls, no reward/judge calls, no training and no graphics processing unit time. Run on the Stanford Network Analysis Project (SNAP) cluster under the parent's authorized worker, with the pinned Lean 4.22.0 project. The evaluator tries `intro n; rfl`, `simp [Candidate.impl]`, then `intro n; simp [Candidate.impl]; omega`, with early stopping after an accepted proof. Each compilation-plus-inspection probe has a 30-second deadline; every control uses this same cap. Actual elapsed seconds and attempt counts are retained. No retry changes the candidate or spends additional unrecorded proof search.

The restricted representation itself prevents import/namespace/metaprogram injection. Do not generalize its protection to arbitrary Lean files. The pinned kernel inspector's complete framed output, clean exit status, source identity, compiled module identity, exact theorem resolution and strict axiom list are all acceptance requirements.

Finite mismatches are first located by an exact interpreter of the bounded expression representation, then checked by a generated Lean inequality certificate. A failed attempt alone yields unknown. The fixed universal equation is false only when a checked finite witness disproves it. Empty tests and obligations are rejected before compilation. Missing infrastructure remains unmeasured, preserving every declared cell in the receipt.

## Reporting

Report engineering control counts and statuses only. Do not compute correlation, confidence intervals, pass-at-one, repair effects or SCSC from these controls. RUNNING is a receipt state generated only when execution begins; PENDING is the current Lean-validation state. Successful local Python tests validate schema and status logic only.

Keep submitted certificates and externally found reference proofs as distinct artifacts and result fields. In a later repair study the fixed reference outcome is evaluator-only; any observed feedback must follow that study's separate leak-control and matching-budget protocol. This checker does not define, implement or score that policy.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] All 24 external engineering controls must pass their frozen expectations before the independent checker is accepted; Lean execution is pending.

**Snapshot:** Actual local evidence is `Ran 10 tests ... OK`; no Lean endpoint observation exists yet.
