# Experiment 22: candidate fixes for the vLLM-vs-trainer log-prob mismatch (Qwen3-1.7B SFT)

Status: finished 2026-10-25 (ultimate_brando9 for Brando, free snap GPUs). Diagnostic only; touches no frozen gate (Exp 20's gate <=1% mismatched tokens, Exp 13 v4 T1 stay as frozen). Follows Experiment 21 (branch ub9/e21-logprob-mismatch, same checkpoint, same harness).

## Question
Exp 20's smoke stopped at 2.62% mismatched tokens (gate <=1%). Exp 21 found fp32/fp32 gives 0.01% and any bf16 side 6.4-8.3%, and that fp32 lm_head alone does not help. Which candidate fix brings the mismatch under 1% on the Exp 20 checkpoint?

## Setup (all logged; code in code/, raw numbers in results/)
- Checkpoint: rl4cv_e08 SFT, Qwen3-1.7B, ckpt/1.7B/hf/step_658 (the Exp 20 starting policy; copied from mercury1).
- Hardware: skampere1 GPUs 3 and 5, NVIDIA A100-SXM4-80GB, both empty when started and released at the end (0 MiB). Exp 21 was on RTX A4000.
- Software: vLLM 0.30.0, torch 2.13.0+cu130 (Exp 21: cu129), transformers 5.20.2, fresh uv venv.
- Prompts/sampling identical to Exp 21: 64 task prompts x 4 samples = 256 rollouts, max 3072 new tokens, T=0.6, top-p 0.95, top-k 20, per-request seeds, one seed, one generation per cell. VLLM_USE_FLASHINFER_SAMPLER=0, vLLM logprobs_mode=processed_logprobs.
- Rescoring: teacher-forced HF forward on the same token ids with the same T/top-k/top-p; same mismatch metric as Exp 21 and the Exp 20 gate: a token is mismatched if |vLLM logprob - HF logprob| > 0.05 or the sampled token is outside the HF top-k/top-p support. Denominator: all generated tokens (about 786k per cell). Only change to score.py: float16 added as a dtype.
- Generators: bf16, fp16, fp32 (vLLM dtype, weights cast from the bf16 checkpoint). Scorers: bf16, bf16 with lm_head fp32, fp16, fp32.
- Commands: `code/lane.sh <gpu> A` (bf16 and fp16 generations) and `lane.sh <gpu> B` (fp32 generation).

## Results (truncated reference, processed logprobs; mismatched share of all tokens)
Gate = 1%. "Pass" only means below 1% on this measurement.

| vLLM generation | HF scorer | tokens | unsupported | share mismatched | median abs | p99 abs | entropy >1 bucket |
|---|---|---|---|---|---|---|---|
| bf16 | bf16 (baseline, Exp 20-like) | 786,432 | 452 | **6.13%** | 0 | 0.247 | 42.2% |
| bf16 | bf16, lm_head fp32 | 786,432 | 450 | 7.95% | 0 | 0.185 | 56.3% |
| bf16 | fp16 | 786,432 | 470 | 7.71% | 0 | 0.177 | 55.2% |
| bf16 | fp32 | 786,432 | 464 | 7.68% | 0 | 0.176 | 54.9% |
| fp16 | bf16 | 785,595 | 362 | 8.05% | 0 | 0.188 | 56.9% |
| **fp16** | **fp16** | 785,595 | 50 | **0.109%** (pass) | 0 | 0.033 | 0.60% |
| fp16 | fp32 | 785,595 | 45 | 0.045% (pass) | 0 | 0.023 | 0.13% |
| fp32 | bf16 | 786,324 | 364 | 8.05% | 0 | 0.187 | 56.4% |
| fp32 | fp16 | 786,324 | 62 | 0.083% (pass) | 0 | 0.026 | 0.32% |
| fp32 | fp32 (upper bound) | 786,324 | 22 | 0.0117% (pass) | 0 | 0.0080 | 0.03% |

Hardware effect: baseline bf16/bf16 is 6.13% on A100 vs 6.42% on A4000 (Exp 21), so Exp 21's numbers carry over; Exp 20's own 2.62% (trainer-side bf16 weights/kernels, different sequences) is lower than both, so the trainer's exact pairing is not reproduced by this harness.

## Importance-sampling (IS) correction, descriptive only (results/is_stats.json, code/is_analysis.py)
IS correction does not change the mismatch share; it reweights. Measured on the saved log-probs for the bf16/bf16 pair: only 0.062% of tokens have an importance ratio outside [0.5, 2] (truncated-IS cap 2 would clip 0.06% of tokens), 1.3% fall outside [0.8, 1.25]; mean ratio 0.9999, mean |log ratio| 0.0104. So the mismatch is many small errors (just over the 0.05 threshold) concentrated in high-entropy tokens (25.8% of entropy>0.1 tokens, which are 23.8% of all tokens), not a few huge ratios. With fp16/fp16 the ratio-outside-[0.8,1.25] share is 0.006%.

## Findings
1. The only candidates that bring the mismatch under 1% are those where both sides run the same 16/32-bit float format with more mantissa than bf16: fp16/fp16 0.109%, fp16 vLLM scored in fp32 0.045%, fp32 vLLM scored in fp16 0.083%, fp32/fp32 0.012%.
2. Any bf16 side fails: 6.1-8.1%, whatever the other side. fp32 lm_head, fp16 or fp32 scoring of bf16 rollouts do not fix it.
3. fp16/fp16 costs no extra memory over bf16 (fp32/fp32 does). It is the cheapest candidate that passes. fp32 vLLM is slower (about 2x longer generation here).
4. IS/TIS correction would clip almost nothing (0.06% beyond cap 2) and would not reduce the gate statistic; it is a reweighting, not a fix for this gate.
5. Nothing here changes any frozen gate; these are numbers to design against.

## Caveats
One checkpoint (the SFT start policy, step 658), one seed, 256 rollouts, one A100 node. This measures rollout-vs-scoring mismatch at fixed weights, not training: a real trainer in fp16 needs loss scaling and could overflow where bf16 does not (not tested; no NaN/inf seen in these rollouts or scores); a run that updates weights, FSDP/flash-attn training kernels, and long contexts beyond 3072 new tokens are untested. The Exp 20 gate's exact trainer path (TRL VLLMGeneration colocated, bf16 weights from an fp32 master, 128 rollouts per update) was not rebuilt. Unsupported counts stay nonzero (22-62 tokens) even in the best cells. A passing share here is not a gate result.

## Options this opens (not decided; Brando decides)
(a) rerun the Exp 20 smoke with vLLM and trainer both in fp16 (fp32 master weights kept) and check the gate; (b) fp32 vLLM + fp16 or fp32 trainer scoring as a fallback if fp16 overflows; (c) keep bf16 and accept the mismatch with a gate rewritten on importance ratios, not the 0.05 log-prob band (changes a frozen gate: needs a new amendment). Same options apply to Exp 13.
