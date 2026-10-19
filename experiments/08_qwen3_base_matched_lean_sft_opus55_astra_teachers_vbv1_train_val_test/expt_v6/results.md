# Concise Lean curriculum: 1.7B / 4B training comparison

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/results.md

**Status:** RUNNING. **Last updated:** 10-19-2026 04:24:48 PDT.

| Condition | Training progress | Assistant tokens consumed | Validation generated | Scoring jobs complete |
|---|---:|---:|---:|---:|
| 1p7_control | 664/664 updates | 5,759,732 | 1080/1,080 | 1/8 |
| 1p7_mixed | 904/904 updates | 5,753,602 | 1080/1,080 | 8/8 |
| 4b_mixed | 443/904 updates | 2,560,539 | 0/1,080 | 0/8 |

4B CPU fused optimizer: **FUSED_TRAINING**; checkpoint target 100; restore verification PASS. [Runtime amendment](AMENDMENT_4b_fused_optimizer.md). The original supervisor's deliberate termination receipt is retained.

## Verified preparation

- Corrected tiny examples: 500/500. Each includes an anonymous executable `example`; original version 5 remains pristine.
- All 135 validation prompts match the prior frozen instruction/system/addendum/prompt hashes.
- Frozen-scorer positive, compile-error and sorry-proof controls passed. The 4B float32 CPU optimizer matched native AdamW in its numerical control.
- Both augmented conditions expose all 500 tiny examples once and 1,308 existing responses; control exposes 1,328 existing responses. Source pool contains 2,585 admitted existing responses.
- Target budget is 5,752,936 assistant loss tokens. Actual crossing totals: control 5,759,732; augmented 5,753,602. Planned updates: control 664; each augmented condition 904.
- 4B uses full-parameter training with float32 CPU master weights/Adam moments and bfloat16 GPU parameters. It has no new replay control.
- Test evaluation is not performed. Formal specification coverage is unmeasured; no judge-dependent aggregate is claimed.

Held-out validation improvement is not yet measured. Training loss is not a correctness result.

[Protocol](PROTOCOL.md) · [Checkpoint](CKPT_tiny_training.md) · [Runtime snapshot](results/runtime_snapshot.json)

**TLDR-end:** [rl4cv: concise Lean training] RUNNING; the full declared evaluation has 3,240 cells.
