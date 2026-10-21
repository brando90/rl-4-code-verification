# Protocol: experiment 18b, does a pre-RL law pick the generated environment that most improves a held-out target?

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18b/PROTOCOL_18b.md>

**TLDR:** 16 Reasoning Gym environments, chosen from the 18a Qwen3-1.7B measurements to span their ρ/H/alignment range, are each used for a short single-environment GRPO run on Qwen3-1.7B (2 seeds, thinking off, fixed budget). The outcome is the held-out gain (post minus pre pass rate on identical items of 5 RG families + GSM8K). Six forecasts (ρ-H law, law+alignment, alignment alone, difficulty only, the 0.6B model, random), computed from `envs_18a.jsonl` and frozen in `forecasts_18b.json` before any training or evaluation job, are compared by Spearman, Kendall, regret and bootstrap CIs over environments. Frozen 10-21-2026, before any 18b job exists; any change after the first job is a new `expt_18b_vN`.

## Status of this file

- Committed on branch `ub9/e18a-reasoning-gym-env-scoring` (PR #17) in a commit that contains this file, `common18b.py`, `select_envs.py`, `make_forecasts.py`, `selection_18b.json`, `forecasts_18b.json` (+ `.sha256`, `forecast_ledger.jsonl`) and nothing that trains or evaluates. `train.py`, `eval.py`, `analyze.py` and the Slurm package come in later commits. The first Slurm job id is recorded in `results_18b.md`; its submit time must postdate the freeze commit.
- Inputs: `expt_v1/results/envs_18a.jsonl` (96 rows, sha256 recorded in `selection_18b.json`), 18a v1 results. The wide v2 data (AT-767) is not used: it was not finished when this was frozen.

## Format handling (decision: exclude, do not change the prompt)

18a found 20 of 96 cells format-dominated (answer-tag rate < 50%). 18b **excludes** every environment whose Qwen3-1.7B cell has an answer-tag rate below 0.5 (1.7B: simple_equations L1, word_sorting L2-L3; simple_equations L2-L3 and word_sorting L1 also drop out by the ρ > 0 rule, and mini_sudoku L3 by pass < 0.02). The system prompt, the answer extraction and the reward stay exactly as in 18a, so the forecasts computed from 18a cells describe the very prompt that is trained and evaluated. No format fix is applied. Format learning is still possible inside a run (an `<answer>` tag raises pass), so the evaluation records the answer-tag rate before and after on every target component, and the analysis reports the target gain with the tag-rate change next to it (secondary table, not a correction).

## Environment selection (frozen, deterministic: `select_envs.py`, output `selection_18b.json`)

Pool: Qwen3-1.7B cells that are complete, not format-dominated, answer-tag rate ≥ 0.5, ρ > 0 (the law takes log ρ), 0.02 ≤ pass rate ≤ 0.98 → 25 environments. Take 16 by farthest-point sampling in the pool-standardised space (log ρ, H, alignment, pass rate), first point = the farthest from the pool centroid, at most 3 environments per family, ties broken by env id. Environment = `rg/<family>/L<level>` exactly as in 18a (UPPER_BOUND curriculum level). Selected list: see `selection_18b.json` (it spans pass 0.047-0.716, alignment -0.435 to +0.481, ρ 132 → 18224).

## Training (frozen: `train.py`, `grpo.py`; hyper-parameters in `common18b.HP`)

- Policy: `Qwen/Qwen3-1.7B` at the 18a revision, thinking off (the same chat template call as 18a), prompts = system `SYSTEM_PROMPTS["default"]` + the item's question. Code: a minimal GRPO loop in PyTorch + Hugging Face `transformers` only (no TRL, verl, vLLM or peft in training): rollouts with `model.generate`, one optimiser step per rollout batch (on-policy, so the clipped ratio is 1 and the loss is the plain policy gradient).
- One run = one environment, one seed ∈ {0, 1}: 40 steps × 32 prompts × 8 samples = 10,240 rollouts, temperature 1.0, top-p 1.0, no top-k, max 1024 new tokens (a response that does not finish is capped, reward 0). Fresh items every step: Reasoning Gym items from the same family/level config with seed `probe_seed + 1,000,000 + 1000 × run_seed` (never an 18a probe item; no item repeats inside a run).
- Reward: the 18a pass indicator (`score_answer >= 1 - 1e-9`, binary). Advantage = reward − group mean (no std normalisation), loss normalised by the number of response tokens in the batch, no KL term, no entropy bonus. AdamW (β = 0.9/0.99, ε = 1e-8, weight decay 0), peak LR 3e-6 with 3 linear warm-up steps then constant, gradient clipping at norm 1.0, a non-finite gradient norm skips the step and is logged. bf16 model with an fp32 master copy in the optimiser.
- **Budget:** matched in rollouts (10,240 per run), prompt count and group size, with the 1024-token cap bounding tokens (≤ 10.5M generated tokens per run). Because response length differs a lot by environment (8 tokens for family_relationships, hundreds for equations), the realised generated-token count is logged per run and reported next to the gain; exact token matching was rejected because it would give an 8-token environment hundreds of steps. This is the one place the matched-token-budget wording of the task is read as "matched rollout budget, token cap, token count reported".
- Checkpoint: bf16 `save_pretrained` after the last step (no intermediate checkpoints), deleted after its post-evaluation succeeds.

## Evaluation and outcome (frozen: `eval.py`)

- Target set = the 18a held-out target set: `rg/gsm_symbolic`, `rg/calendar_arithmetic`, `rg/time_intervals`, `rg/syllogism`, `rg/base_conversion` (256 items each, seeds as in 18a) and `gsm8k/test256` (same 256 items and rewards as 18a). Pre (base model) and post (each run) use the same items, n = 8 samples per item, temperature 1.0, top-p 1.0, max 2048 new tokens, thinking off, vLLM `LLM.chat`, sampling seed 5000 + the 18a set index (identical for pre and post).
- **Outcome:** gain = mean over the 6 target components (equal weights) of (post pass rate − pre pass rate), per run; the environment's realised gain is the mean of its two seeds. Secondary outcomes: GSM8K-only gain, RG-5-only gain, per-component gains, answer-tag-rate change, and the in-environment gain on the first 64 18a probe items of the trained environment.
- Noise ceiling: the Spearman between seed-0 and seed-1 gains over the 16 environments, Spearman-Brown corrected to a 2-seed mean (2r/(1+r)); the best correlation any forecast can reach with the 2-seed mean is about √ of that reliability.

## Forecasts (frozen before training: `make_forecasts.py` → `forecasts_18b.json`, sha256 in `forecasts_18b.sha256`)

A forecast is one score per selected environment; higher = larger predicted held-out gain.

| name | definition |
|---|---|
| `rho_h` | `paper_frozen_14b_model().env_term(ρ, H)` of the repo's utility model (paper Eq. 7: b_ρ·z(log ρ) + b_H·z(H), the paper's own Appendix-D coefficients and standardisers) from the 1.7B cells. Note b_ρ is negative (−0.077) and b_H positive (+0.093) in that fit, so the law as frozen prefers low ρ and high H; it is used as is, not refitted |
| `law_alpha` | z(`rho_h`) + z(alignment), both standardised over the 25-environment pool, equal weights (there is nothing to fit alignment's weight on) |
| `alpha` | the 18a alignment score of the 1.7B cell |
| `difficulty` | −(RG level); level is the generator's own difficulty |
| `smaller_model` | 0.6B p(1−p), p the 0.6B pass rate of the same environment (the signal a smaller model sees) |
| `random` | fixed permutation, `np.random.default_rng(0)` |

Secondary forecasts declared now, reported but not headline: `rho_only`, `H_only`, `pass_band` (−|p − 0.5| at 1.7B).

## Analysis (frozen: `analyze.py`)

Over the 16 environments (2-seed mean gain): Spearman and Kendall τ-b of each forecast against the realised gain (average ranks for ties), **regret of the top pick** = best realised gain − realised gain of the highest-scored environment (ties in score average their gains), mean regret of the top-3, and for `random` the expected regret over all picks. 95% percentile bootstrap CIs resample environments (10,000, seed 0). Headline verdict per forecast: *beats random* if the Spearman CI lower bound > 0; the primary comparison is `rho_h` vs `alpha`, `difficulty` and `smaller_model` by the paired bootstrap difference of Spearman. A seed-level table (per run gain with an item-paired bootstrap CI) is included. If the noise ceiling is below 0.3 the report says that the test cannot rank environments and states the correlations as descriptive only.

## Compute (frozen route)

Sherlock H100 (`-p gpu -G 1 -C GPU_MEM:80GB`), the AT-476 Apptainer image (vLLM 0.30.0, torch 2.13.0+cu130, transformers) for training, evaluation and analysis; L40S is not used for training (fp32 master + Adam states ≈ 36 GB plus activations). Jobs: smoke → pre-eval → train array (32 tasks = 16 env × 2 seeds) → post-eval array (aftercorr on the train array) → analyze. Mail END,FAIL to brandojazz@gmail.com and brando.science@gmail.com. FarmShare L40S (4 at a time) is an alternative only for the evaluation jobs.
