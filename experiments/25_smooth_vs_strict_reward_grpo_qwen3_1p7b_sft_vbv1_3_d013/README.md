# Experiment 25: smooth reward versus strict reward in GRPO, held-out strict pass@1 (Azalia's smooth-to-harsh test)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/25_smooth_vs_strict_reward_grpo_qwen3_1p7b_sft_vbv1_3_d013/README.md>

**TLDR:** Does training Qwen3-1.7B (Lean SFT, Experiment 08) with a smooth partial-credit reward raise held-out strict (harsh) pass@1 more than training with the strict reward, at the same rollouts? This is the direct test of Azalia Mirhoseini's suggestion that was never run (Experiments 13 v3 and 20 are the earlier designs; see [docs/SMOOTH_TO_HARSH.md](../../docs/SMOOTH_TO_HARSH.md)). Status 10-28-2026: **designed, QA passed with fixes ([QA_plan1_10-28-2026.md](QA_plan1_10-28-2026.md)), [PROTOCOL.md](PROTOCOL.md) drafted and not locked, no training run started.** Benchmark: public VeriBench `veribench@1.3` (896 tasks), split D-013 (train 539, validation 135, test 222 sealed). Plan, decisions for Brando and QA verdict: the plan Google Doc <https://docs.google.com/document/d/171HnjJrze_FKKEGOVGCL7xMfEd50DVXnMyzbVRC_SFQ/edit>.

## Hypothesis and decision criterion
- Arm A: strict reward. Arm B: smooth reward (Experiment 13's factored reward, a training proxy: geometric mean of three per-declaration factors, local Lean only; not official SCSC, whose factors equalled strict on all 15 SFT checkpoints in Experiment 13).
- Primary metric: validation strict pass@1 at update 48, B minus A, 135 tasks x 32 samples (QA: power about 50% at +1.5, MDE about 2 points), paired bootstrap over task groups (10,000 draws, seed 20261021), 2 seeds pooled. Supported if B minus A is at least +1.5 points and the interval's lower bound is above 0. Secondary: validation at updates 0, 16, 32; training reward curves; gate statistics. Test split stays sealed.
- Forecast, to be frozen with `rl4cv.forecast.freeze_forecast` before any outcome (D-004): P(supported) 25%, both flat within noise 55%, A better 20%.

## Design (built on Experiment 20 recipe)
16 groups x 8 rollouts per update, 12,288 new tokens, lr 1e-6 (to be re-chosen by the pilot from arm A training reward only), TIS cap 2.0 on in both arms and dtypes, 48 updates, 2 seeds per arm, same prompt stream and seeds across arms, one named start checkpoint (Experiment 08 v1 step_658, validation strict 4.91%, SHA recorded); the lr pilot runs both arms; see PROTOCOL.md.

## Precision
Decided by a measured gate, not by default: stage 0 re-measures bf16 and fp16 vLLM-versus-trainer mismatch on a mercury A4000 (gate at most 1% of tokens, Experiment 20). bf16 with importance-sampling correction if it passes; otherwise fp16 with fp32 master weights and loss scale 16384 (Experiments 22 to 24: bf16 6.1% to 6.4% mismatch, fp16 0.109%). Rationale and sources: [docs/HEURISTICS.md](../../docs/HEURISTICS.md) rules 1 to 3.

## Stages (each must pass before the next)
0. CPU: strict scorer (pin `59059a20`, `--skip-tc`) and smooth adapter running on the scoring host with local Lean 4.22 and Mathlib (the Experiment 20 scorer wrapper `score_sherlock.sh` exists only on Sherlock; rebuild it locally and check strict agreement with saved Experiment 20 scores). 1. One A4000 on mercury: precision gate, trainer memory, seconds per update. 2. Two-update smoke, both arms. 3. Pilot of 12 updates at lr 1e-6 and 5e-6, training reward only. 4. Full A versus B, 2 seeds. Validation evaluations fan out over idle mercury GPUs.

## Hardware (free only)
mercury1 and mercury2 (10 RTX A4000 16 GB each), skampere1 A100 80 GB when idle. The trainer's 6.9 GB fp32 gradient buffer plus colocated vLLM does not fit 16 GB unmodified (Adam state is already on CPU); the fallback is to train on idle A100s and evaluate and score on mercury.

## Stop rules
Mismatch above 1%, NaN or inf, pilot reward not moving in either arm at either lr (report the null power result), Lean strict scores disagreeing with saved scores, another user needing the GPU.

## Status log (newest first)
- 10-28-2026 14:20: QA by a second model: PASS WITH FIXES, 13 defects, all applied in PROTOCOL.md; cost re-estimated at 60 to 75 A100-hours; AT-1786 builds the local scorer.
- 10-28-2026 14:00: folder created; stage 0 precision probe started on mercury1 GPU 0 (`/lfs/mercury1/0/brando9/rl4cv_e25_stage0`); previous partial attempt to wire real Lean scoring (`train_e25.py`, `e25_scoring/` on skampere1, 10-26) never ran and is reused.
