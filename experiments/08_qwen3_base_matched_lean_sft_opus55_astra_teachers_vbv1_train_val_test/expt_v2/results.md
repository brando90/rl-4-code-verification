# Experiment 08 version 2 results — matched step-658 test evaluation at all four sizes

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/results.md>

**TLDR:** Version 2 evaluates 1.7B, 4B and 14B at step 658 once each on the VeriBench V1 test split (222 tasks × 8 samples), using version 1's exact sampling, scorer and judge. With version 1's 8B step-658 result, it then compares all four sizes after identical SFT: the same 1,315 examples, 658 updates and 5,752,936 loss tokens. Nothing has been measured yet.

**Status:** RUNNING (dispatched 10-13-2026). The protocol is locked and the forecast was frozen before generation.

## Declared cells

| System | Role | Declared cells | Known cells | Judge ratings known |
|---|---|---:|---:|---|
| `test_sft_1p7B_f1p0` | new | 1,776 | 0 | 0 |
| `test_sft_4B_f1p0` | new | 1,776 | 0 | 0 |
| `test_sft_14B_f1p0` | new | 1,776 | 0 | 0 |
| `test_sft_8B_f1p0` and the four Base systems | reused from version 1 | 8,880 | 8,880 | complete in version 1 |

## Validation context (version 1, already observed; validation split, 135 tasks × 8)

| Step-658 checkpoint | Extracted / 1,080 | Capped / 1,080 | Mixed tasks / 135 | `kernel_binary` mean pass | Validation gates |
|---|---:|---:|---:|---:|---|
| 1.7B | 897 | 184 | 20 | 0.0491 | fail (extraction, cap) |
| 4B | 946 | 134 | 32 | 0.0926 | fail (extraction, cap) |
| 8B | 974 | 106 | 32 | 0.0963 | PASS |
| 14B | 995 | 84 | 39 | 0.1204 | PASS |

TL;DR: Version 2 is running. No version 2 test number exists yet; this file is updated as each system is generated, scored and judged.
