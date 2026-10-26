# Protocol: experiment 18a, pre-RL scoring of Reasoning Gym environments on Qwen3-0.6B/1.7B/4B

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/PROTOCOL.md>

**TLDR:** 32 procedurally generated environments (8 Reasoning Gym families x 4 curriculum levels) and a 6-part held-out target set are sampled 16 times on 256 fixed items each by Qwen3-0.6B, 1.7B and 4B with thinking off, before any RL. Per environment and model we record pass rate, ρ and H (exactly `rl4cv.experience.measure_environment`) and one alignment score to the target set, defined below. The analysis asks whether generator difficulty ranks environments the same way across sizes, and which environments sit in the learnable band. Frozen 10-20-2026, before any measurement; any change after the first job is a new `expt_vN`.

## Status of this file

- Frozen in its own commit on branch `ub9/e18a-reasoning-gym-env-scoring` before any generation job exists. The first Slurm job id is recorded in `results.md`; its submit time must postdate this commit.
- Experiment 18b (short GRPO, AT-566) reads `envs_18a.jsonl` (schema below). 18b's own forecasts are frozen in 18b's protocol, not here.

## Environments (frozen)

Reasoning Gym `reasoning-gym==0.1.25` (PyPI). Each training environment is one family at one curriculum level. The level is applied with `create_curriculum(family).set_global_level(L)` and turned into a config with `generate_configuration({"seed": s, "size": 256}, context=DefaultCurriculumContext(mode=RangeAttributeMode.UPPER_BOUND))`. UPPER_BOUND makes each level its own difficulty band instead of including all easier levels (the library default, INCLUSIVE), so the four levels of a family are distinct distributions.

| idx | family | category | levels | what the level changes |
|---|---|---|---|---|
| 0 | basic_arithmetic | arithmetic | 0-3 | terms 2→5, digits 1→4 |
| 1 | leg_counting | arithmetic (word problem) | 0-3 | animal kinds 1→4, counts 2-4 → 16-32 |
| 2 | simple_equations | algebra | 0-3 | terms, coefficient size, share of `*` |
| 3 | coin_flip | probability | 0-3 | trials 3→6 |
| 4 | letter_counting | algorithmic (string) | 0-3 | words 5-7 → 11-13 |
| 5 | word_sorting | algorithmic (string) | 0-3 | words 5-10 → 50-100, word length |
| 6 | family_relationships | graphs / relational | 0-3 | family size 3→6 |
| 7 | mini_sudoku | games | 0-3 | empty cells 4-6 → 10-12 |

- Environment id: `rg/<family>/L<level>`; 8 x 4 = 32 environments.
- Item seed: `20261020 + 10*idx + level`. Items are `dataset[i]` for i in 0..255. Generation is deterministic in the seed (checked: two builds give identical questions); `score.py` regenerates each entry and refuses to score if the question's sha256 differs from the one stored at build time.
- Families were chosen on 10-20-2026 from a CPU probe of RG 0.1.25 before any model saw them, for: all 4 levels generate 256 items in seconds, the gold answer scores 1.0 at every level, and the 4 level configs differ. Excluded by that probe: number_sequence (levels ≥1 hang), countdown, polynomial_equations, knights_knaves L3 and shortest_path L3 (generation timeouts), gcd (most answers are "1"), prime_factorization (L2 = L3 config), propositional_logic (gold answer scores 0 on some items).

## Held-out target set (frozen)

Six equally weighted components, none of them a training family:

| component | source | items | seed / selection |
|---|---|---|---|
| `rg/gsm_symbolic` | RG default config | 256 | seed 20261120 |
| `rg/calendar_arithmetic` | RG default config | 256 | seed 20261121 |
| `rg/time_intervals` | RG default config | 256 | seed 20261122 |
| `rg/syllogism` | RG default config | 256 | seed 20261123 |
| `rg/base_conversion` | RG default config | 256 | seed 20261124 |
| `gsm8k/test256` | `openai/gsm8k` main, test split, revision `740312add88f781978c0658806c59bc2815b9866` (parquet sha256 `ee7b8da9…4f59`) | 256 | `sorted(random.Random(20261020).sample(range(1319), 256))` |

The target set is scored with the same models and settings as the environments (it gives 18b its pre-RL baseline).

## Models and sampling (frozen)

- `Qwen/Qwen3-0.6B` rev `c1899de289a04d12100db370d81485cdf75e47ca`, `Qwen/Qwen3-1.7B` rev `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, `Qwen/Qwen3-4B` rev `1cfa9a7208912126459214e8b04321603b3df60c` (the hybrid post-trained checkpoints; 18b trains the same ones). bf16.
- vLLM `LLM.chat` with `chat_template_kwargs={"enable_thinking": False}`; messages = system `reasoning_gym.utils.SYSTEM_PROMPTS["default"]` + user = the item's question (GSM8K: the question text).
- `SamplingParams(n=16, temperature=1.0, top_p=1.0, top_k=-1, max_tokens=4096, seed=1000 + set_index)`. Temperature 1 with no truncation is the GRPO rollout distribution 18b trains with, which is what a pre-RL probe of RL signal should measure (Qwen's recommended non-thinking decoding, T=0.7/top_p=0.8, would understate exploration).
- `set_index` is the position of the set in the frozen order: the 32 environments in table order (family idx, then level), then the 6 target components in table order.
- Context: `max_model_len=8192`. A response that ends with `finish_reason == "length"` (hit 4096) is *capped*.

## Rewards (frozen)

- Answer extraction: `reasoning_gym.utils.extract_answer(response)` (last `<answer>…</answer>`); `None` if there is none.
- Reasoning Gym items: `score = dataset.score_answer(extracted, entry)` (RG's own verifier; some families give partial credit).
- GSM8K: exact numeric match. Take the extracted answer, remove `,`, `$` and spaces, take the last number in it (regex `-?\d+(\.\d+)?`), and compare with the number after `####` in the gold answer; equal within 1e-6 → 1, otherwise (or no tag, or no number) → 0.
- **Pass** = `score >= 1 - 1e-9`. Pass is the reward for ρ and H (primary); the raw score is kept and a raw-score ρ/H is reported as secondary.

## Metrics per (set, model) (frozen)

- **pass rate**: mean pass over 256 x 16 responses; 95% CI by percentile bootstrap over items (10,000 resamples, seed 0).
- **ρ, H and diagnostics**: `rl4cv.experience.measure_environment(groups_from_records(rows, reward_key="pass", group_key="item_id"))`, one group per item (G = 16), `admitted = not capped`, `generated_tokens` = vLLM's output token count. All fields of `EnvironmentMeasurement` are stored.
- Also: mean raw score, answer-tag rate, capped rate, share of items with 0/16 and 16/16 passes.
- **Alignment** (one primary score, defined before any outcome; see below).

### Alignment score (primary)

For model m, every prompt (system + user, chat template applied with thinking off and the generation prompt added, exactly as generated) is run through the model with Hugging Face `transformers` (bf16, no sampling). Its embedding is the mean over prompt tokens of the **last** hidden layer, L2-normalised. Per set S, the centroid μ_S is the mean of its 256 item embeddings. Let c be the mean of the 38 set centroids (32 environments + 6 target components, each weighted equally) and τ = mean over the 6 target components of (μ_T − c). Then

    alignment(e, m) = cos(μ_e − c, τ)

and `alignment_by_target[T] = cos(μ_e − c, μ_T − c)` for each component.

Why this one: (1) it is defined from the starting policy alone, before RL, like ρ and H; (2) it is model specific, which matters because the question is about three sizes; (3) it uses no pass rates, so it cannot restate difficulty (pass rate is already a separate coordinate, and Night 3 showed ρ tracks learnability, not transfer); (4) centring by c removes the shared direction of mean-pooled LLM states, without which every cosine is near 1. A few-shot pass-rate correlation was rejected because environment and target items are not paired and three model sizes give only three points per environment. Known weakness, stated up front: it measures how similar the prompts look to the policy, which can be dominated by format; 18b tests whether it predicts gain. Secondary, exploratory only: the same score from the middle layer (index `num_hidden_layers // 2`).

## Analysis plan (frozen)

All on the 32 training environments unless said otherwise; Spearman with average ranks for ties; bootstrap CIs resample environments (10,000, seed 0).

1. **Difficulty transfer across sizes (primary).** Spearman ρ_s of pass rate between 0.6B–1.7B, 1.7B–4B and 0.6B–4B, with 95% CIs; Kendall's W across all three. *Transfers* if every pairwise ρ_s ≥ 0.7 and its CI lower bound > 0.5; *fails* if any pairwise ρ_s < 0.4; otherwise *partial*.
2. **Within-family difficulty.** Per family and model, Spearman of level vs pass rate (4 points). A family is *monotone* for a model if pass rate does not increase from one level to the next by more than 0.02. Reported: number of monotone families per model (expected ≥ 6 of 8).
3. **Learnable band.** An environment is in the band for model m if 0.1 ≤ pass rate ≤ 0.9 and ρ > 0. Reported per model: count and list; Jaccard overlap of the band between sizes; and the mean level of in-band environments per model (expected to rise with size).
4. **Coordinates.** Per model, Spearman among pass rate, ρ, H and alignment over the 32 environments (descriptive; no claim).
5. **Target baseline.** Pass rate, ρ and H of each target component per model, for 18b.

Validity: a (set, model) cell is complete when it has 256 items x 16 responses. Incomplete cells are listed with their counts and excluded from (1)–(4) for that model, never filled or resampled; infrastructure reruns redo the identical cell (same seed). If a model's answer-tag rate on a set is below 50%, the cell is flagged `format_dominated` but kept.

## Output files (frozen schema)

`results/envs_18a.jsonl`, one row per (environment, model), 96 rows, schema `envs_18a/v1`:

| field | type | meaning |
|---|---|---|
| schema | str | `envs_18a/v1` |
| env_id | str | `rg/<family>/L<level>` |
| family, category | str | from the table above |
| level | int | 0-3 |
| rg_version | str | `0.1.25` |
| rg_config | object | the dataclass config used (seed and size included) |
| probe_seed | int | item seed; 18b must train on other seeds (suggested `train_seed_base = probe_seed + 1_000_000`) |
| n_items, group_size | int | 256, 16 |
| model, model_revision | str | HF id and revision |
| model_size_b | float | 0.6, 1.7, 4.0 |
| complete | bool | 256 x 16 present |
| pass_rate, pass_rate_ci95 | float, [lo, hi] | pass over all responses |
| mean_score | float | raw RG score |
| answer_tag_rate, capped_rate | float | |
| frac_items_all_fail, frac_items_all_pass | float | 0/16 and 16/16 items |
| rho, rho_raw, H, q_mixed_empirical, admission_rate, mean_generated_tokens, total_generated_tokens, advantage_survival, token_weighted_coverage, top_decile_mass_share, n_groups, n_responses, mean_reward | | `EnvironmentMeasurement` on pass |
| rho_score, H_score | float | same on the raw score (secondary) |
| alignment | float | primary alignment |
| alignment_by_target | object | component → cosine |
| alignment_mid | float | middle-layer alignment (exploratory) |
| in_learnable_band | bool | analysis 3 |
| format_dominated | bool | answer-tag rate < 0.5 |

`results/targets_18a.jsonl`: the same fields per (target component, model), without alignment and band fields. `results/summary_18a.json`: every number of analyses 1–5. `results/manifest.json`: item hashes per set, package versions, model revisions, job ids.

## Compute (frozen route)

FarmShare L40S (Brando, 10-20-2026), shared venv `~/venvs/fs_hf` (vLLM 0.32.0, transformers 5.19.0) for generation and embeddings, a small CPU venv `~/venvs/e18a` (reasoning-gym 0.1.25) for build, score and analysis. Generation is one Slurm array over (model, shard) with at most 4 GPUs at once. Sherlock (AT-476 Apptainer image, vLLM 0.30.0) is the fallback if FarmShare's queue stalls for more than a day; the vLLM version is recorded per cell and a different version is not a protocol change. Estimate: ~156k responses per model at an expected 300–900 tokens → about 15–25 L40S GPU-hours for all three models.
