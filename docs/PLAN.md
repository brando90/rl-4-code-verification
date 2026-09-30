# Plan: do environment-utility laws generalize to RL for Lean code verification?

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/PLAN.md>

**TLDR:** The crux is whether the ρ–H law carries over from math to Lean 4 code verification, with VeriBench as the target. The ρ–H law predicts an RL environment's held-out gain from two measurements taken before RL, usable signal density ρ and effective coverage H. The work runs in six gated experiments:

1. Measure small open models on VeriBench.
2. Build Lean environment pools and probe ρ and H.
3. Replicate the paper's prospective 2×2 scale test in Lean.
4. Test judge-gated FSC reward channels.
5. Test mixtures and alignment.
6. Train the best predicted recipe to "solve VeriBench".

Each experiment has a pass/fail gate before the next one spends compute.

## 1. The question

The ICLR 2027 submission (Varun and Brando) shows that, in math, the utility of an RL prompt distribution can be predicted before RL. It measures, under the starting policy, how much group-relative signal survives the loss (usable signal density ρ) and how broadly that signal is spread over prompts (effective coverage H). A five-coefficient model fit on 1.7B–8B then predicted untouched 14B utility curves with 2.29-point RMSE.

Meeting notes B record the reviewers' likely objection: a math-only paper is not novel enough. They also record the stated goal: "show predictive relationship translates across domains".
Meeting notes A add the target: find the RL environment that most improves VeriBench, and (Azalea) show that VeriBench's metrics guide environment and reward design.

**Crux:** does the same pre-RL measurement predict held-out RL utility in a structurally different domain? Lean 4 verified code generation differs from math in three ways:

- the verifier is the Lean kernel;
- responses are long structured files;
- the target metric (VeriBench SCSC) is conjunctive, and one of its factors (FSC, formal specification coverage) is judged by an LLM.

A clean "no" is also a result: it marks where the law stops working, just as the paper's 8B miss and uniform-mixture failure did.

## 2. What the paper established, and what this repository already reproduces

- **Definitions.** U(E, N, C) is the held-out pass@1 change from each scale's warm start at generated-action-token budget C. ρ and H follow paper Eqs. 2–6. Û follows Eq. 7. All are implemented in [`src/rl4cv/`](../src/rl4cv/).
- **Paper evidence.**
  - Choosing the environment moves held-out utility by up to 11.4 points (4B).
  - The first 8B forecast failed: it picked the best cell 0 of 3 times and its intervals covered 0 of 12 means.
  - The revised model was frozen and scored on 14B: RMSE 2.29, rank accuracy 77.8%, regret 0.288.
  - Leave-one-scale-out (LOSO) RMSE 2.09.
- **Paper limits.**
  - One domain, and a held-out panel from the same source as training.
  - Simple rules (fixed HL cell, success/mixedness crossover) match or beat the model on allocation regret.
  - A frozen uniform mixture was predicted last but observed at +1.4 to +4.6 points, so mixture composition is a missing coordinate.
- **Reproduced here.** Running the paper's frozen 14B coefficients through our implementation on its Table 5 and Table 4 values reproduces RMSE 2.291, rank accuracy 14/18 = 77.8% and regret 0.287 points. Our Table 5 standardizers match the paper's to within 2×10⁻⁴. See `tests/test_utility_model.py`.

## 3. Hypotheses: what counts as "the law generalizes"

The numeric thresholds are locked in each experiment's `PROTOCOL.md` before its runs. These are the proposed levels.

| Level | Claim | Proposed pass criterion | Tested in |
|---|---|---|---|
| L1 Existence | Environment choice changes held-out Lean utility at matched token budget | Best-to-worst cell spread at the largest shared budget exceeds the two-seed endpoint gap at ≥ 2 of 4 scales (paper spreads: 3.7–11.4 points) | 03 |
| L2 Form transfer (primary) | The Eq. 7 family, refit on Lean at small scales and frozen, predicts untouched larger-scale Lean curves | At the frozen 14B test: RMSE below the budget/scale-only baseline, pairwise rank accuracy ≥ 70% (paper 77.8%), regret ≤ the fixed-label rule; the 8B test is scored and reported whatever its outcome | 03 |
| L3 Coefficient transfer (exploratory) | The paper's math-fit coefficients, applied to Lean ρ and H, still rank Lean cells | Rank accuracy > 50% with a bootstrap interval that excludes 50% | 03 |
| L4 Reward-channel transfer | ρ and H measured under a judge-gated reward (`fsc_compiled`, `scsc`) predict utility as well as under the kernel reward | Rank accuracy within 10 points of the kernel channel's | 04 |
| L5 Target transfer | Cell effects on the within-source panel carry to VeriBench | Correlation of cell effects > 0.5 (paper, OpenR1 against Polaris: 0.991) | 03 |
| Target | The predicted-best recipe improves VeriBench | SCSC and compile-gated FSC above π0 at every trained scale, all three factors reported with n | 03, 06 |

## 4. Environment families and reward channels

An environment is a prompt distribution under a fixed rollout, verifier and loss contract (paper §1).

| Family | The policy writes | Where prompts come from ([DATASETS.md](DATASETS.md)) |
|---|---|---|
| `full` | The whole VeriBench-format Lean file from a Python program: implementation, `example` tests, specifications, proved theorems | FVAPPS-derived; synthetic VeriBench-style |
| `impl` | Implementation plus `example` tests only | derived from `full` pools |
| `spec` | Theorem statements (and proofs) for a given implementation | derived from `full` pools |
| `proof` | A verified implementation for a given specification | Vericoding Lean subset |
| `math` | Math answers (the paper's own cells) | paper archive |

Reward channels (definitions in [`src/rl4cv/rewards.py`](../src/rl4cv/rewards.py)). Every channel uses VeriBench's kernel rule: a theorem counts as proved only if its axioms are within {`propext`, `Classical.choice`, `Quot.sound`}.

| Channel | Value | Needs a judge |
|---|---|---|
| `kernel_binary` | 1 if the file typechecks, has ≥1 `example`, every stated theorem is kernel-proved and none is vacuous | no |
| `proof_fraction` | IC_tests × IC_proofs, 0 if any theorem is vacuous | no |
| `fsc_compiled` | FSC, paid only when IC_tests = 1 and nothing is vacuous | only for compiling files |
| `scsc` | (IC_tests · IC_proofs · FSC)^(1/3), 0 if vacuous | only when IC_tests · IC_proofs > 0 |
| `fsc` (diagnostic only) | ungated FSC; pays for non-compiling text ([FACTS §3](FACTS_veribench_baselines.md#3-the-fsc-judge)) | yes |

## 5. Held-out outcomes

| Panel | Size | Outcome | Role |
|---|---|---|---|
| Within-source panel (hash-disjoint from all training cells, same pool) | 1,000 | `kernel_binary` pass@1 (and `scsc` where references exist) | Primary for L1–L3; mirrors the paper's OpenR1 panel |
| VeriBench V1 | 896 (core 614 + IndustrySet 282, reported separately) | SCSC with IC_tests, IC_proofs, FSC and n | Target; L5 |
| VERINA | 189 | kernel pass@1 | Optional cross-source panel |

- **Per-checkpoint VeriBench curves** use IC_tests, IC_proofs and exact SCSC. The judge is called only where IC_tests · IC_proofs > 0, because SCSC is exactly 0 elsewhere.
- **Endpoints** (the step-128 policies) get full FSC on every non-empty file, since a valid VeriBench table reports all three factors.
- **Cost at endpoints:** about 896 × $0.40 ≈ $360 per fully judged policy ([FACTS §3](FACTS_veribench_baselines.md#3-the-fsc-judge)).

## 6. Experiments and gates

| # | Experiment | Question | Gate to continue | Status |
|---|---|---|---|---|
| 01 | [Small open models on VeriBench V1, single call](../experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md) | Where do Qwen3.5 (0.8B–9B) and Qwen3 (1.7B–14B) stand, and is there any group-relative signal (G = 8) on VeriBench itself? | Table published for every model, with the full 896-cell denominator. If `kernel_binary` mixed-group share is < 0.05 for every model ≤ 14B, VeriBench cannot be the training environment at these scales; experiment 02 then needs decomposed families and a Lean warm start. | ready to run once D-101 is decided |
| 02 | [Lean environment pools, warm start and ρ–H probes](../experiments/02_lean_environment_pools_warm_start_rho_h_probes/README.md) | Can policy-relative 2×2 cells be built in Lean at each scale, and what are their ρ and H? (the Lean analogue of paper Table 5) | At least one family where all four cells have ρ > 0 at every scale, fresh confirmation success spread ≤ 3 points, and admission contrast ≥ 15 points | designed |
| 03 | [Lean 2×2 prospective scale replication](../experiments/03_lean_2x2_prospective_scale_replication/README.md) | L1, L2, L3 and L5: the crux | Frozen and hashed 8B and 14B forecasts, scored | designed |
| 04 | [Reward-channel generalization: kernel versus judge-gated FSC](../experiments/04_reward_channel_generalization_kernel_vs_fsc/README.md) | L4, and Azalea's reward-design question | Rank agreement across channels | designed |
| 05 | [Cross-family composition and alignment](../experiments/05_cross_family_composition_alignment/README.md) | Can adding alignment and composition coordinates fix the paper's mixture failure? | Frozen mixture forecast beats the uniform-portfolio rule | designed |
| 06 | Solve VeriBench (application) | Train the predicted-best family, reward and mixture at the largest affordable scale | VeriBench SCSC and FSC gains with a regression panel for unintended effects (meeting notes B) | after 03–05 |
| 07 | [Coverage gating: zero-signal bucket × reward density](../experiments/07_coverage_gating_zero_signal_bucket_reward_density/README.md) | Does outcome RL move prompts the warm start never solves (`q_mixed = 0`), and do per-theorem credit or compiler feedback move them where the binary reward cannot? (the notes' §2 claim, tested) | Frozen pre-RL ρ per arm on `Z`; gate H3-A/B/C verdicts and the `Z` re-probe | designed; after 02 |

## 7. Compute (order of magnitude; each protocol refines it with measured lengths)

- **01.** A few GPU-hours per model on one 80 GB GPU for 896 tasks at G = 1, plus a 128-task G = 8 probe. Kernel scoring runs at about 3–14 tasks per minute per scorer (experiment 103), so 1–5 CPU-hours per 896-file job. The judge is only needed where IC > 0 (D-102).
- **02, per scale.**
  - Probe volume, following the paper's Appendix A:
    - Stage A: 4,000 prompts × 8 = 32,000 responses.
    - Stages B and C: up to 2,560 prompts × 8 × 2 = 40,960 responses.
    - Stage D: 8,192 responses.
    - About 81,000 responses in all.
  - At 6–10k tokens each that is 0.5–0.8B generated tokens.
  - Lean checking at about 25 s per file is about 560 CPU-hours, so it needs a persistent Lean server or a wide CPU pool.
  - The Lean warm start (supervised fine-tuning, SFT) repeats the paper's 512-step recipe at each scale.
- **03.**
  - The paper used about 350 B200 GPU-hours for 32 trajectories. Longer Lean responses suggest 500–700 B200 GPU-hours.
  - Evaluation adds 49 policies per scale × (1,000 + 896) generations and their verification.
- **04–05.** Each condition is about one scale-pair of 03, at 1.7B and 4B.

## 8. Integrity rules (enforced in [CLAUDE.md](../CLAUDE.md))

- **Data.** No VeriBench task, reference or derived text is ever used for training or the warm start. Screens are in [DATASETS.md](DATASETS.md).
- **Scoring.**
  - The kernel check is VeriBench's own, from the pinned scorer, and is never loosened.
  - FSC is compile-gated (D-003).
  - Prompts follow VeriBench's prove-first contract: `sorry` is an honest last resort that earns zero, never a template.
- **Forecasts.** Every forecast is frozen and hashed before its outcomes are read (D-004). The 8B test is reported even if it fails.
- **Evaluations.** Each evaluation declares its full cell manifest; every cell has a receipt; missing cells stay missing and in the denominator.
- **Reporting.**
  - Exact model IDs and Hugging Face revisions are recorded.
  - SCSC is the only VeriBench aggregate, always reported with its three factors and n.
- **Model calls.** No agent-written direct provider API calls (agents-config Hard Rule 9); judge calls go through the approved route (D-102).

## 9. Risks

| Risk | Mitigation |
|---|---|
| No mixed groups at small scale (all-failure groups) | Decomposed families and a Lean warm start (02); report the zero-signal boundary as a finding |
| Judge leniency turns FSC into a hackable reward | Compile gate; non-vacuity screen; experiment 103's judge controls (oracle ≥ 4, blank = 0, shuffled ≤ 1, vacuous ≤ 1); endpoint audits |
| Lean verification throughput | Measure in 01. VeriBench has a PyPantograph interface (`py_src/veribench/tools/lean4_interpreter.py`) as a starting point for a persistent checker. |
| Long outputs and thinking tokens hit caps | Measure length distributions in 01 and set the cap per protocol. Admission is itself one of the 2×2 axes, so the cap is a treatment, not a nuisance. |
| Compute availability (experiment 94 waited 48 hours and never got GPUs) | D-103: book the allocation before experiment 03 |
| Pool reference quality (FVAPPS specs are LLM-written) | Curated subset, reference compile and non-vacuity checks, human spot checks |
| Scale range is only about one order of magnitude (notes B) | Add a 30B mixture-of-experts run as a stretch goal, after 03 |

## 10. Order of work (weeks, once D-101 to D-105 are settled)

| Weeks | Work |
|---|---|
| 1 | Experiment 01; acquire and screen the pools |
| 2–3 | Experiment 02 warm start and probes |
| 4–7 | Experiment 03: 1.7B and 4B, fit, freeze the 8B forecast, run 8B, refit, freeze the 14B forecast, run 14B |
| 6–8 | Experiment 04 at 1.7B and 4B |
| 8+ | Experiments 05 and 06 |

This fits Brando's stated cadence of one experiment per night plus weekend blocks, with mentees running pool construction and screens (notes A).
