# Matched automation-restored fresh-base: 17/1080 (1.57%)

**Doc link:** [protocol](PROTOCOL.md)

**Status:** Training COMPLETE. Validation COMPLETE. Test split sealed. **Last updated:** 10-20-2026 10:26 PDT.

V25 holds V20’s 3,568 example identities, prompts, row/batch order, original base revision, seed and actual learning-rate clock fixed, restoring automation-heavy named-proof counterparts with commentary (2,094 restored / 1,474 unchanged). Treatment assistant loss tokens 2,793,297 vs V20’s 2,948,296. Final logged train loss 0.031, peak 43.39 GiB. Checkpoint: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v25/base/run/hf`.

| Measurement | V25 | V20 | V12 current-corpus |
|---|---:|---:|---:|
| Binary successes | 17/1080 (1.57%) | 20/1080 (1.85%) | 120/1080 (11.11%) |
| 95% CI | [0.74%, 2.50%] | [0.83%, 3.06%] | [6.94%, 15.83%] |
| Mixed tasks (1–7/8) | 13 | 14 | 24 |
| Target 25% | no | no | no |
| Test sealed | yes | yes | yes |

Paired V25−V20 difference: −0.28 pp, 95% CI [−1.39%, +0.83%] (QA 11-25-2026: label was reversed; an independent recomputation, 10,000 task draws, seed 0, gives V25−V20 = −0.28 pp [−1.48, +0.83], so the −1.39 endpoint is not reproduced and no comparison script is committed) with exact learning rates verified (`analysis/v20_v25_comparison.json`). Restoring automation proofs on this matched fresh-base cohort does not recover V12-level validation success.

Frozen eval settings match V6/V20. Raw sha256 `bcfde18cc19e5bd8c203eb49496a0e59dde7851f27f1e05b4da711ae8a416543`.

**TLDR-end:** [rl4cv: V25 validation] Matched automation restoration on the fresh-base cohort stays at 17/1080; explicit-vs-automation on this start does not explain the gap to V12’s 11.11%.
