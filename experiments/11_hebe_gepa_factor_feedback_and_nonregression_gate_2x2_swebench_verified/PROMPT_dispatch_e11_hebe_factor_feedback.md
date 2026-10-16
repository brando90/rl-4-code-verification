# Experiment 11 (+ Expt 10 Phase B) dispatch prompt — AlphaHebe Live Factor-Feedback Reflection & `S0+`/IRT Promotion Gate on SWE-bench Verified (`[p 6/10]`)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/PROMPT_dispatch_e11_hebe_factor_feedback.md>

**TLDR:** Once Andrew Zhou grants repository access to `AlphaDiana-dev` (and resolves `AlphaHebe-dev` issues `#27`–`#30`), execute: (1) Experiment 10 Phase B (replay of real AlphaHebe incumbent $\to$ candidate promotion trajectories), and (2) Experiment 11's live evaluation of decomposed Smooth Conjunctive Score for Code (`SCS4C-T`) diagnostic factor feedback in the reflection prompt paired with the validated stricter scalar/IRT promotion margin (`S0+` / `IRT`) on SWE-bench Verified.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Current Blocker & Pre-Flight Check

1. Check whether `AlphaDiana-dev` is accessible using the configured GitHub token:
   ```bash
   GH_TOKEN=$(cat ~/keys/.brando90_github_token.txt) gh repo view AndrewZhou/AlphaDiana-dev 2>/dev/null || \
   GH_TOKEN=$(cat ~/keys/.brando90_github_token.txt) gh api user/repos --jq '.[].full_name' | grep -iE 'diana|hebe'
   ```
2. Check `[FROM-UB9]` comments in `brando90/agents-config#68` for any exported trajectory bundle from Andrew Zhou.
3. **Spending guard (Trigger Rule 72):** Before launching any paid live AlphaHebe solver calls on Vals/Valkyrie, verify `valk run list --status in_progress` has 0 overlapping large experiments, write the exact per-task cost estimate in `CKPT_e11.md`, and run a 10-task pilot first.

## 1. Execution Sequence Once Unblocked

1. **Step 1 — Experiment 10 Phase B (`$0` API spend):**
   - Run `experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/expt_v1/analyze_e10.py` (and `expt_v2/analyze_e10_v2.py`) on the exported real AlphaHebe candidate-incumbent pairs.
   - Measure the natural acceptance rate and conditional Harmful Promotion Rate (`HPR`) of the zero-validation-loss rule (`net_V >= 1 and losses_V = 0`), `S0+`, `R3`, and `S_grm3` on real evolutionary mutations.
2. **Step 2 — Experiment 11 Factor-Feedback Study (`PROTOCOL.md` amendment per Expt 10 H3):**
   - Per Experiment 10's finding (`C_fac = 0.0046 [-0.0027, 0.0117]`, H3 no factor-matrix gate recommendation), drop the factor-matrix gate claim and lock an amended 2-arm (or 2×2 with `S0+` vs `S0`) comparison isolating **decomposed factor feedback (`G`, `T_fix`, `T_keep` + failing test names/tracebacks) vs scalar pass/fail feedback** in AlphaHebe's reflection prompt at matched rollout budget.
   - Publish live progress in `experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/results.md` and send `[RUN START]` / `[RUN DONE]` emails per Trigger Rule 70.
