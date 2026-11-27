# Concise Lean curriculum: 1.7B / 4B training comparison

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/results.md

**Status:** RUNNING in the last measurement. **Last updated:** 10-19-2026 04:55:13 PDT.

**Status refresh 11-27-2026:** no committed file after this date records 4B completion, a terminal exit, or a live process. The RUNNING label is that last measurement. In the table below, 1.7B control is 664/664 with 99/1,080 validation successes and 1.7B mixed is 904/904 with 74/1,080. 4B mixed is 526/904 updates, 3,049,296 assistant tokens, and 0/1,080 validation cells. `results/fused_handoff/status.json` records `FUSED_TRAINING` and a resumed trainer labeled RUNNING at step 100; that file is a host snapshot, not evidence the job is alive on 11-27-2026.

| Condition | Training progress | Assistant tokens consumed | Validation generated | Scoring jobs complete |
|---|---:|---:|---:|---:|
| 1p7_control | 664/664 updates | 5,759,732 | 1080/1,080 | 8/8 |
| 1p7_mixed | 904/904 updates | 5,753,602 | 1080/1,080 | 8/8 |
| 4b_mixed | 526/904 updates | 3,049,296 | 0/1,080 | 0/8 |

4B CPU fused optimizer: **FUSED_TRAINING**; checkpoint target 100; restore verification PASS. [Runtime amendment](AMENDMENT_4b_fused_optimizer.md). The original supervisor's deliberate termination receipt is retained.

## Verified preparation

- Corrected tiny examples: 500/500. Each includes an anonymous executable `example`; original version 5 remains pristine.
- All 135 validation prompts match the prior frozen instruction/system/addendum/prompt hashes.
- Frozen-scorer positive, compile-error and sorry-proof controls passed. The 4B float32 CPU optimizer matched native AdamW in its numerical control.
- Both augmented conditions expose all 500 tiny examples once and 1,308 existing responses; control exposes 1,328 existing responses. Source pool contains 2,585 admitted existing responses.
- Target budget is 5,752,936 assistant loss tokens. Actual crossing totals: control 5,759,732; augmented 5,753,602. Planned updates: control 664; each augmented condition 904.
- 4B uses full-parameter training with float32 CPU master weights/Adam moments and bfloat16 GPU parameters. It has no new replay control.
- Test evaluation is not performed. Formal specification coverage is unmeasured; no judge-dependent aggregate is claimed.

## Primary validation results (2,160/3,240 cells; 4B pending)

| System | Binary successes / 1,080 | Success rate | Tasks with 2–6 successes / 135 |
|---|---:|---:|---:|
| 1p7_control | 99/1,080 | 0.0917 [0.0574, 0.1306] | 18/135 |
| 1p7_mixed | 74/1,080 | 0.0685 [0.0417, 0.0991] | 16/135 |
| starting_1p7b | 55/1,080 | 0.0509 [0.0278, 0.0769] | 14/135 |

Intervals resample tasks with their eight attempts together, 10,000 draws, seed 0; p-val=n/a. Historical starting-checkpoint comparisons are descriptive.

Primary augmented-minus-control difference: -0.0231, 95% interval [-0.03888888888888889, -0.008333333333333333]; **negative**. One training seed; training-seed variability is unmeasured.

[Protocol](PROTOCOL.md) · [Checkpoint](CKPT_tiny_training.md) · [Runtime snapshot](results/runtime_snapshot.json)

**TLDR-end:** [rl4cv: concise Lean training] Last measurement 10-19-2026 04:55 PDT: 1.7B rows complete (99/1,080 and 74/1,080), 4B at 526/904 with 0/1,080 validation cells. Declared evaluation 3,240 cells. Not a live job as of the 11-27-2026 refresh.
