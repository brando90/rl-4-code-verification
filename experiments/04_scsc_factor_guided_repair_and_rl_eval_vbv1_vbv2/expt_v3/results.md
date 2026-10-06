# External factor feedback pilot execution

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v3/results.md>

**TLDR:** The authored 24-cell checker-control panel is reconciled and matches its frozen expectations, while the real external-panel applicability study remains 0/24 and fails its independent 20/24 gate. No solver, judge, repair, or causal outcome has been admitted.

Created: 10-05-2026 22:33 PDT

| Stage | Evidence and status |
|---|---|
| Historical audit | Complete in `../expt_v1`; unchanged |
| Authored checker controls | DONE: 24 / 24 cells measured, 24 / 24 matching frozen expectations; immutable-row reconciliation recorded |
| External source preparation | DONE: FVAPPS and pinned VERINA source receipts; no source is silently promoted to a reference |
| Real 24-task endpoint applicability | DONE, FAIL: 0 / 24 tasks have the audited generic candidate adapter required by the predeclared 20 / 24 gate |
| Matched feedback repair | NOT ADMITTED: 0 / 192 repair cells and 0 / 1,296 judge-member calls, because the independent endpoint is inapplicable |
| Prospective environment comparison | NOT ADMITTED: candidate-only 141 / 24 / 24 train / validation / test split and readiness receipt; no forecast or training result |

The separate Qwen3 Base eight-response evaluation completed under its existing owner: 21,504/21,504 scored cells and 24/24 scoring jobs. Of those generations, 6,214 ended at the generation-length limit but have actual recorded kernel and proof-fraction scores; they are not missing scoring rows. The owner's artifacts remain read-only. This completed feasibility evaluation does not admit warm-start training or remove this study's external-adapter blocker.

Runtime receipts are retained at `/lfs/skampere1/0/brando9/rl4cv_azalia_execute/runtime`, with published findings linked below. A coordinator exit or authored-control pass must not be reported as completion of the repair study.

## Completed authored-control reconciliation

- The original 20 measured rows are retained in `../expt_v2/endpoint_validation/results_2026-10-06T0544Z_controls/results.json`; four previously pending cells (`cap_two_sorry`, `cap_two_helper_sorry`, `cap_two_axiom`, and `cap_two_native_decide`) were measured only once under the same fixed procedure in `results_2026-10-06T0734Z_resume4_retry1/results.json`.
- The first resume preflight (`results_2026-10-06T0732Z_resume4/results.json`) is retained as an infrastructure/input failure: its local scorer checkout lacked the pinned kernel revision, and it measured no cell. The sole identical-infrastructure retry used scorer commit `59059a20d40adf3289869e58302169ad78102877` (SHA-256 `5dbbdcae…6de287`) and pinned Lean 4.22/mathlib receipt `d99caf0b…e4ceef1`.
- `../expt_v2/endpoint_validation/results_2026-10-06T0734Z_reconciliation.json` reconciles all 24 cells against immutable source rows (SHA-256 `0c420a1e…ca7090d`): 24/24 measured and matching. This verifies only the bounded authored harness; it does not alter the real-task adapter result below.

## External-source and applicability receipts

- FVAPPS source bytes matched SHA-256 `e0874ed…d60146bc1`; its 24 selected rows remain blocked because released specifications and executable stubs contain `sorry`.
- VERINA source commit `66b3ce5…7249f` (Apache-2.0, source Lean 4.18) supplied 189 records. Against the pinned VeriBench corpus, normalized exact overlap was 0 / 189 and word-5-gram Jaccard overlap at least 0.70 was 0 / 189. The first 24 source hashes were frozen before Lean or model outcomes.
- Original VERINA bytes compiled under the pinned Lean 4.22 workspace for 22 / 24 tasks; two source proofs failed due Lean-version/API changes. The pinned transitive-axiom inspector found 6 / 24 original reference theorems kernel-honest, 16 / 24 with forbidden `sorryAx`, and 2 / 24 unknown after source compile failure. These are source-reference diagnostics, not candidate certifications.
- All 24 files expose the expected benchmark section markers, but the existing endpoint is deliberately limited to a bounded JSON natural-number-to-natural-number candidate language. No audited mechanical adapter preserves candidate hashes and fixed requirement identities for these arbitrary Lean sources; hence endpoint applicability is 0 / 24 and the repair pilot stops before inference.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] The external-factor feedback pilot completed source validation but failed the independent endpoint applicability gate, so no measured repair comparison was admitted.

**Snapshot:**
```text
VERINA screened=189/189; exact_hits=0; near_hits=0
Lean_4.22_original_source_compile=22/24
original_reference_kernel_honest=6/24
endpoint_applicable=0/24 (gate >=20/24)
authored_controls_measured=24/24; matching=24/24
repair_cells_admitted=0/192; judge_member_calls=0/1296
```
