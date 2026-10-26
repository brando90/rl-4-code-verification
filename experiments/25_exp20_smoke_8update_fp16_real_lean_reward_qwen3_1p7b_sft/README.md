# Experiment 25: 8-update fp16 smoke with the real Lean reward (Qwen3-1.7B SFT)

Status: RUNNING / QUEUED (submitted 2026-10-26 by ultimate_brando9 for Brando). Sherlock job 49639114 (gpu, 1 H100 SXM5, 3 h limit, mail END,FAIL to brandojazz and brando.science). Results below are filled in when it ends; nothing in this file is a result yet.

## Question
Exp 24 ran 8 updates of the fp16/fp16 lane with a stand-in reward (1 if the extracted Lean file has a theorem/lemma and no `sorry`). With the real frozen Lean strict reward instead: (1) does the gate (share of completion tokens with |logp_trainer - logp_vLLM| > 0.05 or outside the recomputed sampling support) stay <= 1% in every update; (2) is training finite; (3) how does the real reward differ from the stand-in, rollout by rollout?

## Setup
Exp 24's recipe unchanged: Exp 20 trainer, TRL 1.16.0 colocated vLLM 0.30.0 (Apptainer image vllm-openai_v0.30.0.sif), arm A, seed 0, 16 groups x 8 = 128 rollouts per update, thinking on, T=0.6, top-p 0.95, top-k 20, max 12288 new tokens, `--smoke`, 8 updates. Start policy: Qwen3-1.7B SFT (expt_v4 seed 20260831 hf checkpoint), `config.json` dtype set to float16 (weights symlinked; `code/setup.sh`); trainer float16, fp32 master weights and AdamW, lr 1e-6, grad clip 1.0, static loss scale 16384. Reward: the frozen Lean scorer (`score_e20.sh` / `score_scsc.py --skip-tc`, strict kernel-binary) run on Sherlock CPUs inside the job, no `--reward-proxy`. `code/train_e25.py` = Exp 24's `train_e24.py` plus one field `proxy_e23` in each rollouts row (the stand-in value computed from the same extracted Lean file), so the reward-vs-stand-in difference is measured on the same rollouts. Diff: `code/train_e25_vs_e24.diff`. Job script: `code/e25.sbatch`. Full state saved every 4 updates; the script resumes from `state_latest` if a second job is needed.

Hardware differs from Exp 24 (A100-SXM4-80GB on skampere1): H100 SXM5 80 GB on Sherlock, so generations are not bitwise comparable to Exp 24.

## Results
Pending (job 49639114).

## Files
`code/` (train_e25.py, train_e25_vs_e24.diff, e25.sbatch, setup.sh). Run dir on Sherlock: /scratch/users/brando9/rl4cv_sherlock/e20/e25/runs/A_s0.
