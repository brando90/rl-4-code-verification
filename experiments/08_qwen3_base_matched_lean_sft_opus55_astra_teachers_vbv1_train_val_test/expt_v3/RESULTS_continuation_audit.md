# Existing validation signal and cached training data

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/RESULTS_continuation_audit.md>

**TLDR:** The 8B and 14B checkpoints pass the existing reinforcement-learning signal gates, while the smaller models fail format and length gates. There are 685 cached additional teacher-response candidates and 587 earlier Python-to-Lean pairs to audit before generating more data; no new model was trained.

## Matched validation measurements

Source: `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1`, step 658, 5,752,936 loss tokens at each size. VeriBench V1 validation: 135 tasks × eight attempts = 1,080 known/declared cells per size. The binary success rule requires kernel-verified tests and proved theorems with the frozen non-vacuity checks; it does not measure semantic completeness of the specification.

| Size | Binary success rate [95% interval] | Extracted /1,080 | Capped /1,080 | Mixed tasks /135 | Tasks with 2–6 successes /135 | Existing gates |
|---|---|---:|---:|---:|---:|---|
| 1.7B | 0.0491 [0.0269, 0.0759] | 897 | 184 | 20 | 11 | FAIL format/length |
| 4B | 0.0926 [0.0602, 0.1306] | 946 | 134 | 32 | 21 | FAIL format/length |
| 8B | 0.0963 [0.0630, 0.1343] | 974 | 106 | 32 | 20 | PASS |
| 14B | 0.1204 [0.0833, 0.1620] | 995 | 84 | 39 | 28 | PASS |

Intervals are post hoc percentile task bootstraps: 10,000 draws, seed 0, keeping eight attempts together. These describe one training seed and do not measure training-seed variation; p-val=n/a (interval estimation, no hypothesis test). All means and count distributions are in [the machine-readable audit](results/continuation_audit.json), along with every input hash.

At equal training tokens, the validation binary success-rate difference (14B minus 8B) is +0.0241 [+0.0074, +0.0407], p-val=n/a. This is not a test-set Smooth Conjunctive Score for Code verification (SCSC) comparison.

The historical gates are ≥972 extractions, ≤108 capped outputs and ≥7 mixed-success tasks, with no unknown cells. 1.7B needs 75 additional extractions and 76 fewer capped outputs to meet the separate format gates; 4B needs 26 of each. These are separate deficits, not counts of disjoint failures.

Varun’s meeting target was 25–75% success over eight attempts. We report the observed 2–6/8 band descriptively: eight samples do not establish a task’s true success probability. This band is not a retrospectively imposed acceptance gate. SCSC is the geometric mean of test correctness, proved-theorem fraction and compile-gated formal specification coverage; it is neither binary pass probability nor pass@8 (at least one success in eight attempts). The validation ladder has no validated-judge SCSC measurement.

## Reuse before generating

| Source | Existing evidence | Remaining admission work |
|---|---|---|
| `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1` selected set | 1,315 examples; 476/539 train tasks | Reuse frozen original for replay control |
| `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1` capped set | 685 candidates; 360 already-covered train tasks; 685 distinct raw Lean hashes | Joint normalized deduplication, exact response hashes, rendering and full-loss-text screen |
| `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3` | 587 pairs; 455 source tasks | Convert its system/user/lean schema, joint deduplication, length/mask and screen checks |

The capped set contributes **zero new source tasks** relative to the selected set. Of its 685 candidates, 389 are security-set examples. More responses can help teach format and proof patterns, but they do not by themselves expand source-task coverage. Distinct raw hashes are not proof of distinct normalized programs. No expanded corpus has yet been admitted.

The [candidate manifest](results/cached_train_candidates.csv) joins every cap exclusion to its recorded train split, successful kernel receipt, extraction consistency and screen status. It provides response paths and hashes without copying raw training content. Its 685 rows are candidates, not newly validated training examples.

## Host availability verified

A subsequent bounded read on `skampere1` verified **685/685 candidate response hashes**, with zero missing or mismatched files, and the MBPP file’s full hash plus **587/587 retained Lean hashes** over 455 tasks. See [host_data_verification.json](results/host_data_verification.json) for the observation time and manifest binding. This establishes available source bytes; it does not replace joint deduplication, conversion and rendering/screening admission. Lethan’s own retrieval remains unverified.

## Reproduce

From the repository root, in the project Python environment:

```bash
python experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/prepare_continuation.py
```

This reads existing score receipts and split metadata only, makes no model calls, and writes version-3 audit outputs. It never reads test outcome files or changes prior-version files. It rejects duplicate/missing validation tasks, groups with fewer than eight known samples, and candidates outside the training split.

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test] The cached evidence supports a matched comparison of more exposure and a broader training pool; the benefit of either intervention remains unmeasured.
