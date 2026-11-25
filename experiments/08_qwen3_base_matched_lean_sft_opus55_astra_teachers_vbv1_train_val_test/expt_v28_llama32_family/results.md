# V28 results: Llama-3.2-1B and 3B, expt_v4 Lean SFT recipe (Sherlock, no DT)

The Qwen3 result does not transfer one-to-one but the shape does. Llama-3.2-1B reaches 2.96% validation pass@1 (no DT, 3 seeds, SD 0.52 pts) and Llama-3.2-3B reaches 7.35% (3 seeds, SD 0.89 pts); 3B beats 1B by +4.38 pts pass@1 (CI [2.62, 6.42]). Both stay below the Qwen3 models at matched size (1.7B 5.03%, 4B 8.84%), as predicted, but the pooled CIs overlap, so no cross-family significance is claimed. Of the predictions locked on 2026-10-31, one did not hold: Llama-3B pooled pass@1 is 7.35%, just above the 1% to 7% range. Seed spread stays inside the predicted bound but is larger than Qwen3-1.7B's 0.30 pts SD.

Metric tag: every number here is no DT. A pass is the Lean kernel check plus the non-vacuity gate (`expt_v6/analyze.evaluate`), with no differential testing; validation split only (135 tasks x 8 samples = 1,080 samples per checkpoint), test unopened. Spend: $0 provider spend, Sherlock only.

## Jobs

All 60 Slurm jobs of the chain ended COMPLETED with exit code 0: 6 trainings, 6 generations, 48 scoring array tasks (6 arrays x 8); the collector 50508663 also COMPLETED. Nothing failed, nothing was rerun, no seed substituted. Source: `results/sacct_v28.txt`, `results/jobs_v28.tsv`. The tarball `expt_v28_results.tgz` (sha256 `da8fa60b04af216f55126aa6e5ad876a92f6c580c23f57d1cf191b96cf4cfde7`) was fetched from Sherlock and its checksum matched the `.sha256` file. All 6 x 1,080 generated samples are present and scored; no system is missing.

## Validation results

| System | Successes / samples (no DT) | pass@1 (no DT) [95% CI] | pass@8 (no DT) tasks / 135 [95% CI] |
|---|---|---|---|
| Llama-3.2-1B seed 20260830 (V28) | 33 / 1080 | 3.06% [1.30, 5.37] | 13 (9.63%) [5.19, 14.81] |
| Llama-3.2-1B seed 20260831 (V28) | 26 / 1080 | 2.41% [1.02, 4.08] | 12 (8.89%) [4.44, 14.07] |
| Llama-3.2-1B seed 20260832 (V28) | 37 / 1080 | 3.43% [1.57, 5.65] | 14 (10.37%) [5.19, 16.30] |
| Llama-3.2-3B seed 20260830 (V28) | 81 / 1080 | 7.50% [4.35, 11.11] | 23 (17.04%) [11.11, 23.70] |
| Llama-3.2-3B seed 20260831 (V28) | 69 / 1080 | 6.39% [3.52, 9.72] | 20 (14.81%) [8.89, 20.74] |
| Llama-3.2-3B seed 20260832 (V28) | 88 / 1080 | 8.15% [4.81, 12.13] | 26 (19.26%) [12.59, 25.93] |
| Llama-3.2-1B pooled (3 seeds) | 96 / 3240 | 2.96% [1.45, 4.85] | n/a |
| Llama-3.2-3B pooled (3 seeds) | 238 / 3240 | 7.35% [4.44, 10.68] | n/a |
| Qwen3-1.7B-Base pooled (3 seeds, V26/expt_v16) | 163 / 3240 | 5.03% [2.87, 7.56] | n/a |
| Qwen3-4B-Base pooled (2 seeds, V26) | 191 / 2160 | 8.84% [5.69, 12.45] | n/a |
| Qwen3-4B-Base seed 20260830 (V26) | 97 / 1080 | 8.98% [5.74, 12.78] | 31 (22.96%) [16.30, 30.37] |
| Qwen3-4B-Base seed 20260831 (V26) | 94 / 1080 | 8.70% [5.56, 12.31] | 30 (22.22%) [15.56, 29.63] |
| Qwen3-1.7B-Base seed 20260832 (V26) | 53 / 1080 | 4.91% [2.69, 7.59] | 21 (15.56%) [9.63, 22.22] |

## Seed spread

| Size | Seeds | pass@1 (no DT) mean (SD) [range] | pass@8 (no DT) mean (SD) [range] |
|---|---|---|---|
| Llama-3.2-1B | 3 | 2.96% (0.52) [1.02] | 9.63% (0.74) [1.48] |
| Llama-3.2-3B | 3 | 7.35% (0.89) [1.76] | 17.04% (2.22) [4.44] |

Qwen3 reference (V26): 1.7B 5.03% (0.30) [0.56] pass@1, 15.56% (2.22) [4.44] pass@8; 4B 8.84% (0.20) [0.28] pass@1, 22.59% (0.52) [0.74] pass@8.

## Paired differences (task bootstrap, 95% CI)

| Comparison | pass@1 diff (no DT) | pass@8 diff (no DT) |
|---|---|---|
| Llama-3.2-3B pooled - 1B pooled | +4.38 [2.62, 6.42] | n/a |
| 1B s20260831 - s20260830 | -0.65 [-2.13, 0.65] | -0.74 [-4.44, 2.96] |
| 1B s20260832 - s20260830 | +0.37 [-1.11, 1.94] | +0.74 [-2.22, 4.44] |
| 1B s20260832 - s20260831 | +1.02 [-0.56, 2.69] | +1.48 [-2.22, 5.93] |
| 3B s20260831 - s20260830 | -1.11 [-3.33, 0.93] | -2.22 [-5.93, 1.48] |
| 3B s20260832 - s20260830 | +0.65 [-1.02, 2.31] | +2.22 [-1.48, 5.93] |
| 3B s20260832 - s20260831 | +1.76 [-0.65, 4.44] | +4.44 [0.74, 8.89] |

## Predictions from PROTOCOL.md (locked 2026-10-31 09:37 PDT) against the result

| Prediction | Result | Held? |
|---|---|---|
| Llama-3.2-1B pass@1 between 0.3% and 3% | pooled 2.96%; seeds 3.06, 2.41, 3.43 | Held for the pooled value, at the edge; two of three single seeds are above 3% |
| Llama-3.2-1B pass@8 between 2% and 14% | pooled mean 9.63%; seeds 9.63, 8.89, 10.37 | Held |
| Llama-3.2-3B pass@1 between 1% and 7% | pooled 7.35%; seeds 7.50, 6.39, 8.15 | **Not held** (pooled 0.35 pts above the range; two of three seeds above) |
| Llama-3.2-3B pass@8 between 6% and 22% | mean 17.04%; seeds 17.04, 14.81, 19.26 | Held |
| 3B pooled minus 1B pooled positive, CI excludes 0 | +4.38 [2.62, 6.42] | Held |
| Llama below Qwen3 at matched or larger size (1.7B 5.0%, 4B 8.8%) | 1B 2.96% vs 1.7B 5.03%; 3B 7.35% vs 4B 8.84% | Held as point estimates; the CIs overlap, so not a significant gap |
| Seed SD under 1 pt pass@1 and under 4 pts pass@8 at each size | 1B 0.52 / 0.74; 3B 0.89 / 2.22 | Held |
| 1B near zero (under 0.5%) would be a floor, not a null | 1B is 2.96%, far above 0.5% | Condition not triggered |

## Notes and caveats

- **Cap hits.** 19.7% to 21.3% of 1B samples and 11.6% to 11.7% of 3B samples ended at the 12,288-token generation cap (`finish_reason` length, a Lean block was usually not extracted; QA 11-25-2026: 2 capped 1B samples did have one, in the s20260830 and s20260831 cell tables); the other samples stopped on the stop token. These count as failures, as in V26. Source: `results/gen_timing/`.
- **Training.** All six runs finished 658 updates, `status` COMPLETE, final train loss 0.19 to 0.36 (1B) and 0.16 to 0.29 (3B), peak GPU 43 to 44 GiB (1B), 54 to 55 GiB (3B, host optimizer). Source: `results/runs/*/result.json`.
- **Format deviation.** Llama sees the Llama-3 header format, with no thinking block (PROTOCOL.md); Qwen3 saw its chat markers with an empty think block. The family comparison is therefore recipe-matched and data-matched, not format-identical.
- **Cross-family claim.** The Qwen3 rows are from V26's committed summary; no paired task-level test across families was run. The statement "Llama below Qwen3" is about point estimates only.
- **Seed noise at 3B.** Seed 20260832 beats seed 20260831 by +4.44 pts on pass@8 with a CI that excludes 0 ([0.74, 8.89]); every other seed pair is inside its CI. Seed SD at 3B (0.89 pts pass@1) is about three times Qwen3-1.7B's (0.30), so single-seed 3B differences under about 2 pts pass@1 should not be read as real.
- **Not measured.** No DT metric, no test split, no open-weight comparison on public VeriBench; this experiment is the training recipe on the private validation split only.

## Files

`results/summary_v28.json` (all numbers), `results/tables_v28.md` (tables as printed by `analyze_v28.py`), `results/analysis/` (per-system sample and task CSVs), `results/runs/` (per-run `result.json`, `steps.csv`, `identity.json`), `results/gen_timing/`, `results/sacct_v28.txt`, `results/jobs_v28.tsv`, `results/prepare_receipt.json`, `results/analyze_stdout.log`.

Reproduce: `python analyze_v28.py --v28-root <extracted expt_v28_results.tgz> --qwen-summary ../expt_v26_sherlock_seed_replicates/results/summary_v26.json --out results` (scorer pinned at `59059a20`).

**TLDR-end:** [rl4cv: model families] Llama-3.2 1B 2.96% and 3B 7.35% validation pass@1 (no DT), 3B beats 1B by +4.38 pts, below Qwen3 at matched size; one prediction missed (3B just above 7%).
