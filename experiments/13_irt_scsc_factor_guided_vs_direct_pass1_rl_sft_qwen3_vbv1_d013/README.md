# Experiment 13 — Does RL guided by a factored model of the evaluation (SCSC factors or a conjunctive IRT model) beat RL on the strict pass@1 reward? Qwen3-4B SFT on VeriBench V1 (D-013)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/README.md>

**TLDR:** This tests the crux of SCSC ↔ evals ↔ RL. At matched compute, does reinforcement learning (RL) guided by a factored, interpretable model of the evaluation improve held-out strict pass@1 more than RL on the strict reward itself? No experiment has tested this yet: experiment 09 failed its technical gate with zero optimizer updates.

A new zero-call measurement shows a naive test would have been null by construction. On all 15 finished supervised fine-tuning (SFT) checkpoints of experiment 08, VeriBench's kernel-checked factors equal the strict pass/fail outcome, so a factored kernel reward adds no learning signal.

The plan has three phases:

- **Phase 0:** build per-declaration partial-credit factors. Lean v4.22.0 reports every theorem's status even when one proof fails.
- **Phase 1:** fit and validate a conjunctive item response theory (IRT) model that predicts held-out pass@1 and pass@k.
- **Phase 2:** run four RL arms from the Qwen3-4B SFT checkpoint: strict reward, SCSC-style factored reward, IRT-guided reward and prompt sampling, and a placebo dense reward.

Status: **DESIGNED 10-09-2026; nothing run; [PROTOCOL.md](PROTOCOL.md) is a draft, not locked.**

- **Created:** 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando.
- **Owner:** Brando (to assign).
- **Terms:**
  - An *arm* is one condition being compared.
  - *Strict* is `kernel_binary`: the file typechecks, states at least one theorem, every stated theorem is a proved theorem with allowed axioms, and none is vacuous.
  - SCSC = (IC_tests · IC_proofs · FSC)^(1/3), where FSC is formal specification coverage.
  - GRPO is group relative policy optimization.

## Origin

- **Brando, 10-09-2026 (chat):** "It seems crucially we have not shown any factored decomposed model (irt or scsc) helps more than optimizing the downstream eval...this is surprising because the features should tell us what to optimize, so I really want to make an excellent experiment plan for this so that it actually works. Is there such an experiment already? If not make it."
- **His other request, same message:** use the SFT models "to make 'irt interpretable models' that improves our RL runs (and alpha apollo, hebe, diana)".
- **The 10-08-2026 meeting** ([record](../meetings/oct_7_2026/oct_7_2026.md)) set the order: first show a factorized measure correlates with the downstream metric, then optimize it, and automate the factors with IRT later.
- **Literature scan and zero-call tests:** the VeriBench idea page [IRT for SCSC factors](https://github.com/brando90/veribench/blob/main/experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md). This experiment takes over its RL-facing tests.

## Is there already such an experiment? No

| Experiment | What it asks | Why it does not answer the crux |
|---|---|---|
| [09](../09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/README.md) | Strict vs SCSC reward vs SCSC plus disclosed factors, Qwen3-1.7B SFT, GRPO | FAILED_TECHNICAL_GATE 10-08-2026: 4/4,077 sampled tokens fell outside the trainer's recomputed top-k/top-p support, and 367/4,073 log-probability errors exceeded 0.05, so there were zero optimizer updates. By the measurement below, its kernel factors would also have equaled its strict reward |
| [03](../03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/README.md) | Binary vs dense reward on never-solved prompts | Designed, not run; uses the same uninformative kernel factors; no placebo |
| [04](../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/README.md), [06](../06_swebench_lite_factor_feedback_matched_budget/README.md) | Factor-guided repair; SWE-bench factor feedback | Blocked before any model update |
| [07](../07_scs4c_vs_pass1_swebench_across_models/README.md) | Does SCS4C track pass@1 across 164 SWE-bench systems? | Evaluation only. Its H2 (ranking systems from 50 tasks) failed, which says nothing about optimization |
| [10](../10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md), [11](../11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md) | AlphaHebe promotion gate replay; live loop | Harness edits, not weights; designed or blocked |
| [12](../12_scsc_vs_hidden_gold_tests_vbv1_across_systems/README.md) | Does SCSC track hidden gold-reference tests? | Validity of the metric, not optimization (running) |
| [Curriculum design note](../meetings/oct_7_2026/item_factor_matrix_experiment_design.md) | Aligned vs permuted factor-informed task sampling | Not launched; no IRT; uses the same kernel factors |

So the crux has never run with a working trainer. With today's factors it could not have shown a difference.

## Why a factored reward could not help yet (zero model calls)

[`design_evidence/factor_redundancy_e08.py`](design_evidence/factor_redundancy_e08.py) reads experiment 08's validation cells (135 tasks × 8 samples per system) and writes [`factor_redundancy_e08.json`](design_evidence/factor_redundancy_e08.json).

| System | Strict pass rate | Tasks with mixed strict outcomes (GRPO signal) | Tasks where only the kernel smooth score varies | Compiled but not strict | No Lean extracted | Lean extracted, does not typecheck |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-4B Base | 0.003 | 3/135 | 0/135 | 2 | 167 | 908 |
| SFT 1.7B, full schedule | 0.049 | 20/135 | 0/135 | 0 | 183 | 844 |
| SFT 4B, full schedule | 0.093 | 32/135 (Wilson 95% [0.173, 0.315]) | 0/135 | 0 | 134 | 846 |
| SFT 8B, full schedule | 0.096 | 32/135 | 0/135 | 0 | 106 | 870 |

- **The factors collapse to one bit.** Across all 15 finished SFT checkpoints, the kernel smooth score `sqrt(IC_tests · IC_proofs)` varies within a group of constant strict outcomes on 0/135 tasks; the one exception is 1/135 at SFT 8B, 12.5% of the schedule. Compiled-but-not-strict samples number 0 on 14 of the 15 checkpoints.
- **Why they collapse.** The fine-tuned models never write `sorry`, and one failed proof makes the whole file fail to typecheck. That zeroes IC_tests, and IC_proofs with it. So a file either passes everything or scores 0 on both kernel factors.
- **SCSC adds nothing for failures.** It also contains FSC, but FSC is compile-gated in rewards (D-003), so SCSC is 0 on every strict failure. It grades coverage only among strict successes, and gives no partial credit where RL lacks signal.
- **Where the signal is missing.** For SFT 4B, 846 of 1,080 samples are Lean files that fail to typecheck, and 134 are cut off at the output cap. Under the strict reward, 103 of 135 tasks give GRPO zero gradient.
- **The fix is available.** [`design_evidence/lean_partial_credit_probe.lean`](design_evidence/lean_partial_credit_probe.lean) and [its output](design_evidence/lean_partial_credit_probe_output.txt) show Lean v4.22.0 keeps elaborating after a failed proof. The failed theorem depends on `sorryAx`; the other theorem depends only on `propext`; a theorem after the failure still elaborates. One compile therefore gives per-declaration status: implementation and examples, each theorem's proof, and how far the file elaborates.

## The model: how IRT relates to SCSC

- **SCSC** is a fixed formula applied to one output. Its weights are equal, and it has no notion of how hard a task is or how able a model is.
- **IRT** is a probabilistic graphical model fit to many outputs, from many models or checkpoints, on many tasks.
  - Latent ability θ (per model) and difficulty b and discrimination a (per task) explain each outcome.
  - Its predictions are probabilities on the pass@1 scale.
- **The bridge is the conjunctive multicomponent latent trait model** ([Whitely, Psychometrika 1980](https://link.springer.com/doi/10.1007/BF02293610); diagnostic version: Embretson and Yang, Psychometrika 2013):

  `P(policy i solves task j) = Π_k σ(a_jk · (θ_ik − b_jk))`, so `log P = Σ_k log σ(a_jk · (θ_ik − b_jk))`.

  - SCSC's geometric mean is the equal-weight, unfitted version of that sum of logs.
  - The fitted model gives per-task, per-component difficulties and per-policy component abilities.
  - It names each task's bottleneck component for a policy.
  - It gives the marginal value of improving component k: `∂P_ij/∂θ_ik = a_jk · P_ij · (1 − σ_ijk)`.
- **Why this should help RL.** The strict reward's signal vanishes whenever any component is near zero, because it is a product. The log-factored objective's per-component gradient, `a_jk · (1 − σ_ijk)`, does not vanish. That is the theoretical case for factored rewards; this experiment tests it.
- **Precedent.** Item parameters can be predicted from item text (Truong et al., ICML 2025, [arXiv 2503.13335](https://arxiv.org/abs/2503.13335)), and ability can be modeled as linear in log compute, which yields pass@k in closed form (Truong et al., ICML 2026, [arXiv 2606.07616](https://arxiv.org/abs/2606.07616)). A 2PL model over rollout × rubric-criterion verdicts has already served as a GRPO reward ([arXiv 2609.35646](https://arxiv.org/abs/2609.35646)), but it was never checked against an external outcome; here the strict target and the test split supply that check.

## Hypotheses and decision criterion

Predictions are agent-suggested. Each is frozen with `rl4cv.forecast.freeze_forecast` before the outcome it predicts is read ([PROTOCOL.md](PROTOCOL.md) § 9).

| ID | Claim | Verdict rule |
|---|---|---|
| H0 | Per-declaration factors are informative where strict is 0 | Gate G0: strict reproduced exactly on every known cell; the share of SFT 4B validation tasks where only the factored score varies is ≥ 0.15; partial progress at the 50% rung predicts strict success at the 100% rung with AUC ≥ 0.65 |
| H1 | The conjunctive IRT model is an interpretable metric that tracks the downstream metric | Gate G1: lower held-out per-sample log-loss than the empirical-rate and SCSC baselines, and Pearson ≥ 0.80 between implied and measured pass@1 across held-out checkpoints |
| H2 | It predicts where RL signal is before any RL rollout | AUC ≥ 0.70 for which train tasks give mixed groups, on an independent rollout batch |
| H3 | **The crux:** factored guidance beats the strict reward | Test strict pass@1: B − A > 0 and C − A > 0, with intervals excluding 0 |
| H4 | The gain comes from factor content, not from denser rewards | B − P > 0 and C − P > 0. Gains concentrate on tasks where the start policy's strict rate is 0 but partial progress is above 0. C − B > 0 if fitted weights and targeted sampling add beyond equal weights |
| H5 | No gaming | No factored arm lowers, relative to A: the hidden gold-test pass rate (experiment 12's adapter), test FSC from the validated judge, or stated-theorem counts |

What follows from each outcome:

- **G0 fails:** stop arms B and C. The factored kernel reward cannot differ from strict on this policy. Next is an FSC-based reward ([02C](../02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge/README.md)) or another start checkpoint.
- **G1 fails:** run arms A, B and P only, and report that the IRT model did not predict.
- **A technical gate fails:** fix it or stop. Science never runs on a failed gate.
- **H3 and H4 hold:** factored guidance helps. Repeat at 8B, and give the fitted model to AlphaHebe (experiments 10 and 11).
- **Only C wins:** the fitted model is what helps, not equal weighting.
- **B ≈ C ≈ P > A:** a dense-reward placebo effect, not factor content.
- **Every factored arm ≤ A, with intervals excluding the minimum detectable effect:** a real negative result, obtained with informative factors and a working trainer.

## Design

### Phase 0 — make the factors informative (CPU only, no model calls)

1. **Build a per-declaration scorer.** It is an rl4cv reward and diagnostic channel; the official VeriBench scorer stays hash-pinned. It compiles each output once, then reads per-declaration errors and `#print axioms`. Components:
   - `e`: Lean extracted and not cut off;
   - `d`: fraction of top-level declarations that elaborate without error;
   - `t`: implementation and `example`s elaborate without error;
   - `p`: fraction of stated theorems that are proved theorems with axioms within {`propext`, `Classical.choice`, `Quot.sound`}.
   - Guards: the existing non-vacuity screen and stated-theorem count. Strict equals `e ∧ d = 1 ∧ t = 1 ∧ p = 1 ∧` non-vacuous.
2. **Run controls.**
   - Authored files: one failed proof; a syntax error in the implementation; `sorry`; `native_decide` in a theorem; a vacuous theorem.
   - Exact reproduction of `kernel_binary` on every known cell: experiment 08's ladder (20,520 cells) and experiment 05 (21,504 cells).
3. **Measure informativeness on validation outputs** that already exist; selection and tuning may use validation (D-013). Gate G0.

### Phase 1 — fit and validate the interpretable model

- **Response data:** per-component outcomes from experiment 08's ladder (19 policies × 135 validation tasks × 8), experiment 05 (3 × 896 × 8), experiment 01 (9 × 896 single responses), and VeriBench experiment 103's single calls (7 frontier models × 896, re-scored from their saved Lean files). On the SWE-bench side, experiment 07's 164 systems × 424 tasks (gate, T_fix, T_keep → resolved).
- **Models compared:**
  - M0: empirical per-task rate.
  - M1: the SCSC-style smooth score.
  - M2: a two-parameter logistic (2PL) model on strict alone.
  - M3: the conjunctive multicomponent model.
  - M3e: M3 with task features (Python-source embedding, reference theorem count, domain) and ability linear in log SFT tokens.
- **Validation:** predict the full-schedule checkpoints from earlier rungs, and predict held-out tasks. Metrics are per-sample log-loss, AUC, Pearson and Spearman of implied vs measured pass@1 and pass@8, and mean error. Gate G1.
- **Train-split fit for arm C (D-013):** generate one train-split rollout batch from the start policy (539 tasks × 8, self-hosted vLLM, the Phase 2 sampler) and fit train-task item parameters. A second independent batch tests H2.

### Phase 2 — the RL comparison

- **Start checkpoint:** experiment 08's Qwen3-4B Base full-schedule SFT export `sft_4B_f1p0`, the fixed final step, chosen now from validation numbers. Experiment 08's own frozen selection is separate. 4B has the most strict signal per device among sizes that fit on four devices.
- **Trainer:** one GRPO implementation for every arm.
  - Rollouts use temperature 1.0 with no top-k/top-p truncation, which removes experiment 09's support failure.
  - Truncated importance sampling corrects residual generation/trainer probability differences ([Yao et al., On the Rollout-Training Mismatch in Modern RL Systems](https://fengyao.notion.site/off-policy-rl); [verl rollout correction](https://verl.readthedocs.io/en/latest/algo/rollout_corr.html)).
  - Maximum 8,192 new tokens, with truncations logged.
  - Each run gets 100 optimizer updates of 32 prompts × G = 8.

| Arm | Reward per rollout | Prompt sampling |
|---|---|---|
| A — direct | Strict `kernel_binary` | Uniform over the 539 train tasks. Groups with zero reward variance are dropped and refilled, as in DAPO's dynamic sampling ([arXiv 2503.14476](https://arxiv.org/abs/2503.14476)) |
| B — factored, SCSC-style | Geometric mean of the Phase 0 components (equal weights), with extraction gate and guards | Same as A |
| C — factored, IRT-guided | M3/M3e posterior probability of strict success given the rollout's component outcomes (fitted weights) | Weights proportional to predicted reward variance for the current policy; θ is refit every 10 updates from the arm's own train rollouts |
| P — placebo | Random value drawn from B's reward distribution, independent of the rollout | Same as A |

- **Why a placebo arm.** Random rewards raised Qwen2.5-Math-7B's MATH-500 score by 21.4% under GRPO ([Spurious Rewards, arXiv 2506.10947](https://arxiv.org/abs/2506.10947)). A factored win on a Qwen model must beat a reward of matched density that carries no information.
- **Matched compute.**
  - Every arm gets the same sampled-token budget, the same number of updates and the same evaluation schedule.
  - Dynamic-sampling refills count against the arm's budget.
  - IRT fitting runs on CPU.
- **Seeds.**
  - **Pilot:** 1 seed per arm plus a second seed of A, 30 updates each. It runs the technical and learning gates and estimates seed variance.
  - **Main:** 3 seeds × 4 arms × 100 updates. Use 5 seeds if the pilot implies a minimum detectable effect above 4 percentage points.
- **Checkpoints.** Select on validation strict pass@1 every 25 updates (135 × 8), with the same rule for every arm. Test once per selected checkpoint (222 tasks × 16 samples).

### Technical gates (before any scientific run)

- T1: generation/trainer probability agreement.
- T2: one real update, then a weight refit into the generator.
- T3: save and resume.
- T4: measured throughput and Lean scoring latency.
- T5: in the pilot, arm A must raise its own train strict reward.

Thresholds are in [PROTOCOL.md](PROTOCOL.md) § 7.

### Outcomes and analysis

- **Primary outcome:** test strict pass@1, the mean over 222 tasks of the 16-sample success rate. Core (152) and IndustrySet (70) are also reported separately.
  - Contrasts B − A and C − A are Holm-adjusted.
  - Intervals come from a hierarchical bootstrap that resamples seeds and paired tasks.
  - With 3 seeds, an exact seed-permutation test cannot reach p < 0.05 after adjustment, so the bootstrap is primary and the permutation p is descriptive.
- **Secondary outcomes:**
  - pass@4 and pass@16 (unbiased estimator).
  - Contrasts C − B, B − P and C − P.
  - Regressions: tasks the start policy solved that are now lost.
  - Factor changes.
  - Test SCSC with the validated FSC judge, one sample per task, through Valkyrie (D-102, D-108).
  - Hidden gold-test pass rate through experiment 12's adapter, if its coverage gate passes.
- **Mechanism analysis:**
  - Per update, the share of prompts whose advantage is nonzero under each arm's reward.
  - Gains split by the start policy's strict and partial-progress strata.
  - Shifts in each task's bottleneck component.

### Compute (estimate; T4 replaces it with a measurement)

- **Per run:** about 25,600 rollouts × about 5,000 generated tokens ≈ 128 million tokens. That is roughly 16–24 A100-hours, plus about 140 CPU-hours of Lean scoring, which runs in parallel.
- **Total:** main runs (12) plus pilot and evaluation come to roughly 260–350 A100-hours.
- **Approval:** Brando approves the device budget at the protocol lock (GPU discipline).

## Connection to AlphaApollo, Diana and Hebe

Phase 1's SWE-bench fit on experiment 07's matrix is a Diana-side measurement model. It feeds two experiments rather than duplicating them:

- An IRT promotion-gate arm for experiment 10. Add it before that draft protocol locks: promote only when the candidate's ability beats the incumbent's by more than its standard error, and when no task's predicted success falls beyond its uncertainty.
- A per-task bottleneck diagnosis for experiment 11's feedback arm.

That is the same hypothesis with harness edits instead of weight updates.

## Binding limits

- D-013 split: test once. Anything that feeds training, including arm C's item parameters, comes from train-split data only.
- The official VeriBench scorer stays hash-pinned. The per-declaration scorer must reproduce `kernel_binary` exactly, and the verifier is never loosened.
- FSC comes only from the validated judge through Valkyrie. It is used for test evaluation, not for training rewards.
- Self-hosted vLLM under D-101. Brando approves the device budget before launch.
- Full manifest accounting: unmeasured cells are listed, never counted as zero.

## Files

| Path | Content |
|---|---|
| [`design_evidence/factor_redundancy_e08.py`](design_evidence/factor_redundancy_e08.py), [`.json`](design_evidence/factor_redundancy_e08.json) | The redundancy table above, reproducible from experiment 08's committed cells |
| [`design_evidence/lean_partial_credit_probe.lean`](design_evidence/lean_partial_credit_probe.lean), [output](design_evidence/lean_partial_credit_probe_output.txt) | Per-declaration status under Lean v4.22.0 |
| [`PROTOCOL.md`](PROTOCOL.md) | Draft protocol: definitions, gates, analysis and forecasts. Not locked |

## Status

DESIGNED 10-09-2026. Nothing run.

Next: Phase 0, CPU only. Build the per-declaration scorer, run its controls, and measure G0 on experiment 08's existing validation outputs.
