# Overnight factored-score training checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/CKPT_e09.md>

**TLDR:** Brando approved automatic overnight experiments on 10-08-2026. Freeze and execute the three-arm exploratory comparison, preserving full factor semantics, common evaluation and cluster ownership.

Created: 10-08-2026 19:01 PDT. Status: RUNNING PRE-FLIGHT.

Master: Codex thread `01a11d6a-30aa-7020-a672-6b34546fdeee`; checkpoint `experiments/CKPT_MASTER_tmuxnone_cxd_01a11d6a.md`. No training launched yet.

Run identity: `0c84fdc2-d5cf-4a04-9137-e214edbd8c36`; start 2026-10-09T02:13:36Z; hard deadline 2026-10-09T18:13:36Z; maximum two A100 devices / 32 device-hours / 200 GiB new owned data / eight scorer workers.

Verified 10-08-2026 19:51 PDT: source NeMo RL is exactly `c751f811217db7df0d4c94abdeaada6626cfc150`; the step-658 Qwen 1.7B config and tokenizer SHA-256 values are in the sanitized runtime receipt. The experiment-08 owner supplied a locked lease interface and active acknowledgement. A bounded lease on GPU 3 passed Qwen3 1.7B raw-feedback/context preflight and was released at 2026-10-09T02:42:44Z. Both validated Vals judge configurations completed 25/25 live positive/negative control cells and the control gate passed. The one-worker frozen-scorer adapter control passed all 14 files in about five minutes; its receipt is owned by experiment09. CPU remains saturated, so this timing is capacity evidence rather than an authorization for unbounded CPU work.

Next: collect the owned scorer-control result, finish the actual two-turn optimizer path and run the fixed 256-rollout calibration. Freeze horizon and all six trajectories before any main update or test outcome.
