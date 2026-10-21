# Experiment 20 results: IRT ability-matched prompt selection for GRPO on Lean, strict vs smooth reward

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/results.md>

Experiment 20 (rl4cv, Azalia's test with IRT): does item-response-theory (IRT) prompt selection for GRPO raise held-out validation strict pass@1 over uniform, a pass-rate filter and DAPO at equal rollouts, crossed with strict versus smooth reward? Setup in progress on Sherlock with the Qwen3-1.7B Lean SFT start policy (experiment 08 v4 seed 20260831, validation strict pass@1 58/1080 = 5.37%); no experiment 20 numbers yet.

**Status:** RUNNING (Phase 0a generation submitted 10-21-2026 11:54 PDT: Sherlock array 48841018_[0-3]; PROTOCOL draft written before any outcome).

**Last updated:** 10-21-2026 11:54 PDT

## Findings so far

1. No measured result yet. The start policy's baseline is inherited from experiment 08 expt_v16 (Sherlock validation of the v4 checkpoints): seed 20260831 strict pass@1 58/1080 = 5.37% [3.15, 8.06], pass@8 24/135 = 17.8%; the two v4 seeds differ by 0.56 points of pass@1 (the seed spread the runbook cites).

**Next step:** finish Phase 0a (539 train tasks x 8 samples, frozen v12 sampler), score it with the pinned scorer under D-109 logging, then Phase 0b (IRT fit, gate G0).

## Phase table

| Phase | State | GPU-h used / cap |
|---|---|---|
| Setup and protocol draft | DONE (PROTOCOL.md draft; lock after the pilot) (10-21-2026 11:45 PDT) | 0 |
| Phase 0a calibration data (539 x 8, Sherlock) | RUNNING: array 48841018_[0-3] submitted 10-21-2026 11:54 PDT; train pack PASS (539 tasks, 135/135 validation prompt hashes reproduced) | 0 / 10 (Phase 0 total) |
| Phase 0b IRT fit and gate G0 | PENDING | CPU only |
| Trainer smoke test | PENDING | counted in pilot cap |
| Pilot (A, C, S x 1 seed x 16 updates) | PENDING | 0 / 15 |
| Main (6 arms x 2 seeds x 48 updates) | PENDING | 0 / 130 |
| Validation evaluation | PENDING | 0 / 80 |

API spend: $0 (open-weight models only; no provider or Vals keys).

**TLDR-end:** [rl4cv: expt20 IRT prompt selection for GRPO] Experiment 20 tests whether IRT-online prompt selection raises validation strict pass@1 for GRPO on Lean at matched rollouts; the worker has set up its checkout, branch and Sherlock access, and Phase 0a calibration generation is being submitted. No numbers yet.
