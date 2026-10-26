# V16: Sherlock validation scoring of the two 08 v4 SFT checkpoints

**TLDR:** The two Sherlock-trained v4 checkpoints reproduce the committed SNAP rung on VeriBench V1 validation: pass@1
4.81% (seed 20260830) and 5.37% (seed 20260831) vs 4.91% for v1 `sft_1p7B_f1p0` (same corpus, 658 updates, same Base
revision). Both paired differences are within half a point, and their 95% CIs include zero. Base scores 0/1080 on
Sherlock and on SNAP. See [results](results.md).

## Question

Does training the 08 SFT recipe on Sherlock (expt_v4, two seeds) give the same validation score as the SNAP run,
when generation (vLLM, frozen expt_v12 settings) and Lean kernel scoring are also done on Sherlock?

## What ran

| Step | Where | Detail |
|---|---|---|
| Training | Sherlock H100 | [expt_v4](../expt_v4/README.md), seeds 20260830 and 20260831, 1,316 updates in total |
| Generation | Sherlock GPU, vLLM in Apptainer | 135 validation tasks x 8 samples per system, expt_v12 frozen settings; Base included |
| Scoring | Sherlock CPU (`normal`, `dev`) | `score_scsc.py --skip-tc` at veribench 59059a2, Lean 4.22, Mathlib 79e94a09 (same as SNAP), 24 sample jobs of 135 files |
| Analysis | local | `scripts/analyze_v16.py`: expt_v6 `analyze.evaluate` (kernel binary + non-vacuity gate), task bootstrap |

The test split was not opened.

## Metrics

- **pass@1**: mean binary success over the 8 samples of every task (1080 cells).
- **pass@8**: share of the 135 tasks solved by at least one of 8 samples.
- **CIs**: 95% task bootstrap, 10,000 draws, numpy seed 0; all samples of a task are resampled together. Differences
  against SNAP rungs are paired on the same task draws, using the committed `expt_v1/results/ladder/*_validation_cells.csv`.

## Scoring notes

- The first `dev` job (48671803) was cancelled at 1h08m: four parallel Lean runs reached the 16 GB cap on `dev`.
  Scoring then ran as one sample per `normal` array task (`score_v16_normal.sbatch`, 48678492), with a claim per sample
  in `score_one.sh` so no sample was scored twice. Samples left partial by the cancelled job were redone by a fill
  array (48681041, tasks 16-19), the same sbatch without `--if-untouched`.
- Array task 48678492_15 (v4 seed 20260831, sample 0) reported one OOM-killed step at 8 GB. The sample still finished
  with rc=0 and all 135 tasks `scored`, and it has the most successes of that seed's samples (9), so it was kept.
- All 24 samples have 135/135 tasks with `scoring_status=scored`.

## Files

- `scripts/score_v16.sh`, `scripts/score_v16b.sh`: dev drivers (materialize jobs, score 4 at a time, tar the results).
- `scripts/score_one.sh`: score one sample with a claim; `scripts/score_v16_normal.sbatch`: one sample per array task.
- `scripts/analyze_v16.py`: the summary, CIs and paired differences. Needs `external/veribench_scorer` (not committed).
- `results/summary_v16.json`, `results/tables_v16.md`, `results/analysis/*_cells.csv` and `*_tasks.csv`.

Sherlock paths: generations in `$SCRATCH/rl4cv_sherlock/v4_validation/{20260830,20260831,base}/full/raw.jsonl`;
scores in `$SCRATCH/rl4cv_sherlock/v4_validation/score_v16/` (`v16_scores.tgz`, sha256 `b8f44692...13df9`).
