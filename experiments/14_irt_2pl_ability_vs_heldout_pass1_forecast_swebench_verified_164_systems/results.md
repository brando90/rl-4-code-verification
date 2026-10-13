# Experiment 14 results: IRT ability versus pass@1 on half A as forecasts of held-out pass@1 (SWE-bench Verified, 164 systems × 424 tasks)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/results.md>

**TLDR:** Not run yet. The single light QA round on draft revision 1 returned FAIL (2 critical, 4 major, 1 minor); all seven findings are fixed in protocol revision 2 and the code, each with a regression test. The lock (forecast freeze) and the real run on `skampere1` are next. No IRT fit or Q1 statistic has been computed on the real matrix.

**Status:** QA FIXED, protocol revision 2 (not locked, not run)

**Last updated:** 10-12-2026 20:57 PDT (worker `ccv-vb-irt-q1-pass1-forecast`, Claude Code `claude-opus-5-5`, effort max, Vals profile)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| Design, protocol draft, code, tests | DONE (draft r1) | [PROTOCOL.md](PROTOCOL.md), `expt_v1/`, `tests/test_e14_irt.py` |
| Pre-lock check: experiment 07 H2 reproduction on the replayed splits | DONE (10-12-2026 15:50 PDT, 10 s on the Mac) | 07's `held_out_prediction` on the replayed stream equals the published H2 block exactly; replayed permutations reproduce median Δ and positive splits at all four sizes (n_A = 50: −0.012139, 92/2000). Cohort 164 × 424 = 69,536 cells, 1 inconsistent cell; graded categories 23,952 / 5,675 / 39,909 (none / partial / resolved) |
| Light QA (one round, Codex GPT-6 Astra, ultra) | DONE (review written 10-12-2026 16:07 PDT; fixes applied 20:38–20:57 PDT) | [review](reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md): `VERDICT: FAIL`, CRITICAL 2, MAJOR 4, MINOR 1. [Resolution](reviews/light_qa_resolution_10-12-2026.md): `VERDICT: FIXED`, 7 fixes with regression tests, no re-review. The review ran on the personal Codex account: Codex-Vals had hit its usage limit and the Stanford account was read-only |
| Lock protocol and freeze forecast | PENDING | `expt_v1/forecasts/` |
| Run on `skampere1` | PENDING | `expt_v1/results/` |

## Deviations

None yet.

**TLDR-end:** [rl4cv: expt14 IRT-vs-held-out-pass@1 forecast (Q1)] The IRT-versus-pass@1 forecast test passed its single light QA round after seven fixes (protocol revision 2); the forecast freeze and the real run on `skampere1` are next.
