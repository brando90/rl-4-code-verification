# Experiment 08 version 2 protocol — matched step-658 test evaluation at all four sizes

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/PROTOCOL_v2.md>

**TLDR:** Version 1 tested only the 8B checkpoint at step 658 and the 14B checkpoint at step 334, so its trained test numbers are not matched across sizes. Version 2 tests the three remaining step-658 checkpoints (1.7B, 4B, 14B) once each on the VeriBench V1 (VBV1) test split. Generation, scoring and judging match version 1 exactly. All four sizes can then be compared after the same supervised fine-tuning (SFT): the same 1,315 examples, 658 updates and 5,752,936 loss tokens. Version 1's verdict, selection and files stay unchanged.

**Status:** LOCKED by the Claude master on 10-13-2026, before any version 2 test generation. The lock is the commit that adds this file. Any later change is a dated, numbered amendment below.

## 1. Why version 2 exists (Brando, 10-13-2026)

- Brando: "make sure to finish the 1.7B and 4B and fully test it. Its crucial that all the models are SFTed on the same data and same number of tokens so that the experiments are comparable." Then: "same number of tokens (whatever that means for batch length, context length etc)".
- **Training is already matched.** PROTOCOL § 8 and `expt_v1/results/sft_config_diff.md` record it, and `expt_v1/results/train_logs/` verifies it per step. Every size used:
  - the same SFT set S (1,315 examples over 476 train tasks), in the same frozen order;
  - 658 updates, global batch 2, micro-batch 1, max sequence length 16,384;
  - no sequence packing, no dynamic batching;
  - the same learning-rate schedule (AdamW 2e-5, 20 warmup updates, then cosine over 638), seed 20260830, one epoch;
  - identical per-step and cumulative loss-token counts, ending at 5,752,936.

  Only the GPU layout differs (tensor parallel 1/2/4/8 and the matching padding multiple), and that changes no loss token.
- **What was missing.** Version 1's PARTIAL rule tested each size's earliest passing checkpoint: 8B step 658 (fraction 1.0) and 14B step 334 (fraction 0.5). 1.7B and 4B passed no validation rung and were not tested. So no version 1 test table compares all sizes at one token budget.
- **The version 2 choice.** Version 2 holds the token budget fixed at the full 5,752,936 tokens (step 658, fraction 1.0) for every size. That is the only fraction where 8B has a test result and where all four sizes have finished training. The choice follows Brando's matched-token instruction and is not based on any test outcome.

## 2. Scientific-integrity disclosure

- **Already observed before this lock:** version 1's test results for `test_sft_8B_f1p0`, `test_sft_14B_f0p5`, `base14b`, `base_1p7B_e05`, `base_4B_e05` and `base_8B_e05`; all 20 validation rungs; experiment 05's Base receipts.
- **Not yet observed:** any test output of the 1.7B, 4B or 14B step-658 checkpoints. None has ever been generated.
- **One test evaluation each.** Each version 2 checkpoint is evaluated on the test split exactly once (CLAUDE.md, D-013: "once per frozen checkpoint"). No test outcome triggers training, tuning, checkpoint selection, resampling or a change of settings.
- **Version 1 is unchanged.** Its PARTIAL verdict, `selection.json`, `test_manifest.json`, `test_eval.json` and every other version 1 file stay byte-identical. Version 2 writes only under `expt_v2/` and new runtime paths.
- **Labels.** 1.7B and 4B step 658 failed version 1's validation format gates (extraction and token cap), so their version 2 numbers are matched-budget diagnostics, not RL-ready warm starts. 14B and 8B step 658 passed all three validation gates.

## 3. Systems and declared cells

| Label | Role | Checkpoint | Loss tokens | Source | Weights manifest SHA-256 (from `expt_v1/results/ladder_manifest.json`) |
|---|---|---|---:|---|---|
| `test_sft_1p7B_f1p0` | trained, **new** | `/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/1.7B/hf/step_658` | 5,752,936 | generated in version 2 | `925d110f5a598d18cc9160f0758c5c64d1097956cb4db3057c9ade82ca6fafb4` |
| `test_sft_4B_f1p0` | trained, **new** | `/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/4B/hf/step_658` | 5,752,936 | generated in version 2 | `c0588065bf8019c11bbe1404431d2cc57cbd5bc656890d1b1b105b9239108120` |
| `test_sft_14B_f1p0` | trained, **new** | `/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/14B/hf/step_658` | 5,752,936 | generated in version 2 | `8c65cc3f0c900fffddb760b5daf77590ea319cdb92039c4df12bc57b9982d0d4` |
| `test_sft_8B_f1p0` | trained, reused | `/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/8B/hf/step_658` | 5,752,936 | version 1 cells and judge ratings, unchanged | `3085508bfd29932193b556c2f769eabe83b26e2d96dd59ef7412cfbcbf8f397d` |
| `base_1p7B_e05`, `base_4B_e05`, `base_8B_e05` | Base, reused | experiment 05 receipts | 0 | version 1 test cells and ratings, unchanged | — |
| `base14b` | Base, reused | `Qwen/Qwen3-14B-Base` @ `0b0bd373…` | 0 | version 1 test cells and ratings, unchanged | — |
| `test_sft_14B_f0p5` | version 1 diagnostic | step 334 | 2,884,708 | version 1, unchanged | reported beside the matched table, not in it |

- **Declared:** 222 test tasks × 8 samples = 1,776 cells per system.
- **New cells:** 3 systems × 1,776 = 5,328.
- **Matched table:** eight systems (four trained at step 658 plus four Base), 14,208 cells: 5,328 new and 8,880 reused.
- **Frozen before generation:** the task-id list, which must hash to `303a6c666d6902bb62e64a37091167a6150e652f1c3b1311c0a62e8c7fccd095` like version 1's, and the version 2 manifest `expt_v2/results/test_manifest_v2.json`. Both are committed and pushed to `origin/main` before the first generation process starts.
- **Admission check.** The first generation process must pass a version 2 admission check. It verifies that the manifest and this protocol are the exact published files on `origin/main`, that the label and model path are in the manifest, and that the export's weight-manifest hash matches the table above.

## 4. Generation and kernel scoring (identical to version 1, PROTOCOL §§ 9–10)

- **Command:** `rl4cv.veribench.generate --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --samples 8`.
- **Same as version 1:** experiment 103's VBV1 pack, `venv_gen` (vLLM 0.30.0), local Hugging Face exports and `run_ladder_e08.sh`'s merge and exact-manifest check.
- **Kernel scoring:** the frozen scorer `score_scsc.py --skip-tc` (`external/deps.lock.json`: `veribench_scorer`), with the same private grading project (Lean v4.22.0 plus the pinned Mathlib), then `collect` and `summarize`.
- **Allowed variation:** the number of data-parallel shards, i.e. how many GPUs each system uses. Version 1 also varied it.
- **Missing cells.** A missing generation or failed scoring is unknown, never zero. Infrastructure retries re-run the identical cell. A cell is never re-sampled or dropped because of its score.

## 5. Formal specification coverage (FSC) and the combined score (identical to version 1, PROTOCOL § 10)

- **Judge.** The validated judge `vb103_judge` (D-102, experiment 100's H2 ensemble) runs through Vals Valkyrie (D-108, Vals-funded): GPT-6 Sol high plus Claude Opus 5.5 max, three ratings each, median per member, mean of the two medians divided by five. Use exactly the frozen bundle version 1 used.
- **What gets judged.** Every new cell with IC_tests = 1 (including IC_proofs = 0), plus the same fixed 60-file audit per system. The audit has 12 cells per core family, ranked by `sha256("rl4cv-e08-audit-v1:" + task_id + "|" + sample_idx)` over the frozen test task list, so the audit cells are identical to version 1's. Judge overlaps once. List missing audit files without replacing them.
- **Compile gate.** `fsc_compiled` = FSC when IC_tests = 1, else 0 (D-003).
- **Route controls.** Before any test rating, pass bounded route controls on the same train-file control pack and thresholds as version 1: 0.90 for the oracle, vacuous, shuffled and blank controls, and 0.80 for half-deletion. Verify the Vals payer and route (host, organization, credential source, payer) and record non-secret evidence before the first call.
- **Retry rule.** Six ratings per file are declared calls, not retries. Each rating follows PROTOCOL § 3's two-request, no-resend-if-possibly-served limit.
- **Combined score (D-009).** SCSC (the smooth conjunctive score for code verification) = (mean IC_tests · mean IC_proofs · mean `fsc_compiled`)^(1/3), over one common known cohort per system. Report all 222 tasks, core 152 and IndustrySet 70 separately.
- **Intervals.** 10,000 task-bootstrap resamples, seed 0, keeping each task's eight samples together. Intervals describe this single training run, not training-seed variation. p-val=n/a (interval estimation only).
- **Incomplete coverage.** If any cell stays unknown, label the measured-cohort score and bound the full-manifest aggregate by setting unknown factors to 0 and to 1.

## 6. Analyses (all prespecified)

1. **Matched step-658 table.** IC_tests, IC_proofs, `fsc_compiled`, SCSC [95%] and the `kernel_binary` mean for the four trained systems and four Base systems, each over all, core and IndustrySet.
2. **SFT minus Base, per size.** Paired differences on the `kernel_binary` mean pass rate and on SCSC, with shared resampled task indices and missing-pair counts.
3. **Size scaling at a matched budget.** SCSC and the `kernel_binary` mean against model size at step 658, plus paired differences between adjacent sizes (4B − 1.7B, 8B − 4B, 14B − 8B), all on the shared resampled tasks.
4. **Version 1 diagnostic.** `test_sft_14B_f0p5` reported beside the matched table, with the paired difference 14B step 658 − 14B step 334.
5. **Frozen-forecast evaluation.** Score every forecast in `expt_v2/forecasts/` (§ 7) as pass or fail, verifying its hash first. Failed forecasts are reported exactly like passing ones.

## 7. Frozen forecast (D-004)

`expt_v2/forecasts/e08v2_matched_step658_test.json` was frozen with `rl4cv.forecast.freeze_forecast` before any version 2 test generation. It is append-only. It predicts only the three not-yet-observed systems, using the validation ladder.

## 8. Budget and resources (Trigger Rules 9 and 51; the estimate is recorded here, not asked)

- **Model calls.** Only the judge, Vals-funded and recorded rather than capped (D-108), as in version 1.
  - The estimate starts from version 1's charge of $252.81 for 4,302 ratings ≈ $0.0588 per rating.
  - Expected judged files per system ≈ validation pass rate × 1,776 plus about 57 audit files: about 144 (1.7B), 220 (4B) and 268 (14B). That is ≈ 632 files × 6 ratings ≈ 3,800 ratings.
  - Expected spend: **≈ $225**, plausible range $150–$450, plus about $3 of route controls.
  - No teacher calls and no training.
- **GPUs.** vLLM generation on skampere1's A100 80 GB devices. Generation is compute-bound; vLLM reserves most of each device's memory.
  - Plan: 1.7B on one device, 4B on one, 14B on one or two data-parallel shards, using only devices idle in `nvidia-smi` and free in `$WORK/pipeline/leases.json`. Never touch other users' devices.
  - Estimated 1–4 hours per system, unmeasured for these checkpoints. Set `CUDA_VISIBLE_DEVICES` explicitly, verify utilization with `nvidia-smi` within minutes of launch, and release each device when its generation ends.
- **CPU.** Kernel scoring is CPU-bound: eight score shards per system, `SCORE_PAR=4`. Several hours per system, as in version 1.
- **Expected total wall time:** about 8–16 hours.

## 9. Amendments

None.

TL;DR: Version 2 tests 1.7B, 4B and 14B at step 658 once each with version 1's exact sampling, scorer and judge, so all four sizes can be compared after identical SFT (same data, 658 updates, 5,752,936 tokens). Version 1's verdict and files are unchanged; the forecast was frozen before generation.
