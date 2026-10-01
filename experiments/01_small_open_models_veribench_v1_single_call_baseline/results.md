# Experiment 01 results — small open-weight Qwen models on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md>

**TLDR:** The GPU run is in progress on `skampere1` (GPUs 2–7, one model per device): preflight passed, full G=1 eval and G=8 probe jobs launched 09-30-2026 12:31. D-101 (self-hosted inference) and D-102 (FSC judge route: `vb103_judge` Valkyrie, payer: Vals gateway) are both accepted. The judge's own controls (oracle/vacuous/blank/shuffled/halfdel) passed on a new, isolated Valkyrie benchmark service (port 9700; $4.57 spent of the $400 cap); FSC judging now runs per model once that model's kernel scoring finishes.

## Judge spend (running total against the $400 cap)

| Suite | Members | Cells | Status | Charges (USD) |
|---|---|---:|---|---:|
| `rl4cv-e01-controls` | H2_sol_high + H2_opus55_max | 60 × 2 | measured, verdict PASS | 4.57 |
| `rl4cv-e01:qwen3.5-4b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 117/120 measured (3 `unmeasured_infra` on H2_opus55_max) | 13.49 |

**Running total: $18.06 of $400.**

Last updated: 09-30-2026 17:41.

## Pipeline validation on CPU (09-30-2026, not the locked preflight)

Run in a 4-CPU cloud container with no GPU, using the transformers backend, the current v7 pack, thinking off and 3 tasks. Every stage ran: prompt construction from experiment 103's pinned code, generation, extraction, scorer jobs, the frozen scorer (`59059a20d`, Lean v4.22.0, Mathlib v4.22.0 from `lake exe cache get`), collection and summary. Evidence: [`expt_v1/results/pipeline_validation_cpu_09-30-2026.json`](expt_v1/results/pipeline_validation_cpu_09-30-2026.json).

| Cell | IC_tests | IC_proofs | Theorems proved | Verdict |
|---|---:|---:|---|---|
| Gold `easy_set__1_myadd` | 1.0 | 1.0 | 6 / 6 | control passes |
| Gold `cs_set__binary_search` | 1.0 | 1.0 | 13 / 13 | control passes |
| Empty file | 0.0 | 0.0 | — | control passes |
| Gold with one proof replaced by `sorry` | 1.0 | 0.667 | 4 / 6 (the `sorry` also reaches a `@[simp]` user) | control passes |
| Qwen3-0.6B on `easy_set__1_myadd`, `easy_set__10_myevensumparity`, `cs_set__binary_search` | 0.0 | 0.0 | 0 compile of 3 | measured on 3 cells only |

Qwen3-0.6B's answers (305, 1,047 and 754 generated tokens, all finished cleanly and extracted) are Lean-3-like pseudo-code (`module`, `definition … where`, `is_int(a)`, `<name>_prop`), matching the failure pattern experiment 103 found for Qwen3.6-27B. Generation ran at about 3 tokens per second on CPU, so the declared 896-task run needs the GPU hosts in [`scripts/cc_prompt_run_experiment_on_snap.md`](../../scripts/cc_prompt_run_experiment_on_snap.md).

## VeriBench V1, G = 1, experiment 103 single-call protocol

The denominator is always 896 declared cells per model. Unmeasured cells are listed, never counted as 0.

| Model | Revision | Measured / 896 | Cut off | No Lean | Compile rate | IC_tests | IC_proofs | FSC | SCSC |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | — | unmeasured | | | | | | | |
| Qwen3.5-2B | — | unmeasured | | | | | | | |
| Qwen3.5-4B | `851bf6e8` | 896/896 | 12 | 3 | 0.45% | 0.0011 | 0.0 | 0.328* | 0.0 (exact) |
| Qwen3.5-9B | — | unmeasured | | | | | | | |
| Qwen3-1.7B | — | unmeasured | | | | | | | |
| Qwen3-4B | — | unmeasured | | | | | | | |
| Qwen3-8B | — | unmeasured | | | | | | | |
| Qwen3-14B | — | unmeasured | | | | | | | |
| Qwen3.6-27B (local route control) | — | unmeasured | | | | | | | |
| *Reference: Qwen3.6-27B via Valkyrie (experiment 103)* | | *604* | *245 at cap* | | | *0.002* | *0.002* | *0.900* | *0.002* |

\* FSC here is the **ungated diagnostic mean over the 60-file core-split audit only** (n=57 measured; 3 `unmeasured_infra`), since Qwen3.5-4B has 0 cells with IC_tests · IC_proofs > 0 (no cells reach the gated `fsc_compiled` scope per D-003). It is never substituted for SCSC, which is exact at 0.0 here because IC_tests · IC_proofs = 0 for every cell. Per-task FSC values: `expt_v1/results/fsc_qwen3.5-4b.json`.

## Compute estimate (09-30-2026, skampere1, before launch)

- **Host/GPUs.** `skampere1`, 8× A100-SXM4-80GB. GPUs 0–2 belong to user `truongvo` (busy) and are never touched; GPUs 3–7 idle (0 MiB, 0%) at baseline. GPU rule (B200 → H200 first) not met: `skampere3` `/lfs` 100% full (21 GB free) and 7/8 GPUs busy; `skampere2` `/lfs` 100% full (99 GB free) and GPUs shared with 4 other users. Using `skampere1` instead.
- **G = 1 generation (9 models × 896 tasks).** From `PROTOCOL.md`: 1–3 GPU-hours/model up to 9B (7 models: Qwen3.5-0.8B/2B/4B/9B, Qwen3-1.7B/4B/8B → 7–21 GPU-hours), 3–8 GPU-hours for 14B and 27B (Qwen3-14B, Qwen3.6-27B-local → 6–16 GPU-hours). **Subtotal: 13–37 GPU-hours.**
- **G = 8 probe (8 models × 132 tasks × 8 samples, control excluded).** 1,056 generations/model at a 12,288-token cap (0.19× the eval cap) vs. 896 at 65,536. Estimated at ≈0.2–0.7 GPU-hours/model for the ≤9B/8B models and ≈0.7–1.8 GPU-hours for the 14B model. **Subtotal: ≈2–7 GPU-hours.**
- **Total generation: ≈15–44 GPU-hours.** Scoring: 1–5 CPU-hours per 896-file job × 9 eval jobs (9–45 CPU-hours) plus 64 probe scoring jobs (8 models × 8 samples) of 132 files each (≈10–50 CPU-hours combined), parallelizable across the host's 128 cores and independent of the GPU critical path.
- **Wall-clock.** One model per free GPU, in parallel across GPUs 3–7 (5 devices), smallest→largest: **≈4–12 hours** for all 9 eval + 8 probe jobs, dominated by the 14B/27B cells and by any cells that hit the token cap (experiment 103 saw 245/896 cells hit the 65,536 cap for Qwen3.6-27B).
- **Go.** Brando's "run my experiments on snap!" (09-30-2026) plus his earlier "just do the experiment ... Go" cover this GPU run (cc.md §5 "Ask"); posted to issue #3 before launch, launching without further wait per `DISPATCH_e01.md`.

## Signal probe, G = 8, 132 tasks

| Model | Channel | Mean reward | pass@8 | Mixed-group share | ρ | H | Gate G1 |
|---|---|---:|---:|---:|---:|---:|---|
| (all) | kernel_binary / proof_fraction | unmeasured | | | | | |
