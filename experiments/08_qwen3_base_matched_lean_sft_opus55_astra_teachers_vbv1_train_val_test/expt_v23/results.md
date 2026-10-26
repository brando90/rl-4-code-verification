# Fresh-base + repaired tiny proofs: 17/1080 (1.57%)

**Doc link:** [protocol](PROTOCOL.md)

**Status:** Training COMPLETE. Validation COMPLETE. Test split sealed. **Last updated:** 10-20-2026 10:26 PDT.

V23 retrains from official Qwen3-1.7B-Base with the V20-style explicit-comment cohort plus 500 repaired tiny proofs and 125 explicit Workbook examples (4,193 admitted rows, 3,097,879 assistant loss tokens). Final logged train loss 0.460, peak 43.57 GiB, seed 20261019. Checkpoint: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v23/base/run/hf`.

| Measurement | V23 | V20 | V12 current-corpus |
|---|---:|---:|---:|
| Binary successes | 17/1080 (1.57%) | 20/1080 (1.85%) | 120/1080 (11.11%) |
| 95% CI | [0.74%, 2.59%] | [0.83%, 3.06%] | [6.94%, 15.83%] |
| Mixed tasks (1–7/8) | 13 | 14 | 24 |
| Target 25% | no | no | no |
| Test sealed | yes | yes | yes |

Paired V20−V23 task bootstrap difference: −0.28 pp, 95% CI [−1.11%, +0.46%] (`analysis/v20_v23_comparison.json`). One seed each; cohort size and schedule differ, so this is descriptive, not a causal isolate of the repaired tiny set.

Frozen eval settings match V6/V20 (seed 91, T0.6, p0.95, k20, 12288 tokens, thinking on, `<|im_end|>`). Raw sha256 `65105968ff611438936880f9d4d9df8dd8b7207262b42e417e5e1dbb42efe7c0`.

**TLDR-end:** [rl4cv: V23 validation] Adding repaired tiny proofs to fresh-base SFT does not lift validation above ~1.6%; V12’s 11.11% current-corpus checkpoint remains the better RL start.
