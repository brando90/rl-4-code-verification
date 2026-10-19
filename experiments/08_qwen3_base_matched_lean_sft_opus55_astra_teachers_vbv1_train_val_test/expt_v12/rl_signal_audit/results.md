# Existing validation reinforcement-learning signal audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v12/rl_signal_audit/results.md>

**Status:** COMPLETE. Local measurement and Sherlock job 48510183 agree on every reported quantity. **Last updated:** 10-19-2026 12:56 PDT.

This is a descriptive post-hoc audit of the already published current-corpus validation scores. It does not generate new answers, open the test split, or show that reinforcement learning improves the checkpoint.

## Local measurement

Inputs are the committed `../results/analysis_v12_current_cells.csv` (sha256 `072fff2f…0cb0`) and the 135 validation task IDs in `../../expt_v1/results/split/vbv1_validation_task_ids.txt` (sha256 `666d6d6b…c84d`). All 1,080 cells are present, eight samples per task. Capped outputs stay in the reward baseline and receive zero loss weight. The receipt is `results/local_reference/summary.json`. Three targeted tests passed.

| Quantity | Value | 95% interval | Unit |
|---|---:|---|---|
| Binary successes | 120/1080 (11.11%) | — | responses |
| Admitted signal density ρ | 15.37 | [9.37, 22.76] | advantage mass per million generated tokens |
| Effective coverage H | 0.164 | [0.107, 0.228] | normalized across 135 tasks |
| Mixed-task share | 24/135 (17.8%) | [11.9%, 24.4%] | tasks with both successes and failures |
| Target band | 16/135 | — | tasks with 2–6 successes out of 8 |
| Nonzero admitted advantages | 191 | — | responses |
| Admitted mass in the heaviest 10% of tasks | 71.1% | — | share of admitted advantage mass |

Intervals are 10,000-draw bootstraps of whole validation tasks, seed 0, keeping all eight responses. No hypothesis test was planned, so p-val=n/a. The task bootstrap does not estimate variability across training seeds.

Verdict: **nonzero validation reward signal**. The checkpoint is a candidate starting point. The frozen formatting gates and the 25% accuracy milestone remain separate and unmet. Actual reinforcement-learning improvement is unmeasured.

## Sherlock recovery

The first submission, bridge run 39309938703, used the interactive-only `dev` partition and was rejected before Slurm admission. Its directory is preserved. Job **48509206** reached a `normal` compute node and failed in 7 seconds: `module load` did not put NumPy on the batch interpreter's path. Job **48510183** is the infrastructure retry. It used the `normal` partition, one processor, 2 GB, 18 seconds, and zero graphics processors, with Python 3.12.1 and NumPy 2.2.6 on `sh02-01n56`. Exit code 0. Its summary matches the local receipt on status, verdict, measurement, intervals, counts, and input hashes. The receipt is `results/sherlock_48510183_summary.json`.

**TLDR-end:** [rl4cv: validation signal audit] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v12` has nonzero reward signal on the published validation set (ρ 15.37 [9.37, 22.76], H 0.164 [0.107, 0.228], 24/135 mixed tasks). Sherlock job 48510183 reproduced that measurement.
