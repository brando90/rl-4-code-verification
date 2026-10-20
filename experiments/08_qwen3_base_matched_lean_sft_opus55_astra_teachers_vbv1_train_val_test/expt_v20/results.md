# Fresh-base 1.7B validation finished: 20/1080 (1.85%)

**Doc link:** [protocol](PROTOCOL.md)

**Status:** Training COMPLETE. Validation COMPLETE (eth127 recovery3). Test split sealed. **Last updated:** 10-20-2026 10:20 PDT.

The fresh Qwen3-1.7B-Base run in `expt_v20` finished its one declared training pass and the full frozen 1,080-cell validation. It did not reuse a previous fine-tune or optimizer. Formal specification coverage was not measured. This setup changes both initialization and the admitted dataset relative to V12, so the gap does not identify which component caused the drop.

| Measurement | V20 fresh-base | V12 current-corpus (reference) |
|---|---:|---:|
| Binary successes | 20/1080 (1.85%) | 120/1080 (11.11%) |
| 95% CI (task bootstrap) | [0.83%, 3.06%] | [6.94%, 15.83%] |
| pass@8 tasks | 14/135 | 28/135 |
| Mixed tasks (1–7/8) | 14 | 24 |
| Target band (2–6/8) | 3 | 16 |
| Extracted / compiles / capped | 950 / 20 / 131 | 971 / 120 / 110 |
| Mean generated tokens | 4,266 | 4,760 |
| Target 25% reached | no | no |
| Test split opened | no | no |

Training receipt (unchanged): 1,784/1,784 updates, 3,568 admitted rows, 2,948,296 assistant loss tokens, final logged loss 0.476, peak 43.79 GiB, physical GPU 0, seed 20261019. Checkpoint: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/run/hf`.

Validation used the frozen V6 adapter settings: seed 91 (per-cell `91*100003+k`), temperature 0.6, top-p 0.95, top-k 20, 12,288 new tokens, thinking on, `<|im_end|>` stop, backend vLLM. Verified 1,080 unique cells; raw sha256 `f81b3e5ea5e70c6c262a0c914d82c7e7aec4b83964c25eb9190ba16693130955`. Owner path: eth127 `v20_base_recovery3` under `corpus_training_v20/validation/v20_base/`. A parallel brando9 recovery waiter died on CUDA 12.4 FlashInfer JIT (`nvcc fatal: Unknown option --compress-mode`); that path wrote zero cells and is superseded by the eth127 receipt.

Failure inventory (lexical, not causal): 929 extracted non-compiling uncapped cells; 130 empty extractions; `native_decide` present in 940/940 nonempty closed sources (also common on successful V12 files when used in anonymous tests). No `sorry`/`admit`/`axiom` markers in the inventory.

**Implication for RL starts:** V20 is far below V12 on the same frozen validation panel, and the confidence intervals do not overlap. Prefer the V12 current-corpus 11.11% checkpoint (already shown to carry usable ρ/H signal) as the RL warm-start candidate. Do not claim RL improvement from V20. A better next SFT for RL should beat V12’s validation success and mixed-task count, not restart from this fresh-base score.

**TLDR-end:** [rl4cv: V20 validation] Fresh-base SFT scored 20/1080 (1.85%) on sealed VeriBench V1 validation versus V12’s 120/1080 (11.11%); V12 remains the better RL start.
