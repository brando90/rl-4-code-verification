# Experiment 20: CPU Phase 0 calibration

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/RESULTS_phase0_calibration.md>

**TLDR:** Primary calibration gate G0: **PASS**. Frozen item parameters: **verified**. Trainer **FAILED**, unchanged; this CPU follow-up does not authorize training.

Experiment: `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013`. The post-stop CPU dispatcher was authorized on **10-21-2026** to score saved generations, fit calibration models and freeze parameters. The link above is the intended branch publication location.

Declared cohort: VeriBench V1 train **539 tasks / 400 task groups / 4,312 saved samples** (8 samples per task). Strict scoring: **4312/4312** measured; smooth reward: **4202/4312** known (3,203 measured plus 999 registered malformed-source zeros), **110** missing. Joint strict/smooth observed cells **4202/4312**. Panel measured cells **5234/5929**; unmeasured entries remain missing and are never silently recoded as zero.

## Primary held-out calibration

Selected model: **Explanatory 2PL**. Area under the receiver-operating-characteristic curve (AUC): **0.9313 [0.9093, 0.9519] p-val=0.0001**; log loss **0.3044 [0.2761, 0.3325] p-val=n/a** versus population Beta(1,1) baseline **0.4812 [0.4554, 0.5081] p-val=n/a**. Paired baseline-minus-model log-loss gain: **0.1768 [0.1533, 0.2011] p-val=0.0001**.

G0 requires AUC ≥ 0.70 and lower log loss than the in-fold population Beta(1,1) forecast (registered E20 protocol §3; AUC threshold from E13 F2). These are point-estimate gates; calibration error and alternatives are descriptive. No training gate is reopened by a calibration PASS.

Expected calibration error (ECE; 10 equal-width bins): **0.1122 [0.0978, 0.1375] p-val=n/a**. Predicted active share **0.2485 [0.2273, 0.2694] p-val=n/a** versus observed **0.1373 [0.1068, 0.1691] p-val=n/a**. Mean absolute error **0.2366 [0.2173, 0.2554] p-val=n/a**; mean bias **0.1112 [0.08835, 0.1335] p-val=n/a** (prediction minus observation; positive means overprediction).

## Alternatives on the same task folds

| Model | Status | AUC [95% interval] | Log loss [95% interval] | ECE [95% interval] | Predicted / observed active share |
|---|---|---|---|---|---|
| Random-intercept 2PL | available | 0.8735 [0.8358, 0.9088] | 0.3053 [0.2673, 0.3445] | 0.07082 [0.05329, 0.0974] | 0.2076 / 0.1373 |
| Explanatory 2PL | available | 0.9313 [0.9093, 0.9519] | 0.3044 [0.2761, 0.3325] | 0.1122 [0.0978, 0.1375] | 0.2485 / 0.1373 |
| Random-intercept 1PL | available | 0.8709 [0.8321, 0.9074] | 0.3576 [0.3293, 0.3866] | 0.1252 [0.1107, 0.154] | 0.2619 / 0.1373 |
| Explanatory 1PL | available | 0.9335 [0.9122, 0.9535] | 0.3162 [0.2878, 0.3439] | 0.138 [0.1177, 0.1616] | 0.2645 / 0.1373 |
| Features only | available | 0.9243 [0.9018, 0.947] | 0.3171 [0.2881, 0.3453] | 0.1271 [0.104, 0.1518] | 0.2556 / 0.1373 |
| Population Beta(1,1) | available | 0.4226 [0.349, 0.4986] | 0.4812 [0.4554, 0.5081] | 0.168 [0.1377, 0.1989] | 0.3053 / 0.1373 |
| Panel strict rate (ranking only) | available: ranking only | 0.8632 [0.8226, 0.901] | not a probability forecast | not applicable | not applicable |

2PL = two-parameter logistic item response model; 1PL fixes every discrimination slope to one. Panel-rate comparison uses the original 11-system strict pass rates for ranking only. Selected-minus-panel AUC difference: **0.06808 [0.04302, 0.09714] p-val=0.0001**.

Intervals use **10000** paired train-task-group bootstrap draws (registered 10,000; seed **20261021**). Resampling unit: **D-013 train task group**. Limits: conditional on fitted/selected models; not refit or nested-selection uncertainty. AUC p-values above compare with 0.70; paired difference p-values use the two-sided percentile test of zero, floored at 1/draws. Other level statistics and descriptive table entries have p-val=n/a. Selected AUC finite bootstrap draws: **10000/10000**. Eight generated samples are not repeated rescoring trials; rescoring variability was not measured.

## Priors and numerical convergence

Each 2PL family has 20 prior pairs × 5 grouped cell folds; each descriptive 1PL family has 5 residual scales × 5 folds. Every accepted count fit must satisfy maximum absolute gradient ≤ 1e-4 on both the 1,201-node fitting grid and the 4,801-node check grid. The table separates observed counts from the registered required counts.

| Dataset / model | Chosen slope SD / residual SD | Eligible priors / observed / required | Converged CV fits / observed / required | Converged G0 fits / observed / required | Final fit status; fitting / check gradient |
|---|---|---|---|---|---|
| Primary / Random-intercept 2PL | 0.25 / 0.25 | 20 / 20 / 20 | 100 / 100 / 100 | 5 / 5 / 5 | converged; 7.87e-06 / 7.87e-06 |
| Primary / Explanatory 2PL | 0.1 / 0.5 | 20 / 20 / 20 | 100 / 100 / 100 | 5 / 5 / 5 | converged; 6.991e-06 / 6.991e-06 |
| Primary / Random-intercept 1PL | 1 / 1 | 5 / 5 / 5 | 25 / 25 / 25 | 5 / 5 / 5 | converged; 2.193e-08 / 2.193e-08 |
| Primary / Explanatory 1PL | 1 / 0.5 | 5 / 5 / 5 | 25 / 25 / 25 | 5 / 5 / 5 | converged; 3.924e-06 / 3.924e-06 |
| With E05 / Random-intercept 2PL | 0.1 / 1 | 20 / 20 / 20 | 100 / 100 / 100 | 5 / 5 / 5 | converged; 1.667e-07 / 1.667e-07 |
| With E05 / Explanatory 2PL | 0.1 / 0.5 | 20 / 20 / 20 | 100 / 100 / 100 | 5 / 5 / 5 | converged; 9.622e-06 / 9.622e-06 |
| With E05 / Random-intercept 1PL | 1 / 1 | 5 / 5 / 5 | 25 / 25 / 25 | 5 / 5 / 5 | converged; 4.493e-08 / 4.493e-08 |
| With E05 / Explanatory 1PL | 1 / 0.5 | 5 / 5 / 5 | 25 / 25 / 25 | 5 / 5 / 5 | converged; 7.321e-06 / 7.321e-06 |

Primary features-only numerical fits: **5/5 observed**, 5 required; max fitting/check gradients **9.783e-06 / 9.783e-06**.
With E05 features-only numerical fits: **5/5 observed**, 5 required; max fitting/check gradients **3.654e-06 / 3.654e-06**.

## E05 Base-model sensitivity

Alternative including three E05 Base models: **PASS**, selected **explanatory**, AUC **0.9332 [0.9117, 0.9533] p-val=0.0001**, log loss **0.3119 [0.2839, 0.3394] p-val=n/a** versus baseline **0.4812 [0.4554, 0.5081] p-val=n/a**. Primary-selection policy: No outcome-driven replacement: substantive fit-change threshold was not preregistered; report both.

| Model | Mean / maximum absolute slope change | Mean / maximum absolute intercept change | Mean absolute active-probability change | Ability change |
|---|---|---|---|---|
| Random-intercept 2PL | 0.164 / 0.4638 | 6.42 / 7.737 | 0.07803 | 6.713 |
| Explanatory 2PL | 0.01654 / 0.0717 | 2.247 / 2.304 | 0.0153 | 2.316 |
| Random-intercept 1PL | 0 / 0 | 1.344 / 1.427 | 0.001666 | 1.347 |
| Explanatory 1PL | 0 / 0 | 1.378 / 1.44 | 0.003281 | 1.396 |

The registration says to add Base models if the fit changes but supplies no substantive-change threshold. Both fits must be reported, preserving the specified 11-system primary; no favorable-G0 substitution is made.

## Smooth reward and dimensionality

Graded smooth-reward model: **available**; measured/declared smooth cells **4202/4312**, missing **110**. fitting/check maximum gradients **3.299e-06 / 3.299e-06** (gate ≤ 1e-4). Predicted nonconstant-category share **0.9542** across all 539 items. Observed category-nonconstant share sharp bounds **[0.7792, 0.8033]** and exact-reward-nonconstant share sharp bounds **[0.8367, 0.8497]**; these deterministic bounds include all missing smooth cells and are not confidence intervals. Smooth summaries are conditional on observed smooth cells: missing-at-random is not established. The ordinal forecast is a lower bound on exact smooth-reward nonconstancy because within-bin differences are unidentifiable. These are posterior replications, not prospective predictions of the already observed Phase 0 outcomes.
Smooth missingness reasons: **{'unresolved: duplicate fully qualified declaration identity': 110}**. Likelihood handling: **unobserved smooth cells are ignored through the observation mask; estimates are conditional on observed smooth cells and missing-at-random is not established**. Registered malformed-source zeroes are observed zero rewards; duplicate fully qualified declaration identities remain missing.

| Strict difficulty versus graded threshold | Pearson [95% interval] | Spearman [95% interval] | Kendall [95% interval] |
|---|---|---|---|
| First ability threshold −cut₁/b | 0.735 [0.6935, 0.7724] | 0.7367 [0.6865, 0.7809] | 0.5493 [0.5062, 0.592] |
| Literal first logit cut (sensitivity) | -0.7347 [-0.7721, -0.6935] | -0.7358 [-0.7808, -0.6826] | -0.5474 [-0.5901, -0.5014] |

Correlation intervals: **1000** item-group bootstrap draws (registered 1,000), **400** groups; conditional on fitted parameters, no model refitting; all correlation p-val=n/a.

Tied versus untied skill comparison: **available**. Joint held-out log likelihood: tied **-5761**, untied **-5763**, difference **-1.726**, **4202** observed paired cells / **4312** declared. The log score integrates the strict outcome and ordinal category jointly, preserving within-cell dependence. Selection limitation: held-out likelihood scores only cells where both strict and smooth were observed; it is conditional on that selected cohort and missing-at-random is not established. This descriptive partial-reward analysis does not gate strict G0; a failed full-fit or held-out numerical check makes the dimensional comparison unavailable.

| Dimensional model | Full-fit convergence | Fitting / finer-check gradient | Converged held-out fits / observed / required |
|---|---|---|---|
| tied | yes | 4.013e-06 / 4.013e-06 | 5 / 5 / 5 |
| untied | yes | 1.361e-06 / 1.361e-06 | 5 / 5 / 5 |

Supplementary absolute agreement on the saved smooth-category predictions: mean absolute error bounds **[0.1955, 0.2148]**, mean bias (prediction minus observation) bounds **[+0.1509, +0.1750]**, p-val=n/a. Binary category-nonconstancy is determined for 526/539 tasks and unresolved for 13; these are deterministic missing-label bounds, conditional on the fitted model, not confidence intervals. [Calculation and source hash](expt_v1/results/phase0b/smooth_agreement_bounds.json).

The full-precision held-out likelihoods are −5760.845167 (tied) and −5762.570966 (untied), with difference **−1.725799 [n/a, n/a], p-val=n/a**. No likelihood-difference uncertainty interval was registered or computed; this is a descriptive comparison, not evidence about shared skills across systems.

## Frozen parameters and completeness

Native `rl4cv.forecast.verify_forecast`: **True**; freeze status **verified**; task count **539**; all parameter arrays have 539 finite entries **True**; input identity matches **True**. Start-policy ability **-3.963**, posterior standard deviation **0.0784**. File: `/lfs/skampere1/0/brando9/rl4cv_e20/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/forecasts/phase0_item_parameters_e20.json`.

The frozen forecasts target future draws and retain both posterior-integrated and ability-mean probabilities. The payload does not invent numeric H1–H4 training-effect forecasts; those would require a separate pretraining registration if training were ever reauthorized. The [canonical input pins](expt_v1/input_pins_e20.json) are byte-identical to the analysis input pins, with SHA-256 `777d9096c08b56ba9636d477dc942ba63368e1f6509e8931e35d256614f4c3c5`.

Missing strict cells: **0**; missing smooth cells: **110** (full list in `input_audit.json`; all panel statuses in `panel_train_cells.csv`). Scorer-versus-adapter strict disagreements: **0/3,203 compared cells** (999 registered parse-failure zeros and 110 missing partial cells are not compared); the pinned scorer remains authoritative. Strict G0 uses its full strict cohort independently of descriptive partial-reward missingness. No validation/test outcomes or new generations are used in this analysis.

First missing-cell receipts:

- `aerospace_set_real__my_fprime_crc_match` sample 6: strict measured; smooth unresolved: duplicate fully qualified declaration identity.
- `aerospace_set_real__my_fprime_sequence_nonempty` sample 2: strict measured; smooth unresolved: duplicate fully qualified declaration identity.
- `aerospace_set_synthetic__my_clamp_actuator` sample 1: strict measured; smooth unresolved: duplicate fully qualified declaration identity.
- `aerospace_set_synthetic__my_clamp_actuator` sample 4: strict measured; smooth unresolved: duplicate fully qualified declaration identity.
- `aerospace_set_synthetic__my_edac_syndrome_detect` sample 6: strict measured; smooth unresolved: duplicate fully qualified declaration identity.

**Copy-ready message:** I evaluated the saved calibration outputs under the registered task-group checks. The calibration gate is PASS, and the parameter freeze is verified; the trainer remains failed and no training has resumed.

**TLDR-end:** [rl4cv: E20 CPU calibration] `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013`: G0 **PASS**, parameter freeze **verified**; trainer **FAILED**, unchanged.

**Snapshot:**

```text
Primary model: explanatory
G0: PASS
Tasks/groups observed: 539/400
Native freeze hash verification: True
Trainer: FAILED; no training authorized
```
