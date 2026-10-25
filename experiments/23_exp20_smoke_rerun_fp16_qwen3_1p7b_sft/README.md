# Experiment 23: Exp 20 trainer smoke rerun with vLLM and trainer both in fp16 (Qwen3-1.7B SFT)

Status: finished 2026-10-25 (ultimate_brando9 for Brando, free snap GPUs). Diagnostic smoke; touches no frozen gate (Exp 20's gate stays: <=1% of completion tokens with |logp_trainer - logp_vLLM| > 0.05 or outside the recomputed sampling support). Follows Experiment 22 (branch ub9/e22-mismatch-fix).

## Question
Exp 22 showed fp16 on both sides cuts the rollout-vs-scoring mismatch to 0.11% at fixed weights. Does Exp 20's own trainer loop, with vLLM and the trainer both in fp16 (fp32 master weights kept), pass the smoke gate over two real optimizer updates, and do the fp16 training steps stay finite?

## Setup
- Code: Exp 20's own trainer `train_e20.py` (repo commit 2f81381d on skampere1; TRL 1.16.0 `VLLMGeneration` colocated, arm A, seed 0, 2 updates of 16 groups x 8 = 128 rollouts, thinking on, T=0.6, top-p 0.95, top-k 20, max 12288 new tokens, `--smoke`). Unchanged from the Exp 20 run except the patch in `code/train_e20.patch`: `--dtype` (model weights dtype), `--loss-scale`, `--reward-proxy`, per-sequence non-finite skip, and grad/param finiteness stats.
- Start policy: the Exp 20 start checkpoint (Qwen3-1.7B SFT, rl4cv_e08 step_658; config.json torch_dtype bfloat16). fp16 lane: same weights, config.json copied with torch_dtype float16 so vLLM loads fp16 (TRL's helper passes no dtype); the trainer model is loaded with dtype float16. The bf16 lane is the unmodified Exp 20 configuration on the same harness.
- Precision: fp16 lane: vLLM fp16, trainer forward/backward fp16, fp32 CPU master weights and fp32 AdamW state (lr 1e-6, grad clip 1.0, as Exp 20), loss scale 16384 static (loss is token-normalized over about 0.86M tokens, so raw gradients are tiny), gradients unscaled and accumulated in fp32, a sequence with a non-finite loss or gradient is skipped and counted (none occurred), the optimizer step is skipped if the accumulated norm is non-finite (did not occur). Mismatch check: `lm_head` logits computed in the trainer dtype, then fp32 log-softmax on the truncated support (unchanged).
- Hardware/software: skampere1, two NVIDIA A100-SXM4-80GB (GPUs 3 fp16, 5 bf16, both empty at start, 0 MiB at the end), vLLM 0.30.0, torch 2.13.0+cu130, transformers 5.17.0 (Exp 20: image with transformers 5.17.0), trl 1.16.0, scipy 1.18.1, python 3.12.14; `results/pip_freeze.txt`. Exp 20's smoke ran on Sherlock L40S/H100 in the Apptainer image.
- **Deviation (reward):** the Sherlock Lean grader and train pack could not be reached (Stanford sign-in expired). Rewards are a stand-in: 1 if the extracted Lean file contains a theorem or lemma and no `sorry`, else 0. Prompts are the real 539-task train pack (exp103 prompt builder, from rl4cv_e08/pack_train539). The mismatch and finiteness measurements do not depend on reward values, but which groups get nonzero advantage (hence which sequences are back-propagated) does: 80/96 (fp16) and 88/88 (bf16) sequences were back-propagated per update. This tests numerics, not learning.
- Seed 0 in both lanes (same rollout seeds); the two lanes' generations differ because the dtype differs.

## Results (gate = 1%; share = (tokens with |delta| > 0.05, in support, + sampled tokens outside the truncated support) / all generated tokens)

| lane | update | tokens | outside support | abs delta > 0.05 | share mismatched | mean abs delta | max abs delta | gate |
|---|---|---|---|---|---|---|---|---|
| fp16 / fp16 | 1 | 857,536 | 18 | 538 | **0.0648%** | 0.00053 | 0.230 | pass |
| fp16 / fp16 | 2 | 882,468 | 13 | 490 | **0.0570%** | 0.00051 | 0.298 | pass |
| bf16 / bf16 (Exp 20 config, baseline) | 1 | 878,541 | 191 | 21,085 | 2.4217% | 0.00405 | 1.130 | fail |
| bf16 / bf16 (baseline) | 2 | 861,170 | 180 | 20,638 | 2.4174% | 0.00402 | 1.588 | fail |

Gate value (max over updates): fp16 0.0648% (pass, 15x under the gate); bf16 baseline 2.4217% (fail; Exp 20's recorded 2.6198% on Sherlock). Full-softmax diagnostic share (not the gate): fp16 1.03%, 1.06%; bf16 2.82%, 2.83%. Note the full-softmax variant for fp16 is just above 1%, because it counts tokens outside the sampling support that were never sampled-from; the Exp 20 gate uses the truncated support.

## Finiteness of fp16 training

| update | sequences back-propagated | non-finite sequences | non-finite params after step | grad norm (clip 1.0) | max scaled grad (fp16 max 65504) | IS ratio min / max / mean | loss |
|---|---|---|---|---|---|---|---|
| 1 | 80 | 0 | 0 | 0.1075 | 50.3 | 0.677 / 1.098 / 0.9976 | 0.238 |
| 2 | 96 | 0 | 0 | 0.1145 | 34.4 | 0.687 / 1.177 / 0.9974 | 0.377 |

- No overflow, no NaN/inf in loss, gradients or weights; loss scale 16384 left more than 1000x headroom to the fp16 maximum (scaled max grad 50). The smallest nonzero scaled gradient is 6e-8 = fp16's smallest subnormal, so a few of the tiniest gradient entries are at the underflow floor; the scale could be raised about 100x if underflow of those entries mattered. Not tested here.
- bf16 baseline importance ratios range 0.0002-2.0 (clipped at the cap 2); fp16 ratios stay within 0.68-1.18, so the importance correction is near-inert in fp16.
- Wall time per update about 13 min in both lanes (generation about 10 min, train step about 3.3 min): fp16 costs no measurable time.

## Caveats
Two updates, one seed, one start checkpoint, A100 not L40S/H100, stand-in reward (no Lean compile), 12288-token rollouts as in Exp 20. At lr 1e-6 the cast fp16 weights change little in two updates (the fp32 master weights accumulate; half-precision weights move only when the accumulated change crosses their rounding step, in bf16 even more rarely), so the gate value after dozens of updates, as weights drift and loss scaling is exercised on harder batches, is untested. Exp 13 (NeMo RL backend) was not run. No gate was changed; Exp 20 itself was not resumed.

## Options (Brando decides)
(a) run Exp 20's pilot with the trainer and vLLM both in fp16 and this loss scale, keeping the smoke gate as written (this smoke passes); (b) first extend this smoke to 8 updates with the real Lean reward on Sherlock/snap CPUs to see whether drift reopens the mismatch; (c) fp32 vLLM as fallback if fp16 overflows later (Exp 22: fp32 rollouts + fp16 scoring 0.083%).

## Reproduce
`setup.sh` (venv), then `lane.sh <gpu> fp16 16384 <port>` and `lane.sh <gpu> bf16 1 <port>` in /lfs/skampere1/0/brando9/rl4cv_e23_fp16_smoke (full run dirs, about 23 GB each, kept there; small outputs in `results/`).
