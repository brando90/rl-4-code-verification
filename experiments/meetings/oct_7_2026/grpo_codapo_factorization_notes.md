# GRPO, CoDaPO and a controlled test of factored feedback

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_7_2026/grpo_codapo_factorization_notes.md>

**TLDR:** The intended pilot uses the same Group Relative Policy Optimization (GRPO) implementation for three arms: a strict binary counterpart of the existing Smooth Conjunctive Score for Code verification (SCSC), SCSC as a continuous reward, and that same continuous reward with named factor feedback. This separates reward partial credit from access to decomposition. Confidence and Difficulty-adaptive Policy Optimization (CoDaPO) is a different adaptive sampling/update method, not an existing factor-conditioned learner. Training has not established improvement; this note records the prospective design and implementation constraints.

Prepared 10-08-2026. This design note supports the new experiment's executable protocol; it does not replace that protocol, freeze an unmeasured runtime forecast, or modify earlier experiments.

## Intended comparison and initialization

The coordinator selected the immutable 100%-token supervised fine-tuning (SFT) export of Qwen3-1.7B-Base from `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`. Record the export, tokenizer and prompt-template hashes before execution. This is an exploratory fixed-initialization pilot even though experiment 08's multi-scale readiness gate has not passed. It does not retrospectively select a winning experiment-08 checkpoint or relax that experiment's gate.

Let a scored response have factors `IC_tests` (internal consistency of tests), `IC_proofs` (internal consistency of proved theorems), and `FSC` (formal specification coverage). Their authoritative definitions and kernel restrictions remain those of the pinned VeriBench scorer and validated coverage judge. For non-vacuous eligible responses, define

\[
 s=(IC_{tests}\,IC_{proofs}\,FSC)^{1/3},\qquad
 b=\mathbf 1[IC_{tests}=1\ \land\ IC_{proofs}=1\ \land\ FSC=1].
\]

Apply the existing extraction, compilation, allowed-axiom and non-vacuity gates; do not add format bonuses, additive factor rewards or a replacement aggregate. The binary comparison uses exact normalized judge value one, without rounding or an epsilon threshold. It is a strict **judge-dependent conjunction**, not a mechanically proved semantic-completeness claim. Keep the existing `kernel_binary` as a separately named diagnostic; it is not the arm-A reward because it omits coverage.

| Arm | Final training reward | Feedback after the first response |
|---|---|---|
| A: binary conjunction | `b` | Scalar `s`, bit `b`, and bounded compiler text |
| B: smooth scalar | `s` | Exactly the same feedback fields and rendering as A |
| C: smooth scalar with factors | `s` | The same scalar, bit and compiler text, plus named `IC_tests`, `IC_proofs`, `FSC` values |

All arms receive the same information available to the compiler and the same bounded compiler text; only C additionally receives the named numeric factor vector. A deliberately receives scalar feedback too, so B minus A isolates the **training-reward** change. B minus A does not claim that A lacks all partial-credit information. C minus B tests the benefit of named factor feedback during training while keeping the objective fixed. Compiler messages and the strict bit can already reveal some factor information, so this is the incremental effect of explicit decomposition, not access versus complete absence of factor information.

Use the same original task order, group size eight, two response turns, initialization, optimizer, generation settings, generated-token ceilings, truncation policy and paired training seeds. Freeze feedback rendering, truncation and token accounting before training. C's extra context tokens are a treatment cost: use the same generated-action-token allowance, record total context/compute costs, and do not claim identical total compute merely because generation caps match. Do not stop successful first responses early in one arm while giving another arm two turns.

Use final-turn reward only: the first response produces feedback but contributes reward zero; the final response contributes `b` or `s`. This avoids silently optimizing the sum of first- and second-turn quality. Both assistant responses may receive the same final-trajectory advantage, with environment/prompt tokens excluded from the loss.

## Why the kernel-only comparison is currently uninformative

The read-only readiness audit directly checked all 2,160 recorded validation responses at the 75% SFT rung: 1,080 for 1.7B and 1,080 for 4B, each 135 tasks times eight samples. The stored `kernel_binary` and `proof_fraction` rewards disagree on **0/2,160** responses; all rows have `status=scored`. Factor pairs are `(0,0)` for 1,036/1,080 and `(1,1)` for 44/1,080 in 1.7B; corresponding 4B counts are 1,040/1,080 and 40/1,080. There are no intermediate proof fractions in these artifacts. These are exhaustive equality checks on the observed files, not population estimates; confidence intervals and hypothesis tests are not applicable.

Private source artifacts, inspected by the readiness owner:

- `/lfs/skampere1/0/brando9/rl4cv_e08/ladder/validation/scored/scored_sft_1p7B_f0p75_g8.jsonl`
- `/lfs/skampere1/0/brando9/rl4cv_e08/ladder/validation/scored/scored_sft_4B_f0p75_g8.jsonl`

Derived evidence is in [experiment 08's validation ladder](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/validation_ladder.json), with per-cell tables under its `results/ladder/`, at commit `c9afab7` or later. These observations concern the 75% rung, not the newly selected 100% starting export. `FSC` is unmeasured in these files, so they establish neither a full-SCSC contrast nor its absence. A `kernel_binary` versus `proof_fraction` pilot needs an observed reward-differentiation gate before it is scientifically useful.

For the selected full-SCSC design, score the prospectively frozen **training-only** preflight groups before updates. Require a measured `s != b` response and positive within-group variation in `s` before admitting the informative comparison. Record all-failure, mixed and all-success groups for both rewards. A binary arm with no positive support is an admissible frozen finding; no extra sampling or easier-task replacement may be selected from its outcome. Do not treat missing required judge results as zero. A mathematically determined zero from a failed compilation/proof gate is distinct from an unmeasured coverage factor.

## GRPO implementation contract in the existing NeMo runtime

The recorded experiment-08 runtime is NVIDIA NeMo Reinforcement Learning (NeMo RL) 0.4.0 at `c751f811217db7df0d4c94abdeaada6626cfc150`; [its checkpoint](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/CKPT_e08.md) reports working SFT execution. That is evidence of the SFT runtime, not proof that the new GRPO/Lean/judge loop works. Verify actual installed revision, resolved dependencies, weight synchronization and the new environment before training.

The pinned [GRPO implementation](https://github.com/NVIDIA-NeMo/RL/blob/c751f811217db7df0d4c94abdeaada6626cfc150/nemo_rl/algorithms/grpo.py) supports multi-turn rollouts, group-size and turn-count controls, optional reward normalization, leave-one-out baselines, dynamic sampling and asynchronous operation. Freeze these switches explicitly. For the initial causal comparison, keep dynamic sampling and asynchronous policy staleness disabled; otherwise the reward change can also change which tasks receive training. The code applies a trajectory advantage to assistant tokens and masks other roles. Test this on a synthetic two-turn transcript, including exact token boundaries.

For a group of eight complete trajectories with rewards `r_i`, conventional normalized GRPO uses

\[
 A_i=\frac{r_i-\overline r}{\sigma_r+\epsilon},\qquad
 L=-\mathop{\mathrm{aggregate}}_{i,t}
 \min\!\left(q_{i,t} A_i,
 \operatorname{clip}(q_{i,t},1-\epsilon_{lo},1+\epsilon_{hi})A_i\right),
\]

where `q` is the new-policy/behavior-policy probability ratio and aggregation applies only to generated assistant tokens. Freeze population versus sample standard deviation, stabilizer, clipping, loss normalization and any reference-policy penalty identically. If using the leave-one-out baseline, name that variant and use `(sum_j r_j - r_i)/7`; do not present it as the all-eight mean. The pinned [baseline utility](https://github.com/NVIDIA-NeMo/RL/blob/c751f811217db7df0d4c94abdeaada6626cfc150/nemo_rl/algorithms/utils.py) handles this option and validity masks, so a unit test must compare its actual output with the frozen formula, including constant and incomplete groups. A model update is not established by a nonzero reported loss alone: record parameter/checkpoint changes and nonzero admitted advantages.

The [environment interface](https://github.com/NVIDIA-NeMo/RL/blob/c751f811217db7df0d4c94abdeaada6626cfc150/nemo_rl/environments/interfaces.py) returns observations, metadata, stop strings, rewards and termination flags. Keep privileged references and judge material in the environment, not in the model observation. The [rollout implementation](https://github.com/NVIDIA-NeMo/RL/blob/c751f811217db7df0d4c94abdeaada6626cfc150/nemo_rl/experience/rollouts.py) sums per-turn rewards, making first-turn zero essential. Its observation tokenization must be checked with the exact Qwen template: verify the second assistant turn receives correctly delimited feedback and that no environment bytes enter the assistant loss mask. A terminal flag, maximum-turn cutoff and length truncation are different events and need separate receipts.

Coverage scoring uses the validated `vb103_judge` Valkyrie route, funded by Vals, with the recorded model ensemble, effort, rubric and aggregation. Complete route controls before its first use here; working credentials or experiment-08 SFT are not that evidence. Every arm computes the same factors and incurs the same diagnostic/judge contract even when it hides components. Use immutable task/response/turn identities for asynchronous judge jobs, then wait for the complete scoring group before an optimizer update. Infrastructure recovery may resume identical missing cells but may not replace a low-scoring response.

## CoDaPO: what would constitute a different experiment

[CoDaPO's paper](https://arxiv.org/html/2606.07950v1) defines confidence as the exponential of the average per-response mean token log probability. With binary rewards, difficulty is one minus group accuracy. The value is `confidence * (1 - 4*(difficulty - 0.5)^2)`; it weights normalized advantages and guides extra sampling. The two updates split the compute budget between the original and selected batches. This is an adaptive optimizer/data-allocation mechanism, not the named-factor feedback intervention above.

The public Apache-2.0 implementation was resolved on 10-08-2026 to `210c2051f54de76fdf92eb4cef9bb919dd404789`. Its [advantage function](https://github.com/tmlr-group/CoDaPO/blob/210c2051f54de76fdf92eb4cef9bb919dd404789/alphaapollo/core/generation/verl/trainer/ppo/core_algos.py#L390) counts `reward == 1` for difficulty and adds a default `weight_offset=0.1`; the [trainer](https://github.com/tmlr-group/CoDaPO/blob/210c2051f54de76fdf92eb4cef9bb919dd404789/codapo/ray_trainer.py) duplicates batches for selection and focused updates. Feeding it continuous SCSC unchanged does not redefine its success-frequency calculation. Changing that calculation is a new adaptation requiring its own name and tests.

Its [installation recipe](https://github.com/tmlr-group/CoDaPO/blob/210c2051f54de76fdf92eb4cef9bb919dd404789/installation.sh) pins PyTorch 2.6.0 with CUDA 12.4, FlashAttention 2.7.4.post1, vLLM 0.8.5, Ray 2.47.1 and parameter-efficient fine-tuning library 0.15.2; [package metadata](https://github.com/tmlr-group/CoDaPO/blob/210c2051f54de76fdf92eb4cef9bb919dd404789/setup.py) requires Transformers at most 4.51.1. This is a separate bundled verl stack, not a drop-in option in NeMo RL 0.4.0. Do not replace the working SFT runtime to import it for this pilot.

For provenance, local `rl-env-scaling` main `c75755c07481c335e87e3ce3455132d6b4892390` has a placeholder pilot, while its project-pinned historical commit `7118b86f84e8ce0d8607b09c9826a4a6ffbbd015` does contain executable math GRPO launchers and a custom scalar-reward hook for verl 0.7.1. Neither is a complete Lean environment. AlphaApollo main resolved to `712a04dcdefb0eabdb6622350460f187e9bb5941`; the [local AlphaApollo paper](../../../docs/related_work/alphaapollo_arxiv_2510.06261v2.pdf) motivates masking environment feedback in multi-turn learning but does not establish this pilot's validity.

## Budget, chronology and the scope of a result

Use two prospectively fixed, paired training seeds: three arms times two seeds gives six trajectories. If the executable protocol adopts 32 optimizer updates per trajectory, that is 192 updates, not a measured runtime forecast. With `P` prompts per update, eight trajectories per prompt and two turns, the training ceiling is `6 * 32 * P * 8 * 2 = 3,072 P` generated responses. Compute feedback on both turns; judge only the eligible files required by the frozen contract. A six-member validated ensemble can require up to `18,432 P` member responses before controls, evaluation, preflight and bounded infrastructure recovery. Freeze actual job/member/retry accounting from the route; a nominal optimizer-step count is not a spending or overnight-duration estimate.

Measure end-to-end generation, Lean checking, judge completion and one-update throughput before the main allocation. Freeze the complete horizon, token ceilings, two seeds, evaluation manifest and directional hypotheses before observing main training outcomes. The hypotheses are B above A and C above B on the common endpoint; they are not a fitted usable-signal-density/effective-coverage law forecast, and no numeric coefficient-transfer claim follows. If a token limit binds before the frozen horizon, follow the prospectively frozen truncation/endpoint rule rather than choosing favorable checkpoints. Preserve every incomplete trajectory.

The primary downstream comparison is the strict conjunctive pass rate under the **same one-turn, no-feedback inference harness** for the starting checkpoint and every frozen trained checkpoint. Also report official SCSC, all three factors, formal specification coverage and measured/declared/missing counts, separating core and IndustrySet. Use the existing train / validation / test split: training and reward preflight use train only, checkpoint decisions use validation only, and each frozen checkpoint receives its declared test evaluation once. Official SCSC uses the geometric mean of factor means on a common measured cohort; mean per-response `s` remains a separately labeled diagnostic.

Report paired task uncertainty and seed-by-seed results; two training seeds do not support a strong population claim about optimizer robustness. Common no-feedback evaluation tests a change in the trained policy, while any training-harness evaluation is a secondary system result. A finished run, higher training reward, a single favorable task, or better two-turn performance with richer feedback is not by itself confirmed improvement in the common downstream endpoint. Null, negative and zero-support results remain outcomes of the frozen pilot.

**TLDR-end:** [rl-4-code-verification: factored-reward model training] The selected three-arm pilot distinguishes a full-SCSC reward change from explicit factor feedback using the fixed initialization from `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`; CoDaPO remains a separate future optimizer comparison. Real improvement requires the frozen, common downstream evaluation after actual verified training.
