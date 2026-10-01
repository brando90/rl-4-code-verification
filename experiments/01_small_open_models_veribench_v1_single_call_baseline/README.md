# Experiment 01 — small open-weight Qwen models on VeriBench V1, single call (baseline and signal probe)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md>

**TLDR:** This measures IC_tests, IC_proofs, FSC and SCSC for eight small open-weight Qwen models (Qwen3.5 0.8B–9B and Qwen3 1.7B–14B) on all 896 VeriBench V1 tasks, using experiment 103's single-call protocol, so the numbers sit beside experiment 103's table. An 8-sample probe on 132 tasks then shows whether VeriBench itself yields any group-relative learning signal at these scales. Nothing has been run yet.

## Goal, hypothesis and decision criterion

- **Uncertainty:** No model at or below 14B has ever been scored on VeriBench ([FACTS §1](../../docs/FACTS_veribench_baselines.md#1-small-open-weight-models-nothing-at-or-below-14b-has-been-measured)). The only small-open-model evidence is Qwen3.6-27B at SCSC 0.002, where 87.5% of the sampled zeros do not parse as Lean 4.
- **Hypothesis:**
  - IC_tests and IC_proofs are near 0 for every model at or below 14B.
  - FSC is high on the judge's raw scale even when nothing compiles.
  - The `kernel_binary` mixed-group share is below 0.05 on VeriBench tasks.
- **Decision criterion (gate G1 in [PLAN §6](../../docs/PLAN.md#6-experiments-and-gates)):**
  - If every model at or below 14B has a `kernel_binary` mixed-group share below 0.05, experiment 02 builds decomposed task families and a Lean warm start rather than training on VeriBench-style full-file tasks directly.
  - If any model reaches a share of 0.2 or more on some splits, those splits seed experiment 02's pools.
  - The per-model table is the deliverable whatever the outcome.

Locked thresholds and parameters: [PROTOCOL.md](PROTOCOL.md). Live status: [results.md](results.md).

## Structure

```
01_small_open_models_veribench_v1_single_call_baseline/
├── README.md        ← this design doc
├── PROTOCOL.md      ← locked before any GPU or judge spend
├── results.md       ← live results and status
└── expt_v1/
    ├── cc.md        ← agent prompt to run the experiment on a GPU host
    ├── models.yaml  ← declared models, sampling and probe settings
    ├── run_model.sh ← one model: generate → materialize → kernel-score → collect → summarize (→ ρ/H)
    └── results/     ← summaries committed here; raw generations stay on the host
```

## Method

1. **Pin.** Fetch the external pins (`make external`). Verify the frozen scorer's file hashes and experiment 103's prompt hashes (addendum `a7a0fc1b…`, system prompt `dc051963…`).
2. **Freeze the tasks.** Use experiment 103's gated v6 pack and its 896-id list (SHA-256 `5d4e64e4…`). Resolve every model's Hugging Face revision and record it before generation.
3. **Preflight.** On 5 tasks, run one small model end to end with scorer controls:
   - a gold file must score IC_tests = IC_proofs = 1;
   - an empty file must score 0;
   - a `sorry` proof must score IC_proofs 0.

   Then check that the delivered prompt hashes match.
4. **Evaluate.** G = 1 on all 896 tasks per model, with experiment 103's Qwen settings: temperature 1.0, top-p 0.95, top-k 20, a 65,536-token cap, thinking on.
5. **Probe.** G = 8 on the 132-task stratified subset (4 per split, outcome-blind hash order), with the paper's RL decoding: temperature 0.6, top-p 0.95, top-k 20, a 12,288-token cap.
6. **Score.** Kernel-score every cell with the frozen scorer (`--skip-tc`).
   - SCSC is exact without a judge wherever IC_tests · IC_proofs = 0.
   - FSC comes from `vb103_judge`, once decision D-102 is settled, for every cell with IC_tests · IC_proofs > 0, plus a 60-file stratified audit per model that includes non-compiling files.
7. **Publish.**
   - Per-model table: IC_tests, IC_proofs, FSC, SCSC and n, with core 614 and IndustrySet 282 reported separately, cut-off and unextracted counts, and mean generated tokens.
   - Probe table: mean reward, pass@8, mixed-group share, ρ and H per split, for `kernel_binary` and `proof_fraction`.
8. **Control.** Rerun Qwen3.6-27B locally to compare with experiment 103's Valkyrie row. Report any gap as a route difference rather than hiding it.

## Dependencies

- **Code and pins:** VeriBench at the commits pinned in [`external/deps.lock.json`](../../external/deps.lock.json), the `rl4cv` package, and vLLM on the GPU host.
- **Host resources:** experiment 103's gated pack and grading Lean project on SNAP (`skampere1`, per experiment 103's deployment record); re-verify both on the chosen host.
- **Decisions:**
  - D-101: self-hosted inference authorization.
  - D-102: judge route and payer, for FSC only.

## Status

| Step | Status | Notes |
|---|---|---|
| Design and protocol | Done (09-30-2026) | this folder |
| D-101 self-hosted inference | Done (09-30-2026) | approved by Brando; model substitution allowed |
| Preflight (5 tasks, controls) | Done (09-30-2026) | expt_v1/cc.md step 3 |
| G = 1 evaluation, 9 models (8 + 27B control) | Done (10-01-2026 06:45) | all 896/896 cells generated and kernel-scored for every model |
| G = 8 probe, 8 models | Done (09-30-2026) | all 1024/1024 cells generated and scored for every probe model |
| FSC judging | Done (10-01-2026 09:08) | route: `vb103_judge` Valkyrie, payer: Vals gateway; all 9 suites (controls + 8 models) admitted and harvested, $102.55 of $400 spent |
| Results table and gate G1 decision | Done (09-30-2026 19:20 for Gate G1; 10-01-2026 09:08 for the full table) | results.md; Gate G1 **PASS** |

**Experiment complete as of 10-01-2026 09:08** (`STATUS_e01 = DONE`; see `CKPT_e01.md`). Per the index table in `experiments/README.md`, this folder is slated to be renamed `01_small_qwen_vbv1_single_call_baseline_g8_signal_probe` after the run — **not yet done**, since it touches every cross-reference and doc link in this folder; left for Brando or the next agent to execute deliberately rather than as an unprompted structural change here.
