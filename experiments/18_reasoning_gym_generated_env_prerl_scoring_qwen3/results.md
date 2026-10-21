# Experiment 18a results (live)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e18a-reasoning-gym-env-scoring/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/results.md>

**TLDR:** All 96 environment cells and 18 target cells completed (256 items x 16 responses each, no incomplete cells, nothing rerun). The primary analysis gives **partial** difficulty transfer across sizes by the frozen rule: pairwise Spearman of pass rate is 0.70 (0.6B–1.7B, CI 0.39–0.89), 0.79 (0.6B–4B, CI 0.60–0.88) and 0.81 (1.7B–4B, CI 0.62–0.91), Kendall's W 0.84; it is not "transfers" because 0.6B–1.7B is below 0.7 and its CI lower bound is below 0.5. Within-family difficulty is monotone in 8/8 (0.6B), 6/8 (1.7B) and 7/8 (4B) families. The learnable band has 12, 23 and 11 environments. Main caveat: 20 of 96 environment cells are `format_dominated` (answer-tag rate below 50%), 11 of them for 0.6B, so part of the "difficulty" is formatting (see Caveats).

## Slurm jobs

| date (PT) | cluster | job id | what | state | notes |
|---|---|---|---|---|---|
| 10-20-2026 17:22 | FarmShare | 1861295 | smoke (Qwen3-4B, 10 sets x 8 items x 4) | COMPLETED 0:06:11, exit 0 | after `prepare.sh`: PREPARE OK, 38 item sets, 57 tests passed. SMOKE OK on L40S: 10 sets, answer-tag rate 1.00 on 7, 0.75 simple_equations, 0.19 word_sorting (capped 0.56, mean 2398 tok), 0.00 mini_sudoku (mean 31 tok); capped 0 on 8 of 10; 812 tok/s at tiny batch, 4B full-run upper bound 23.1 GPU-h |
| 10-20-2026 17:38 | FarmShare | 1861305 | gen part 1: array 5-8%4 (qwen3_4b shards 0-3 of 4) | all four shards COMPLETED (5-7: 0:10:56, 0:21:47, 1:59:59; 8 finished by 23:01), exit 0, GEN TASK OK | split from `submit_full.sh` because QOS gpu allows 32 submitted tasks per user and Exp 22 held 28 |
| 10-20-2026 22:06 | FarmShare | 1861865 | gen part 2: array 0-4%4 (qwen3_0p6b 2 shards, qwen3_1p7b 3 shards) | COMPLETED, exit 0 (mail 10-20 ~23:00 to 01:17) | submitted when QOS gpu use fell to 23/32; one slot left free for Zip-Mix Stage A |
| 10-20-2026 22:06 | FarmShare | 1861866 | embed array 0-2%4 | COMPLETED, exit 0 (mail 10-20 22:42) | QOS gpu 31/32 after this |
| 10-20-2026 22:06 | FarmShare | 1861867 | score array 0-2 (afterany: 1861305, 1861865) | COMPLETED, exit 0 | CPU |
| 10-20-2026 22:06 | FarmShare | 1861868 | analyze (afterany: 1861867, 1861866) | COMPLETED, exit 0 (mail 10-21 01:17) | CPU; writes ~/e18a/e18a_results.tgz |

## Results

Source: `expt_v1/results/summary_18a.json` (written by `expt_v1/analyze.py` on FarmShare, job 1861868; results tarball sha256 `ff07d96e201b71f3…`, 4.31 MB). Rows: `results/envs_18a.jsonl` (96), `results/targets_18a.jsonl` (18). Scored per-response files are in `results/scored_18a.tgz`, embeddings in `results/emb/`. No cell failed, so there were no reruns. Analyses follow the frozen plan in `PROTOCOL.md` unchanged.

**1. Difficulty transfer across sizes (primary): PARTIAL.**

| pair | Spearman of pass rate (32 envs) | 95% CI |
|---|---|---|
| 0.6B–1.7B | 0.704 | 0.386–0.894 |
| 0.6B–4B | 0.789 | 0.595–0.884 |
| 1.7B–4B | 0.808 | 0.621–0.906 |

Kendall's W = 0.841. "Transfers" needed every pair ≥ 0.7 with CI lower bound > 0.5; 0.6B–1.7B has its CI lower bound at 0.39, and no pair is below 0.4, so the rule gives "partial".

**2. Within-family monotonicity (level vs pass rate).** 0.6B: 8/8 families monotone. 1.7B: 6/8 (not monotone: leg_counting, family_relationships). 4B: 7/8 (not monotone: family_relationships). The expectation was at least 6 of 8 per model: met for all three.

**3. Learnable band (0.1 ≤ pass ≤ 0.9 and ρ > 0).** 0.6B: 12 environments; 1.7B: 23; 4B: 11. Jaccard overlap: 0.6B–1.7B 0.52, 0.6B–4B 0.44, 1.7B–4B 0.42. Mean level of in-band environments: 1.08, 1.35, 1.27, so the expectation that it rises with size holds from 0.6B to 1.7B but not to 4B. The 4B band is smaller than the 1.7B band because 6 of its environments are above 0.9 and 15 are below 0.1 (the 1.7B model has 0 above 0.9 and 9 below 0.1); 0.6B has 0 above and 20 below. Per-model lists are in `summary_18a.json` under `analysis3_learnable_band`.

**4. Coordinates (Spearman over the 32 environments, descriptive).**

| model | pass~ρ | pass~H | pass~align | ρ~H | ρ~align | H~align |
|---|---|---|---|---|---|---|
| 0.6B | 0.83 | 0.97 | 0.39 | 0.76 | 0.64 | 0.37 |
| 1.7B | 0.79 | 0.85 | 0.65 | 0.64 | 0.80 | 0.46 |
| 4B | 0.60 | 0.74 | 0.43 | 0.85 | 0.58 | 0.49 |

Pass rate, ρ and H are strongly tied (ρ_s 0.6–0.97), so ρ and H add little beyond difficulty in this probe; alignment is only moderately tied to pass rate and is the least redundant coordinate.

**5. Target baselines (for 18b).** Pass rates, ρ and H of the five RG target components and GSM8K-256 per model are in `analysis5_targets`. GSM8K-256 pass: 0.6B 0.31, 1.7B 0.66, 4B 0.82.

Mean pass rate over the 32 environments: 0.107 (0.6B), 0.256 (1.7B), 0.323 (4B). Mean capped fraction 0.013, 0.076, 0.051.

## Caveats

- **Format domination.** 20 of 96 environment cells have an answer-tag rate below 50% (kept per protocol, flagged `format_dominated`): 0.6B on basic_arithmetic L1–L3, simple_equations L0–L3, coin_flip L0–L3 (11); 1.7B on simple_equations L1, word_sorting L2–L3 (3); 4B on word_sorting L2–L3 and mini_sudoku L0–L3 (6). One target cell is also flagged (syllogism, 4B, tag rate 0.48). In these cells pass rate partly measures whether the model writes `<answer>` tags, not whether it can solve the task, so the primary verdict mixes difficulty and format compliance.
- **Exploratory sensitivity (not in the frozen plan, not a verdict).** Dropping the 17 environments that have a format-dominated cell for any model leaves 15 environments; pairwise Spearman is then 0.18 (0.6B–1.7B), 0.74 (0.6B–4B) and 0.54 (1.7B–4B). Difficulty transfer from 0.6B to 1.7B therefore looks weaker on the clean subset, and 15 environments are too few for a CI to mean much. 18b should either fix the answer format (a format reward or a one-shot example) or report results by `format_dominated` status.
- The pass-rate~H correlation (0.74–0.97) and the format effect interact: low-tag cells have few correct answers and low H together.


## Level vs pass rate (AT-598 addendum)

Mean over the 8 families of the within-family Spearman of RG level against pass rate (values from `analysis2_within_family`; negative = harder level, lower pass; bootstrap over families, 5000 resamples, seed 0, descriptive): 0.6B −0.87 (CI −0.97 to −0.72), 1.7B −0.74 (−0.97 to −0.34), 4B −0.66 (−0.93 to −0.34). Exceptions: 1.7B leg_counting (+0.60, L2 above L1), 4B word_sorting (+0.11, all near 0), and coin_flip is nearly flat for 4B (≥ 0.91 at every level) and 0.6B (~0.15), so RG level orders difficulty well in arithmetic, equations and sudoku but barely in coin_flip and letter_counting.

## Plots and full table

- `expt_v1/results/plots/pass_by_env.png` (pass rate per env x model with the 0.1–0.9 band), `size_transfer.png` (pairwise pass-rate scatter, format-dominated cells marked), `level_vs_pass.png`, `coordinates_vs_pass.png` (rho, H, alignment against pass rate). Script: `expt_v1/plots_18a.py`.
- `expt_v1/results/table_18a.md`: the 96-row table (env x model: n items, n samples, pass, rho, H, alignment, tag rate, band, format-dominated).
- Negative findings in the plots: 0.6B has no environment above 0.9 and 20 below 0.1; mini_sudoku and word_sorting sit near 0 for all sizes (format plus task difficulty); rho and H track pass rate (0.6–0.97), so they add little beyond difficulty.

## Deviations from PROTOCOL.md

None in the analyses (analyze.py was run as frozen, job 1861868). Additions outside the frozen plan, all labelled exploratory: the format-dominated sensitivity subset, the family-bootstrap above, the plots and table. `results/manifest.json` (item hashes, package versions) was not produced by analyze.py; the item manifest is at `expt_v1/results/items/manifest.json` on FarmShare and in `scratch/at597/x/items/` locally. `envs_18a.jsonl` has all 96 rows with every schema field of `envs_18a/v1` including `in_learnable_band` (46 true = 12+23+11).
