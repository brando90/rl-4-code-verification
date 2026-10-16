# Experiment 10 v2 dispatch prompt — Matched-Test-Lists Sensitivity (`164 × 421`) & 2PL IRT Validation-Ability Promotion Gate (`IRT-S0+` / `R_irt`) (`[p 8/10]`)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/expt_v2/PROMPT_dispatch_e10_v2_irt_gate.md>

**TLDR:** Execute `10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs` (`expt_v2`, zero model calls, CPU only, `$0` spend) to: (1) resolve the `(164, 421)` vs `(164, 420)` shape stop rule that blocked `expt_v1`'s `matched_test_lists` sensitivity check (3 of the 4 drift tasks lie in the 424-task common cohort, leaving `164 × 421`), and (2) test whether ranking candidate promotions by **2-Parameter Logistic (2PL) Item Response Theory (IRT) validation ability gain ($\Delta \hat{\theta}_{\text{2PL},V}$)** or **Graded Response Model (`GRM3`) partial-credit validation ability gain ($\Delta \hat{\theta}_{\text{GRM3},V}$)** from Experiment 14 beats unweighted scalar validation gain (`S0+`) and factor-matrix ranking (`R3`) in AlphaHebe's small-validation-gain regime (`P_near`: $1 \le \text{net}_V \le 10$ of 212 validation tasks).

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 1. Scientific questions & hypotheses (`expt_v2`)

1. **Part A — Unblock `matched_test_lists` sensitivity (`164 × 421`):**
   - In `expt_v1`, `inputs/test_list_drift_e07.json` lists 4 tasks (`django__django-10097`, `sympy__sympy-13031`, `sympy__sympy-18189`, `sympy__sympy-24213`), of which `django__django-10097` is already outside the 424-task common cohort (`common_cohort = False`). Dropping the 4 drift tasks therefore yields `(164, 421)`.
   - Verify that all `expt_v1` H1, H2, and H3 verdicts on `164 × 421` (1,000 splits × 1,000 dyadic bootstrap draws) match the `164 × 424` primary findings.
2. **Part B — 2PL IRT & Graded IRT (`GRM3`) promotion gates in `P_near` (`164 × 424`):**
   - Using Experiment 14's locked 10-fold cross-validated item parameters (`experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1/results/fits_e14.json.gz`, where each fold's item parameters $(a_j, d_j)$ were fitted on the other 9 folds' systems) and Leave-Pair-Out (or out-of-fold / anchor) item weights on the validation half $V$, compute for each system $i$ on validation half $V$:
     - Expected a posteriori (EAP) ability $\hat{\theta}_{\text{2PL},V}(i)$ and held-out pass@1 forecast $\hat{p}_{\text{2PL},V\to E}(i)$ from binary validation responses;
     - Graded Response Model (`GRM3`) EAP ability $\hat{\theta}_{\text{GRM3},V}(i)$ and held-out forecast $\hat{p}_{\text{GRM3},V\to E}(i)$ from 3-category `SCS4C-T` validation responses (`0 = fail`, `1 = partial credit`, `2 = resolved`).
   - Evaluate four new promotion policies inside `analyze_e10_v2.py` at $q \in \{0.5, 0.25, 0.75\}$ over the exact 1,000 splits × 1,000 dyadic bootstrap draws:
     - `S_irt2pl` (unstratified: largest $\Delta \hat{p}_{\text{2PL},V\to E} = \hat{p}_{\text{2PL},V\to E}(C) - \hat{p}_{\text{2PL},V\to E}(I)$);
     - `S_grm3` (unstratified: largest $\Delta \hat{p}_{\text{GRM3},V\to E}$, combining 2PL IRT with `SCS4C-T` partial credit);
     - `R_irt2pl` (gain-stratified: within each `net_V` stratum, largest $\Delta \hat{p}_{\text{2PL},V\to E}$);
     - `R_grm3` (gain-stratified: within each `net_V` stratum, largest $\Delta \hat{p}_{\text{GRM3},V\to E}$).
   - Compare their Harmful Promotion Rate (`HPR`) and held-out test gain (`mean Δpass1_E`) against `S0+` (unweighted largest `net_V`), `R0` (scalar hash order), `R2` (binary losses), and `R3` (factor-regression matrix).

## 2. Execution & publication

1. Implement `expt_v2/analyze_e10_v2.py` and unit tests in `tests/test_e10_v2.py` (preserving `expt_v1/` byte-for-byte untouched).
2. Run both `--sensitivity matched_test_lists` (`164 × 421`) and `--sensitivity none` (`164 × 424` with IRT policies) for 1,000 splits × 1,000 draws with 32 CPU workers.
3. Write `expt_v2/results.md`, update top-level `results.md` and `experiments/README.md`, run `make test`, commit, and push to `main`.
