# Retained artifact feasibility audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v1/results/RESULTS_existing_artifacts.md>

**TLDR:** The frozen factor snapshot has no independently measured fixed-reference pass@1 endpoint. Historical adapter and proof-replay labels are available, but do not establish strict kernel correctness or an intervention effect.

Audit host: `skampere1.stanford.edu`. Source snapshot time: `2026-09-29T16:29:29.684354+00:00` (machine timestamp).

Saved rows: 5420; complete factor rows: 4444. These are finite-file counts; intervals and p-val=n/a.

Original V1 snapshot coverage: 5376/6272 declared cells; 896 absent. This is snapshot coverage, not a claim that live jobs were unattempted.

SCSC means Smooth Conjunctive Score for Code verification. Core and IndustrySet panels are separate. Other conditions have saved-row counts only; this audit has not independently reconstructed their declared task manifests.

| Benchmark / panel | Condition | Model | Saved / declared original | All factors | Known zero artifact product | Supplied SCSC |
|---|---|---|---:|---:|---:|---:|
| multifile_E97P001 | expt103-single-call-multifile-v1 | claude-opus-5-max | 1 / not reconstructed | 0 | 0 | 0 |
| multifile_E97P001 | expt103-single-call-multifile-v1 | gemini-3.1-pro-high | 1 / not reconstructed | 1 | 1 | 1 |
| multifile_E97P001 | expt103-single-call-multifile-v1 | gpt-5.6-luna-high | 1 / not reconstructed | 1 | 1 | 1 |
| multifile_E97P001 | expt103-single-call-multifile-v1 | gpt-5.6-sol-high | 1 / not reconstructed | 1 | 1 | 1 |
| multifile_E97P001 | expt103-single-call-multifile-v1 | gpt-6-astra-high | 1 / not reconstructed | 1 | 1 | 1 |
| multifile_E97P001 | expt103-single-call-multifile-v1 | gpt-6-luna-high | 1 / not reconstructed | 1 | 1 | 1 |
| multifile_E97P001 | expt103-single-call-multifile-v1 | qwen3.6-27b-thinking | 1 / not reconstructed | 1 | 1 | 1 |
| core_614 | expt103-single-call-vbv1-v1 | claude-opus-5-max | 0 / 614 | 0 | 0 | 0 |
| industry_282 | expt103-single-call-vbv1-v1 | claude-opus-5-max | 0 / 282 | 0 | 0 | 0 |
| core_614 | expt103-single-call-vbv1-v1 | gemini-3.1-pro-high | 614 / 614 | 611 | 574 | 611 |
| industry_282 | expt103-single-call-vbv1-v1 | gemini-3.1-pro-high | 282 / 282 | 278 | 265 | 278 |
| core_614 | expt103-single-call-vbv1-v1 | gpt-5.6-luna-high | 614 / 614 | 612 | 476 | 612 |
| industry_282 | expt103-single-call-vbv1-v1 | gpt-5.6-luna-high | 282 / 282 | 278 | 269 | 278 |
| core_614 | expt103-single-call-vbv1-v1 | gpt-5.6-sol-high | 614 / 614 | 614 | 313 | 614 |
| industry_282 | expt103-single-call-vbv1-v1 | gpt-5.6-sol-high | 282 / 282 | 275 | 231 | 275 |
| core_614 | expt103-single-call-vbv1-v1 | gpt-6-astra-high | 614 / 614 | 592 | 227 | 592 |
| industry_282 | expt103-single-call-vbv1-v1 | gpt-6-astra-high | 282 / 282 | 263 | 180 | 263 |
| core_614 | expt103-single-call-vbv1-v1 | gpt-6-luna-high | 614 / 614 | 611 | 488 | 611 |
| industry_282 | expt103-single-call-vbv1-v1 | gpt-6-luna-high | 282 / 282 | 277 | 273 | 277 |
| core_614 | expt103-single-call-vbv1-v1 | qwen3.6-27b-thinking | 614 / 614 | 0 | 0 | 0 |
| industry_282 | expt103-single-call-vbv1-v1 | qwen3.6-27b-thinking | 282 / 282 | 0 | 0 | 0 |
| vbv2_full_source | expt103-single-call-vbv2-recovery_1 | gemini-3.1-pro-high | 1 / not reconstructed | 1 | 1 | 1 |
| vbv2_full_source | expt103-single-call-vbv2-recovery_1 | gpt-6-astra-high | 1 / not reconstructed | 1 | 1 | 1 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | claude-opus-5-max | 5 / not reconstructed | 0 | 0 | 0 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | gemini-3.1-pro-high | 5 / not reconstructed | 4 | 4 | 4 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | gpt-5.6-luna-high | 5 / not reconstructed | 5 | 5 | 5 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | gpt-5.6-sol-high | 5 / not reconstructed | 5 | 5 | 5 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | gpt-6-astra-high | 5 / not reconstructed | 4 | 4 | 4 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | gpt-6-luna-high | 5 / not reconstructed | 5 | 4 | 5 |
| vbv2_full_source | expt103-single-call-vbv2-v1 | qwen3.6-27b-thinking | 5 / not reconstructed | 2 | 2 | 2 |

## Historical adapter and replay inventory

All labels below are historical ordinary Lean outcomes. No proof was rerun, and transitive axiom trust was not revalidated.

Adapter rows: 3112; recorded labels: `{"failed": 598, "found": 1061, "name_only": 776, "type_mismatch": 677}`.

Replay pair rows: 3112; recorded decisions: `{"all_proved": 1496, "undecided": 1616}`.

## Decision and limitations

**Independent-outcome correlation: NOT IDENTIFIABLE from these inputs.** The audit found no fields for the specified reference-test or strict reference-obligation outcomes. This is a schema/construct conclusion, not a negative correlation result.

The V1 task list is represented by a hash in the upstream manifest, not copied here as a reconstructed full task manifest. Missing counts are reconciled at model/panel level. Recovery and multifile conditions remain separate. A valid zero factor identifies a zero per-artifact product even when another factor is absent; it does not supply the missing factor or a complete official aggregate.

The frozen inputs already existed and selected prior outcomes were known when this audit was designed. No prospective prediction, intervention gain, population estimate or proof certificate is claimed. Statistical intervals, repeated-run variation and hypothesis-test p-values are unavailable/not applicable to this descriptive inventory.

**[p 9/10] Validate fixed-reference endpoints on screened external tasks**, because trusted independent outcomes are missing; then freeze a cost-matched component-versus-scalar feedback comparison.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] Retained inputs support an availability audit, not a new correctness correlation. Endpoint validation is the next dependency.

**Snapshot:**
```text
saved_rows=5420
complete_factor_rows=4444
v1_snapshot_cells=5376/6272
independent_reference_outcome=unavailable
new_model_calls=0
```
