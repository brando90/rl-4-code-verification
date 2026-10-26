# Experiment 13 v4: Codex consult on the proposed V4-A4, 10-20-2026

**TLDR:** One read-only consult (Codex `gpt-6-astra`, ultra) graded the proposed V4-A4 ADOPT WITH CHANGES, 8/10. All three must-fix items are incorporated in the adopted [V4-A4](AMENDMENT_V4-A4_importance_correction_at_uncertified_positions_10-20-2026.md). The verdict follows verbatim.

The prompt included the dispatch 2 blocker report, V4-A1, NeMo RL 0.4.0 `loss_functions.py` lines 270–370, and the four-rule proposal.

**ADOPT WITH CHANGES — 8/10.**

Defensible for a machine-learning paper as a disclosed approximation. The 2× cap bounds each substituted weight’s absolute error by 1, **not gradient bias by 1%**. V4-T1’s agreement thresholds exclude uncertified positions from probability-error quantiles; they cannot establish negligible bias there.

Must-fix wording:

- **[p 10/10] Prevent hidden changes:** “A4 changes the actor-loss estimator. Preserve unknown generator probabilities as unknown; use detached imputation only for actor correction. Verify unchanged policy ratios, clipping, advantages, and normalization. Audit other consumers: active generation-dependent Kullback–Leibler regularization requires an explicit resolution before launch. Exclude imputations from measured agreement and label affected diagnostics.” The [v0.4.0 source](https://github.com/NVIDIA-NeMo/RL/blob/v0.4.0/nemo_rl/algorithms/loss_functions.py) also uses `generation_logprobs` in regularization and entropy metrics.

- **[p 10/10] Make the guard meaningful:** “Require uncertified fractions ≤1% among both generated positions and valid actor-loss tokens, aggregated across all ranks and accumulation microbatches before each optimizer step. A breach stops the training run; never discard individual rollouts or resample. Preserve all existing support gates.”

- **[p 9/10] Quantify sensitivity:** “Additionally report certified log-weight 1st-percentiles and the bound \(B=N^{-1}\sum_{t\in U}|\ell_t|\), where \(N\) counts actor-loss tokens, \(U\) contains uncertified tokens, and \(\ell_t\) is their unweighted clipped loss.” This bounds absolute loss perturbation against exact capped correction, not gradient perturbation.

Deferring the sampler hook is reasonable under these conditions.

