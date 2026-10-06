# Experiment 02A — Lean environment pools, Lean warm start, and ρ–H probes (the Lean analogue of paper Table 5)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/README.md>

**Part of:** [experiment 02](../README.md) (ρ–H-guided Lean environment design), phase A; numbered experiment 02 before D-007

**TLDR:** This builds contamination-screened Lean task pools and a 1,000-task within-source held-out panel. It also gives Qwen3 Base 1.7B, 4B, 8B and 14B an identical Lean warm start, then runs the paper's four-stage policy-relative probe to build 2×2 cells. The measured ρ, H, success, mixedness and admission per scale, family and reward channel are the Lean version of the paper's Table 5.

## Goal, hypothesis and decision criterion

- **Uncertainty.** Experiment 02B can only test the law if Lean environments carry measurable, varied usable signal at every scale. That needs mixed groups (success strictly between 0 and G) and an admission contrast.
- **Hypothesis.** With a Lean warm start, the `full` or `impl` family yields four disjoint 256-prompt cells at each scale, with:
  - matched starting success (fresh-confirmation spread ≤ 3 points);
  - an admission contrast ≥ 15 points;
  - ρ > 0 in every cell.
- **Decision:**
  - **Pass (gate G2):** at least one family passes at all four scales. Experiment 02B uses it.
  - **Fail:** report which stage failed (too few mixed prompts, no admission contrast, unbalanced success) and propose a changed pool, decomposition or warm start as experiment 02A v2.

## Structure

```
phase_a_lean_env_pools_warm_start_rho_h_probes/
├── README.md
├── PROTOCOL.md      ← written and locked before the first probe (template: experiment 01)
├── results.md
└── expt_v1/
    ├── cc.md        ← agent prompt
    └── results/
```

## Method

1. **Pools** ([DATASETS.md](../../../docs/DATASETS.md)):
   - Acquire FVAPPS (curated subset first), the Vericoding Lean subset and VERINA at pinned revisions, and record their licenses.
   - Convert each FVAPPS item to a VeriBench-style task. The instruction is VeriBench's current agent-spec prove-first template plus the Python solution; the reference is the FVAPPS theorem statements, used for FSC.
   - Keep a reference only if it compiles and passes the non-vacuity check.
2. **Screens.** Run `rl4cv.screens` against VeriBench `py_src` and `lean_src` (pinned) and against every held-out panel. Remove exact hits; record near hits (≥ 0.7).
3. **Held-out panel first.** Draw a 1,000-task within-source panel by outcome-blind hash order. Freeze and hash it before any probe.
4. **Warm start.**
   - **Data.** A Lean supervised fine-tuning (SFT) set built from pool tasks (never panel tasks): teacher answers kept only if the kernel accepts every theorem and the non-vacuity check passes. The teacher route and budget are decision D-104.
   - **Recipe.** The paper's recipe at every scale: response-only full-parameter SFT, AdamW 2×10⁻⁵, weight decay 0.1, clipping 1.0, 3% warmup with cosine decay, step-512 checkpoint gated on format, coverage, truncation, repetition and diversity. Mix in the paper's 1,024 math and 1,024 code examples, so the warm start differs from the paper's only by the added Lean data.
5. **Probes per scale** (paper Appendix A, implemented in `rl4cv.cells`):
   - **Stage A:** 4,000 pool prompts × G = 8, then band assignment with hash caps of 640 per band.
   - **Stages B and C:** two more independent G = 8 probes of the candidates.
   - **Selection:** balanced disjoint cells of 256 prompts (`select_balanced_cells`).
   - **Stage D:** a fresh confirmation probe (`stage_d_confirmation`: success spread ≤ 3 points, pairwise standardized difference ≤ 0.10, admission contrast ≥ 15 points).
6. **Measure.** For each scale, cell and reward channel, compute ρ, H, q_mixed, admission, mean length, survival and top-decile share on the Stage D probe (`rl4cv.probe`). Judge-gated channels need FSC for compiling responses only (D-102).
7. **Record.** `results.md` gets the Table 5 analogue, the number of prompts surviving each stage, and the probe token cost (paper: the 14B Stage D probe equalled 30% of the RL tokens).

## Dependencies

- Experiment 01's gate G1 verdict and its measured response lengths (to set the cap).
- Decisions D-101 (self-hosted inference), D-102 (judge, for FSC channels), D-103 (GPUs), D-104 (pool and teacher) and D-105 (the paper's code and configs).

## Current execution status

The [bounded version-2 source preparation](expt_v2/results.md), published 10-06-2026, screened external candidates and froze outcome-blind partitions of 141 train, 24 validation and 24 test tasks. They remain candidate-only. The external endpoint study in `04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2` found 0/24 supported generic adapters versus its fixed 20/24 engineering gate, despite 24/24 matching authored checker controls. No candidate has entered warm-start training, probes, repair, judge scoring or checkpoint selection. Its [draft adapter plan](../../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v4/README.md) is the next engineering dependency, with zero new model calls admitted.

The table below retains the larger phase design; completing candidate preparation does not complete its warm starts or policy-relative probes.

| Step | Status |
|---|---|
| Design | Done (09-30-2026) |
| Protocols | Version-2 bounded preflight protocol exists; larger phase protocol remains pending its gates |
| Pools, screens, panel | Version-2 source screening and candidate partitions published; accepted training references remain blocked |
| Warm start ×4 scales | TODO |
| Probes and cells ×4 scales | TODO |
