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

## Results (share of tokens mismatched, truncated-support definition)
| vLLM generation | HF scorer | tokens | mismatched | unsupported | p99 abs | by entropy (<0.1 / 0.1-1 / >1) | by position (0-256 / 256-1024 / >1024) |
|---|---|---|---|---|---|---|---|
| bf16, processed | bf16 | 775,985 | 6.42% | 463 | 0.255 | 0.0002% / 17.4% / 42.2% | 16.1% / 13.8% / 2.4% |
| bf16, processed | bf16, lm_head fp32 | 775,985 | 8.29% | 448 | 0.188 | 0.0003% / 21.4% / 56.4% | 21.4% / 18.0% / 2.9% |
| bf16, processed | fp32 | 775,985 | 7.98% | 423 | 0.179 | 0% / 20.6% / 54.5% | 20.9% / 17.3% / 2.8% |
| fp32, processed | bf16 | 786,413 | 8.14% | 352 | 0.189 | 0% / 21.7% / 56.5% | 21.4% / 18.1% / 2.7% |
| **fp32, processed** | **fp32** | 786,413 | **0.01%** | 22 | 0.008 | 0% / 0.05% / 0.02% | 0.02% / 0.02% / 0.01% |
| bf16, raw logprobs | bf16 (scored at T=0.6, mismatched reference, ignore) | 781,096 | 26.96% | 419 | 0.843 | n/a | n/a |
| bf16, raw logprobs | bf16, full softmax at T=1 | 781,096 | 5.89% (full-softmax definition) | 0 | 0.151 | 0% / 23.0% / 81.8% | 48.3% / 41.4% / 5.3% (truncated def.) |

The bf16-raw / T=0.6 row compares vLLM's temperature-1 raw logprobs against a T=0.6 reference, so its 27% is by construction and is not a finding; the T=1 row is the like-for-like one.

## Findings
1. The mismatch is a precision effect, not an implementation bug: with both sides in fp32 only 0.01% of tokens (22 of 786k) mismatch, p99 0.008. Any pairing that has a bf16 side lands at 6-8%.
2. Making only lm_head fp32 does not help (6.4% -> 8.3%, slightly worse): the error comes from the bf16 transformer body, and bf16/bf16 shares some rounding behaviour that fp32 on one side breaks. Do not expect an fp32 head alone to bring Exp 20 under its 1% gate.
3. The mismatch is concentrated: tokens with entropy < 0.1 (75% of tokens) essentially never mismatch (<=0.0003%); entropy 0.1-1: 17-22%; entropy > 1: 42-56%. By position, the first 1024 tokens carry 14-21% and tokens beyond 1024 only 2-3%.
4. Nothing here changes any frozen gate; these are the numbers to design against, not a gate result.

## Caveats
One checkpoint, one seed, 256 rollouts, A4000 not A100 (kernel choices differ, so absolute levels may differ on A100/H200); vLLM's fused kernels vs HF eager/SDPA; the bf16 raw run used the non-flashinfer sampler. Sub-run failures along the way (lm_head dtype bug, fp32 OOM / "Invalid backend" in SDPA, flashinfer JIT) were fixed in score.py and re-run; the final scripts are in code/ (run order: laneA/B, A2/B2, A3/B3, A4/B4; laneB3 fp32-eager runs OOMed and were superseded by lane A4/B4).

## Options this opens (not decided)
Importance-sampling correction of the rollout/trainer ratio (truncated/masked IS), fp32 scoring of old logprobs on a high-memory GPU, restricting the gate to entropy>0.1 tokens, or measuring on A100/H200 first. Brando decides which, if any, for Exp 20 / 13.
