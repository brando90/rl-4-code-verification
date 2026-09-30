# Experiment 01 results — small open-weight Qwen models on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md>

**TLDR:** The pipeline is validated on CPU (scorer controls 4 of 4 pass; Qwen3-0.6B compiled 0 of 3 tasks), but the locked measurement has not started: every value in the tables below is still unmeasured. D-101 (self-hosted inference) was approved on 09-30-2026; FSC still waits on D-102 (judge route and payer).

Last updated: 09-30-2026.

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
| Qwen3.5-4B | — | unmeasured | | | | | | | |
| Qwen3.5-9B | — | unmeasured | | | | | | | |
| Qwen3-1.7B | — | unmeasured | | | | | | | |
| Qwen3-4B | — | unmeasured | | | | | | | |
| Qwen3-8B | — | unmeasured | | | | | | | |
| Qwen3-14B | — | unmeasured | | | | | | | |
| Qwen3.6-27B (local route control) | — | unmeasured | | | | | | | |
| *Reference: Qwen3.6-27B via Valkyrie (experiment 103)* | | *604* | *245 at cap* | | | *0.002* | *0.002* | *0.900* | *0.002* |

## Signal probe, G = 8, 132 tasks

| Model | Channel | Mean reward | pass@8 | Mixed-group share | ρ | H | Gate G1 |
|---|---|---:|---:|---:|---:|---:|---|
| (all) | kernel_binary / proof_fraction | unmeasured | | | | | |
