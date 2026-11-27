# Experiment 08 version 3 — 14B memory fix and launch plan (11-27-2026)

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/r1_14b_oom_fix_launch_plan_11-27-2026.md

**TLDR:** The four missing 14B rungs stay at 0/1,080 each. The 10-17-2026 CUDA out-of-memory on skampere3 was a foreign process holding 130.69 GiB on a 178 GiB GPU during step 184 of expansion's half segment, not the Gemma-3 full-logit failure. Relaunch one tensor-parallel-8 job on eight exclusive B200s (skampere3), else eight exclusive H200s (skampere2). Do not use A100-80GB. This file does not launch a job and does not edit the locked protocol, the frozen forecast, or the 12,960 measured cells.

**Authorization:** Brando, 11-27-2026: "fix it all, I want 'yes go ahead, move the projects forward, I approve!'" for the non-GPU prep in `docs/NEXT_STEPS_11-26-2026.md`. A GPU launch still needs a fresh inventory and an agent-sync claim. Free hardware only (D-111).

**Harness named for the SNAP run, not this note:** the existing NeMo RL 0.4.0 continuation (`train_continuation.sh` → `examples/run_sft.py`), no agent harness, no paid API, no DT. Validation stays Lean `kernel_binary` on VeriBench V1 validation, 135 tasks × 8 attempts. The locked protocol's pins stay (VeriBench task pin `c11b99ba` inside `PROTOCOL.md`). This continuation is not a new experiment, so it does not move to a later VeriBench release. The public release name on 10-28-2026 remains `veribench@1.3` for any new experiment.

## Diagnosis

Committed record, `results.md` execution check 10-18-2026 10:30 PDT and `resume_e14_after_oom.py`:

- Expansion 14B (`condition E`) reached step 183 of 335 and died during step 184 at 10-17-2026 22:03 PDT with `torch.OutOfMemoryError` on skampere3.
- A foreign process held 130.69 GiB on that 178 GiB GPU.
- No `step_335` checkpoint was kept. Replay 14B had not started.
- `results/multinode_eight_gpu_recovery02.json` records `planning_peak_memory_gib_per_rank` 73.18 and `memory_estimate_is_upper_bound: false`.

The historical device plan in `multinode_training.py` is `skampere1` GPUs 1–2 (A100-80GB), `skampere2` GPUs 3 and 5 (H200, cooperative share allowed), `skampere3` GPUs 2, 4, 5 and 7 (B200, exclusive at admission). Admission required `used_mib == 0` on the exclusive cards, so the foreign 130.69 GiB allocation appeared after admission, during a segment that does not checkpoint until step 335 (`checkpointing.save_period: 1000000` in the YAML). Two of the eight ranks sat on 80 GB A100s, where a 73.18 GiB non-upper-bound peak has under 7 GiB of margin.

What already matches the later memory fixes, and what does not:

| Knob | 14B YAML today | v28 Gemma smoke (11-26-2026) | This relaunch |
|---|---|---|---|
| Activation checkpointing | `dtensor_cfg.activation_checkpointing: true` | on | unchanged |
| Microbatch | `train_micro_batch_size: 1`, global batch 2 | microbatch 1, accumulation 2 | unchanged |
| CPU offload | `cpu_offload: false` | host AdamW for Gemma 4B | leave false; turning it on would move the locked full-parameter bf16 AdamW |
| Chunked lm-head | not used; NeMo tensor parallel 8 | `chunked_lm_loss`, vocab 262,144, one GPU, 16.82 GiB fp32 logits at 17,221 tokens | does not apply; see the byte check below |
| Allocator | unset | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | set this; the Gemma note records no numerical effect |

Byte check (CPU, `r1_14b_memory_budget_11-27-2026.py`): one fp32 logit tensor at Gemma's 17,221 × 262,144 is 16.82 GiB. Qwen3 vocabulary 151,936 at the locked 16,384-token cap is 9.27 GiB unsharded and 1.16 GiB per rank at tensor parallel 8. That is not what fills a 178 GiB card. The recorded cause is the foreign 130.69 GiB.

## Memory budget and flags

Run the gate in `r1_14b_memory_budget_11-27-2026.py` (`admit_node`) on a fresh `nvidia-smi` inventory. It admits only when all eight GPUs on one node pass.

| Host | Class | Admit when | Free-memory floor |
|---|---|---|---|
| skampere3 | 8× B200 | first choice; every GPU exclusive | `free_mib >= 163840` (160 GiB), `used_mib == 0`, utilization 0, no compute PID, `total_mib >= 170000` |
| skampere2 | 8× H200 | only if skampere3 fails the gate | `free_mib >= 122880` (120 GiB), same exclusive rule, `total_mib >= 130000` |
| skampere1 | 8× A100-80GB | refused | the 73.18 GiB peak is not an upper bound |

Do not reuse the cross-node `DEVICE_PLAN` and do not use skampere2's old cooperative-share rule (4,096 MiB used / 102,400 MiB free). A process that arrives after admission is what killed step 184.

Flags and non-changes:

- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
- Locked YAML stays byte-identical: bf16, global batch 2, microbatch 1, sequence cap 16,384, no packing, tensor parallel 8, activation checkpointing on, `cpu_offload: false`, AdamW `2e-5`, betas `(0.9, 0.98)`, eps `1e-5`, weight decay `0.1`, clip `1.0`, seed `20260830`.
- Watchdog: before each optimizer step, if any leased GPU has a compute PID outside the job, stop the step and keep the last durable checkpoint. Do not kill the foreign process.
- Do not set `checkpointing.save_period=20` unless the operator has checked that NeMo will not delete the scientific rung directory. The scientific checkpoints remain schedule steps only. A failed segment still restarts from `ckpt/14B/hf/step_658`, which is the same scientific restart as the 10-18-2026 resume. One rolling infrastructure copy is allowed only if the rung directory is preserved.

## The four rungs

Start weights: `ckpt/14B/hf/step_658`, hash-checked against the version-1 `weights_sha256_manifest` before the first update. The historical path is `/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/14B/hf/step_658`. Copy or read it from `/lfs`, not from DFS home.

Schedule steps, from `results/sft_schedule_v3_E.json` and `results/sft_schedule_v3_R.json`:

| Order | System | Train through step | Declared validation cells today |
|---|---|---:|---|
| 1 | `v3_E_14b_f0p5` | 335 (half of E; the dead segment) | 0/1,080 known, status `missing` |
| 2 | `v3_E_14b_f1p0` | 667 | 0/1,080 known, status `missing` |
| 3 | `v3_R_14b_f0p5` | 334 | 0/1,080 known, status `missing` |
| 4 | `v3_R_14b_f1p0` | 658 | 0/1,080 known, status `missing` |

One 14B job at a time. E then R. `train_continuation.sh` already walks `f0p5` then `f1p0` for one condition. After E's two exports, run R. Then generate each rung: 135 validation tasks × 8 attempts, thinking on, seed 91, stop `<|im_end|>`, 12,288-token cap, temperature 0.6, top-p 0.95, top-k 20, frozen scorer, non-vacuity screen, no DT. Formal-specification judging stays deferred at $0.

Work root: `/lfs/$(hostname)/0/$USER/rl4cv_e08_v3_r1_14b` via `work_root`. Set `E08_WORK` to that directory. The script's default `/lfs/skampere1/0/brando9/rl4cv_e08` is the old host path, not this job.

Exact command after `admit_node` returns `admitted: true` (it prints the argv; it does not exec):

```bash
export E08_WORK=/lfs/$(hostname -s)/0/$USER/rl4cv_e08_v3_r1_14b
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# condition E first, GPUs 0-7 on the admitted host; then the same with R
bash train_continuation.sh E 14b 0,1,2,3,4,5,6,7 production
```

`planned_command` in the memory-budget module returns that argv. Do not call `multinode_training.py`.

## Evidence to write, and files that stay untouched

Write new files beside the measured results. Suggested committed summaries, after the host run, under `expt_v3/results/r1_14b_11-27-2026/`:

- `inventory.json` — the three hosts, every GPU, compute PIDs.
- `admission.json` — the `admit_node` result and the chosen host.
- `agent_sync_claim.txt` — the claim id, written before launch.
- `E/segment_to_step_335.log`, `E/segment_to_step_667.log`, `R/segment_to_step_334.log`, `R/segment_to_step_658.log` — copies of the driver logs, including the peak memory line.
- `exports/<system>/SHA256SUMS` for `v3_E_14b_f0p5`, `v3_E_14b_f1p0`, `v3_R_14b_f0p5`, `v3_R_14b_f1p0`.
- `coverage/<system>.csv` — new 1,080-row tables. Do not overwrite `results/coverage/v3_*_14b_*.csv` (each is 1,080 rows, `known` 0, status `missing`).
- A new `validation_summary_r1_14b.json`. Do not edit `results/validation_summary_v3.json` until that new file exists and a dated note says how it was joined.

Leave untouched:

- `PROTOCOL.md` (locked 10-15-2026).
- Frozen forecast files and `results/forecast_assessment_v3.json`.
- The 12 measured rung tables (12,960 cells) and their coverage CSVs.
- The four missing-rung CSVs above, until a real generation is joined into the new directory.
- The test split.

VeriBench V1 validation denominator remains 17,280. Unmeasured 14B cells stay in that denominator. Do not impute zeros.

## What this environment did not do

No GPU inventory was taken here, no agent-sync claim was posted, and no training or generation process was started. The SNAP handoff is `docs/HANDOFF_ub9sc_11-27-2026.md`.

**TLDR-end:** [rl4cv: e08 v3 14B memory plan] Exclusive 8× B200 on skampere3, else exclusive 8× H200 on skampere2, 160 GiB or 120 GiB free, expandable segments, no A100 rank; four rungs E-335, E-667, R-334, R-658; new evidence beside the 12,960 measured cells.
