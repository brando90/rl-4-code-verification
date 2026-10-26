# Experiment 24: 8-update fp16 smoke (Qwen3-1.7B SFT), and what the 1.03% full-softmax number is

Status: finished 2026-10-25 (ultimate_brando9 for Brando, free snap GPU). Diagnostic smoke; touches no frozen gate (Exp 20's gate stays: <=1% of completion tokens with |logp_trainer - logp_vLLM| > 0.05 or outside the recomputed sampling support). Follows Experiment 23 (branch ub9/e23-fp16-smoke), which ran 2 updates.

## Question
(1) Does the fp16/fp16 lane (vLLM and trainer fp16, fp32 master weights and AdamW) keep passing the gate over 8 real optimizer updates, with finite training and no drift? (2) Exp 23 reported a "full-softmax diagnostic" of 1.03% and 1.06%, just above 1%: what is it?

## Setup
Identical to Exp 23's fp16 lane except 8 updates (`--updates 8`) and `code/train_e24.py` (= `train_e20.py` plus saving per-token trainer truncated / full-softmax / vLLM-sampler logprobs each update; diff in `code/train_e24_vs_e20.diff`). Exp 20 trainer, TRL 1.16.0 colocated vLLM, arm A, seed 0, 16 groups x 8 = 128 rollouts per update, thinking on, T=0.6, top-p 0.95, top-k 20, max 12288 new tokens, `--smoke`. Start policy: Exp 20 start checkpoint (Qwen3-1.7B SFT, rl4cv_e08 step_658), config.json torch_dtype set to float16 for vLLM; trainer model loaded float16; fp32 master weights, lr 1e-6, grad clip 1.0, static loss scale 16384, non-finite sequences/steps skipped and counted. Hardware/software as Exp 23: skampere1 A100-SXM4-80GB (GPU 3, empty at start, 0 MiB after), vLLM 0.30.0, torch 2.13.0+cu130, transformers 5.17.0, trl 1.16.0 (`pip_freeze.txt` in Exp 23 results; same venv). Command: `code/lane8.sh 3 fp16 16384 <port>` in /lfs/skampere1/0/brando9/rl4cv_e23_fp16_smoke. 4,961 s wall (~13 min for updates 1-2, 8-12 min after: shorter rollouts).

**Deviation (reward):** the Lean grader and train pack are on Sherlock (Stanford sign-in expired), so the reward is the stand-in from Exp 23: 1 if the extracted Lean file has a theorem/lemma and no `sorry`, else 0. Mismatch and finiteness do not depend on reward values; which groups get nonzero advantage (so which sequences are back-propagated: 24-80 of 128 per update) does. This tests numerics, not learning. Update 1 reproduces Exp 23's fp16 update 1 exactly (857,536 tokens, 538 tokens over tolerance), so the run is deterministic at fixed seed.

## Gate (truncated support), per update, vs 1%
share = (in-support tokens with |delta| > 0.05 + sampled tokens outside the recomputed support) / generated tokens.

| update | tokens | outside support | abs delta > 0.05 | gate share | mean abs delta | max abs delta | gate |
|---|---|---|---|---|---|---|---|
| 1 | 857,536 | 18 | 538 | 0.0648% | 0.00053 | 0.230 | pass |
| 2 | 828,568 | 23 | 468 | 0.0593% | 0.00053 | 0.164 | pass |
| 3 | 682,108 | 20 | 503 | 0.0767% | 0.00058 | 0.191 | pass |
| 4 | 640,624 | 26 | 468 | 0.0771% | 0.00063 | 0.146 | pass |
| 5 | 626,872 | 21 | 454 | 0.0758% | 0.00061 | 0.293 | pass |
| 6 | 776,095 | 22 | 586 | 0.0783% | 0.00058 | 0.302 | pass |
| 7 | 621,883 | 17 | 448 | 0.0748% | 0.00062 | 0.334 | pass |
| 8 | 685,342 | 22 | 488 | 0.0744% | 0.00060 | 0.260 | pass |

Gate value (max over updates) 0.0783%, 12.8x under 1%. After update 2 the share sits flat at 0.074-0.078%; no upward trend over 8 updates (weights moved at most 8e-6 per element by the end, see below). Exp 23's run used an update-2 value of 0.0570%; here 0.0593% (this run counts 23 outside-support tokens vs 13; generations are not bitwise identical after update 1).

## Full-softmax diagnostic (not the gate) and what it is
Full-softmax share = tokens with |logp_trainer_full_softmax - logp_vLLM_sampler| > 0.05, all tokens counted.

| update | full-softmax share | of which not in the gate share | tokens where log(kept mass after top-k/top-p) < -0.05 |
|---|---|---|---|
| 1 | 1.034% | 95.8% | 0.804% |
| 2 | 1.130% | 96.8% | 0.895% |
| 3 | 1.135% | 95.6% | 0.847% |
| 4 | 1.375% | 96.6% | 1.120% |
| 5 | 1.195% | 96.3% | 0.912% |
| 6 | 1.118% | 95.7% | 0.846% |
| 7 | 1.169% | 96.0% | 0.876% |
| 8 | 1.202% | 96.3% | 0.918% |

Reading (from `code/analyze_e24.py`, `results/full_softmax_decomposition.jsonl`): vLLM reports the logprob of the sampled token after top-k=20 / top-p=0.95 truncation and renormalization. The full-softmax variant compares the trainer's untruncated logprob with that renormalized one, so it differs by log(kept mass) whenever the truncation removes more than about 5% of the probability. That is 0.80-1.12% of tokens per update (last column), and 95.6-96.8% of the full-softmax mismatches are tokens that are not mismatched in the gate's truncated-support comparison. So the number above 1% is almost entirely the renormalization after truncation, not fp16 numeric mismatch; the numeric mismatch is the gate share (0.06-0.08%). The full-softmax share is above 1% in all 8 updates (1.03-1.38%); it moves with how many flat-distribution tokens the rollouts contain (update 4 has the most and the shortest rollouts), not with a trend over updates. This is an interpretation from one seed and one analysis, not a separate test; the gate (truncated support, as Exp 20 defines it) is unchanged and is the number to use.

## Finiteness and drift (fp16 training)

| update | sequences back-propagated | non-finite sequences | non-finite params after step | grad norm (clip 1.0) | max scaled grad (fp16 max 65504) | IS ratio min / max / mean | loss | max abs (fp16 weights - fp32 master) |
|---|---|---|---|---|---|---|---|---|
| 1 | 80 | 0 | 0 | 0.1075 | 50.3 | 0.677 / 1.098 / 0.9976 | 0.238 | 1.9e-06 |
| 2 | 80 | 0 | 0 | 0.1151 | 40.5 | 0.641 / 1.125 / 0.9975 | 0.295 | 2.0e-06 |
| 3 | 48 | 0 | 0 | 0.0904 | 49.3 | 0.674 / 1.168 / 0.9975 | 0.214 | 3.0e-06 |
| 4 | 48 | 0 | 0 | 0.1106 | 59.3 | 0.644 / 1.127 / 0.9968 | 0.210 | 4.0e-06 |
| 5 | 72 | 0 | 0 | 0.1273 | 74.3 | 0.693 / 1.152 / 0.9973 | 0.346 | 5.0e-06 |
| 6 | 80 | 0 | 0 | 0.1186 | 86.7 | 0.578 / 1.155 / 0.9974 | 0.262 | 6.0e-06 |
| 7 | 24 | 0 | 0 | 0.0675 | 39.9 | 0.686 / 1.188 / 0.9977 | 0.090 | 7.0e-06 |
| 8 | 72 | 0 | 0 | 0.1169 | 61.7 | 0.635 / 1.196 / 0.9973 | 0.295 | 7.9e-06 |

- No NaN/inf anywhere (loss, gradients, weights), no skipped optimizer step. Largest scaled gradient 86.7 against the fp16 maximum 65,504: more than 700x headroom at loss scale 16384.
- Underflow: the smallest nonzero scaled gradient is 5.96e-8 = fp16's smallest subnormal in every update, so the tiniest gradient entries sit at the underflow floor. Not tested whether raising the scale (about 100x would still fit) changes anything.
- Drift: the last column grows by about 1e-6 per update (8e-6 at update 8) on the largest-moving element; importance ratios stay within 0.58-1.20 with mean 0.997. Gate share does not move with it.
- Rollout quality proxies (stand-in reward only): strict-success count per update 93, 89, 103, 107, 107, 100, 113, 103 of 128; truncated rollouts 35, 38, 25, 21, 21, 27, 15, 24. These are not learning evidence (stand-in reward, lr 1e-6, 8 updates, one seed).

## Caveats
Eight updates, one seed, one start checkpoint, A100 (Exp 20 used L40S/H100 in Apptainer), stand-in reward (no Lean compile), no bf16 8-update baseline lane (the second GPU used by Exp 23 was taken by another user). Exp 23's bf16 2-update baseline (2.42%, fail) is the comparison. Drift is bounded at 8 updates at lr 1e-6; a longer pilot is untested. Exp 13 (NeMo RL backend) was not run. No gate changed; Exp 20 not resumed.

## Options (Brando decides)
(a) run Exp 20's pilot with trainer and vLLM both fp16, loss scale 16384, gate as written (passes 10/10 updates so far across Exp 23 and 24); (b) rerun this 8-update smoke with the real Lean reward once Sherlock is reachable; (c) fp32 vLLM as fallback if fp16 overflows in a longer run (Exp 22: fp32 rollouts + fp16 scoring 0.083%).

## Files
`code/` (train_e24.py, train_e24_vs_e20.diff, analyze_e24.py, lane8.sh), `results/` (per-update log, rollouts, manifest, gate check json, full-softmax decomposition). Per-token tensors (e24_tokens_u001-008.pt, ~75 MB) and the 23 GB run dir are in /lfs/skampere1/0/brando9/rl4cv_e23_fp16_smoke/run/fp16_8u.
