# Experiment 08 SFT configs — Varun's matched warm-start recipe (source) and this experiment's derived configs

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/configs/README.md>

**TLDR:** The `varun_*` files are byte-for-byte copies of Varun Madan's paper-1 phase-1c matched SFT run on `skampere3`, which is the recipe experiment 08 must match at every Qwen3 size. The worker adds `e08_sft_<size>.yaml`, which may differ from Varun's config only where PROTOCOL § 8 allows, and a diff report.

## Provenance (copied 10-07-2026 by the master, read-only from `/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/`)

| File here | Source file | Source mtime | SHA-256 |
|---|---|---|---|
| `varun_phase1c_production_sft.yaml` | `phase1c_production_sft.yaml` | 2026-08-30 02:21 PDT | `8e45b9f5605dbd5eeaf448bc1e0088760d572b0eecebeb9908d1eaacbdf9a290` |
| `varun_launch_phase1c_production_sft.sh` | `launch_phase1c_production_sft.sh` | 2026-08-30 02:28 PDT | `276ecaa286fd453285e51f46d5ee40cb87fc4b61b6629d37bc558631c069b3b2` |
| `varun_phase1c_production_manifest.json` | `phase1c_production_manifest.json` | 2026-08-30 02:21 PDT | `239c87d26e9ad3007272c2ec6a3cd231e6ca4ee5a52ad39936eeeb36c61a36ee` |
| `varun_matched_sft_recipe.json` | `matched_sft_recipe.json` | 2026-08-30 00:51 PDT | `b65f15939504ddd31c7809b8255ba3f90df51373fd4d2acf1af0af43540f1a6a` |

## What Varun's run used

NeMo RL 0.4.0 (`/lfs/skampere3/0/vmadan/vendor/nemo_rl_v040_cuda128`), DTensor with activation checkpointing, on one GPU per run.

| Setting | Value |
|---|---|
| Epochs and steps | 1 epoch, 1,024 updates over 2,048 rows |
| Batch | global batch 2, micro-batch 1 |
| Sequence length | maximum 16,384 |
| Precision and loss | bf16, assistant-only loss |
| Optimizer | AdamW: lr 2×10⁻⁵, betas (0.9, 0.98), eps 1×10⁻⁵, weight decay 0.1 |
| Gradient clipping | 1.0 |
| Schedule | linear warmup over 31 updates (start factor 1/31), then cosine to 0 over 993 |
| Checkpoints | every 256 updates (update quartiles), reporting cumulative admitted assistant tokens at each |
| Data | `ResponseDataset` (`input` / `output`), default chat template, no shuffling |
| Logging | Weights & Biases on |

## Allowed differences in `e08_sft_<size>.yaml` (PROTOCOL § 8)

- **Run-specific inputs:** the model path and revision, data paths and dataset adapter (system + user + assistant messages rendered exactly as at evaluation), and output, checkpoint and log directories.
- **Step and checkpoint settings:** total steps ⌈|S| / 2⌉; Varun's schedule form with W = ⌈0.03 · steps⌉ warmup updates (`LinearLR` from 1/W of the peak, then cosine to 0); seed 20260830 as in his config; checkpoints at the precomputed steps where cumulative assistant tokens first reach 12.5 / 25 / 50 / 75 / 100% (PROTOCOL § 8). Varun's run saved update quartiles and reported tokens; his recipe JSON names token fractions. SFT-time validation is off; the PROTOCOL § 9 ladder selects checkpoints.
- **Logging:** Weights & Biases off; TensorBoard and CSV logs on.
- **GPU layout:** GPU count, data or tensor parallel sharding, and micro-batching, without changing global batch 2.
