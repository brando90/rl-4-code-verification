# Project line: smooth-to-harsh (Azalia's suggestion)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/SMOOTH_TO_HARSH.md>

**TLDR:** Azalia Mirhoseini's suggestion is that VeriBench's smooth score (SCSC, a geometric mean of factors) should be shown to improve the harsh score (strict pass@1: the all-or-nothing proved-and-compiled outcome), as a reward, a feedback loop or an environment-selection signal, not only as a correlate. Brando made it a named project line on 10-28-2026, run under RL for code verification. Earlier experiments 04, 06, 07, 09, 12, 13, 19 and 20 already touch it; none has yet measured a smooth reward raising held-out harsh pass@1. No new run is admitted until Brando has seen the history below and a plan has passed QA.

Status (11-10-2026 08:45): **first direct test done: Experiment 25, B (smooth reward) minus A (strict reward) = +4.25 points validation strict pass@1 at update 48, 95% interval [+1.05, +7.78], 2 seeds per arm, meets the pre-registered rule (at least +1.5, lower bound above 0), but is seed-fragile.** Per run: A 37.3% and 54.3%, B 49.9% and 50.2% (seed-paired B minus A +12.5 and -4.0; the bootstrap resamples tasks, not seeds; an exact 2-vs-2 permutation over run means gives p=1.0). Both arms rose about +41 to +46 points over the 4.26% start. No smooth-specific gaming signal in the audit. Setup: [Experiment 25](../experiments/25_smooth_vs_strict_reward_grpo_qwen3_1p7b_sft_vbv1_3_d013/README.md), Qwen3-1.7B Lean SFT, `veribench@1.3`, fp16 (bf16 failed the log-prob gate at 6.1% to 6.4%, fp16 0.10%), trained on a skampere1 A100 (the A4000 fit was verified on mercury but training and generation ran on the A100), validation scored on local Lean, test split sealed. Open: a third seed per arm (about 1 day wall) to separate the effect from seed variance; statement coverage of the gold and validation smooth SCSC were not measured. Plan Doc: <https://docs.google.com/document/d/171HnjJrze_FKKEGOVGCL7xMfEd50DVXnMyzbVRC_SFQ/edit>.

## Source of the suggestion

- Her own words: [experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/sources/email_supplied.md](../experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/sources/email_supplied.md): "it'd be very impactful if you could show how these metrics not just correlate with downstream evals, but also can help guide designing better environments, feedback loops for model test time scaling (so performance on downstream evals improve), or as a reward for model fine tuning (e.g. in an RL setup)."
- How the repository turned it into work: [PLAN §11](PLAN.md#11-azalias-actionable-metric-thesis-extension-10-05-2026) and [D-008](DECISIONS.md).
- Her feedback restated in the 10-13-2026 team meeting: [experiments/meetings/oct_13_2026/summary.md](../experiments/meetings/oct_13_2026/summary.md), item 2 (show the decomposition raises the preferred downstream metric, pass@1 or accuracy).
- Brando's 10-28-2026 request (voice note) to track it as a project line: he refers to a later call about VeriBench with her; no written recap of that call is in this repository.

## What already ran (state as of the repository on main, 10-28-2026)

| Exp | Date | Question | State and result |
|---|---|---|---|
| 04 | 10-05 to 10-06 | Does revealing the factors improve repair or training decisions beyond aggregate feedback? | Authored checker controls 24/24 measured and matching; external applicability 0/24 against a 20/24 gate (`unsupported_adapter`); repair and training not admitted |
| 06 | 10-05 to 10-08 | Same question on SWE-bench Lite at matched repair budget | Version 2 finished below the diagnostic and evaluator gates; version 3 blocked (0/16 official controls, 0/8 author calls, 0/56 solver cells) |
| 07 | 10-07 | Does SCS4C track pass@1 across 164 systems, and does partial credit carry signal pass@1 discards? | Phase A done at zero model calls: H1 rho 0.985, H1b rho 0.736, H2 fails (median delta -0.012); phases B and C designed, not admitted |
| 09 | 10-08 | Does a full smooth reward improve GRPO learning, and do named factors help further? (Qwen3-1.7B) | Failed the technical gate (log-probability support and error checks); zero optimizer updates; no learning conclusion |
| 12 | 10-09 to 10-16 | Does SCSC track hidden gold tests? | Done: P1 Spearman 0.8909 [0.7818, 0.9000]; formal specification coverage adds AUC +0.2451 [+0.1049, +0.3596] over mechanical factors |
| 13 | 10-14 to 10-22 | Does a partial-credit or item-weighted reward improve strict pass@1 at matched tokens? | Version 2 stopped at T2 (10-16). Version 3 pilot, last record 10-19: factored arm mean reward about 0.008 to 0.010 after 13 updates, +0.02 gate not met; no conclusion in the repository after 10-22 |
| 19 | 10-20 to 10-21 | Do IRT models of the factors predict held-out harsh success? | Done: calibrated smooth SCSC predicts held-out harsh worse than raw rates (MAE 0.180 versus 0.027) |
| 20 | 10-21 | IRT prompt selection for GRPO, strict versus smooth reward, matched rollouts | Stopped at the trainer gate: 2.62% mismatched tokens against a 1% limit; benefit unmeasured. Experiments 21 to 24 diagnosed the mismatch (fp16/fp16 0.11% against bf16/bf16 6.1%); experiment 23 passes the gate in fp16 (0.065%) |

Reading: the **direct test has not been done**. Experiment 13 version 3 and experiment 20 are the two designs that compare a smooth reward against a strict reward on held-out strict pass@1, and both are blocked or unfinished. The fp16 fix from experiments 22 to 24 removed experiment 20's blocker.

## First-step sketch (not admitted; needs a plan and QA)

1. Read experiment 13 version 3's latest records on SNAP (skampere1) and decide whether to finish it or fold it into experiment 20.
2. Rerun experiment 20's arms in fp16 with the smallest informative comparison: uniform prompts with strict reward versus uniform prompts with smooth reward, same rollouts, Qwen3-1.7B Lean SFT, D-013 validation only, two seeds.
3. Pre-register the primary metric (validation strict pass@1 at the same update, paired task-bootstrap interval) before any rollout, per D-004.
4. Only then consider the IRT-selection arms and the factor-feedback arms.

## Rules that apply

- Public VeriBench version: [CLAUDE.md](../CLAUDE.md), "VeriBench public release".
- Work lands on `main` in the experiment's own folder; no branches (Brando, 10-28-2026).
- Free hardware first; model calls follow D-108.
