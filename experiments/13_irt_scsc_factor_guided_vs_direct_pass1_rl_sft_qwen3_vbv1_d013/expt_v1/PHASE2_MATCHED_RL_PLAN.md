# Experiment 13 Phase 2: matched token budgets and accountable reinforcement learning

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/PHASE2_MATCHED_RL_PLAN.md>

**TLDR:** Compare four arms at a common generated-token budget, enforce at most 1% measured boundary mismatch, and report actual device/scorer costs. Pilot and main locks are separate, with scientific validity, probability controls and a valid allocation required before training.

`../PROTOCOL.md` §§5–8 govern the exact arms, gates, seed IDs, token-budget stopping rules and analysis. Group relative policy optimization (GRPO) uses eight rollouts per prompt and 32 prompts per scheduled update. A/B/P share a prompt stream by cumulative group index and the same token stopping rule; C changes sampler and weights together. Zero-variance groups do not trigger refills. Record actual optimizer steps separately from scheduled update opportunities.

The placebo is a deterministic independent draw from a frozen train-only B distribution. `rl4cv.e13.placebo_reward` keys by seed/update/group/slot and accepts no task/response field. A response-dependent permutation or contemporaneous matching is not this placebo. Report its evolving variance/density differences from B.

LP is a prospective bounded pilot manifest and resource lock. It admits the T1 probability check; only passing T1 permits the real update/refit and resume tests. T4 measures costs before T5's learning pilot. L2 then freezes the main manifest and measured allocation with reserve. There is no “run a pilot before any work is allowed” circular prerequisite. SNAP task preapproval supplies authorization; actual scheduler/device availability remains unverified and no lease exists.

Preserve the failed technical result and zero updates in `09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013`; removing sampling filters is not proof the replacement passes. Preserve the exhausted layout-probe budget and ownership of `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`. Neither transfers resources to this experiment.

The three paired main seeds give exploratory estimates. Exact two-sided sign-swap resolution is .25; a bootstrap cannot manufacture confirmatory significance. Keep seed pairing in uncertainty calculations and use task groups. Remove outcome-selected A2 and extra seeds. The primary comparison uses four precommitted cumulative-token thresholds derived from the fixed A pilot. Each boundary stops after a complete group; its overshoot is recorded and must satisfy the 1% matching gate. Update counts may differ; there is no fixed-100-update plus fixed-token contradiction. The pilot retains its fixed update horizon for technical T5.

Freeze mutation/coverage audit sets before learning and apply the protocol's gaming stop rule. H5 is unresolved if hidden-test or validated coverage measurements are missing. Evaluation pins and funding follow the existing validated Valkyrie route; no shared evaluator environment is changed.
