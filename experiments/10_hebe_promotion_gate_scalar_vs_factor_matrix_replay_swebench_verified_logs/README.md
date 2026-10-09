# Experiment 10: replaying AlphaHebe's promotion decision with a per-item factor matrix on SWE-bench Verified logs

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md>

**TLDR:** AlphaHebe promotes a candidate harness edit whenever its single held-out score beats the incumbent's (`candidate.score > incumbent.score`). The AlphaApollo team reported that such edits fix some tasks and silently break others. This experiment asks, with **zero model calls**, whether a per-item factor matrix (patch gate, FAIL_TO_PASS fraction, PASS_TO_PASS fraction per task) predicts those regressions better than per-item pass/fail alone, and whether a promotion gate built on it makes fewer harmful promotions. The data is 164 real SWE-bench Verified systems from [experiment 07](../07_scs4c_vs_pass1_swebench_across_models/README.md), treated as incumbent → candidate pairs on random search / held-out task splits. Status: designed, protocol draft under review, not run.

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

## Goal, hypotheses and decision criterion

Units are ordered pairs (incumbent I, candidate C) of included systems, evaluated on random 50/50 splits of the common-cohort tasks into a search half S (what the gate sees) and a held-out half H (the truth).

- **Held-out losses:** the number of held-out tasks resolved by I but not by C.
- **Harmful promotion:** a promoted pair with pass@1_H(C) < pass@1_H(I).

| ID | Question | Prediction (agent-suggested; frozen in PROTOCOL before analysis) | Verdict rule |
|---|---|---|---|
| H1 | How often does AlphaHebe's current scalar gate (promote iff pass@1_S(C) > pass@1_S(I)) make harmful promotions, and how many held-out losses come with a promotion? | Descriptive | Quantifies the reported regression problem on real agent systems |
| H2 | Do factor regressions on S that pass/fail does not see predict held-out losses beyond S's binary losses and gains? Factor regression here means per-item drops in gate, T_fix or T_keep on items that did not flip | Partial Spearman > 0, 95% system-cluster bootstrap interval excluding 0 | Positive: the matrix carries regression signal pass/fail discards. Null: it does not, on SWE-bench tests-only factors |
| H3 | At a matched promotion rate, does a factor-matrix gate make fewer harmful promotions than (a) the scalar gate made stricter by a margin and (b) a binary per-item non-regression gate? | Relative reduction ≥ 20% versus (a), interval excluding 0; versus (b) reported | Positive: implement the factor gate in AlphaHebe (issue) and make it a primary arm of experiment 11 |
| H3b | Does the binary per-item non-regression gate alone beat the stricter scalar gate at matched rate? | Reported | A positive H3b without H3 means "monotone acceptance" helps but factors add nothing |
| H4 | Can factor deltas tell a model change from a harness change? Pairs come from submission metadata: same scaffold with a different base model, or the same base model with a different scaffold | Leave-one-family-out area under the curve (AUC) ≥ 0.65, interval excluding 0.5 | Positive: factor deltas can feed Hebe's model-versus-harness diagnosis. Null: do not build routing on these factors |

**What follows:**

- **H2 and H3 positive:** build the factor gate in AlphaHebe and run experiment 11 with it.
- **H2 positive, H3 null:** the matrix has signal the simple gate does not use. Experiment 11 tests factor *feedback* to the optimizer first.
- **H2 null:** on SWE-bench tests-only factors, per-item pass/fail already captures the regression information. Experiment 11 keeps only the binary per-item gate, and the factor design is revisited with the gold-differential factor D_gold (experiment 07 phase B) or VeriBench's SCSC factors.

## Method (details and exact thresholds live in [PROTOCOL.md](PROTOCOL.md))

1. **Inputs:** `../07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz` (SHA-256 pinned in the protocol): 182 systems × 500 tasks, with `gate`, `t_fix`, `t_keep` and `resolved` per cell.
   - Use the 164 included systems on the 424-task common cohort, exactly as experiment 07 defined them.
   - Phase A2 adds public submission metadata (`metadata.yaml` in `SWE-bench/experiments`, pinned commit) to label model-change and harness-change pairs for H4. Unlabeled pairs are listed, never guessed.
2. **Splits:** 1,000 random 50/50 task splits (seed frozen).
3. **Per pair and split**, compute on S: Δpass@1, binary gains and losses, ΔSCS4C-T, and the factor-regression mass on non-flipped items. On H, compute the outcomes.
4. **Gates:**
   - G0, the current scalar rule;
   - G0+, the scalar rule with a margin set to match each other gate's promotion rate;
   - G1, the aggregate SCS4C-T rule (expected null, given experiment 07 H2);
   - G2, the binary per-item non-regression rule;
   - G3, the factor-matrix rule.
5. **Statistics:** pairs share systems, so intervals resample systems (cluster bootstrap) and task splits. Report `x [lo, hi] p-val=…` per agents-config Hard Rule 11. The pair populations are all ordered pairs, near-tie pairs (|Δpass@1_S| ≤ 0.05), and metadata-labeled edit pairs. All are fixed before analysis.
6. **Phase B (needs the AlphaHebe team):** replay the same gates on real AlphaHebe incumbent/candidate per-task records from their existing GEPA and Meta-Harness runs. Zero new model calls. Admission requires per-task scores for the incumbent and every candidate on both the search and promotion envelopes ([issue](https://github.com/AndrewZhou924/AlphaHebe-dev/issues)).

## Structure

| Path | Content |
|---|---|
| [PROTOCOL.md](PROTOCOL.md) | Draft; locked, with a frozen forecast (`rl4cv.forecast.freeze_forecast`), before any pair statistic is computed |
| [results.md](results.md) | Live results ledger |
| `expt_v1/cc.md` | Agent runbook: build the replay, lock, freeze, run, publish |
| `expt_v1/results/` | Outputs (per-gate tables, pair-level records, bootstrap draws) |
| `reviews/` | Design reviews (GPT-6 Astra ultra, Claude Fable 5.1) and how each point was resolved |

## Dependencies

- Experiment 07 phase A outputs (done 10-07-2026). Only already-published per-cell data is used; no new fetch except the public metadata for H4.
- No model calls, no GPUs, no Valkyrie. This runs on a laptop or SNAP in minutes.
- AlphaHebe semantics are pinned to `AlphaHebe-dev@f89294e`. Phase B depends on records the AlphaHebe team exports.

## Status

DESIGNED (10-09-2026). Protocol draft under GPT-6 Astra (effort ultra) and Claude Fable 5.1 review; not locked; no pair statistic computed.
