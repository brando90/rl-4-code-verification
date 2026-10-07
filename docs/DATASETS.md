# Candidate environment pools and held-out panels

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/DATASETS.md>

**TLDR:** This lists where RL prompts and held-out panels can come from. VeriBench V1 is split into train / validation / test (D-013): only its train split may be trained on, its validation split selects checkpoints, and its test split is held out. The training pools come from other sources: FVAPPS (the largest public Lean spec set that comes with Python programs), the Vericoding Lean subset, and synthetic VeriBench-style tasks. Every pool must pass license checks and contamination screens before it is used.

Environment families refer to the plan's families (see [PLAN.md §4](PLAN.md#4-environment-families-and-reward-channels)).
Sizes are as reported by the sources on 2026-09-30.
Every row marked "verify" has to be checked before use; nothing here has been downloaded yet.

| Pool | What a task gives the policy | Size | Reward channels it supports | Reference specs for FSC | Role | Status |
|---|---|---|---|---|---|---|
| [FVAPPS](https://huggingface.co/datasets/quinn-dougherty/fvapps) ([paper](https://arxiv.org/abs/2502.05714)) | An APPS programming problem plus Lean 4 theorem statements with `sorry`. The APPS Python solutions give the VeriBench-style Python input. | 4,715 samples (1,083 curated) | kernel_binary, proof_fraction, fsc_compiled, scsc | Yes, the FVAPPS theorem statements. They are LLM-written, so prefer the curated 1,083 or re-validate. | Main within-source pool for the full-file family; source of the within-source held-out panel | verify license, schema and Python-solution availability |
| [Vericoding benchmark](https://github.com/Beneficial-AI-Foundation/vericoding-benchmark) ([paper](https://arxiv.org/abs/2509.22908)) | A formal specification; the policy writes a verified implementation | 7,141 Lean specifications (of 12,504 across Lean, Dafny and Verus) | kernel_binary | Not needed (the specification is given) | Proof/implementation family | verify license and Lean version compatibility (VeriBench pins Lean v4.22.0) |
| Synthetic VeriBench-style tasks | New Python programs in VeriBench's splits, with reference Lean written by a frontier agent and kept only if it compiles, every theorem is kernel-proved and it passes a non-vacuity check | as many as funded | all channels | Yes, "silver" references | Closest match to the target; also warm-start supervised fine-tuning (SFT) data | needs a generation route and budget (decision D-104) |
| [VERINA](https://huggingface.co/datasets/sunblaze-ucb/verina) ([paper](https://arxiv.org/abs/2505.23135)) | A natural-language problem; the reference has a Lean implementation, specification and optional proof | 189 | kernel_binary, spec checks | Yes (gold) | Cross-source held-out panel only | verify license |
| [CLEVER](https://arxiv.org/abs/2505.13938) | Specification-first verified code generation | 161 | — | — | **Do not use.** It is derived from HumanEval, which overlaps VeriBench's `humaneval_set`. | excluded |
| [FVSpec](https://arxiv.org/abs/2606.01008) | Real-world property-based tests turned into Lean challenges | verify | kernel_binary | verify | Candidate specification family | verify |
| Paper's OpenR1-Math cells | Math problems | 4 cells × 256 per scale | Math-Verify binary | n/a | The "far" family: does math RL move Lean utility? | available from the paper's archive (decision D-105) |
| **VeriBench V1** | Python program to a full Lean file | 896 = core 614 + IndustrySet 282 | official factors | gold | **D-013 split: train 539 (training pool, experiment 08), validation 135 (selection), test 222 (held-out panel, never trained on).** Experiments locked before D-013 hold out all 896. | pinned in `external/deps.lock.json`; split manifest in `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/` |
| VeriBench V2 / V2.1 | Multi-file tasks from VeriSoftBench | small (pilot sets) | official factors | gold | Out-of-distribution panel where FSC has headroom | only if VSB-derived data stay out of training |

## Contamination and integrity screens (required before any pool is used)

1. **Exact overlap.** Compare normalized hashes of the Python source and of any Lean text against VeriBench's `veribench_dataset/py_src` and `lean_src` (at the pinned commit). Any overlap is removed.
2. **Near-duplicates.** Use the paper's word-5-gram Jaccard screen (flag ≥ 0.7) against VeriBench Python and against every held-out panel. Report flagged counts, and report the held-out result with and without flagged items, as the paper's Appendix A does.
3. **Excluded sources.** Nothing derived from HumanEval (because of VeriBench `humaneval_set`). Nothing derived from VeriSoftBench if VBV2 is used as a panel.
4. **Reference quality.** Reference specifications used for FSC rewards must compile and must pass a non-vacuity check (no theorem whose conclusion is only `True` or a self-equality), matching VeriBench's `tests/test_reference_specs_nonvacuous.py`.
5. **No gold in rollouts.** The rollout sandbox never contains a reference, the scorer or the judge prompt. Scoring runs outside, after generation.
