# Experiment 17 Protocol: Held-Out Prediction of Unseen Experiments with Environment-Utility & Latent Scaling Laws

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law/PROTOCOL.md>

**Status:** FROZEN 10-18-2026. Zero model calls, strictly $0 API spend.

---

## 1. Background & Motivation (Andrew's Steer)

In review feedback on the Reinforcement Learning (RL) environment-utility scaling law paper (*Which Environments Should LLMs Learn From? Predicting the Utility of Reinforcement Learning Prompt Distributions*), Andrew (Zhanke) Zhou offered three key points:
1. *Novelty:* Scaling laws are no longer novel on their own; usefulness must be the core contribution.
2. *Crux:* What makes scaling laws land is demonstrating that they **predict the outcome of unseen experiments**, particularly for **agentic RL post-training** and **recursive self-improvement (RSI)** on specific environments.
3. *Rigor:* Avoid overclaiming; reviewers will scrutinize whether the empirical claims are solid and informative.

This protocol operationalizes Andrew's steer across three empirical test suites using real multi-scale, multi-rung, and agentic benchmark datasets already committed in the repository.

---

## 2. Mathematical Framework

The paper's compact environment-utility scaling law (Eq. 7, implemented in [`src/rl4cv/utility_model.py`](../../src/rl4cv/utility_model.py)):

$$\hat{U}(N, C, \rho, H) = \beta_0 + \beta_N x_N + \beta_C s(C) + \beta_\rho s(C) z(\log \rho) + \beta_H s(C) z(H)$$

where:
- $N$ is model scale / parameter count, with normalized covariate $x_N = \frac{\log(N / N_a)}{\log(N_b / N_a)}$ ($N_a = 1.7\text{B}, N_b = 4.0\text{B}$).
- $C$ is RL / SFT training compute (in millions of generated/loss tokens), with saturating scale $s(C) = \frac{C}{C + C_0}$ ($C_0$ median training budget).
- $\rho$ is pre-training / current-policy usable signal density (e.g. group-relative mixed-group share $q_{\text{mixed}} = 1 - p^G - (1-p)^G$).
- $H$ is effective coverage (entropy / spread of solvable tasks across the environment).
- $z(\cdot)$ denotes training-fold standardization (zero mean, unit variance).
- $U$ is held-out performance change (utility, $\Delta \text{pass@1}$).

---

## 3. Four Evaluation Suites & Decision Rules

### Suite 1: Recursive Self-Improvement (RSI) on Lean Code Verification (`Expt 08`)
- **Dataset:** 4 scales ($1.7\text{B}, 4\text{B}, 8\text{B}, 14\text{B}$) across 5 continuation rungs ($12.5\%, 25\%, 50\%, 75\%, 100\%$ of matched budget: $0.72\text{M}$ to $5.75\text{M}$ tokens) on 135 VeriBench validation tasks ($1,080$ attempts per cell).
- **Task 1A (Unseen Scale Extrapolation):** Fit law *strictly* on $1.7\text{B}, 4\text{B}, 8\text{B}$ (15 rungs), predict the complete 5-rung trajectory of untouched $14\text{B}$.
  - *Success criterion:* Law RMSE $\le 2.0$ pp, Pearson $r \ge 0.90$.
- **Task 1B (Cross-Regime Transfer):** Fit law *strictly* on Replay ($R$), predict the utility of the unseen Expansion ($E$) regime using Expansion's pre-training $\rho$ and $H$.
  - *Success criterion:* Transfer RMSE $\le 3.5$ pp, Pearson $r \ge 0.95$.
- **Task 1C (RSI Horizon Extrapolation):** Fit law on early rungs ($C \le 50\%$), predict final $100\%$ budget outcome across all 4 scales.
  - *Success criterion:* Law RMSE lower than Last-Observed-Rung baseline with relative error reduction $\ge 30\%$.

### Suite 2: Agentic RL Post-Training & System Evaluation on SWE-bench Verified (`Expt 14`)
- **Dataset:** 164 agentic systems $\times$ 424 tasks.
- **Protocol:** Probe $n_A = 50$ tasks $\to$ predict full held-out $n_B = 374$ tasks across 2,000 random splits.
- *Success criterion:* Two-parameter logistic (2PL) item response theory (IRT) ability model achieves median Spearman $\rho \ge 0.95$ across systems and beats empirical pass@1 in $\ge 60\%$ of splits; MAE reduction $> 0.020$ over raw pass@1 with 95% bootstrap CI excluding 0.

### Suite 3: Leave-One-Environment-Out (LOEO) Math RLVR Scaling Law
- **Dataset:** 4 environment cells ($\text{HH, HL, LH, LL}$) $\times$ 4 scales $\times$ 3 budgets ($14\text{B}$ target).
- **Protocol:** For each cell, fit on the other 3 cells across all scales/budgets; predict the held-out unseen cell on $14\text{B}$.
- *Success criterion:* Overall LOEO RMSE $\le 2.5$ pp; allocation regret lower than uniformly random environment selection.

### Suite 4: Critical Boundary & Anti-Overclaiming Audit
- Disclose exact failure modes, plateau regimes, and zero-signal boundaries (e.g. 100% gradient starvation when $\rho = 0$, as established in Expt 13).
