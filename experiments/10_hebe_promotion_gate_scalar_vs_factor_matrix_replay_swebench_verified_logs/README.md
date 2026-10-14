# Experiment 10: replaying AlphaHebe's promotion decision with a per-item factor matrix on SWE-bench Verified logs

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md>

**TLDR:** AlphaHebe promotes a candidate harness edit whenever its single held-out score beats the incumbent's (`candidate.score > incumbent.score`). The AlphaApollo team reported that such edits fix some tasks and silently break others. This experiment asks, with **zero model calls**, whether a per-item factor matrix (patch gate, FAIL_TO_PASS fraction, PASS_TO_PASS fraction per task) predicts those regressions better than per-item pass/fail alone, and whether a promotion gate built on it makes fewer harmful promotions. The data is 164 real SWE-bench Verified systems from [experiment 07](../07_scs4c_vs_pass1_swebench_across_models/README.md), treated as incumbent → candidate pairs on random search / held-out task splits. Status: protocol revision 3 LOCKED (commit `55d1c53`, 10-09-2026); phase A primary replay DONE 10-14-2026 with **no gate recommendation** under the frozen rules (C_fac and C_bin intervals include 0; C_fac0 = 0.0210 [0.0017, 0.0403] excludes it), see [results.md](results.md).

Created: 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando. Owner: Brando; AlphaHebe-side records (phase B) come from the AlphaHebe team. Companion live study: [experiment 11](../11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md).

## Origin

- **10-08-2026 meeting with the AlphaApollo / AlphaDiana / AlphaHebe team** ([verbatim record](../meetings/oct_7_2026/oct_7_2026.md), [whiteboard description](../meetings/oct_7_2026/self_improving_with_factored_decomposed_smooth_metric_meeting_pic.md)).
  - A team member deploying Hebe reported: "some questions are improvement. They can solve these questions, and some questions that previously can be solved is wrong."
  - Brando proposed using the task × factor matrix to see "what is going on per data point, per feature", and accepting an edit only if it does not make items go down ("you only accept things like … it always monotonically improve").
- **Brando, 10-09-2026:** "create experiment folders based on the meeting … and see if the SCSC type factorized matrix per item can guide alpha-hebe diana apollo system to self improve."
- **What AlphaHebe does today** (checked at `AndrewZhou924/AlphaHebe-dev` commit `f89294e`, 09-18-2026):
  - `alphahebe/control/promotion.py::gate_decision` promotes iff `candidate.score > incumbent.score` on the independent promotion envelope.
  - `alphahebe/integrations/diana/search_feedback.py::TrainingFeedback` gives optimizers only `{per_task: mean score, traces}`.
  - There is no per-item or per-factor check anywhere in promotion.

## Why this test first (the consequential uncertainty)

The live loop (experiment 11) needs private repositories we cannot yet read (AlphaDiana-dev, AlphaApollo-v3-dev), new scorer fields, GPUs or Valkyrie, and a working SWE-bench or VeriBench harness. Experiments [06](../06_swebench_lite_factor_feedback_matched_budget/README.md) and [09](../09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/README.md) both stalled on exactly that kind of infrastructure.

The assumption whose failure would sink the whole idea is that **the per-item factor matrix carries decision-relevant information that the scalar score and per-item pass/fail do not**. That can be tested now on 164 × 424 measured cells that already exist.

Prior evidence that shapes the predictions:

- Experiment 07 H2 found that an *aggregate* smooth score (SCS4C-T) on a task subset does **not** rank systems better than pass@1 on held-out tasks (median Δ −0.012 at 50 tasks).
- So this experiment does not expect an aggregate smooth gate to help. Its question is about the **per-item structure**: partial regressions on items that did not flip, such as a candidate that now breaks previously passing PASS_TO_PASS tests on a still-unresolved task.

## Goal, hypotheses and decision criterion (summary of [PROTOCOL.md](PROTOCOL.md) revision 3)

**Setup.** Units are ordered pairs (incumbent I, candidate C) of included systems. Each of 1,000 random task splits gives:

- a **validation** half V (212 tasks), which a promotion policy sees, mirroring AlphaHebe's promotion envelope;
- a **test** half E (212 tasks), which is the outcome.

**Scope.** Public system pairs leave out candidate generation and search, so this is a screening study of promotion rules, not of live edits.

**Primary population.** Pairs with a small validation gain (net 1–10 tasks of 212), where real edits live.

| ID | Question | Status in the protocol |
|---|---|---|
| H1 | How often does the scalar rule make a harmful promotion (test pass@1 lower), and with how many test losses? | Descriptive |
| H2 | Do hidden factor regressions (partial drops on jointly unresolved tasks) predict test losses beyond binary losses and gains? | Descriptive association only. On synthetic data it was positive even without any regression mechanism, because factor values also sharpen the ability estimate |
| H3 (primary) | At equal validation gain, does per-item information pick safer promotions? Gain-stratified, matched-rate policies: R0 (scalar only), R2 (fewest binary losses), R3 (lowest factor-regression mass), R3h (hidden regressions only) | Contrasts C_bin = R0 − R2, C_fac = R2 − R3, C_fac0 = R0 − R3, with a utility guard on the test gain kept |

**Verdict rules.**

- **Factor gate:** recommend it for AlphaHebe, and make it a primary arm of experiment 11, only if C_fac and C_fac0 are both positive with intervals excluding 0 and the utility guard passes.
- **Binary non-regression gate:** otherwise, recommend it if C_bin is positive with its interval excluding 0 and the guard passes.
- **Otherwise:** no recommendation ("superiority or retained utility not established", with reason codes). This is not evidence that per-item information has no value.
- **Deferred:** the earlier model-versus-harness hypothesis (organization tags do not identify interventions).

## Method

1. **Inputs:** experiment 07's per-cell factors (SHA-256 pinned), 164 included systems × 424 common-cohort tasks, with derived gated factors (g, g·t_fix, g·t_keep). The sensitivity analysis drops the 4 tasks with test-list drift (66 cells).
2. **Splits and populations:** 1,000 splits (seed `20261009`), near-gain population primary, all positive-gain pairs secondary. The secondary population gets point estimates and split ranges only.
3. **Policies:** the five gain-stratified policies (R0, R1, R2, R3, R3h) plus four unstratified comparators (S0+ "just be stricter", S1, S2, S3) at q = 0.5 (0.25 and 0.75 as sensitivities). All are matched by retained weight, with ties broken by an outcome-independent hash.
4. **Statistics:** a dyadic system bootstrap (1,000 draws, pair weight = the product of the two systems' resample counts) over the same splits. Families share a common split support with draw invalidation and a 90% support floor. Undefined denominators stay undefined. Estimates are reported as `x [lo, hi] p-val=n/a`.
5. **Phase B (needs the AlphaHebe team, [issue #30](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/30)):** replay the policies on real AlphaHebe incumbent/candidate records. Promotion outcomes that made a decision cannot also measure its later harm, so untouched tasks or a prospective decision/test partition are required.

## Structure

| Path | Content |
|---|---|
| [PROTOCOL.md](PROTOCOL.md) | LOCKED, revision 3 (commit `55d1c53`), with the forecast frozen by `rl4cv.forecast.freeze_forecast` (`expt_v1/forecasts/e10_forecast.json`, SHA-256 `e4eccd8b…3c23`) before any pair statistic was computed |
| [results.md](results.md) | Live results ledger |
| [`expt_v1/cc.md`](expt_v1/cc.md) | Agent runbook: verify the lock, run the primary and sensitivity replays, score the frozen predictions, publish |
| `expt_v1/results/` | Outputs (per-gate tables, pair-level records, bootstrap draws) |
| `reviews/` | Design reviews (GPT-6 Astra ultra, Claude Fable 5.1) and how each point was resolved |

## Dependencies

- Experiment 07 phase A outputs (done 10-07-2026). Only already-published per-cell data is used; no new fetch except the public metadata for H4.
- No model calls, no GPUs, no Valkyrie. This runs on a laptop or SNAP in minutes.
- AlphaHebe semantics are pinned to `AlphaHebe-dev@f89294e`. Phase B depends on records the AlphaHebe team exports.

## Status

PHASE A PRIMARY DONE; SENSITIVITY BLOCKED; PHASE B WAITING (10-14-2026).

- **10-09-2026:** protocol revision 3 LOCKED (commit `55d1c53`, 16:43 PDT) after two GPT-6 Astra (effort ultra) reviews; forecast frozen with `rl4cv.forecast.freeze_forecast` (`expt_v1/forecasts/e10_forecast.json`, SHA-256 `e4eccd8b…3c23`). Claude Fable 5.1 review unavailable (no credits on any account; none bought).
- **10-14-2026, phase A primary DONE** (skampere1, tmux `rl4cv-e10-phase-a-10-14`, 13:02–13:04:56 PDT, zero model calls; lock re-verified first: `verify_forecast` True, all pins match, 15/15 tests on the host). 164 × 424 reproduced; 1,000 splits (0 degenerate) × 1,000 dyadic system-bootstrap draws; median 2,382 near-gain pairs per split. Scored as frozen ([results.md](results.md)): H1 scalar-rule harmful promotion rate 0.2580 [0.2410, 0.2821] p-val=n/a; H2a 0.1265 [0.0840, 0.1675] p-val=n/a, supported but descriptive (null-sized); H3 **no recommendation** (`interval_includes_zero`): C_fac = R2 − R3 0.0046 [−0.0027, 0.0117], C_bin = R0 − R2 0.0163 [−0.0014, 0.0355], C_fac0 = R0 − R3 0.0210 [0.0017, 0.0403], all utility guards pass; "just be stricter" S0+ is safer than R3 by 0.0652 [0.0443, 0.0838] at the same rate. The factor-feedback question moves to experiment 11 without a gate claim.
- **10-14-2026, matched-test-lists sensitivity BLOCKED** by the protocol's own shape stop rule (`STOP: expected (164, 420), got (164, 421)`: `django__django-10097` is outside the 424-task cohort). Needs a dated amendment or `expt_v2`; Brando decides.
- **Phase B:** WAITING on the AlphaHebe team's record export.
