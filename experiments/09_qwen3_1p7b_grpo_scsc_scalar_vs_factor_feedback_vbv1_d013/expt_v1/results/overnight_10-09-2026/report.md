# Overnight factored-score learning: final supervision report

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/results/overnight_10-09-2026/report.md>

**TLDR:** Whether decomposed smooth feedback improves learned model weights remains unmeasured: the reinforcement-learning adapter failed a probability-consistency check before its first optimizer update. The separate supervised warm-start study has 15/20 trained checkpoints fully evaluated on validation, with five 14B checkpoints pending. This report closes parent overnight supervision after its 10-09-2026 11:13:36 PDT cutoff; it does not terminate the continuing warm-start study.

Observations: 10-09-2026 11:43–11:50 PDT. This is a parent reconciliation of published scientific artifacts and fresh runtime receipts. The original warm-start owner's requested final checkpoint was blocked by its usage allowance before acknowledgment; this report is not represented as that owner's finalization.

## What the learning experiment does and does not establish

`09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` implements the intended distinction between **partial credit** and **decomposition**. Its smooth conjunctive score for code (SCSC) combines test consistency, proof consistency and formal specification coverage through a geometric mean and frozen validity gates. The planned three arms were: A, strict binary reward; B, full smooth scalar reward; C, the same smooth reward with named factor feedback between two attempts. B minus A would test the reward change; C minus B would test the added factor information. The held-out endpoint uses a common single response without feedback, so an improvement would concern learned weights rather than another repair attempt.

Neither contrast was measured. The real disposable control generated 32 two-turn trajectories with 4,077 assistant tokens. The message-boundary and loss-mask check passed, but replay assigned zero probability to 4/4,077 sampled actions and exceeded the frozen 0.05 log-probability tolerance on 367/4,073 supported actions. Zero support mismatches were allowed. The owner stopped before optimization; changing the sampler or weakening that gate was not authorized. Backend numerical differences remain a plausible, unproven cause. These are exhaustive diagnostic counts for one saved batch, not estimates of a learning effect.

The 14/14 scorer controls matched expected outcomes. All 50/50 planned coverage-judge control ratings were measured, and both configurations passed their frozen category gates; this does not mean 50/50 expected-label accuracy. Completed judge-control charges were $3.0558; charges for earlier failed admission attempts remain unknown. There were zero scientific judge ratings. The attempt recorded 0.553611 device-hours and closed before its resource cap or original deadline. The deadline has now elapsed without a relaunch.

| Declared scientific work | Completed / declared | Missing |
|---|---:|---:|
| Calibration rollouts | 0/256 | 256 |
| Calibration responses | 0/512 | 512 |
| Training trajectories: three arms × two seeds | 0/6 | 6 |
| Validation evaluation cells | 0/945 | 945 |
| Held-out test evaluation cells | 0/1,554 | 1,554 |
| Before/after pairs | 0/2,142 | 2,142 |

All endpoint weights remain unfrozen. The maximum 12,288-response training plan was never an admitted denominator because no horizon was selected. Treatment effects and 95% confidence intervals are unavailable; p-val=n/a. The recorded [-1,+1] missing-data bounds are worst-case bounds, not confidence intervals. [Failed-gate report](../../../results.md), [terminal receipt](../terminal_receipt.json), and [aligned factor/strict-target matrix](../aligned/aligned_task_factors.csv) preserve every declared evaluation cell, with unknown outcomes blank rather than zero.

## Supervised warm-start evidence and remaining work

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` is a separate supervised fine-tuning (SFT) prerequisite study. All five training checkpoints for each of 1.7B, 4B and 8B are exported and scored. Each checkpoint has 135 validation tasks × eight samples = 1,080 cells. All five trained 14B checkpoints remain entirely unmeasured because training requires eight available graphics processing units (GPUs); only one was free in the final observation.

| Validation population | Measured / declared | Missing |
|---|---:|---:|
| Twenty trained checkpoints | 16,200/21,600 | 5,400 |
| Above plus newly evaluated Base14B | 17,280/22,680 | 5,400 |
| Above plus three reused base-model evaluations | 20,520/25,920 | 5,400 |

The [consolidated item-by-factor matrix](warm_start_validation_item_factors.csv) includes all 25,920 declared cells, including all 5,400 missing cells. It places test and proof factors next to kernel-only binary success. Formal specification coverage (`FSC`), full smooth score (`SCSC`) and full strict score are explicitly unmeasured throughout; the kernel-only diagnostic is not a substitute for them. [Accounting and input hashes](warm_start_accounting.json) bind the matrix to the published manifest and source tables. No held-out test content was opened to build it.

There is useful readiness evidence at the full training fraction (step 658):

| Model size | Tasks with mixed success among eight samples, share [95% Wilson interval] | Extracted responses, gate ≥90% | Responses hitting token cap, gate ≤10% | All readiness gates |
|---|---|---|---|---|
| 1.7B | 20/135; 0.1481 [0.0980, 0.2178] | 897/1,080; 83.06% | 184/1,080; 17.04% | Fail |
| 4B | 32/135; 0.2370 [0.1732, 0.3154] | 946/1,080; 87.59% | 134/1,080; 12.41% | Fail |
| 8B | 32/135; 0.2370 [0.1732, 0.3154] | 974/1,080; 90.19% | 106/1,080; 9.81% | Pass |
| 14B trained | Unmeasured | Unmeasured | Unmeasured | Not evaluated |

“Mixed success” means one to seven kernel-only successes among eight samples for a task, providing possible within-task learning signal. It is not accuracy or a measured benefit of factor feedback. The frozen mixed-task gate is ≥5%. These are existing point-estimate gates from the [published validation analysis](../../../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/validation_ladder.json); p-val=n/a. Wilson intervals use tasks as units, do not model dependence between related task variants, and do not measure variation across training seeds. Response extraction/cap counts are descriptive census counts for the frozen validation batch. This table does not select a checkpoint.

Selection and held-out testing remain unadmitted, with no selected test manifest or test-runtime files. The conditional protocol plan totals 14,208 test cells across eight systems (8,880 new + 5,328 reused, 222 tasks × eight samples per system). Those planned reused cells are not counted as completed evaluation in this study. Coverage-judge calls depend on later eligibility and have no frozen admitted count yet.

## Runtime closeout and continuation boundary

The original warm-start session remained `d3968eac-37d1-4b77-b339-a69389689c9c`, actual `claude-fable-5-1`/high with full permissions. Its final-observation handoff at 11:43:50 PDT immediately returned “You're out of usage credits. /model to switch models.” No acknowledgment or first useful action followed. No replacement owner, smaller-model probe, allowance reset or credit purchase was attempted. Interactive continuation through that owner requires restored allowance; its reset time is unknown.

The independent pipeline remained live and fresh (11:50:01 PDT tick), with its watchdog healthy at 11:45:03 PDT, zero compute children and zero live leases. Its admitted finite stages can continue when resources become available. The parent reporting cutoff is not a new study wall-time or device-hour cap. Preserve the original owner's work, pipeline, watchdog, completed artifacts and scientific pins. A live coordinator is not a scientific result.

`06_swebench_lite_factor_feedback_matched_budget` version 3 remains blocked before admission: 3/3 coordinator launches spent, 0/16 official controls, 0/8 author calls and 0/56 solver cells. Its 10:50 PDT deadline elapsed with no further execution. The final 11:48 PDT check found no owner, scientific jobs, owned containers, observer or task cron entry. The [blocked receipt](../../../../06_swebench_lite_factor_feedback_matched_budget/expt_v3/results/supervision_blocked_10-08-2026.json) and 23-file unfinished-source archive are preserved. Its five preliminary smoke executions are not admitted controls; repair efficacy remains unmeasured.

The learning study's original processes and watchers are absent, all nine leases are released, and the published aligned-artifact hashes match the runtime. Neither stopped study is authorized to restart. No new follow-on study was started. Correlations, repair improvements and learned-weight improvements remain distinct claims.

## Verification and publication

The repository checks passed on 10-09-2026: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 make test` → 162 passed, four skipped in 16.58 seconds. The deterministic join checks manifest identity, unique task/sample/system keys, all declared denominators and blank missing values. Re-running it reproduces both accounting outputs byte-for-byte. The parent [closure receipt](supervision_closeout.json) records observation provenance and the failed owner handoff. The report was published to main in `a99e681` before the overnight heartbeat was confirmed **PAUSED** at 10-09-2026 11:54:04 PDT. Its prompt and schedule were preserved. A subsequent 11:54:20 PDT check verified that the remote warm-start pipeline remained alive with a fresh 11:54:13 tick; its watchdog and study remain preserved.

**TLDR-end:** [rl-4-code-verification: 09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013] Factored-score learning has no measured treatment effect because the adapter failed before optimization. The final overnight accounting preserves completed warm-start evidence, all missing cells and the continuing study.
**Snapshot:**
```text
optimizer updates: 0
learning validation: 0/945; test: 0/1554
warm-start trained checkpoints: 15/20
warm-start validation factors: 20520/25920
warm-start missing validation cells: 5400
warm-start owner final handoff: allowance blocked before acknowledgment
warm-start pipeline/watchdog: preserved
repair official controls: 0/16; solver cells: 0/56
```
