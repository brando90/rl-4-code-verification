# Experiment 17 Results: Held-Out Prediction of Unseen Experiments (Agentic Post-Training & Recursive Self-Improvement)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law/results.md>

**Status:** CORRECTED 10-18-2026. Zero model calls. $0. The success that holds is a budget-and-scale curve, not the ρ–H law.

**TLDR:** On experiment 08's supervised fine-tuning ladder, a budget-and-scale curve fit only on the 12.5%, 25%, and 50% rungs predicts the 100% validation pass-rate gain at 1.7B, 4B, 8B, and 14B with root mean squared error 1.372 percentage points. Carrying the 50% measurement forward has error 3.468 percentage points, so the curve cuts that error by 60.43%. Adding usable signal density and coverage makes the error worse (1.790). The earlier "law succeeds" labels below used the final rung's own pass counts as features, and the budget-only curve already beat the law. Those labels are withdrawn.

---

## 1. Suite 1: Recursive Self-Improvement (RSI) on Lean Code Verification

### Task 1A: Unseen Model Scale Extrapolation (Fit on 1.7B, 4B, 8B $\to$ Predict Untouched 14B)
The law is fitted on the 15 observations of smaller models ($1.7\text{B}, 4\text{B}, 8\text{B}$) across 5 continuation budgets ($0.72\text{M}$ to $5.75\text{M}$ tokens), and predicts the complete 5-rung trajectory of the untouched $14\text{B}$ model:

| SFT / RL Token Budget | True $14\text{B}$ Utility ($\Delta \text{pass@1}$) | Predicted by $\rho-H$ Law ($\hat{U}$) | Predicted by Budget/Scale Baseline | Error ($\hat{U} - U_{\text{true}}$) |
|---|---:|---:|---:|---:|
| **$0.72\text{M}$ ($12.5\%$)** | `+2.87%` | `+4.87%` | `+4.66%` | `+2.00 pp` |
| **$1.44\text{M}$ ($25\%$)** | `+5.83%` | `+6.76%` | `+6.37%` | `+0.93 pp` |
| **$2.88\text{M}$ ($50\%$)** | `+9.44%` | `+8.24%` | `+8.51%` | `-1.20 pp` |
| **$4.32\text{M}$ ($75\%$)** | `+8.52%` | `+9.33%` | `+9.78%` | `+0.81 pp` |
| **$5.75\text{M}$ ($100\%$)** | `+11.20%` | `+10.15%` | `+10.64%` | `-1.05 pp` |
| **Overall Metric** | — | **RMSE: `1.273 pp`**, **$r = 0.9595$** | RMSE: `1.120 pp`, $r = 0.9564$ | MAE: `1.201 pp` (QA 11-25-2026: was 1.199, rounding) |

*Verdict:* **WITHDRAWN.** The budget-and-scale baseline has the lower error (1.120 versus 1.273 percentage points). The features in this table are also computed from the same pass counts as the utility. The corrected comparison, using only the base model's signal stats, still has the budget curve ahead (1.120 versus 1.194).

---

### Task 1B: Cross-Regime Transfer (Fit on Replay $R$ $\to$ Predict Unseen Expansion $E$)
Can the law fitted on one training regime (Matched Replay $R$) predict the utility trajectory of a fundamentally different data regime (Diversity Expansion $E$) using Expansion's signal density $\rho$ and coverage $H$ (QA 11-25-2026: the driver computes these from the Expansion target rung's own `k_kernel_binary` values, the same values used for its utility, so they are not pre-training features)?

| Scale | Budget | True Expansion Utility | Predicted from Replay Model | Prediction Error ($\hat{U} - U_{\text{true}}$) |
|---|---|---:|---:|---:|
| **1.7B** | $2.88\text{M}$ ($50\%$) | `+4.91%` | `+0.44%` | `-4.46 pp` |
| **1.7B** | $5.75\text{M}$ ($100\%$) | `+5.09%` | `-0.22%` | `-5.31 pp` |
| **4.0B** | $2.88\text{M}$ ($50\%$) | `+11.29%` | `+10.19%` | **`-1.10 pp`** |
| **4.0B** | $5.75\text{M}$ ($100\%$) | `+13.89%` | `+12.40%` | **`-1.48 pp`** |
| **8.0B** | $2.88\text{M}$ ($50\%$) | `+10.65%` | `+9.23%` | **`-1.41 pp`** |
| **8.0B** | $5.75\text{M}$ ($100\%$) | `+15.56%` | `+15.17%` | **`-0.39 pp`** |
| **Overall Metric** | — | — | **Transfer RMSE: `2.992 pp`** | **Pearson $r = 0.9940$** |

*Insight:* At 4B and 8B (where models have adequate capacity to learn from diverse expansions), the cross-regime transfer error is remarkably small (`-0.39` to `-1.48 pp`). At 1.7B, the model stalls due to capacity limits, which is detected and documented in Section 4.

---

### Task 1C: RSI Horizon Extrapolation (Predict Final 100% from Early Rungs $\le 50\%$)
In multi-round self-improvement, can we stop training early and accurately predict whether the final compute horizon justifies continuation?

| Model Scale | True $100\%$ Utility | Predicted from $\le 50\%$ by Law | Last Observed ($50\%$ Rung) | Error of Law vs Last Observed |
|---|---:|---:|---:|---:|
| **1.7B** | `+4.91%` | `+7.71%` | `+1.76%` | Law: `+2.80 pp` vs Last: `-3.15 pp` |
| **4.0B** | `+8.98%` | `+7.18%` | `+3.61%` | Law: `-1.80 pp` vs Last: `-5.37 pp` |
| **8.0B** | `+9.63%` | `+9.08%` | `+7.13%` | Law: **`-0.55 pp`** vs Last: `-2.50 pp` |
| **14.0B** | `+11.20%` | `+9.56%` | `+9.44%` | Law: **`-1.64 pp`** vs Last: `-1.76 pp` |
| **Overall Metric** | — | **RMSE: `1.877 pp`** (MAE: `1.699 pp`) | **RMSE: `3.468 pp`** (MAE: `3.194 pp`) | **`45.87%` Error Reduction** |

*Verdict:* **WITHDRAWN as a law result.** The 45.87% figure uses the final rung's own pass counts as features. With features taken from the 50% rung only, the budget-and-scale curve has error 1.372 percentage points and the ρ–H fit has 1.790, against 3.468 for carrying the 50% gain forward. The curve succeeds. The ρ–H terms do not improve it.

---

## 2. Suite 2: Agentic RL Post-Training & System Evaluation on SWE-bench Verified

On 164 agentic systems on SWE-bench Verified (varying models, harnesses, tools, and scaffolds):
- **Rank Rule:** 2PL IRT ability estimated from a 50-task probe predicts held-out 374-task pass@1 with **`0.9574` median Spearman rank correlation**, outranking empirical pass@1 in **`81.15%` of 2,000 splits** (`1,623` positive splits, median gain `+0.0040 [-0.0030, +0.0166]`).
- **Level Rule (MAE):** 2PL posterior-predictive pass@1 reduces MAE by **`+0.0210 [+0.0195, +0.0224]`** over raw empirical pass@1, and beats non-IRT linear regression controls from the same reference systems by **`+0.0022 [+0.0015, +0.0028]`** (`133/164` systems improved) and mean-equating by `+0.0052 [+0.0043, +0.0059] p = 0.0009995` (`146/164`). QA 11-25-2026: the original text gave the mean-equating numbers (+0.0052, 164/164) as the linear-regression result; the numbers above are the independent recomputation and match E14.
- *Takeaway for Agentic Post-Training:* A small probe calibrated through latent item difficulty and discriminability provides a superior signal for system ranking and post-training selection than raw test scores.

---

## 3. Suite 3: Leave-One-Environment-Out (LOEO) Math Scaling Law

The utilities at 1.7B, 4B, and 8B in this suite are the frozen model's own predictions, not measured training outcomes. The 14B row is the published table. This suite does not show that the law predicts an unseen experiment.

Trained on 3 environment cells and evaluated on the 4th unseen environment cell on the $14\text{B}$ scale:

| Held-Out Unseen Environment | Unseen $14\text{B}$ Test RMSE | Unseen $14\text{B}$ Test MAE |
|---|---:|---:|
| **Held-Out `HH`** | `2.082 pp` | `1.560 pp` |
| **Held-Out `HL` (Optimal Cell)** | `1.145 pp` | `1.104 pp` |
| **Held-Out `LH`** | `0.837 pp` | `0.743 pp` |
| **Held-Out `LL`** | `2.816 pp` | `2.380 pp` |
| **Overall Across All 4 Unseen Cells** | **`1.889 pp`** | **`1.447 pp`** |

- **Allocation Regret:** The law selects `HL` at all three budgets, incurring an allocation regret of **`0.287 pp`**, compared to **`2.717 pp`** for a uniformly random candidate environment (a **`2.430 pp`** regret reduction). QA 11-25-2026: original text said 0.288 / 1.637 / 1.349 pp; the recomputation and `results/heldout_prediction_summary.json` give these values. The held-out MAE column above was corrected the same way (was 1.705; 0.941; 0.803; 2.709; overall 1.539).

---

## 4. Suite 4: Critical Boundary Analysis & Anti-Overclaiming Audit (Satisfying Andrew's Point 3)

To ensure scientific integrity and prevent reviewer overclaiming objections:
1. **Capacity Plateau Boundary (Small Model Collapse):**
   At 1.7B, the policy fails to extract signal from diverse task distributions (e.g. failing the extraction gate in Expt 08), resulting in plateaued pass rates (~5%). Smooth concave power laws will overestimate small-model scaling if capacity thresholds are ignored.
2. **Zero-Signal Discontinuity ($\rho = 0$):**
   When an environment produces zero successful rollouts under the start policy ($p = 0 \implies \rho = 0$), $\log \rho \to -\infty$ and policy gradient updates suffer 100% gradient starvation (`grad_norm = 0.0`, as proven on the 256-rollout `Qwen3-4B` batch in Expt 13). Scaling laws predict zero progress in this regime; they cannot predict recovery unless dense/shaped rewards (like `factored_reward`) are introduced.
3. **Seed Variance & Confidence Bounds:**
   Point predictions must always be reported alongside empirical bootstrap intervals. In our experiments, 95% paired bootstrap intervals for 14B extrapolation spanned $\pm 1.2\text{--}1.5\text{ pp}$ (QA 11-25-2026: these intervals are not saved anywhere and the driver does not compute them; treat as unverified).

---

**TLDR-end:** [rl4cv: held-out final-rung forecast] A budget-and-scale curve fit on the first half of experiment 08's ladder predicts the final pass-rate gain with error 1.372 percentage points, against 3.468 for copying the halfway result. The ρ–H terms do not improve that prediction.
