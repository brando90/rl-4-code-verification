# Experiment 16 Night 2 dispatch prompt — Toy GINC HMM $\rho$–$H$ Environment-Generation Law with KL Regularization, Multi-Token Outputs, and Mixture Candidates (`[p 8/10]`)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/PROMPT_dispatch_e16_night2.md>

**TLDR:** Execute Night 2 (`expt_v2` / `pilot_v3`) of `16_toy_env_generation_ginc_hmm_rho_h_law` on CPU (`$0` spend) to fix the two failure modes discovered in Night 1 (`0/288` positive target-gain runs due to unregularized Group Relative Policy Optimization (GRPO) catastrophic forgetting `corr = -0.92`, and `corr(log \rho, H) = 0.995` collinearity from 1-token answers): add Kullback-Leibler (KL) regularization (`kl_coef = 1.0`) to the start policy, require multi-token hidden-state/emission predictions ($K_{\text{out}} = 4$ tokens so $\log \rho$ and conditional entropy $H$ decorrelate), include generator-proposed mixture environments in the candidate pool, and test whether Eq. 7 ($\rho \cdot H$ scaling law) selects/generates an environment with strictly positive held-out target utility at scale `n4`.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Context from Night 1 (`expt_v1/results/pilot_v2`)

- In Night 1 (branch `ub9/e16-toy-env-generation`, PR `#15`), fitting Eq. 7 on scales `n1`–`n3` predicted held-out scale `n4` (604k params) with rank accuracy `0.742` (vs `0.500` chance) and `0.00` pts regret (vs `12.63` pts for uniform random choice).
- However,Night 1's verdict was **NOT YET MEANINGFUL (CHOICE ONLY)** because:
  1. `0/288` unregularized GRPO runs improved target accuracy (`corr(in-env gain, target utility) = -0.92`; 2-concept envs lost `-27.1` pts vs `-4.2` pts for 64-concept envs).
  2. `corr(log \rho, H) = 0.995` because 1-token answers bound conditional entropy and alignment together.
  3. A diagnostic with `kl_coef = 1.0` (`diag_kl.log`) eliminated catastrophic forgetting on `n3 e10` (target `0.502 -> 0.501` while in-env rose `0.725 -> 0.818`).

## 1. Night 2 (`expt_v2`) design & implementation

Work in a dedicated clone `/lfs/skampere1/0/brando9/rl4cv_e16_night2/rl-4-code-verification` on branch `ub9/e16-toy-env-generation` (CPU only, `nice -n 10`, `$0` spend):

1. **Multi-token target & environment rollouts ($K_{\text{out}} = 4$ tokens):**
   - Extend the GINC Hidden Markov Model (HMM) task in `expt_v2/` so each prompt asks the policy to predict the next $K_{\text{out}} = 4$ tokens (or hidden-state + 3 continuation tokens), verified token-by-token and jointly by the exact forward-algorithm oracle.
   - Verify before running GRPO that across the candidate environments, `|corr(log \rho, H)| < 0.85` (decorrelating alignment $\rho$ from multi-token conditional entropy $H$).
2. **KL-regularized GRPO (`kl_coef = 1.0`) + stronger pretraining:**
   - Include the exact per-token KL penalty $\beta_{\text{KL}} D_{\text{KL}}(\pi_\theta \,\|\, \pi_0)$ with $\beta_{\text{KL}} = 1.0$ in the GRPO loss so training on specialized environments cannot erase multi-concept target competence.
   - Ensure at least `30%` of training runs achieve positive held-out target utility ($U > 0$).
3. **Generator-proposed mixture environments:**
   - In addition to the 12 base grid environments (`e00`–`e11`), add 4 mixture/generated candidate environments (`m00`–`m03`) that sample from high-$\rho$ and sweet-spot-$H$ regimes.
4. **Full 4-scale sweep (`n1, n2, n3` train scales $\to$ `n4` held-out test scale):**
   - Run 4 scales × 16 environments (12 grid + 4 mixtures) × 2 seeds × 3 budgets on CPU (`nice -n 10`).
   - Evaluate Eq. 7 (`\rho`–`H` law) fit on `n1`–`n3` for predicting held-out `n4` utility against all baselines: (a) uniform random environment, (b) best fixed environment at `n3`, (c) highest pass-variance / mixed-group share at `n4`, (d) $\rho$-only, and (e) $H$-only.

## 2. Verification, publication & notifications

1. Send `[RUN START] rl4cv-e16-night2-ginc-hmm-rho-h` To `brando.science@gmail.com` with CC `brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai`.
2. Add unit tests in `tests/test_e16_ginc_toy.py` covering multi-token forward scoring, KL penalty gradients, and mixture environment determinism; run `pytest -q tests/test_e16_ginc_toy.py`.
3. Update `experiments/16_toy_env_generation_ginc_hmm_rho_h_law/results.md` with the Night 2 tables, bootstrap 95% confidence intervals (`x [lo, hi] p-val=...`), and explicit verdict (`MEANINGFUL POSITIVE TRANSFER` vs `TIE WITH BASELINES` vs `NO ADVANTAGE`).
4. Commit and push to `ub9/e16-toy-env-generation` (updating PR `#15`), and send `[RUN DONE] rl4cv-e16-night2-ginc-hmm-rho-h: success` To `brando.science@gmail.com` with CC `brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai`.
