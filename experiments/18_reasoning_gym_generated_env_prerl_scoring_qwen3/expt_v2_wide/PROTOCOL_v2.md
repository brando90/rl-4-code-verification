# Protocol: experiment 18a v2 (wide), pre-RL scoring of every fast-generating Reasoning Gym family on Qwen3-0.6B/1.7B

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-v2-wide/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/PROTOCOL_v2.md>

**TLDR:** 18a v1 scores 32 environments from 8 hand-picked Reasoning Gym families. v2 scores every Reasoning Gym 0.1.25 family that passed a CPU probe of generation speed and verifier sanity: 75 families, 243 (family, level) environments, plus v1's 6-part target set, sampled 16 times on 256 fixed items by Qwen3-0.6B and Qwen3-1.7B with thinking off, before any RL. Same metrics as v1 (pass rate, ρ, H, alignment). It asks two pre-registered questions: does v1's 8-family picture hold across 75 families, and how well does difficulty rank-transfer from 0.6B to 1.7B. Frozen 10-20-2026 in its own commit before any v2 job; any change after the first job is `expt_v3`.

## Status of this file

- Frozen in its own commit on branch `ub9/e18a-v2-wide` (off 18a v1's `ub9/e18a-reasoning-gym-env-scoring`) before any v2 Slurm job. The first v2 job id goes into `../results_v2.md`; its submit time must postdate this commit.
- Everything not stated here is v1's `../PROTOCOL.md` unchanged: prompts, sampling, rewards, metrics, alignment definition, validity rules.

## Environments (frozen): the probe

`probe_families.py` built every family that has a curriculum in `reasoning-gym==0.1.25` (`sorted(CURRICULA)`, 102 names) at levels 0–3, each level in its own worker process, 256 items at the level's v2 seed, levels applied exactly as v1 (`set_global_level(L)`, `RangeAttributeMode.UPPER_BOUND`). No model saw any item. Probe host: 4 vCPUs, 4 families in parallel. A (family, level) is an environment if **all** hold:

1. **Speed:** building 256 items and verifying the 256 gold answers takes ≤ 60 s; a level silent for 120 s is killed (hang).
2. **Verifier sanity:** the gold answer scores 1.0 (a pass) on every item and a missing answer (`None`) never passes (some families give it 0.01 partial credit; pass is the reward, so that is kept).
3. **Fits the context:** system prompt + question + 32 template tokens ≤ 4096 Qwen3 tokens (so 4096 generated tokens fit `max_model_len=8192`).
4. **Not degenerate:** ≥ 8 distinct questions, and no single gold answer on more than 60% of items.
5. **Distinct level:** its config (seed and size removed) differs from every lower included level of the family.
6. **Deterministic:** a second process (another `PYTHONHASHSEED`) builds identical items (sha256 over the item hashes).
7. **Not a target:** the family is not one of v1's held-out target families.

A family enters with its passing levels if at least 2 pass (within-family analyses need two). The result is frozen in `families_v2.json`; `probe_v2.jsonl` holds every row with its timings, item hash and the reasons a row is out. `build.py` refuses to build an item set whose hash differs from the probe's.

- Environment id `rg/<family>/L<level>`; item seed `20262000 + 10*k + level`, k = the family's index in `sorted(CURRICULA)` (independent of which families pass); items are `dataset[i]`, i in 0..255.
- Order (sets the sampling seed): families in `families_v2.json` order (alphabetical), levels ascending, then the 6 targets. Sampling seed `2000 + set_index` (v1 used 1000+).
- Category = Reasoning Gym's package for the family. Environments per category: algorithmic 79, arithmetic 52, games 33, graphs 20, cognition 16, algebra 15, logic 12, geometry 7, probability 4, arc 3, code 2.
- v1's families inside v2: 8 of 8 (basic_arithmetic, leg_counting, simple_equations, coin_flip, letter_counting, word_sorting, family_relationships, mini_sudoku), at new item seeds, so v2 also replicates those v1 cells.

### Included families (75 families, 243 environments)

| # | family | category | k | levels | slowest level (s) | min distinct questions | max prompt tokens |
|---|---|---|---|---|---|---|---|
| 0 | ab | algorithmic | 0 | 0,1,2,3 | 1.8 | 256 | 471 |
| 1 | advanced_geometry | geometry | 1 | 0,1,2,3 | 12.0 | 256 | 226 |
| 2 | aiw | logic | 2 | 0,1,2,3 | 0.0 | 213 | 232 |
| 3 | arc_1d | arc | 3 | 0,1,2 | 0.2 | 256 | 920 |
| 4 | basic_arithmetic (v1) | arithmetic | 6 | 0,1,2,3 | 1.1 | 233 | 158 |
| 5 | bf | code | 7 | 0,1 | 45.7 | 234 | 685 |
| 6 | binary_alternation | algorithmic | 8 | 0,1,2 | 0.3 | 256 | 1217 |
| 7 | binary_matrix | algorithmic | 9 | 0,1 | 1.7 | 256 | 1438 |
| 8 | bitwise_arithmetic | arithmetic | 10 | 0,1,2,3 | 0.1 | 256 | 291 |
| 9 | caesar_cipher | algorithmic | 12 | 0,1 | 0.1 | 225 | 222 |
| 10 | chain_sum | arithmetic | 14 | 0,1,2,3 | 0.1 | 143 | 157 |
| 11 | coin_flip (v1) | probability | 17 | 0,1,2,3 | 0.1 | 8 | 135 |
| 12 | color_cube_rotation | cognition | 18 | 0,1,2,3 | 1.1 | 256 | 1570 |
| 13 | complex_arithmetic | algebra | 19 | 0,1,2,3 | 0.1 | 256 | 195 |
| 14 | count_bits | arithmetic | 20 | 0,1,2,3 | 0.0 | 227 | 143 |
| 15 | count_primes | algorithmic | 21 | 0,1,2,3 | 1.1 | 256 | 143 |
| 16 | course_schedule | graphs | 23 | 0,1,2,3 | 1.3 | 256 | 3668 |
| 17 | cryptarithm | algorithmic | 24 | 0,1,2 | 0.9 | 256 | 428 |
| 18 | decimal_arithmetic | arithmetic | 25 | 0,1,2,3 | 0.2 | 256 | 255 |
| 19 | decimal_chain_sum | arithmetic | 26 | 0,1,2,3 | 0.2 | 256 | 332 |
| 20 | dice | arithmetic | 27 | 0,1,2,3 | 5.4 | 253 | 241 |
| 21 | emoji_mystery | games | 28 | 0,1,2,3 | 0.4 | 249 | 1445 |
| 22 | family_relationships (v1) | graphs | 29 | 0,1,2,3 | 0.5 | 256 | 164 |
| 23 | figlet_font | cognition | 30 | 0,1,2,3 | 7.4 | 256 | 2465 |
| 24 | fraction_simplification | arithmetic | 31 | 0,1,2 | 0.1 | 254 | 156 |
| 25 | game_of_life_halting | algorithmic | 34 | 0,1 | 8.9 | 173 | 1456 |
| 26 | group_anagrams | algorithmic | 37 | 0,1,2 | 3.7 | 256 | 1348 |
| 27 | intermediate_integration | algebra | 38 | 0,1,2 | 33.9 | 118 | 308 |
| 28 | kakurasu | games | 41 | 0,1,2 | 21.7 | 255 | 434 |
| 29 | knights_knaves | logic | 43 | 0,1,2,3 | 8.7 | 256 | 463 |
| 30 | largest_island | graphs | 44 | 0,1 | 0.6 | 251 | 1460 |
| 31 | lcm | arithmetic | 45 | 0,1,2,3 | 0.1 | 256 | 164 |
| 32 | leg_counting (v1) | arithmetic | 46 | 0,1,2,3 | 0.1 | 96 | 176 |
| 33 | letter_counting (v1) | algorithmic | 47 | 0,1,2,3 | 0.1 | 256 | 156 |
| 34 | letter_jumble | algorithmic | 48 | 0,1 | 0.6 | 256 | 345 |
| 35 | mahjong_puzzle | games | 49 | 0,1,2 | 7.7 | 256 | 1849 |
| 36 | manipulate_matrix | algorithmic | 50 | 0,1 | 1.1 | 256 | 1448 |
| 37 | maze | games | 51 | 0,1 | 20.2 | 256 | 2329 |
| 38 | mini_sudoku (v1) | games | 52 | 0,1,2,3 | 4.9 | 256 | 238 |
| 39 | modulo_grid | cognition | 53 | 0,2 | 7.4 | 247 | 3806 |
| 40 | n_queens | games | 54 | 0,1,2,3 | 8.7 | 21 | 341 |
| 41 | needle_haystack | cognition | 55 | 0,1 | 0.5 | 256 | 3886 |
| 42 | number_filtering | algorithmic | 56 | 0,1,2,3 | 1.2 | 256 | 2510 |
| 43 | number_format | arithmetic | 57 | 0,1 | 0.3 | 256 | 1917 |
| 44 | number_sorting | algorithmic | 59 | 0,1 | 9.1 | 256 | 3862 |
| 45 | palindrome_generation | algorithmic | 60 | 0,1,2 | 0.3 | 256 | 1191 |
| 46 | palindrome_partitioning | algorithmic | 61 | 0,1,2 | 0.5 | 217 | 209 |
| 47 | path_star | graphs | 62 | 0,1,2,3 | 0.4 | 256 | 730 |
| 48 | pool_matrix | algorithmic | 65 | 0,1 | 2.8 | 256 | 1471 |
| 49 | power_function | arithmetic | 66 | 0,1,2,3 | 0.0 | 256 | 177 |
| 50 | prime_factorization | arithmetic | 67 | 0,1,2 | 0.1 | 234 | 156 |
| 51 | products | arithmetic | 68 | 0,1,2,3 | 0.0 | 95 | 162 |
| 52 | quantum_lock | graphs | 71 | 0,1,2,3 | 0.3 | 215 | 247 |
| 53 | rectangle_count | cognition | 74 | 0,1,2,3 | 2.0 | 256 | 1834 |
| 54 | rotate_matrix | algorithmic | 75 | 0,1 | 1.2 | 256 | 1406 |
| 55 | rotten_oranges | algorithmic | 76 | 0,1 | 1.1 | 256 | 1483 |
| 56 | self_reference | logic | 79 | 0,1,2,3 | 0.2 | 199 | 258 |
| 57 | sentence_reordering | algorithmic | 80 | 0,1,2 | 0.1 | 256 | 270 |
| 58 | shortest_path | graphs | 81 | 0,1 | 0.7 | 256 | 925 |
| 59 | simple_equations (v1) | algebra | 82 | 0,1,2,3 | 3.5 | 256 | 477 |
| 60 | simple_geometry | geometry | 83 | 0,1,2 | 0.1 | 256 | 382 |
| 61 | simple_integration | algebra | 84 | 0,1,2,3 | 28.9 | 256 | 295 |
| 62 | spell_backward | algorithmic | 86 | 0,1,2,3 | 0.4 | 231 | 133 |
| 63 | spiral_matrix | algorithmic | 87 | 0,1 | 2.2 | 256 | 1541 |
| 64 | string_insertion | algorithmic | 88 | 0,1,2 | 1.7 | 256 | 560 |
| 65 | string_manipulation | algorithmic | 89 | 0,1,2 | 2.7 | 256 | 782 |
| 66 | string_splitting | algorithmic | 90 | 0,1,2 | 27.8 | 256 | 522 |
| 67 | string_synthesis | algorithmic | 91 | 0,1,2 | 3.5 | 256 | 506 |
| 68 | sudoku | games | 92 | 0,1 | 42.8 | 256 | 298 |
| 69 | survo | games | 93 | 0,1,2,3 | 0.6 | 256 | 380 |
| 70 | tower_of_hanoi | games | 96 | 1,2,3 | 1.0 | 12 | 236 |
| 71 | tsumego | games | 97 | 0,1,2,3 | 0.7 | 240 | 595 |
| 72 | word_ladder | algorithmic | 98 | 0,1 | 12.7 | 256 | 163 |
| 73 | word_sequence_reversal | algorithmic | 99 | 0,1,2 | 0.2 | 256 | 363 |
| 74 | word_sorting (v1) | algorithmic | 100 | 0,1,2,3 | 0.4 | 256 | 444 |

### Families left out, and why (first reason per level)

| family | reason |
|---|---|
| arc_agi | L0: prompt up to 16401 tokens > 4096; L1: prompt up to 16401 tokens > 4096; L2: prompt up to 16401 tokens > 4096; L3: prompt up to 16401 tokens > 4096 |
| base_conversion | held-out target family (v1's target set) |
| boxnet | L0: gold answer fails on 100% of items; L1: gold answer fails on 100% of items; L2: gold answer fails on 100% of items; L3: gold answer fails on 100% of items |
| calendar_arithmetic | held-out target family (v1's target set) |
| circuit_logic | L0: family has fewer than 2 usable levels; L1: answer '0' on 61% of items; L2: answer '0' on 65% of items; L3: killed after 120 s (hang or too slow) |
| codeio | L0: prompt up to 7100 tokens > 4096; L1: prompt up to 11753 tokens > 4096; L2: TypeError: Object of type complex is not JSON serializable; L3: prompt up to 4740 tokens > 4096 |
| countdown | L0: family has fewer than 2 usable levels; L1: ValueError: Failed to generate valid expression after 100 attempts; L2: ValueError: Failed to generate valid expression after 100 attempts; L3: ValueError: Failed to generate valid expression after 100 attempts |
| futoshiki | L0: family has fewer than 2 usable levels; L1: too slow: 127 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| game_of_life | L0: family has fewer than 2 usable levels; L1: too slow: 91 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| gcd | L0: family has fewer than 2 usable levels; L1: answer '1' on 64% of items; L2: answer '1' on 78% of items; L3: answer '1' on 93% of items |
| graph_color | L0: gold answer fails on 100% of items; L1: gold answer fails on 100% of items; L2: gold answer fails on 100% of items; L3: gold answer fails on 100% of items |
| isomorphic_strings | L0: items differ in a second process; L1: items differ in a second process; L2: items differ in a second process; L3: items differ in a second process |
| jugs | L0: family has fewer than 2 usable levels; L1: too slow: 110 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| knight_swap | L0: AssertionError: min_nodes must be >= 6; L1: ValueError: Failed to generate valid puzzle after trying 100 different boards; L2: ValueError: Failed to generate valid puzzle after trying 100 different boards; L3: ValueError: Failed to generate valid puzzle after trying 100 different boards |
| number_sequence | L0: family has fewer than 2 usable levels; L1: too slow: 107 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| polynomial_equations | L0: family has fewer than 2 usable levels; L1: too slow: 79 s > 60 s for 256 items + gold check; L2: too slow: 80 s > 60 s for 256 items + gold check; L3: killed after 120 s (hang or too slow) |
| polynomial_multiplication | L0: items differ in a second process; L1: too slow: 112 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| propositional_logic | L0: gold answer fails on 100% of items; L1: gold answer fails on 100% of items; L2: gold answer fails on 100% of items; L3: gold answer fails on 100% of items |
| puzzle24 | L0: too slow: 98 s > 60 s for 256 items + gold check; L1: too slow: 80 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| ransom_note | L0: items differ in a second process; L1: items differ in a second process; L2: items differ in a second process; L3: items differ in a second process |
| rearc | L0: family has fewer than 2 usable levels; L1: prompt up to 4357 tokens > 4096; L2: prompt up to 4451 tokens > 4096; L3: prompt up to 4227 tokens > 4096 |
| rubiks_cube | L0: gold answer fails on 100% of items; L1: gold answer fails on 100% of items; L2: gold answer fails on 100% of items; L3: gold answer fails on 100% of items |
| rush_hour | L0: gold answer fails on 100% of items; L1: gold answer fails on 100% of items; L2: gold answer fails on 100% of items; L3: gold answer fails on 100% of items |
| sokoban | L0: killed after 120 s (hang or too slow); L1: too slow: 97 s > 60 s for 256 items + gold check; L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| syllogism | held-out target family (v1's target set) |
| time_intervals | held-out target family (v1's target set) |
| zebra_puzzles | L0: needs pycosat (no wheel; not buildable in the Sherlock fallback image); L1: needs pycosat (no wheel; not buildable in the Sherlock fallback image); L2: needs pycosat (no wheel; not buildable in the Sherlock fallback image); L3: needs pycosat (no wheel; not buildable in the Sherlock fallback image) |

### Included families with some levels left out

| family | levels out |
|---|---|
| arc_1d | L3: killed after 120 s (hang or too slow) |
| bf | L2: killed after 120 s (hang or too slow); L3: killed after 120 s (hang or too slow) |
| binary_alternation | L3: same config as a lower level |
| binary_matrix | L2: prompt up to 5188 tokens > 4096; L3: prompt up to 20188 tokens > 4096 |
| caesar_cipher | L2: AssertionError: rotation must be in range [1,25]; L3: AssertionError: rotation must be in range [1,25] |
| cryptarithm | L3: same config as a lower level |
| fraction_simplification | L3: same config as a lower level |
| game_of_life_halting | L2: only 7 distinct questions; L3: only 5 distinct questions |
| group_anagrams | L3: same config as a lower level |
| intermediate_integration | L3: too slow: 130 s > 60 s for 256 items + gold check |
| kakurasu | L3: killed after 120 s (hang or too slow) |
| largest_island | L2: prompt up to 5210 tokens > 4096; L3: prompt up to 20212 tokens > 4096 |
| letter_jumble | L2: ValueError: empty range in randrange(0, -14); L3: ValueError: empty range in randrange(0, -68) |
| mahjong_puzzle | L3: prompt up to 8249 tokens > 4096 |
| manipulate_matrix | L2: prompt up to 5233 tokens > 4096; L3: prompt up to 20295 tokens > 4096 |
| maze | L2: too slow: 101 s > 60 s for 256 items + gold check; L3: killed after 120 s (hang or too slow) |
| modulo_grid | L1: AssertionError: max_target must be greater than 0; L3: prompt up to 6626 tokens > 4096 |
| needle_haystack | L2: prompt up to 7607 tokens > 4096; L3: prompt up to 7607 tokens > 4096 |
| number_format | L2: prompt up to 9507 tokens > 4096; L3: prompt up to 9355 tokens > 4096 |
| number_sorting | L2: prompt up to 8507 tokens > 4096; L3: prompt up to 10500 tokens > 4096 |
| palindrome_generation | L3: same config as a lower level |
| palindrome_partitioning | L3: same config as a lower level |
| pool_matrix | L2: prompt up to 5221 tokens > 4096; L3: prompt up to 20221 tokens > 4096 |
| prime_factorization | L3: same config as a lower level |
| rotate_matrix | L2: prompt up to 5157 tokens > 4096; L3: prompt up to 20157 tokens > 4096 |
| rotten_oranges | L2: answer '-1' on 79% of items; L3: answer '-1' on 100% of items |
| sentence_reordering | L3: same config as a lower level |
| shortest_path | L2: answer 'infeasible' on 63% of items; L3: answer 'infeasible' on 64% of items |
| simple_geometry | L3: same config as a lower level |
| spiral_matrix | L2: prompt up to 5291 tokens > 4096; L3: prompt up to 20291 tokens > 4096 |
| string_insertion | L3: same config as a lower level |
| string_manipulation | L3: gold answer fails on 1% of items |
| string_splitting | L3: same config as a lower level |
| string_synthesis | L3: same config as a lower level |
| sudoku | L2: too slow: 68 s > 60 s for 256 items + gold check; L3: killed after 120 s (hang or too slow) |
| tower_of_hanoi | L0: only 6 distinct questions |
| word_ladder | L2: same config as a lower level; L3: same config as a lower level |
| word_sequence_reversal | L3: same config as a lower level |

## Held-out target set (frozen, identical to v1)

v1's six components with v1's items: `rg/gsm_symbolic` (seed 20261120), `rg/calendar_arithmetic` (20261121), `rg/time_intervals` (20261122), `rg/syllogism` (20261123), `rg/base_conversion` (20261124), each 256 items at RG's default config, and `gsm8k/test256` (openai/gsm8k test at revision `740312ad…`, `sorted(random.Random(20261020).sample(range(1319), 256))`). Same item hashes as v1; only the sampling seeds differ.

## Models and sampling (frozen)

- `Qwen/Qwen3-0.6B` rev `c1899de289a04d12100db370d81485cdf75e47ca` and `Qwen/Qwen3-1.7B` rev `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` (bf16). Qwen3-4B is v1 only (cost).
- vLLM `LLM.chat`, `enable_thinking=False`, system prompt `reasoning_gym.utils.SYSTEM_PROMPTS["default"]`, `SamplingParams(n=16, temperature=1.0, top_p=1.0, top_k=-1, max_tokens=4096, seed=2000+set_index)`, `max_model_len=8192`, `finish_reason == "length"` = capped. Rewards, pass (score ≥ 1 − 1e-9), ρ/H via `rl4cv.experience.measure_environment`, raw-score ρ/H, alignment (last-layer mean-pooled prompt embeddings, centroids centred by the mean of all 249 set centroids, cosine to τ) and the middle-layer alignment: exactly v1.

## Pre-registered questions

- **Q2 (primary): size transfer.** Spearman ρ_s of pass rate between 0.6B and 1.7B over all complete environments. CI: percentile bootstrap resampling **families** (10,000, seed 0), because levels of one family are correlated; v1's environment-resampling CI is reported too. Verdict with v1's thresholds: *transfers* if ρ_s ≥ 0.7 and the family-bootstrap CI lower bound > 0.5; *fails* if ρ_s < 0.4; otherwise *partial*. Forecast (written before data): transfers, ρ_s ≈ 0.85.
- **Q1: does v1's 8-family picture hold across 75 families.** The v1-family environments inside v2 are compared with all other families on four checks: (a) the same Q2 verdict; (b) share of monotone families (pass rate never rises by more than 0.02 from one level to the next) within 0.25, for each model; (c) share of environments in the learnable band (0.1 ≤ pass ≤ 0.9 and ρ > 0) within 0.20, for each model; (d) every coordinate correlation (Spearman among pass rate, ρ, H, alignment) with |ρ_s| ≥ 0.3 among v1 families has the same sign among the others. Verdict: *holds* if (a)–(d) all pass; *partially_holds* if (a) passes and any of (b)–(d) fails; *does_not_hold* if (a) fails. Typicality: the v1 subset's 0.6B→1.7B ρ_s as a percentile among 10,000 random 8-family subsets of v2 (seed 0); outside 5–95% = *the 8 families were atypical*. Forecast: partially_holds (v1's families are easier and more monotone than RG at large).

## Analysis plan (frozen)

All on complete environment cells; Spearman with average ranks; family-bootstrap CIs unless stated.

1. **Size transfer (Q2)** as above; plus descriptive per-category ρ_s for categories with ≥ 8 environments.
2. **Within-family difficulty:** per model, number and share of monotone families among those with ≥ 2 levels.
3. **Learnable band:** per model count, share, the list, Jaccard overlap 0.6B~1.7B, mean level of in-band environments.
4. **Coordinates:** per model, Spearman among pass rate, ρ, H, alignment (descriptive).
5. **Targets:** pass rate, ρ, H, tag rate per target component and model (18b baseline); v1's target cells at the same items are a cross-run check, reported only.
6. **Q1** as above (checks, verdict, typicality).
7. **Robustness:** η² of pass rate by family (share of variance between families) per model; Q2 recomputed without environments with < 64 distinct questions and without `format_dominated` cells (tag rate < 0.5); and, when v1's results exist, v1-vs-v2 replication on shared (family, level, model) cells (new item and sampling seeds): Spearman and mean |Δ pass rate| (expected ≥ 0.9 and ≤ 0.05).

Validity (v1's): a cell is complete with 256 items × 16 responses; incomplete cells are listed and excluded, never filled or resampled; reruns repeat the identical cell; tag rate < 50% flags `format_dominated` but keeps the cell.

## Output files (frozen schema)

`results/envs_18a_v2.jsonl`: one row per (environment, model), schema `envs_18a_v2/v1` = every field of v1's `envs_18a/v1` plus `unique_questions` and `top_answer_share` (the share of the most common gold answer: a guessing floor). `results/targets_18a_v2.jsonl` (12 rows), `results/summary_18a_v2.json` (analyses 1–7). 18b may read `envs_18a_v2.jsonl` exactly as it reads v1's file (suggested training seed base = probe seed + 1,000,000).

## Compute (frozen route)

FarmShare L40S, shared `~/venvs/fs_hf` (vLLM 0.32.0, transformers 5.19.0; `VLLM_USE_FLASHINFER_SAMPLER=0` and the pip CUDA_HOME), v1's CPU venv `~/venvs/e18a` and v1's model snapshots. Generation: one array of 10 tasks (0.6B in 4 shards, 1.7B in 6, round-robin over sets), `%2`, 12 h wall, resumable per set; embeddings: 2 tasks `%1`; 12 QOS gpu slots in all so other experiments fit beside it under QOS gpu's 32 submitted / 4 running per user. Scoring (8 CPU tasks) and analysis on `-p normal`. Sherlock (AT-476 image, vLLM 0.30.0) is the fallback if FarmShare's queue stalls for more than a day; the vLLM version is recorded per cell and a different version is not a protocol change. Estimate: 249 sets × 4,096 responses ≈ 1.02M responses per model; at 500–900 tokens per response that is ≈ 510–918M tokens per model, at an assumed 25k tok/s (0.6B) and 12k tok/s (1.7B) on one L40S with full n=16 batches that is about 6–10 GPU-h for 0.6B and 12–21 for 1.7B, so **about 17–31 GPU-h in all** (capped 4,096-token responses push toward the top), plus under 1 GPU-h of embeddings. The smoke prints a measured bound before the full chain goes in.
