# Experiment 13 protocol (DRAFT, not locked): factored and IRT-guided RL vs strict-reward RL from Qwen3-4B SFT on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/PROTOCOL.md>

**TLDR:** This draft fixes the definitions, gates, arms, budgets, analysis and forecasts for [experiment 13](README.md):

1. Per-declaration partial-credit factors (Phase 0).
2. A conjunctive item response theory (IRT) model validated against held-out pass@1 and pass@k (Phase 1).
3. Four GRPO (group relative policy optimization) arms from the same supervised fine-tuning (SFT) checkpoint (Phase 2).

Thresholds are agent-suggested; Brando may edit them until the matching lock. Lock 1 precedes any Phase 0 or Phase 1 outcome; lock 2 precedes the main RL runs.

**Draft status:** written 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando. Not locked; no outcome has been read except the zero-call design evidence in the README (`design_evidence/`), which motivates the design and is not a study outcome.

## 1. Locks

| Lock | Freezes | Before |
|---|---|---|
| L1 | §§ 3–4: scorer definition, controls, G0 and G1 metrics and thresholds, Phase 1 model set and validation splits, forecasts F0–F2 | Any per-declaration score of a study output, any Phase 1 fit |
| L2 | §§ 5–8: start checkpoint hash, trainer, sampler, hyperparameters, arms, budgets, seed count, evaluation schedule, analysis, forecast F3 | The first main-run update (pilot outcomes may set the seed count and horizon by the rules in § 5) |

Freeze each forecast with `rl4cv.forecast.freeze_forecast` before reading the outcome it predicts. Forecasts are append-only. Later changes are numbered amendments that state what had been seen.

## 2. Populations and splits (D-013)

- **Splits.** VeriBench V1 is split train 539 / validation 135 / test 222, using the manifest in experiment 08's `expt_v1/results/split/`.
- **Training data.** Training, and every input to arm C's reward and sampler, use train-split tasks only.
- **Validation.** Phase 0 measurements, Phase 1 validation and checkpoint selection use validation tasks.
- **Test.** The test split is generated and scored once per selected checkpoint.
- **Reporting.** Report core (152) and IndustrySet (70) test results separately as well as pooled.

## 3. Phase 0 — per-declaration scorer and G0 (CPU)

### Scorer

Lean v4.22.0, the VeriBench-pinned toolchain. The scorer compiles each extracted file once, collects per-declaration errors, and runs `#print axioms` for every stated theorem.

- `e ∈ {0,1}`: Lean was extracted and the output was not cut off at the token cap.
- `d ∈ [0,1]`: the fraction of top-level declarations that elaborate without an error message.
- `t ∈ {0,1}`: every implementation `def` and every `example` elaborates without error. `native_decide` is allowed only in examples, as VeriBench allows.
- `p ∈ [0,1]`: the fraction of stated theorems whose axioms are within {`propext`, `Classical.choice`, `Quot.sound`}. A theorem with an error, `sorry`, `admit`, a declared axiom or `native_decide` fails.
- Guards:
  - `v ∈ {0,1}`: the existing non-vacuity screen (`rl4cv.rewards.is_vacuous_statement`).
  - `n_thm`: the stated-theorem count, logged against the reference's count.
- Strict = `e · 1[d = 1] · t · 1[p = 1] · v · 1[n_thm ≥ 1]`.

### Controls (all required)

1. **Authored files**, one per condition, each with the expected component values:
   - one failed proof among proved ones;
   - a syntax error in the implementation;
   - `sorry` in one theorem;
   - `native_decide` in a theorem;
   - a vacuous theorem;
   - a truncated file;
   - a file with no theorem.
2. **Exact reproduction of `kernel_binary`** on every known cell of experiment 08's ladder (20,520 cells) and experiment 05 (21,504 cells). Any mismatch fails the control until explained and fixed by an amendment.

### G0, measured on existing validation outputs

| Metric | Threshold |
|---|---|
| Strict reproduction (control 2) | 100% of known cells |
| Dense-only share: SFT 4B full-schedule validation tasks whose 8 strict outcomes are equal but whose arm-B score varies | ≥ 0.15 (forecast F0: 0.50) |
| Predictive validity within each size: among tasks with strict rate 0 at the 50% rung, AUC of mean arm-B score for "strict rate > 0 at the 100% rung" | ≥ 0.65 for the 4B size; reported for 1.7B and 8B |

If G0 fails, stop arms B and C (README decision rules).

## 4. Phase 1 — the measurement model and G1

### Data

The models are fit to per-component outcomes (`e`, `d`, `t`, `p`, strict) from:

- experiment 08's ladder: 19 policies × 135 validation tasks × 8 samples;
- experiment 05: 3 × 896 × 8;
- experiment 01: 9 × 896 single responses;
- VeriBench experiment 103's seven single-call frontier models × 896, re-scored from their saved Lean files.

SWE-bench side: experiment 07's `per_cell_e07.jsonl.gz`, 164 systems × 424 tasks, with components gate, T_fix and T_keep and target `resolved`.

### Models

- **M0:** the empirical per-task strict rate for a policy.
- **M1:** the arm-B score, mapped to probability by monotone regression fit on training folds.
- **M2:** a 2PL model on strict only, `P = σ(a_j(θ_i − b_j))`.
- **M3:** conjunctive multicomponent, `P(strict) = Π_k σ(a_jk(θ_ik − b_jk))` for k ∈ {t, p}. Here `e` is modeled as a logistic factor with policy-specific length behavior, and `d` and `p` as binomial over declarations and theorems.
- **M3e:** M3 with `b_jk = f_k(task features)` (Python-source embedding, reference theorem count, domain, source lines) and `θ_ik = α_k + β_k · log(SFT tokens)` within a model size.
- **Fitting:** maximum a posteriori with N(0, 1) priors on abilities and N(0, 2) on difficulties, plus log-normal priors on discriminations. The R package `GMLTM` implements the multicomponent model family; a direct PyTorch or NumPyro fit is equally acceptable. Record the library and version at L1.

### Validation (G1)

- **Leave-checkpoint-out:** fit on base and the 12.5–75% rungs; predict the full-schedule rung of each size.
- **Leave-task-out:** 5-fold over validation tasks, grouped as in D-013.
- **Metrics:**
  - per-sample log-loss;
  - AUC;
  - Pearson and Spearman of implied vs measured pass@1 and pass@8 across held-out policies;
  - mean error, implied minus measured.
- **G1 passes** when M3 or M3e has lower held-out log-loss than both M0 and M1, with a task-bootstrap 95% interval of the difference excluding 0, and Pearson ≥ 0.80 for pass@1 (forecast F1: 0.85). For reference, Item Response Scaling Laws reported 0.78–0.93 on four test-time benchmarks.
- **SWE-bench:** report the same metrics on experiment 07's matrix for resolved and pass@1. This is the input to experiments 10 and 11, not a gate here.

### H2 (signal forecast)

1. Generate two independent train-split batches from the start policy: 539 tasks × 8, Phase 2 sampler.
2. Fit train-task parameters on batch 1.
3. Predict mixed strict groups on batch 2. The forecast is AUC = 0.75 (F2); the gate is AUC ≥ 0.70.

## 5. Phase 2 — RL arms

### Start checkpoint and trainer

- **Start:** experiment 08 `sft_4B_f1p0` (Qwen3-4B Base, 658 SFT steps). Record the export hash at L2.
- **Trainer:** one GRPO implementation for every arm: the installed NeMo RL or verl, whichever passes the technical gates first, never switched mid-study.
- **Draft hyperparameters, to confirm at L2:**
  - AdamW, learning rate 1e-6;
  - clip 0.2 (upper 0.28);
  - Kullback–Leibler coefficient 0;
  - token-level loss normalization;
  - G = 8;
  - 32 prompts per update;
  - 100 updates;
  - maximum 8,192 new tokens;
  - rollout temperature 1.0 with no top-k or top-p truncation;
  - truncated importance sampling with cap 2.

### Arm rewards and samplers

| Arm | Reward | Sampler |
|---|---|---|
| A | Strict | Uniform without replacement within an epoch |
| B | SCSC-style geometric mean of the graded components `d`, `t`, `p`, gated by `e`, `v` and `n_thm ≥ 1`. The exact form, including any floor that keeps one zero component from erasing partial credit, is frozen at L1 from Phase 0's validation distributions, before any RL outcome | Same as A |
| C | `Π_k σ(a_jk(ẑ_r − b_jk))`, where `ẑ_r` is the rollout's MAP quality given its outcomes on the task's units (declarations, examples, theorems), using train-task unit parameters from Phase 1 (method of [arXiv 2609.35646](https://arxiv.org/abs/2609.35646)) | 0.5 uniform + 0.5 proportional to the task's information at the current policy, `Σ_u a_ju² P_ju(1 − P_ju)`, with θ refit every 10 updates from the arm's own train rollouts |
| P | An independent draw from the empirical distribution of B's rewards on phase 1 batch 1, independent of the rollout | Same as A |

### Matched budget

- Every arm generates exactly 32 × 8 rollouts per update for 100 updates.
- Groups with zero reward variance contribute no loss in every arm.
- Sensitivity arm A2 (only if B or C beats A): A with 2× oversample-and-filter at the same update count. It checks that A's loss was not just the missing refills.

### Seeds

- **Pilot:** A × 2 seeds, B, C and P × 1 seed, 30 updates.
- **Main:** 3 seeds per arm. Use 5 if the pilot's seed standard deviation implies a minimum detectable effect, 2.8 × standard error of the arm difference, above 4 percentage points. The count is decided at L2, before any main-run outcome.

## 6. Evaluation

- **Sampling:** experiment 08's ladder configuration, for comparability with the start checkpoint's validation numbers.
- **Validation:** every 25 updates, 135 tasks × 8 samples. Select the checkpoint with the highest validation strict pass@1; ties go to the later checkpoint. The same rule applies to every arm.
- **Test:** 222 tasks × 16 samples per selected checkpoint, scored with the hash-pinned VeriBench scorer (`external/deps.lock.json`).
- **FSC:** one sample per task, from the validated judge through Valkyrie (D-102, D-108), after route controls.
- **Hidden gold tests:** through experiment 12's frozen adapter, if its coverage gate passed.

## 7. Technical gates (pilot, before any main run)

| Gate | Requirement |
|---|---|
| T1 | Generation/trainer log-probabilities on a fixed probe batch: median absolute difference ≤ 0.01, 99th percentile ≤ 0.10, tokens truncated by importance sampling ≤ 1% |
| T2 | One real update changes the weight hash; the refit generator matches trainer log-probabilities on the probe batch with median ≤ 0.01 |
| T3 | Save and resume reproduce the next update's loss on the same batch within 1e-3 |
| T4 | Measured seconds per update and Lean scoring latency. Recompute § 5's budget; Brando approves devices at L2 |
| T5 | Arm A's own train strict reward, moving average over 10 updates, rises ≥ 2 percentage points from updates 1–10 to 21–30. Otherwise extend the pilot once to 60 updates; otherwise stop |

## 8. Analysis

### Primary estimand

- Test strict pass@1 per arm: the mean over 222 tasks of the success rate over 16 samples, averaged over seeds.
- Primary contrasts: B − A and C − A, Holm-adjusted at α = 0.05 (two-sided).

### Inference

- **Hierarchical bootstrap,** 10,000 draws: resample seeds within each arm, then tasks paired across arms; 95% percentile intervals.
- **Exact permutation test over seed labels:** reported as descriptive only. With 3 seeds per arm its smallest one-sided p is 0.05, so it cannot clear the Holm threshold.

### Secondary analyses

- pass@4 and pass@16 (unbiased estimator).
- Contrasts C − B, B − P and C − P.
- Regressions: tasks with a start strict rate above 0.5 that fall below 0.5.
- Per-component changes.
- Test FSC and SCSC.
- Hidden gold-test pass rate.
- Theorem-count and vacuity audits.

### Mechanism

- Per update, the share of groups with nonzero advantage under each arm's reward.
- Test gains by stratum: start strict rate 0 vs > 0, crossed with partial progress 0 vs > 0.
- Bottleneck-component transitions under M3.

### Missing cells

- Infrastructure retries rerun the identical cell.
- Cells still missing are listed and kept in the declared denominator.
- Primary results use the common measured cohort and give full-manifest bounds.

## 9. Forecasts (agent-suggested; freeze before the outcome)

| ID | Quantity | Forecast | Freeze before |
|---|---|---|---|
| F0 | Dense-only share, SFT 4B validation | 0.50 | Phase 0 measurement |
| F1 | Pearson, implied vs measured pass@1, held-out full-schedule checkpoints (M3e) | 0.85 | Phase 1 fit |
| F2 | AUC, mixed-group prediction on train batch 2 | 0.75 | Batch 2 scoring |
| F3 | Test strict pass@1 differences in percentage points: B − A, C − A, P − A | +2.0, +3.0, 0.0 | First main-run update |
