# Item–factor matrices for learning better verified-code models

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_7_2026/item_factor_matrix_experiment_design.md>

**TLDR:** Keep each solution's factor vector beside its strict binary outcome, then compare binary reward, dense scalar reward, and a precisely specified use of the factor vector. The adopted overnight study uses the full geometric-mean score and its validated automated coverage judge, without new human labels. The curriculum and kernel-only variants below are alternative designs, not the executable overnight protocol.

Created: 10-08-2026. Status: research interpretation and alternative designs; reinforcement learning (RL) has not run here. The adopted three-arm full-score experiment is [09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013](../../09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/PROTOCOL.md), which tests factor disclosure with the same scalar reward. Its protocol governs execution; the four-arm curriculum below is not launched.

**Goal:** Determine whether retaining item-level factor information produces better verified-code models at a matched training budget.
**Confidence:** High that the proposed measurements distinguish the mechanisms; unmeasured whether any treatment improves the model.
**Importance:** 10/10, an agent judgment reflecting Brando's stated interest.
**Key uncertainty:** Do the factors supply actionable information beyond the scalar reward, rather than merely revealing additional ways an output failed?

## What the meeting image establishes

Source: the preserved [whiteboard photograph](self_improving_with_factored_decomposed_smooth_metric_meeting_pic.jpeg), independently inspected for this design; SHA-256 `5c7a73f14123767f2e7d21b5fc9a6b0a5d581bf4bfeb57a4f1c4a81e2db64a66`. The [existing description](self_improving_with_factored_decomposed_smooth_metric_meeting_pic.md), [verbatim transcript](transcription.md) and [meeting provenance](oct_7_2026.md) remain unchanged. Fathom dates the meeting 10-08-2026; the user-chosen folder remains `oct_7_2026`.

The top-center diagram visibly places a grid headed “features” beside a narrow right-hand outcome column. Its illustrative row contains `1`, `0.01`, `1`, `0.01`, and a separate rightmost `0`. A faint `S` and the column boundaries make the precise division between factors and an intermediate aggregate uncertain. This design therefore does not claim that the row defines four factors. The nearby relation `S = F(…) ≈ pass@1` connects a combined score to the desired downstream success rate. Here pass@1 means the probability of success from one sampled solution under the specified generation protocol.

The transcript supports the interpretation that a binary failure can conceal useful partial progress and that measurements should be compared by item and feature. The right side of the board proposes a measurement → improver → model/harness/prompt edit → remeasurement loop. Neither the drawing nor the transcript establishes which optimizer, factor weights or acceptance rule works. The handwritten decimals are examples, not measurements. In particular, this design does not use the board's illustrative `0.77` as a calculated geometric mean or empirical result.

**Research inference:** the useful object is an aligned record of factors, aggregate and downstream outcome before and after a change. A weak factor suggests a candidate intervention; it does not identify whether the model, tool wrapper or prompt caused the failure. That causal question requires a controlled intervention.

## The matrix and its aligned target

For task `i`, policy/checkpoint `t` and sample `k`, retain one immutable record:

```text
task_id | policy_hash | sample_id | split | factor_1 ... factor_J | scalar_score || strict_target
        | generation_hash | scorer_hash | factor_denominators | missing_reason | generated_tokens
```

Let `F[i,k,j,t]` be factor `j` in `[0,1]`, `s[i,k,t] = g(F[i,k,:,t])` the declared scalar aggregation, and `b[i,k,t]` the strict binary target. Unknown measurements are null, not zero. For a fixed policy and sample, `[F | s || b]` is the requested task × factor matrix with its aligned binary target. With repeated samples, preserve every underlying row and additionally show task means and measured/declared counts. A mean over eight binary outcomes is an empirical success rate, not a binary per-solution outcome and not pass@8.

Store both before and after matrices with the same task identities and scorer definitions. Define factor changes and target changes only where both observations exist. For independently sampled before/after policies, compare task-level means; equal sample indices do not make the two generated trajectories identical counterfactuals. For an edited patch, retain its actual parent patch and compare that concrete before/after pair.

The useful displays are:

- factor changes alongside target changes, including factor improvement while the target remains zero;
- previously successful tasks becoming unsuccessful and previously unsuccessful tasks becoming successful;
- factor tradeoffs, such as better proofs but fewer files satisfying the typecheck/example gate;
- missing measurements and infrastructure failures as a separate category.

A no-regression rule on every observed item and factor is an interesting optional acceptance policy, not an established guarantee against forgetting. With stochastic generations, rejecting every negative sample difference can reject useful updates because of sampling variation. Freeze any such rule and its reference set separately; always report the losses it rejects and the gains it forgoes.

## Use the current definitions, not a new name for a different score

| Setting | Factor vector and scalar | Aligned strict target | What is not established |
|---|---|---|---|
| Lean, deterministic first study | `c = IC_tests`: extracted file typechecks and contains at least one example; `p = IC_proofs`: fraction of stated theorems proved by the allowed kernel axioms; retain stated/proved counts and the syntactic non-vacuity result. Existing `proof_fraction` reward is `c × p`, zeroed if any theorem is vacuous. | Existing `kernel_binary`: `c = 1`, at least one stated theorem, every stated theorem proved, and zero detected vacuous theorems. | Whether the stated theorems cover the intended task. A non-vacuity screen does not establish semantic adequacy. |
| VeriBench's complete score | Smooth Conjunctive Score for Code Verification (SCS4CV, code identifier `scsc`, historically SCSC): per-response `(IC_tests × IC_proofs × FSC)^(1/3)`, with the repository's compilation and non-vacuity rules. Formal Specification Coverage (FSC) is the validated model-judged coverage factor. | A separately declared strict outcome; do not define “correct” merely by thresholding this same scalar. | Missing FSC cannot be inferred from proofs, replaced with a constant, or called measured. |
| `07_scs4c_vs_pass1_swebench_across_models` | Smooth Conjunctive Score for Code (SCS4C), tests-only version: `G × sqrt(T_fix × T_keep)`, where `G` is the patch-usable gate, `T_fix` the fraction of issue tests passed and `T_keep` the fraction of regression tests preserved. Full SCS4C adds gold-behavior agreement, `D_gold`, as a third geometric-mean factor. | Official issue resolution from the frozen independent evaluator. | Strong association is partly built in when the target is the conjunction of the same test factors. It does not prove that optimizing the partial credit improves learning. |
| `06_swebench_lite_factor_feedback_matched_budget` | Public syntax/viability, regression-preservation and issue-check factors; the scalar and vector conditions use the same frozen checks. | Hidden official issue resolution, evaluated after patches are frozen. | These public diagnostics are not experiment 07's gold-referenced factors. Do not expose official tests or outcomes through feedback. |

Authoritative implementations are [rewards.py](../../../src/rl4cv/rewards.py) and [scs4c.py](../../../src/rl4cv/scs4c.py). Preserve the verifier's allowed axioms and the pinned non-vacuity adapter. Retain theorem counts because improving a fraction by stating fewer obligations is a possible failure mode. For official VeriBench summaries, use the geometric mean of the factor means on one common measured cohort, as decision D-009 requires; averaging per-response scalar rewards is a separate diagnostic.

The first deterministic Lean experiment can claim an improvement in the **strict verified-artifact rate** if its target improves. It cannot automatically claim improved intended-program correctness. Existing validated FSC scoring can be an additional automatic evaluation when its route and funding are available; no new human labels are required. Without that measurement, keep the semantic limitation explicit.

## A real, small before/after matrix already available

The following rows are an illustration from `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`, not an RL result. They compare Qwen3-4B-Base with the first supervised fine-tuning (SFT) checkpoint at 12.5% of the frozen training-token schedule. Rows were chosen as the first three task identifiers in lexical order, independently of their outcomes. Each side has eight known validation samples per task.

| Task | Typecheck/example successes, before → after | Compile-gated proved-theorem fraction, before → after | Strict verified-artifact successes, before → after |
|---|---:|---:|---:|
| `aerospace_set_synthetic__my_arming_interlock` | 0/8 → 0/8 | 0 → 0 | 0/8 → 0/8 |
| `aerospace_set_synthetic__my_fcs_gain_schedule` | 1/8 → 0/8 | 0 → 0 | 0/8 → 0/8 |
| `aerospace_set_synthetic__my_sensor_watchdog_fresh` | 0/8 → 0/8 | 0 → 0 | 0/8 → 0/8 |

The middle row makes the visualization useful: the target remains zero while a factor changes. This is a descriptive finite sample, not a population estimate or a finding of systematic forgetting; no acceptance threshold, confidence interval or significance test is applied (`p-val=n/a`). FSC is unmeasured in these source tables. Other tasks and checkpoints may behave differently.

Sources, each containing 135 validation-task rows:

- [base_4B_e05_validation_per_task.csv](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/ladder/base_4B_e05_validation_per_task.csv), SHA-256 `d0a295f1b40009666d6c942be49bf5d9f32816824456e1accd5c36443c1d1dcd`.
- [sft_4B_f0p125_validation_per_task.csv](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/ladder/sft_4B_f0p125_validation_per_task.csv), SHA-256 `ef7a0a2dead3cc38ebf7e2d30d9fcb5637631ad51ad974cfa2002ebee7577b4a`.

Reproduction: join by `task_id`, sort task identifiers and take the first three; report `k_ic_tests/samples_known`, `mean_proof_fraction`, and `k_kernel_binary/samples_known`. Never display a zero from a row with `samples_known = 0` as a measured factor. The [validation ladder](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/validation_ladder.json) includes explicitly incomplete checkpoint rows; their placeholder zeros are not outcomes. This inspection did not read test-split outcomes or select a checkpoint.

## Alternative curriculum design: separate reward density from use of the vector

Replacing binary reward with `proof_fraction` tests a **scalar reward change**. Recording or displaying the factors while the optimizer receives the same scalar leaves the learning rule unchanged. Passing a vector to a function that immediately computes the same scalar also does not test whether factor identities help.

Use Group Relative Policy Optimization (GRPO) as one fixed optimizer if its Lean trainer is already operational; it was introduced in [DeepSeekMath](https://arxiv.org/abs/2402.03300). Confidence and Difficulty-adaptive Policy Optimization (CoDaPO) uses rollout confidence and empirical difficulty to reweight updates and resample questions, according to its [primary paper](https://arxiv.org/abs/2606.07950). Either is a possible fixed backbone. Switching optimizer and reward simultaneously cannot identify the source of a gain. Do not silently replace CoDaPO's difficulty statistic with the mean smooth reward; any adaptation needs a declared definition and pinned implementation.

**[p 10/10] First compare binary and dense rewards on existing groups, then train the pair.** Recompute both channels on exactly the same complete rollout groups from one policy and sampling configuration. Count groups whose binary rewards are constant but whose dense rewards vary, and groups where the dense rewards themselves are constant. If the two reward arrays are identical, the proposed ablation has no treatment difference. Teachers from two different models must not be combined into one on-policy group: four samples from each teacher do not form eight samples from the proposed initial policy.

**[p 9/10] Test one explicit use of the matrix with a matched negative control.** A small first mechanism is factor-informed task sampling, while preserving the dense scalar reward and optimizer. The following four conditions isolate the necessary comparisons:

| Condition | Reward | Training-task selection | Question |
|---|---|---|---|
| Binary baseline | `kernel_binary` | Uniform over the frozen train pool | Strict-reward reference |
| Dense scalar | Existing `proof_fraction` | Same uniform rule | Does partial credit improve the held-out strict target? |
| Dense plus aligned matrix | Same `proof_fraction` | Frozen factor-informed sampler below | Does item-specific factor information improve allocation? |
| Dense plus permuted matrix | Same `proof_fraction` | Same sampler with factor rows permuted across tasks | Does alignment to the correct task matter beyond changing the sampling distribution? |

One concrete sampler, to freeze before training: collect or reuse a common initial-policy train rollout group of size eight per task. Form task means for `c`, `p` and an indicator that at least one theorem is stated with no detected vacuity and all statement types parse. Assign each task to its lowest-mean factor, breaking ties in that listed order. Draw half of training tasks uniformly; for the other half, choose a nonempty factor bucket uniformly, then a task uniformly from that bucket. Keep these buckets fixed in the first experiment. The one-half mixture is an agent-proposed design parameter, not an empirically selected optimum. Report the bucket sizes and resulting sampling probabilities; if all tasks enter one bucket, this treatment collapses to uniform sampling and is not an informative comparison.

For the permuted control, use a frozen random permutation of complete task-level factor rows, preserving the bucket sizes, total sampling-weight distribution and uniform mixture. Preserve the real scalar rewards of the actual generated solutions. Where sufficient tasks share the same initial scalar/binary-success summary, permute within those prespecified strata to better control for general difficulty; report the number of tasks whose assignment actually changes. An unrestricted permutation also changes the relationship to difficulty, so its interpretation must be correspondingly narrower. If no nontrivial permutation is possible, record that the control is uninformative instead of inventing additional factor signal.

This treatment tests a specific curriculum mechanism. It does not establish that every vector-based reward or improver works. Per-factor advantage normalization is a separate alternative: it changes the effective weighting of factors, and in some cases is algebraically equivalent to a dynamically weighted scalar reward. Do not label an equivalent computation an independent vector method.

**[p 8/10] Add the other optimizer only after the first comparison is interpretable.** Repeat the fixed reward/information contrasts under CoDaPO or GRPO as a separate optimizer factor. The first overnight study need not become an optimizer × reward × model-size sweep. Use the same exact initial checkpoint for every included condition; a changed checkpoint is another confound.

## Existing-data analysis and an executable overnight boundary

The first analysis requires no model calls or human ratings. On existing train groups, compute complete/declared counts, distinct reward values, within-group reward variation, added nonzero advantages under the dense channel, and the factor-bucket sizes. Use the exact trainer's advantage normalization and zero-variance rule; a positive partial score shared by every response in a group creates no relative learning signal. Where generated-token lengths and the required estimator inputs exist, reuse `rl4cv.probe` for usable signal per token and its coverage across prompts. Do not infer token log-probabilities needed by CoDaPO from correctness labels.

Validation matrices can describe before/after gains, losses and factor tradeoffs. They must not become training prompts or training-task sampling inputs. Keep the project's frozen train / validation / test split: 539 / 135 / 222 VeriBench tasks under D-013. New training that adopts that split belongs to a new executable protocol; experiments locked under the older all-VeriBench-held-out rule retain that rule. Finish the existing warm-start selection rather than silently choosing the most flattering partial checkpoint from its incomplete ladder.

Before training, freeze the complete condition × seed × checkpoint × task declarations, initial weights, optimizer/code/environment pins, factor definitions, sampler/permutation, generated-token and update budgets, evaluation schedule, and source hashes. Charge the common initial factor probe and all diagnostic computation equally. Record actual generated tokens, completed updates and resource use, not only nominal caps. An existing-data audit can identify a collapsed contrast; it cannot certify how much RL will improve a model or that training will finish overnight.

The minimum claim-producing comparison is dense versus binary at fixed optimizer and matched budget; the decisive matrix claim is aligned versus permuted factor information at the same dense reward. Report the held-out strict-target difference with 95% task-paired bootstrap intervals carrying all samples, gained/lost successes, all missing cells and bounds over the full manifest. Use a prespecified paired test when making a verdict, and name its null and assumptions. A single training seed only supports a seed-conditional result; task resampling does not measure training-seed uncertainty. Select checkpoints using validation only, then evaluate the frozen selected policies on test once under the adopted protocol.

Keep machine-verifiable failure classes separate from missing infrastructure. No reward, sampling rule or factor-guided edit may weaken the kernel, add accepted axioms, remove required checks or turn unavailable coverage into success. The overnight execution owner still needs the shared compute/storage ledger, a working pinned trainer and a verified funding route for any measured external-model calls. This design introduces no new human-judgment requirement and authorizes no messages to collaborators.

**TLDR-end:** [rl-4-code-verification: item-factor matrix experiments] Preserve the item-level matrix beside the strict target, first establish that dense rewards change the learning signal, then test a concrete use of correctly aligned factors against the same use of permuted factors.
**Snapshot:** Actual validation illustration, base 4B → first SFT checkpoint:
```text
aerospace_set_synthetic__my_fcs_gain_schedule
known samples:                  8 → 8
typecheck/example successes:    1/8 → 0/8
mean proved-theorem fraction:   0 → 0
strict verified-artifact wins:  0/8 → 0/8
```
