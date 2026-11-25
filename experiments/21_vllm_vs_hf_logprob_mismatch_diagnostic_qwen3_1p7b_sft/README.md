# Experiment 21: vLLM-vs-trainer log-prob mismatch diagnostic (Qwen3-1.7B SFT)

Status: finished 2026-10-25 (run by ultimate_brando9 for Brando on free snap GPUs). Diagnostic only; touches no frozen gate.

## Why
Experiment 20 (smoke: 2.62% mismatched tokens vs a <=1% gate, STOPPED) and Experiment 13 v4 T1 (STOP_A4_CAP) both stop on the rollout-vs-trainer log-prob mismatch, and the saved receipts kept no quantiles or slices. This run measures where the mismatch comes from.

## Setup (all logged; code in code/, raw numbers in results/)
- Model: rl4cv_e08 SFT checkpoint, Qwen3-1.7B, ckpt/1.7B/hf/step_658.
- Prompts: 64 task prompts x 4 samples = 256 rollouts, max 3072 new tokens, T=0.6, top-p 0.95, top-k 20.
- Generation: vLLM 0.30.0, torch 2.13.0+cu129, transformers 5.20.2 (HF scorer), one seed, one generation per cell.
- Hardware: mercury1 GPUs 8 and 9, NVIDIA RTX A4000 16 GB (not the staged A100; mismatch levels are A4000 numbers).
- Generations: (a) bf16 vLLM, processed logprobs (post temperature/top-k/top-p); (b) fp32 vLLM, processed logprobs; (c) bf16 vLLM, raw logprobs (VLLM_USE_FLASHINFER_SAMPLER=0, its JIT build failed on this node).
- Re-scoring: teacher-forced HF forward on the same token ids, applying the same T/top-k/top-p. Variants: bf16, bf16 with lm_head in fp32 (computed as hidden.float() @ W.float().T), full fp32 (SDPA mem-efficient, GQA expansion forced, math backend off).
- Mismatch metric: a token counts as mismatched if |vLLM logprob - HF logprob| > 0.05 or the sampled token falls outside the HF top-k/top-p support ("unsupported"). Denominator: all generated tokens (~776k-786k per cell). "full" columns score against the untruncated tempered softmax instead.

## Results
Mismatched = |vLLM logprob - HF logprob| > 0.05 or sampled token outside the HF top-k/top-p support. Denominator = all generated tokens. Medians of 0 mean most tokens match to float precision.

**Comparable reference per generator** (processed-logprob generations are compared with the truncated/renormalised T=0.6, top-k 20, top-p 0.95 distribution; the raw-logprob generation is compared with the full T=1 softmax, which is what vLLM's raw logprobs are). One table, one row per generator/scorer pairing:

| vLLM generation | HF scorer | reference used | tokens | share mismatched | unsupported | median abs | p99 abs |
|---|---|---|---|---|---|---|---|
| bf16, processed | bf16 | truncated T=0.6 | 775,985 | 6.42% | 463 | 0 | 0.255 |
| bf16, processed | bf16, lm_head fp32 | truncated T=0.6 | 775,985 | 8.29% | 448 | 0 | 0.188 |
| bf16, processed | fp32 | truncated T=0.6 | 775,985 | 7.98% | 423 | 0 | 0.179 |
| fp32, processed | bf16 | truncated T=0.6 | 786,413 | 8.14% | 352 | 0 | 0.189 |
| fp32, processed | fp32 | truncated T=0.6 | 786,413 | 0.0092% (about 0.01%) | 22 | 0 | 0.0078 |
| bf16, raw logprobs | bf16 | full softmax T=1 | 781,096 | 5.89% | 0 | 1.35e-05 | 0.151 |

**Full-softmax variants** (the same processed generations scored against the untruncated T=0.6 softmax). These are not like-for-like: vLLM's processed logprob is renormalised over the top-k/top-p set, so a gap appears by construction even with no numerical error. Shown for completeness:

| vLLM generation | HF scorer | share mismatched (full softmax, T=0.6) | median abs | p99 abs |
|---|---|---|---|---|
| bf16, processed | bf16 | 8.51% | 1.4e-06 | 0.271 |
| bf16, processed | bf16, lm_head fp32 | 10.25% | 1.6e-06 | 0.210 |
| bf16, processed | fp32 | 9.94% | 1.4e-06 | 0.202 |
| fp32, processed | bf16 | 10.21% | 1.1e-06 | 0.209 |
| fp32, processed | fp32 | **4.20%** (by construction; 0.0092% under truncated support) | 1.1e-06 | 0.0745 |

Not a finding: the bf16 raw-logprob generation scored against the T=0.6 reference (26.96% truncated, 26.55% full softmax; median 3.1e-04, p99 0.84) compares vLLM's temperature-1 raw logprobs with a T=0.6 reference. Its truncated-reference rescoring at T=1 (17.98%) is likewise not comparable (raw logprobs are not truncated); the full-softmax T=1 row above is the like-for-like one.

**Breakdowns (truncated reference, processed generations; mismatched share):**
| vLLM / HF | entropy <0.1 | entropy 0.1-1 | entropy >1 | pos 0-256 | pos 256-1024 | pos >1024 |
|---|---|---|---|---|---|---|
| bf16 / bf16 | 0.0002% | 17.4% | 42.2% | 16.1% | 13.8% | 2.4% |
| bf16 / lm_head fp32 | 0.0003% | 21.4% | 56.4% | 21.4% | 18.0% | 2.9% |
| bf16 / fp32 | 0% | 20.6% | 54.5% | 20.9% | 17.3% | 2.8% |
| fp32 / bf16 | 0% | 21.7% | 56.5% | 21.4% | 18.1% | 2.7% |
| fp32 / fp32 | 0% | 0.05% | 0.02% | 0.02% | 0.02% | 0.01% |

Token counts per entropy bucket (bf16/bf16): 585k (<0.1), 124k (0.1-1), 67k (>1).

## Findings
1. With fp32 on both sides, the mismatch disappears under the truncated-support definition (0.0092%, 72 of 786,413 tokens: 50 in-support violations plus 22 unsupported; QA 11-25-2026: the original said 22 of 786,413, which would be 0.0028%; p99 0.0078). Every pairing with a bf16 side is 6.4-8.3% (8.1% for fp32-generated tokens scored in bf16). This points to bf16 numerics as the source, but the evidence is one checkpoint, one seed and A4000 hardware only; whether the same holds on A100/H200, or with the trainer's own kernels (e.g. FSDP/flash-attn training forward), is untested.
2. Making only lm_head fp32 does not help (6.4% -> 8.3%, slightly worse than bf16/bf16): the error does not come from the head alone.
3. The mismatch is concentrated: entropy <0.1 tokens (about 75% of tokens) essentially never mismatch; entropy 0.1-1: 17-22%; entropy >1: 42-56%. By position, the first 1024 tokens carry 14-21% and later tokens 2-3%.
4. Nothing here changes any frozen gate; these are numbers to design against, not a gate result.

## Caveats
One checkpoint, one seed, 256 rollouts, A4000 not A100 (kernel choices differ, so absolute levels may differ on A100/H200); vLLM's fused kernels vs HF eager/SDPA; the bf16 raw run used the non-flashinfer sampler. Sub-run failures along the way (lm_head dtype bug, fp32 OOM / "Invalid backend" in SDPA, flashinfer JIT) were fixed in score.py and re-run; the final scripts are in code/ (run order: laneA/B, A2/B2, A3/B3, A4/B4; laneB3 fp32-eager runs OOMed and were superseded by lane A4/B4).

## Options this opens (not decided)
Importance-sampling correction of the rollout/trainer ratio (truncated/masked IS), fp32 scoring of old logprobs on a high-memory GPU, restricting the gate to entropy>0.1 tokens, or measuring on A100/H200 first. Brando decides which, if any, for Exp 20 / 13.

## How it was run
Directory on mercury1 (reached via skampere1): /lfs/mercury1/0/brando9/rl4cv_e21_logprob_mismatch. Generation: `python gen.py --model $M --packs $PK --dtype {bfloat16|float32} --mode {processed_logprobs|raw_logprobs} --gpu-util 0.85 --out out/gen_<name>.jsonl` (see laneA*.sh / laneB*.sh). Scoring: `python score.py --model ckpt/step_658 --gen out/gen_<name>.jsonl --dtype {bfloat16|float32} [--lm-head-fp32] [--T 1.0] --out out/score_<name>__<scorer>.json`; fp32 scoring forces mem-efficient SDPA (GQA expanded, math backend off) to fit 16 GB. Settings of the run are in results/versions.json. Env: CUDA_VISIBLE_DEVICES=8 or 9, PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True, VLLM_USE_FLASHINFER_SAMPLER=0 for the raw run.
