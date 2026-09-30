# Experiment 02D — train the forecast-selected Lean environment and reward, report VeriBench V1 (the application)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_d_train_forecast_selected_env_report_vbv1/README.md>

**Part of:** [experiment 02](../README.md) (ρ–H-guided Lean environment design), phase D; the planned experiment 06 ("solve VeriBench") before D-007

**TLDR:** Train on the Lean environment and reward that the frozen ρ–H equation ranks best (from phases 02B and 02C), at the largest affordable scale. Report IC_tests, IC_proofs, FSC, SCSC and n on VeriBench V1, with core 614 and IndustrySet 282 separately. VeriBench stays held out: never trained on, warm-started on or used to select checkpoints. This phase is designed after 02B and 02C.

## From the plan

- **Question** ([PLAN §6](../../../docs/PLAN.md#6-experiments-and-gates), formerly row 06): train the predicted-best family, reward and mixture at the largest affordable scale. A mixture applies only if the deferred [cross-family mixtures idea](../../ideas/cross_family_env_mixtures_alignment/README.md) is revived.
- **Outcome:** VeriBench SCSC and FSC gains, with a regression panel for unintended effects (meeting notes B).
- **Target level** ([PLAN §3](../../../docs/PLAN.md#3-hypotheses-what-counts-as-the-law-generalizes)): the predicted-best recipe improves VeriBench. SCSC and compile-gated FSC are above π0 at every trained scale, and all three factors are reported with n.
- **Reporting** ([CLAUDE.md](../../../CLAUDE.md)): SCSC with IC_tests, IC_proofs, FSC and n; unmeasured cells stay in the denominator; FSC only from the D-102 judge and compile-gated (D-003).

## Status

| Step | Status |
|---|---|
| Design, `PROTOCOL.md` | TODO, after 02B and 02C |
