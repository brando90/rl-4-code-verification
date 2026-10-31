# V26 results: Sherlock seed replicates

**TLDR:** The 1.7B v4 recipe has a three-seed noise bar of 0.30 pts SD (0.56 pts range) on validation pass@1 (no DT) and 2.2 pts SD (4.4 pts range) on pass@8 (no DT); the 4B checkpoints match SNAP's `sft_4B_f1p0` within noise and beat 1.7B by +3.8 pts pass@1 (CI [2.27, 5.62]). Seed noise is smaller than the task-sampling noise of 135 tasks (95% CI about +-2.4 pts pass@1), so single-seed differences under about 1 pt pass@1 or 5 pts pass@8 mean nothing. Validation split only; test unopened; $0 provider spend.

Metric tag: every number here is no DT. A pass is a Lean kernel check plus the non-vacuity gate, with no differential testing; DT was not run on these checkpoints. The SNAP and expt_v16 rows use the same criterion.

## Validation results (135 tasks x 8 samples = 1,080 cells per checkpoint)

| System | Successes / cells (no DT) | pass@1 (no DT) [95% CI] | pass@8 (no DT) tasks / 135 [95% CI] |
|---|---|---|---|
| 1.7B v4 seed 20260830 (expt_v16) | 52 / 1080 | 4.81% [2.50, 7.50] | 18 (13.33%) [8.15, 19.26] |
| 1.7B v4 seed 20260831 (expt_v16) | 58 / 1080 | 5.37% [3.15, 8.06] | 24 (17.78%) [11.85, 24.44] |
| 1.7B v4 seed 20260832 (V26) | 53 / 1080 | 4.91% [2.69, 7.59] | 21 (15.56%) [9.63, 22.22] |
| 4B v4 seed 20260830 (V26) | 97 / 1080 | 8.98% [5.74, 12.78] | 31 (22.96%) [16.30, 30.37] |
| 4B v4 seed 20260831 (V26) | 94 / 1080 | 8.70% [5.56, 12.31] | 30 (22.22%) [15.56, 29.63] |
| 1.7B pooled (3 seeds) | 163 / 3240 | 5.03% [2.87, 7.56] | n/a |
| 4B pooled (2 seeds) | 191 / 2160 | 8.84% [5.69, 12.45] | n/a |
| SNAP `sft_1p7B_f1p0` | 53 / 1080 | 4.91% [2.69, 7.59] | 20 (14.81%) [8.89, 21.48] |
| SNAP `sft_4B_f1p0` | 100 / 1080 | 9.26% [6.02, 13.06] | 33 (24.44%) [17.04, 31.85] |

## Seed spread

| Size | Seeds | pass@1 (no DT) mean (SD) [range] | pass@8 (no DT) mean (SD) [range] |
|---|---|---|---|
| 1.7B | 3 | 5.03% (0.30) [0.56] | 15.56% (2.22) [4.44] |
| 4B | 2 | 8.84% (0.20) [0.28] | 22.59% (0.52) [0.74] |

## Paired differences (task bootstrap, 95% CI)

| Comparison | pass@1 diff (no DT) | pass@8 diff (no DT) |
|---|---|---|
| 1.7B s20260832 - 1.7B s20260830 | +0.09 [-1.11, 1.30] | +2.22 [-1.48, 5.93] |
| 1.7B s20260832 - 1.7B s20260831 | -0.46 [-1.94, 0.83] | -2.22 [-6.67, 2.22] |
| 1.7B s20260832 - SNAP 1.7B | 0.00 [-1.11, 1.11] | +0.74 [-4.44, 6.67] |
| 4B s20260830 - SNAP 4B | -0.28 [-1.67, 1.20] | -1.48 [-5.93, 2.22] |
| 4B s20260831 - SNAP 4B | -0.56 [-2.41, 1.30] | -2.22 [-8.15, 2.96] |
| 4B s20260830 - 4B s20260831 | +0.28 [-1.30, 1.94] | +0.74 [-2.96, 4.44] |
| 4B pooled - 1.7B pooled | +3.81 [2.27, 5.62] | n/a |
| 4B pooled - SNAP 4B | -0.42 [-1.85, 1.02] | n/a |
| 1.7B pooled - SNAP 1.7B | +0.12 [-0.86, 1.08] | n/a |

## Predictions in PROTOCOL.md

| Prediction | Result |
|---|---|
| 1.7B s20260832 pass@1 in 3.5-6.5%, pass@8 in 10-21%, three-seed SD < 1 pt | Met (4.91%, 15.56%, SD 0.30) |
| 4B per-seed pass@1 in 6.5-12%, both differences vs SNAP 4B inside their CIs | Met (8.98%, 8.70%) |
| 4B pooled - 1.7B pooled about +4 pts, CI excludes 0 | Met (+3.81 [2.27, 5.62]) |
| 4B seed spread similar to or larger than 1.7B's | Not shown: two 4B seeds give a smaller range (0.28 vs 0.56 pts), but two seeds cannot estimate a spread |

## Noise bar for SNAP single-seed comparisons

- Seed-to-seed SD at 1.7B is 0.30 pts pass@1 and 2.2 pts pass@8 (3 seeds); the largest gap between two seeds is 0.56 pts and 4.4 pts.
- Every paired difference between Sherlock seeds, and between Sherlock seeds and SNAP, has a CI that contains 0. SNAP's single-seed 1.7B (4.91%) and 4B (9.26%) sit inside the Sherlock bands.
- A SNAP single-seed gain below about 1 pt pass@1 (or 5 pts pass@8) is within seed noise at this validation size.

## Criterion check

- 1.7B/4B V26 rows and the two expt_v16 rows: `expt_v6/analyze.evaluate`, `kernel_binary` with the non-vacuity gate (`analyze_v26.py` header, `PROTOCOL.md`).
- SNAP rows: read from `expt_v1/results/ladder/<label>_validation_cells.csv`, column `kernel_binary`. In those files no successful cell has a vacuous theorem or an unparseable file (0 of 53 for 1.7B, 0 of 100 for 4B), so the gate changes nothing and the counts equal the gated ones. No row uses `IC_tests` or `IC_proofs`.

## Deviations

- 4B seed 20260830: the first train job 48743246 died at step 174/658 (CUDA OOM in backward, allocator fragmentation). The full chain was rerun with the same code and arguments and only `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (allocator only; no numeric change): train 49980191, gen 49980207, score 49980208, collector 49980209. Its data order hash differs from the other 4B seed because the seed differs; code, data and token hashes equal across all three checkpoints.
- Score tasks 7 of 48743274 and 2, 3, 6 of 49980208 hit Slurm OUT_OF_MEMORY (exit 125) in Slurm's memory accounting (the job logs report rc=0); every one of the 8 score directories of each checkpoint holds its full per-task files, so there is no gap.
- Only two 4B seeds, so no 4B seed SD beyond the range of two.

## Jobs and GPU-hours

| Phase | Job ids | State | Wall / GPU-h |
|---|---|---|---|
| prepare | 48743229 | COMPLETED | 0.05 h (CPU) |
| 1.7B s20260832 | train 48743232, gen 48743234, score 48743241 [0-7] | COMPLETED | train 1.02, gen 1.56 GPU-h |
| 4B s20260830 first attempt | train 48743246 (FAILED, OOM); gen 48743247, score 48743265 cancelled | FAILED | 0.68 GPU-h |
| 4B s20260830 rerun | train 49980191, gen 49980207, score 49980208 [0-7], collect 49980209 | COMPLETED | train 2.37, gen 0.61 GPU-h |
| 4B s20260831 | train 48743269, gen 48743273, score 48743274 [0-7], collect 48743277 | COMPLETED | train 2.36, gen 2.29 GPU-h |
| scoring (24 array tasks) | `normal`, 3 CPUs each | COMPLETED | 20.8 job-hours |

Total GPU time: 6.43 h training (0.68 h of it the failed attempt) + 4.46 h generation = 10.9 GPU-hours on H100/L40S `gpu` nodes. Provider spend: $0.

Source: `expt_v26_results.tgz` (9,028,473 bytes, sha256 `d2720bc21e2cab7fe1bbfdd2865776dae1f5a0037d6a5bb7864d43dd1362a20e`, collector 49980209), run locally with `analyze_v26.py` (tables in `results/tables_v26.md`, `results/summary_v26.json`, per-cell and per-task CSVs in `results/analysis/`). The expt_v16 rows come from `expt_v16`'s committed scores.
