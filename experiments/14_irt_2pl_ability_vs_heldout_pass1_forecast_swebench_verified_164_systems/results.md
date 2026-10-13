# Experiment 14 results: IRT ability versus pass@1 on half A as forecasts of held-out pass@1 (SWE-bench Verified, 164 systems × 424 tasks)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/results.md>

**TLDR:** Not run yet. The single light QA round on draft revision 1 returned FAIL (2 critical, 4 major, 1 minor); all seven findings are fixed in protocol revision 2 and the code, each with a regression test. Protocol revision 2 is locked (forecast SHA-256 `33de7cd2…6890`, 10-12-2026 21:54 PDT); the real run on `skampere1` is next. No IRT fit or Q1 statistic has been computed on the real matrix.

**Status:** LOCKED (revision 2); run pending on `skampere1`

**Last updated:** 10-12-2026 21:54 PDT (worker `ccv-vb-irt-q1-pass1-forecast`, Claude Code `claude-opus-5-5`, effort max, Vals profile)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| Design, protocol draft, code, tests | DONE (draft r1) | [PROTOCOL.md](PROTOCOL.md), `expt_v1/`, `tests/test_e14_irt.py` |
| Pre-lock check: experiment 07 H2 reproduction on the replayed splits | DONE (10-12-2026 15:50 PDT, 10 s on the Mac) | 07's `held_out_prediction` on the replayed stream equals the published H2 block exactly; replayed permutations reproduce median Δ and positive splits at all four sizes (n_A = 50: −0.012139, 92/2000). Cohort 164 × 424 = 69,536 cells, 1 inconsistent cell; graded categories 23,952 / 5,675 / 39,909 (none / partial / resolved) |
| Light QA (one round, Codex GPT-6 Astra, ultra) | DONE (review written 10-12-2026 16:07 PDT; fixes applied 20:38–20:57 PDT) | [review](reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md): `VERDICT: FAIL`, CRITICAL 2, MAJOR 4, MINOR 1. [Resolution](reviews/light_qa_resolution_10-12-2026.md): `VERDICT: FIXED`, 7 fixes with regression tests, no re-review. The review ran on the personal Codex account: Codex-Vals had hit its usage limit and the Stanford account was read-only |
| Lock protocol and freeze forecast | DONE (10-12-2026 21:54:40 PDT) | `expt_v1/forecasts/e14_forecast.json` SHA-256 `33de7cd2268f60ed4d4d828d6eec7f5c5b79a9ce457cc8da881f5d54dc706890` (`verify_forecast` True; ledger `git_head` `c15fcb0`); 21 predictions |
| Run on `skampere1` | PENDING | `expt_v1/results/` |

## Deviations

None yet.

**TLDR-end:** [rl4cv: expt14 IRT-vs-held-out-pass@1 forecast (Q1)] The IRT-versus-pass@1 forecast test passed its single light QA round after seven fixes (protocol revision 2); the forecast freeze and the real run on `skampere1` are next.
