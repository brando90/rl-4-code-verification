# Experiment 18: score procedurally generated Reasoning Gym environments before RL (18a), then test whether a pre-RL law picks the best one (18b)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/README.md>

**TLDR:** RL project 2 asks whether a pre-RL law (ρ, H, plus a target-alignment term) can choose or generate RL environments that improve a new target. 18a measures 32 generated environments (8 Reasoning Gym families x 4 difficulty levels) on Qwen3-0.6B/1.7B/4B with no training: pass rate, ρ, H and alignment to a held-out target set (5 other Reasoning Gym families + GSM8K). It answers two questions: does generator difficulty rank environments the same way across model sizes, and which environments sit in the learnable band. 18b (AT-566) then trains short single-environment GRPO runs on ~16 of them and checks which frozen forecast predicts held-out gain. Status 10-20-2026: protocol frozen, code and Slurm package built and CPU-tested; no GPU job has run.

## Goal, hypotheses and decision criteria

- **Question 1 (difficulty transfer).** Spearman of environment pass rate between each pair of sizes. Transfers if all three ≥ 0.7 with CI lower bound > 0.5; fails if any < 0.4; else partial (`PROTOCOL.md`, analysis 1).
- **Question 2 (learnable band).** Environments with 0.1 ≤ pass rate ≤ 0.9 and ρ > 0, per size; we expect the band to move to harder levels as size grows (analysis 3).
- **Why alignment is in every row.** Night 3 showed ρ is inflated by reward noise and tracks learnability, not transfer, so a utility forecast for a *target* needs a separate alignment coordinate. 18a defines it once (centred cosine of the policy's own prompt embeddings, `PROTOCOL.md`), 18b tests it.
- **Decision.** If difficulty transfers, 18b may forecast with the smallest model's measurements; if it fails, 18b must measure at the trained size (1.7B).

## Structure

| path | what |
|---|---|
| `PROTOCOL.md` | frozen design: environments, seeds, models, sampling, rewards, metrics, alignment, analysis plan, output schema |
| `results.md` | live: Slurm job ids, then the results |
| `expt_v1/e18a_common.py` | frozen constants and helpers (sets, seeds, models, prompts, rewards) |
| `expt_v1/build.py` | CPU: item files for the 38 sets (+ manifest with hashes) |
| `expt_v1/generate.py` | GPU: vLLM sampling, 16 x 256 per set, resumable; `--backend fake` for CPU dry runs |
| `expt_v1/score.py` | CPU: Reasoning Gym `score_answer`, GSM8K exact numeric match |
| `expt_v1/embed.py` | GPU: prompt embeddings for alignment (transformers); `--backend fake` |
| `expt_v1/analyze.py` | CPU: per-cell metrics via `rl4cv.experience.measure_environment`, analyses 1–5, `envs_18a.jsonl` |
| `expt_v1/slurm/farmshare/` | primary route: `prepare.sh`, `smoke.sbatch`, `gen.sbatch` (array 0-8%4 over `tasks.tsv`), `embed.sbatch`, `score.sbatch`, `analyze.sbatch`, `submit_full.sh` |
| `expt_v1/slurm/sherlock/` | fallback route on the AT-476 Apptainer image |
| `expt_v1/SUBMIT.md` | step-by-step submit instructions |
| `expt_v1/cc.md` | the prompt for the agent that runs it |
| `tests/test_e18a_reasoning_gym.py` | CPU tests: generators, verifiers, metric code, fake-model end-to-end and smoke chain |
| `expt_v2_wide/PROTOCOL_v2.md` | 18a v2 (wide), frozen: every Reasoning Gym family that passed a CPU probe (75 families, 243 environments) on Qwen3-0.6B/1.7B; Q1 does the 8-family picture hold, Q2 0.6B→1.7B rank transfer |
| `expt_v2_wide/families_v2.json`, `probe_v2.jsonl` | frozen family list and every probe row with its timings and the reason a level is out (`probe_families.py`) |
| `expt_v2_wide/` (code, `slurm/`, `SUBMIT.md`, `cc.md`) | v1's pipeline driven by the family file; FarmShare gen 0-9%2 + embed 0-1 (12 QOS gpu slots), Sherlock fallback |
| `results_v2.md` | live: v2 Slurm job ids, then the v2 results |
| `tests/test_e18a_v2_wide.py` | v2 CPU tests: family file and probe rules, every environment's generator and verifier, analyses, fake end-to-end and smoke chain |

## Method (short)

Items: `reasoning-gym==0.1.25`, curriculum level L via `set_global_level(L)` with the UPPER_BOUND context, 256 items per environment at a fixed seed. Sampling: thinking off, temperature 1, top_p 1, max 4096 tokens, 16 samples per item. Reward: RG's own `score_answer`; pass = score 1; ρ/H on pass with capped responses not admitted. Compute: FarmShare L40S, 9 generation tasks (0.6B: 2 shards, 1.7B: 3, 4B: 4), at most 4 GPUs at once, est. 15–25 GPU-h; embeddings 3 short GPU jobs; scoring and analysis on CPU.

## Dependencies

`src/rl4cv/experience.py` (ρ, H); FarmShare `~/venvs/fs_hf` (vLLM 0.32.0, transformers 5.19.0; AT-615) and a small CPU venv; GSM8K test parquet and Qwen3 snapshots at pinned revisions (downloaded by `prepare.sh`). Self-hosted inference is authorized by D-101.

## Status

- 10-20-2026: protocol frozen (commit before any job); code, tests (57 CPU tests pass) and the FarmShare/Sherlock package built. Next: AT-597 runs the smoke, then the full chain, and records job ids in `results.md`; AT-598 analyzes as frozen.
