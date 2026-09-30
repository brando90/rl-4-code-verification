# Experiment 01 results — small open-weight Qwen models on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md>

**TLDR:** Not started. Nothing has been measured yet, and every value below is unmeasured. D-101 (self-hosted inference) was approved on 09-30-2026; FSC still waits on D-102 (judge route and payer).

Last updated: 09-30-2026.

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
