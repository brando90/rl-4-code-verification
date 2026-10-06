# Experiment 05 results — Qwen3 Base 1.7B/4B/8B on VeriBench V1 at G=8

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md>

**TLDR:** Live ledger for the Qwen3 Base G=8 signal check that decides whether RL on Lean code verification needs an SFT warm start. Nothing has been measured yet; the table below fills in as each model's generation and kernel scoring land.

**Status:** PLANNED (protocol locked 10-05-2026; launch on `skampere1` follows the preflight)

**Last updated:** 10-05-2026 18:30

## Phases

| Phase | Status | Evidence |
|---|---|---|
| Preflight: 5 tasks × 2 samples, Qwen3-1.7B-Base | PENDING | `expt_v1/results/preflight_qwen3-1.7b-base.json` |
| Generation, 896 × 8 per model (1.7B, 4B, 8B) | PENDING | per-model shard logs under `/lfs/skampere1/0/brando9/rl4cv_e05/logs/` |
| Kernel scoring, 24 jobs of 896 files | PENDING | `expt_v1/results/summary_<label>_g8.json` |
| Analysis and verdicts | PENDING | `expt_v1/results/analysis_e05.json`, `analysis_e05_table.md`, `per_task_<label>_g8.csv` |

## Compute estimate (10-05-2026, before launch)

- **Host.** `skampere1`, 8× A100-SXM4-80GB. At 17:41, GPUs 0–3 and 5–7 were idle (0 MiB) and GPU 4 held another user's job (36.7 GB, 89%), which is never touched. `skampere2` (`/lfs` 46 GB free, 7 of 8 GPUs in use) and `skampere3` (`/lfs` 99% full, all 8 B200s holding memory) were not usable. The CPU load average was about 3,000 on 128 cores (another user's jobs); the kernel's per-session CPU scheduling (`sched_autogroup_enabled = 1`) shares the CPU across sessions, and one gold-file Lean compile took 1.5 s.
- **GPU plan.** Qwen3-1.7B-Base on GPU 0; Qwen3-4B-Base on GPUs 1–2; Qwen3-8B-Base on GPUs 3, 5, 6 (one vLLM process per GPU, tasks sharded by line index). GPU 7 stays free; it hosts the preflight.
- **Memory.** bf16 weights about 3.4 GB (1.7B), 8 GB (4B) and 16.4 GB (8B); vLLM reserves 88% of each 80 GB GPU for weights plus KV cache. Decode is compute- and memory-bandwidth-bound.
- **Generation.** 7,168 cells per model, up to 12,288 output tokens each. Experiment 01's post-trained Qwen3 probe averaged 5,700–6,500 tokens per cell at about 1,400–1,900 tokens/s per GPU with 64 prompts in flight; this run submits 1,024 at a time. Estimate 1–4 h wall-clock, 6–20 GPU-hours in total.
- **Scoring.** 24 jobs × 896 files; about 2 h per job at experiment 01's 8 files per minute, 4 concurrent scorers per model (12 in total), overlapping generation: about 4 h, about 45 CPU-hours.
- **Total:** about 5–9 h. No judge and no API spend.
- **Go.** Brando, 10-05-2026: "evaluate the qwen models we discussed ... 1.7b 4.b 8b on vbv1 ... Go!", plus the standing SNAP pre-approval (agents-config Trigger Rule 51).

## Results

Pending. The headline table (`kernel_binary` mixed-group share with 95% Wilson interval and one-sided exact binomial p-value against 0.05, pass@8 share, all-pass share, mean pass rate with 95% task-bootstrap interval, `ic_tests` mixed share, verdict) is written here from `expt_v1/results/analysis_e05_table.md` as each model lands. Every row keeps its full denominator (896 tasks × 8 samples); unmeasured cells are listed, never counted as zero.

## Deviations and open questions

None yet.

**TLDR-end:** [rl4cv: 05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk] Qwen3 Base 1.7B/4B/8B G=8 VeriBench V1 signal check to decide whether RL needs an SFT warm start; planned and locked, not yet measured.
