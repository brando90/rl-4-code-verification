# Project line: smooth-to-harsh (Azalia's suggestion)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/SMOOTH_TO_HARSH.md>

**TLDR:** Azalia Mirhoseini's suggestion is that VeriBench's smooth score (SCSC, a geometric mean of factors) should be shown to improve the harsh score (strict pass@1: the all-or-nothing proved-and-compiled outcome), as a reward, a feedback loop or an environment-selection signal, not only as a correlate. Brando made it a named project line on 10-28-2026, run under RL for code verification. Earlier experiments 04, 06, 07, 09, 12, 13, 19 and 20 already touch it; none had measured a smooth reward raising held-out harsh pass@1 as of 10-28-2026; Experiment 25 (11-11-2026) then did, and found no reliable gain (see the results summary). No new run is admitted until Brando has seen the history below and a plan has passed QA.

Status (11-11-2026 14:10): **third seed per arm changed the Experiment 25 result: 3 seeds pooled, B (smooth) minus A (strict) = -16.25 points [-19.17, -13.28] at update 48 (task bootstrap), pre-registered rule not met; seed-paired B minus A +12.5, -4.0, -57.2 (B seed 2 stalled at 3.82%, A seed 2 reached 61.06%); run-level permutation p=0.50, so no reliable difference and a smooth-reward failure mode.** Earlier status (11-10-2026 08:45, superseded): **first direct test done: Experiment 25, B (smooth reward) minus A (strict reward) = +4.25 points validation strict pass@1 at update 48, 95% interval [+1.05, +7.78], 2 seeds per arm, meets the pre-registered rule (at least +1.5, lower bound above 0), but is seed-fragile.** Per run: A 37.3% and 54.3%, B 49.9% and 50.2% (seed-paired B minus A +12.5 and -4.0; the bootstrap resamples tasks, not seeds; an exact 2-vs-2 permutation over run means gives p=1.0). Both arms rose about +41 to +46 points over the 4.26% start. No smooth-specific gaming signal in the audit. Setup: [Experiment 25](../experiments/25_smooth_vs_strict_reward_grpo_qwen3_1p7b_sft_vbv1_3_d013/README.md), Qwen3-1.7B Lean SFT, `veribench@1.3`, fp16 (bf16 failed the log-prob gate at 6.1% to 6.4%, fp16 0.10%), trained on a skampere1 A100 (the A4000 fit was verified on mercury but training and generation ran on the A100), validation scored on local Lean, test split sealed. Open: a third seed per arm (about 1 day wall) to separate the effect from seed variance; statement coverage of the gold and validation smooth SCSC were not measured. Plan Doc: <https://docs.google.com/document/d/171HnjJrze_FKKEGOVGCL7xMfEd50DVXnMyzbVRC_SFQ/edit>.

## Results summary for the defense (11-11-2026, AT-3010)

**Google Doc (same content):** <https://docs.google.com/document/d/1f3z_-Ij_uA5e457xmYEVtn27Ww106PsNENnf2FT2ReA/edit>

**Bottom line.** The smooth score (SCSC) ranks systems like outside outcomes do (vs hidden gold tests on VeriBench: Spearman 0.89; vs pass@1 on SWE-bench with a tests-only score: 0.985, partly by construction), but nothing so far shows that training on it, or selecting prompts by it, raises the harsh score (strict pass@1). The only direct test, Exp 25 (Qwen3-1.7B Lean SFT, GRPO, no DT, 3 runs per condition), did not replicate the earlier gain: smooth minus strict is -16.25 points [-19.17, -13.28] at update 48 (that interval resamples tasks only), the run-level permutation p is 0.50, and one smooth run never learned (3.82%). The earlier +4.25 from 2 runs is gone. For the defense, claim "smooth ranks systems like pass@1 and hidden gold tests do" (with the by-construction caveat on Exp 07); do not claim "smooth predicts harsh better than the raw rate" or "smooth reward improves harsh", and do not cite +4.25.

| Exp | Question | Harness and model | Strict (harsh) | Smooth | What it shows |
|---|---|---|---|---|---|
| 04 | Do factor diagnostics improve repair/training? | Checker audit, 0 model calls | Controls 24/24 match | External applicability 0/24 (gate 20/24) | Gate failed; no benefit measured |
| 06 | Same, SWE-bench Lite, matched budget | Claude Code coordinator, skampere2 | Not measured | Not measured | v3 blocked: 0/16 controls, 0/56 solver cells |
| 07 | Does smooth (SCS4C-T) track pass@1 on SWE-bench? | 164 systems, 424 tasks, 0 model calls | pass@1 reference | Spearman 0.985 [0.979, 0.987]; on failed tasks 0.736 [0.507, 0.801] | **Supports** ranking like pass@1, partly by construction (resolved implies both factors equal 1); SWE-bench, tests-only score, not Lean; 50-task forecast no better than pass@1 (median delta -0.012) |
| 09 | Does smooth reward improve GRPO learning? | Qwen3-1.7B, NeMo RL | None completed | None completed | Failed implementation gate; 0 updates; no conclusion |
| 12 | Does SCSC track hidden gold tests? | 11 systems x 896 VeriBench v1 tasks, 0 model calls | Gold tests reference | System Spearman 0.8909 [0.7818, 0.9000]; within-system 0.1445 [0.0497, 0.2290] | **Supports** across systems, weakly within one; spec coverage adds AUC +0.2451 [+0.1049, +0.3596] |
| 13 | Does factored reward beat strict reward? | Qwen3 SFT, NeMo RL, local Lean | Arm A strict: 0/255 positive rewards (T2 batch) | Arm B factored: 21/255 positive (same batch); pilot mean train reward 0.0085 (updates 11 to 13) vs 0.0104 (updates 1 to 10), +0.02 gate not met | **No conclusion**: official factors equal strict on 15 of 15 SFT checkpoints; v3 gate not met (Oct 19); v4 never finished |
| 19 | Do IRT/factor models predict harsh success? | 11 systems, 0 model calls | IRT picks prompts with mixed strict outcomes: AUC 0.862 [0.792, 0.925] (plain panel strict rate 0.852) | System-level forecast MAE, own rate vs smooth: strict target 0.030 vs 0.033 (p=0.67); harsh-SCSC target 0.027 vs 0.180; gold-check 0.034 vs 0.102 | **Does not support**: smooth forecasts no better on strict, worse on harsh-SCSC and gold-check; IRT adds nothing over a simple additive model |
| 20 | IRT prompt selection, strict vs smooth reward | Qwen3-1.7B Lean SFT, GRPO | Calibration AUC 0.9313 [0.9093, 0.9519] | Not measured | Stopped at log-prob gate (2.62% vs 1%); benefit unmeasured |
| 25 | Direct test: smooth vs strict reward on strict pass@1 | train_e25.py, Qwen3-1.7B Lean SFT, skampere1 A100, 135 val tasks, update 48 | A 50.89% [43.55, 57.84]; runs 37.34, 54.26, 61.06 | B 34.64% [28.99, 40.15]; runs 49.86, 50.23, 3.82 | **Does not support**: B minus A -16.25 [-19.17, -13.28]; run-level p=0.50; one B run stalled; earlier +4.25 superseded |

All rows are no DT. Strict (harsh) = strict pass@1 (all-or-nothing proved and compiled). Smooth = SCSC, geometric mean of tests correctness, proof correctness and formal specification coverage; SCS4C-T is the tests-only SWE-bench version. In Exp 25 the smooth reward B is a local training proxy (geometric mean of per-declaration factors), not official SCSC. A = strict reward, B = smooth reward; a run is one training run with one seed.

**Supports a defense claim:** smooth ranks systems like hidden gold tests do on VeriBench (Exp 12) and like pass@1 on SWE-bench (Exp 07, partly by construction, tests-only score); spec coverage adds signal (Exp 12). **Does not support:** a smooth reward improving harsh pass@1 (Exp 25), smooth forecasts beating the raw strict rate (Exp 19: no better on strict, worse on harsh-SCSC and gold-check), factor feedback improving repair (Exp 04, 06, 09, 13, 20: gates failed, nothing measured). **Open, paused:** a fourth Exp 25 run and a stall check were cancelled when RL was paused until after Dec 10; Azalia's idea stays open, later if at all (Brando, 11-11-2026).

**Caveats.** Exp 25 intervals resample the 135 validation tasks with six trained models held fixed, so they are not seed-level tests; with 3 runs per condition the exact permutation p cannot go below 0.10. Seed 2 of both conditions resumed from update 8 after a skampere1 reboot; the resume path was not tested. Exp 25 seeds 0 and 1 alone: +4.25 [+1.05, +7.78], seed-fragile (+12.5 and -4.0). Exp 13 v3 and Exp 06 v3 are last records (Oct 19, Oct 8), not final results. Sources: the results.md or README.md of experiments 04, 06, 07, 09, 12 (expt_v2/RESULTS_analysis_v2.md), 13 (expt_v3/results.md, expt_v4/CKPT_v4_implementation.md), 19, 20, 25. Not checked: raw run data (nothing was rerun); no second-model cross-check was run.

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

Reading (as of 10-28-2026, superseded by Experiment 25 and the results summary above): the direct test had not been done. Experiment 13 version 3 and experiment 20 were the two designs that compare a smooth reward against a strict reward on held-out strict pass@1, and both were blocked or unfinished. The fp16 fix from experiments 22 to 24 removed experiment 20's blocker.

## First-step sketch (not admitted; needs a plan and QA)

1. Read experiment 13 version 3's latest records on SNAP (skampere1) and decide whether to finish it or fold it into experiment 20.
2. Rerun experiment 20's arms in fp16 with the smallest informative comparison: uniform prompts with strict reward versus uniform prompts with smooth reward, same rollouts, Qwen3-1.7B Lean SFT, D-013 validation only, two seeds.
3. Pre-register the primary metric (validation strict pass@1 at the same update, paired task-bootstrap interval) before any rollout, per D-004.
4. Only then consider the IRT-selection arms and the factor-feedback arms.

## Rules that apply

- Public VeriBench version: [CLAUDE.md](../CLAUDE.md), "VeriBench public release".
- Work lands on `main` in the experiment's own folder; no branches (Brando, 10-28-2026).
- Free hardware first; model calls follow D-108.
