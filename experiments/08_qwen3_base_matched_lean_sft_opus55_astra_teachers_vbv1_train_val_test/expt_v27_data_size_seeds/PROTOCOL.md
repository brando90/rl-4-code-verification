# V27: SFT data-size ablation with seeds — Qwen3-1.7B-Base, v4 recipe, 12.5% / 25% / 50% of S, 2 seeds each

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/08-v27-data-size-seeds/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v27_data_size_seeds/PROTOCOL.md>

**TLDR:** Train six fresh Qwen3-1.7B-Base checkpoints on Sherlock with the exact [expt_v4](../expt_v4/PROTOCOL.md) recipe on the first 12.5%, 25% and 50% of S (the same nested examples experiment 08's ladder rungs had seen), two data-order seeds each, then generate and Lean-score 135 validation tasks x 8 per checkpoint exactly like [expt_v16](https://github.com/brando90/rl-4-code-verification/pull/16). The 100% rung is the two existing v4 seeds. The question is whether each doubling of SFT data buys more validation pass@1 / pass@8 than seed noise (0.56 pts / 4.4 pts), and whether experiment 17's budget-and-scale curve predicts the rungs. The test split stays sealed.

**Status:** LOCKED 10-20-2026 20:00 PDT, before any job of this version is submitted. Changes after this point go in a dated addendum below; nothing above it is edited.

## Why this version

Experiment 08's ladder ([expt_v1 results](../expt_v1/results/ladder_manifest.json)) gives one 1.7B value per data fraction, from a single SNAP run with one data order: 0.37% / 0.09% / 1.76% / 4.07% / 4.91% pass@1 at 12.5 / 25 / 50 / 75 / 100%. [Experiment 17](../../17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law/results.md) fits a budget-and-scale curve to the 12.5–50% rungs and predicts the 100% rung within 1.37 pts RMSE across sizes. Since expt_v16 measured the v4 recipe's seed spread at 100% (0.56 pts pass@1, 4.4 pts pass@8), a single-seed rung-to-rung step of ~1–2 pts at 1.7B is not yet evidence that more data helps. This version puts two seeds under each lower rung.

## Data subsets (reused from the ladder, nested)

The ladder rungs are checkpoints of one run that consumed S in `expt_v1/results/sft_set_manifest.csv` order, two examples per step, stopping at steps 82 / 164 / 334. So the ladder's subsets are exactly the **first 164 / 328 / 668 examples of S in manifest order**. That order is the row order of `s_v1.jsonl` and of `../expt_v4/token_manifest.jsonl` (task ids checked equal row by row). The subsets are nested by construction and need no new file.

| Fraction | Examples (first n in manifest order) | Loss tokens (`token_manifest`) | Ladder rung (step, cumulative tokens) | Updates here |
|---|---|---|---|---|
| 12.5% | 164 | 720,775 | step 82, 720,775 | 82 |
| 25% | 328 | 1,442,549 | step 164, 1,442,549 | 164 |
| 50% | 668 | 2,884,708 | step 334, 2,884,708 | 334 |
| 100% (existing) | 1,315 | 5,752,936 | step 658, 5,752,936 | 658 (expt_v4) |

## Runs

| Index | Fraction | Seed | Run name | Label |
|---|---|---|---|---|
| 0 | 12.5% | 20260830 | `f0p125_s20260830` | `v27_f0p125_s20260830` |
| 1 | 12.5% | 20260831 | `f0p125_s20260831` | `v27_f0p125_s20260831` |
| 2 | 25% | 20260830 | `f0p25_s20260830` | `v27_f0p25_s20260830` |
| 3 | 25% | 20260831 | `f0p25_s20260831` | `v27_f0p25_s20260831` |
| 4 | 50% | 20260830 | `f0p5_s20260830` | `v27_f0p5_s20260830` |
| 5 | 50% | 20260831 | `f0p5_s20260831` | `v27_f0p5_s20260831` |
| — | 100% | 20260830, 20260831 | expt_v4 `runs/<seed>` | `v16_v4_20260830`, `v16_v4_20260831` (scored in expt_v16) |

**Existing runs skipped.** On Sherlock (10-20-2026) the only 1.7B v4-recipe trajectories are expt_v4's two full runs (seeds 20260830/20260831; only the final export is kept, and its every-100-step states are full-schedule states, not subset runs) and V26's third full seed (20260832, not yet run). No 12.5/25/50% run exists, so all six are new; the 100% rung reuses the two v4 seeds and their expt_v16 scores (no re-training, re-generation or re-scoring). The training script refuses to start over an existing trajectory directory.

Seeds are expt_v4's seed values, so each 100% run and the subset runs of the same seed share the seed (the order within a subset is `random.Random(seed).shuffle` of that subset's indices, as expt_v4 shuffles all 1,315).

## Training recipe

expt_v4 exactly, except for the number of examples and updates: Qwen3-1.7B-Base at `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` (safetensors checked against the Hub LFS SHA-256), one 80 GB GPU, global batch 2 as two serial microbatches of 1, token-normalized assistant-only loss, AdamW lr 2e-5, betas (0.9, 0.98), eps 1e-5, weight decay 0.1 (`fused=False, foreach=False`), clip 1.0, one epoch, activation checkpointing, float32 parameters, bfloat16 autocast, SDPA attention, TF32 off, Sherlock modules python/3.14.2, py-pytorch/2.9.1_py314, py-transformers/4.57.3_py314. Token gate: every example's prompt and assistant token ids must hash to the committed `../expt_v4/token_manifest.jsonl`.

**Schedule.** Each run is a complete training run on its subset: 20-step linear warmup from 5% to full rate, then cosine decay to zero over the remaining `steps − 20` updates (62 / 144 / 314). This keeps the v4 schedule's shape (fixed warmup, cosine to zero at the run's end). It differs from the ladder rungs, which were cut from the 658-step schedule while the rate was still ~98% / 88% / 51% of peak. That difference is measured, not assumed away (secondary readout below).

Checkpoints every 100 updates and at the last update; final Hugging Face export with a SHA-256 manifest.

## Pipeline (one dependency chain, `submit.sh`)

1. **prep** (`normal`, CPU 4c/32G/2h): copy + hash the corpus; download Qwen3-1.7B-Base at the pinned revision and hash every file; token gate; write `data/tokens.pt` and `data/subsets.json` (indices, digests, loss tokens per fraction, checked against the table above); check the vLLM image hash, validation pack and Lean grading directory exist.
2. **train** array 0–5, throttled `%3` (`gpu`, `GPU_MEM:80GB` as expt_v4, 4c/64G, 2 h wall; expected 10–40 min each), `afterok:prep`.
3. **gen** array 0–5, throttled `%3`, `aftercorr:train` (index i waits on training i): AT-476's vLLM 0.30.0 Apptainer command with expt_v16's frozen v12 settings — 135 validation tasks x 8 samples, thinking on, seed 91, temperature 0.6, top-p 0.95, top-k 20, 12,288-token cap, stop `<|im_end|>`, batch 128, L40S or H100 (`GPU_SKU:L40S|GPU_SKU:H100_SXM5`), 5 h wall (the ladder's 12.5% rung hit the cap on 608/1,080 cells, Base-like; Base took ~3.2 GPU-h). Then the 8 per-sample Lean job directories. Fails unless all 1,080 cells exist.
4. **score**: one array 0–7 per run, throttled `%4` (`normal`, `-c 1 --mem 16G`, 3 h), `afterok` on that run's generation task: AT-477's `score_one.sh` (veribench `score_scsc.py --skip-tc` at 59059a2, Lean 4.22, Mathlib 79e94a09).
5. **collect** (`normal`, `afterany` on everything): one tarball of receipts, step tables, subsets, raw generations, scores, logs and a sacct table (no weights) at `$SCRATCH/rl4cv_sherlock/expt_v27_results.tgz` (+ `.sha256`).

All jobs mail BEGIN, END and FAIL to brandojazz@gmail.com and brando.science@gmail.com; every job id is appended to `jobs_v27.tsv`. A failed step cancels its dependents (`--kill-on-invalid-dep=yes`); no automatic retry, seed substitution or data resampling. A generation that hits its wall may be resubmitted with the same command (it resumes); that goes in an addendum.

## Metrics (identical to expt_v16)

Per-attempt binary success = `kernel_binary` with the inherited non-vacuity gate (expt_v6 `analyze.evaluate`). **pass@1** = mean success over 1,080 cells; **pass@8** = share of 135 tasks solved by at least one of 8 samples. **95% CIs**: task bootstrap, 10,000 draws, numpy seed 0, all samples of a task resampled together; paired differences on the same draws. Also reported: finish_reason=length share, extraction counts, mean generated tokens.

## Pre-registered readout (`analyze_v27.py`)

Rungs r ∈ {12.5, 25, 50, 100}. Per rung: each seed's pass@1 and pass@8 with CIs; the seed pool (16 samples per task) pass@1 with CI; the rung's pass@8 as the mean of its two seeds' pass@8; the rung's own seed spread |s0 − s1|.

**Primary — rung-to-rung gains vs seed spread.** For 12.5→25, 25→50, 50→100 and 12.5→100: the paired gain in pooled pass@1 and in seed-mean pass@8, with 95% task-bootstrap CIs. A step **counts as a data effect** only if (a) the gain exceeds the measured 100% seed spread — **0.56 pts pass@1**, **4.4 pts pass@8** (expt_v16) — and (b) its 95% CI excludes 0. A step that meets one but not both is reported as "not distinguishable from seed noise". If a rung's own seed spread exceeds the 100% spread, that is reported and the larger of the two is used as the bar for steps touching that rung.

**Primary — vs experiment 17's curve.** Experiment 17's corrected budget-and-scale curve (`rl4cv.utility_model`, `BUDGET_SCALE_ONLY`, fit on the 12 ladder rungs ≤ 50% of all four sizes; U = −0.05765 + 0.02253·x_N + 0.12843·C/(C + 1.442549), C in M loss tokens, x_N = 0 at 1.7B; Base 1.7B validation pass rate 0) predicts 1.7B pass@1:

| Rung | E17 prediction (raw) | Floored at 0 | Predicted step gain (floored) |
|---|---|---|---|
| 12.5% | −1.49% | 0.00% | — |
| 25% | 0.66% | 0.66% | +0.66 pts |
| 50% | 2.80% | 2.80% | +2.14 pts |
| 100% | 4.50% | 4.50% | +1.70 pts |

Reported: each rung's pooled pass@1 minus the floored prediction (with CI), whether the prediction lies inside the rung's 95% CI, RMSE over the four rungs, and each observed step gain minus the predicted step gain. Experiment 17 makes no pass@8 prediction. The 12.5–50% predictions are in-sample for experiment 17 (fit on single-seed, unannealed ladder rungs); only 100% was held out there. So this tests whether the curve describes seeded, complete runs, not a fresh forecast.

**Secondary — complete runs vs ladder rungs.** At 12.5 / 25 / 50%, pooled V27 pass@1 minus SNAP's ladder rung (`sft_1p7B_f0p125/f0p25/f0p5`, committed cells), paired, with CI. This separates "less data" from "stopped mid-schedule".

No model selection happens here, so there is no multiplicity correction; every interval is reported.

## Predictions (written before any job)

- **Monotone:** pooled pass@1 rises with data: 12.5% ≤ 25% ≤ 50% ≤ 100%.
- **Small rungs near the floor:** 12.5% and 25% pooled pass@1 each below 2%, with many length-capped generations (the ladder's 12.5% rung capped 608/1,080).
- **Steps:** 12.5→25 is not a data effect (within noise); 50→100 is (gain > 0.56 pts, CI excluding 0); 25→50 is uncertain (I expect a gain of ~1–2 pts, about even odds of clearing both bars). pass@8 steps clear 4.4 pts only for 25→50 or 50→100, not 12.5→25. 12.5→100 clears both bars.
- **E17:** the floored curve lies inside the pooled 95% CI at ≥ 3 of 4 rungs; it under-predicts at 12.5%.
- **Complete vs ladder:** the complete runs match or beat the ladder rungs (annealing to zero helps a small run), by < 1 pt at 12.5/25% and by an amount inside its CI at 50%.

**Interpretation fixed in advance.** If 50→100 is a data effect and the curve tracks the rungs, more SFT data of this kind is still a lever at 1.7B and experiment 17's curve is fit for data planning. If 50→100 is within noise, the 1.7B run is near its data plateau on this corpus (experiment 17 §4's capacity boundary) and the scale arm (V26 at 4B) is the next lever, not more 1.7B data. If complete runs beat the ladder by more than seed noise, the ladder rungs understate small-budget performance and experiment 17's fit inherits that schedule artifact; that is flagged for experiments 15 and 17.

## Scope, resources, stopping

Validation split only; the test split is never loaded. No paid API calls ($0 provider spend). GPU estimate: training ~0.9 GPU-h of compute per seed (0.875 of a full 1.06 GPU-h v4 run) plus ~5 min model loading per job, ~2.4 GPU-h for six; generation 1.6–3.2 GPU-h per checkpoint (100% checkpoints took 1.6; Base-like outputs 3.2), ~10–19 GPU-h for six; **total ~12–22 GPU-h** (central ~17) on public `gpu` nodes, at most 3 GPUs at once, within QOS and fair use (Brando dropped the 8 GPU-hour cap on 10-20-2026). Scoring 48 single-core jobs of ~1–2 h on `normal`. Canonical remote home: `$SCRATCH/rl4cv_sherlock/expt_v27`. Other people's runs (SNAP, Ethan Lee's and Varun's folders, `sherlock-agent-bridge` jobs) are never touched.

**TLDR-end:** [rl4cv: SFT data-size ablation] `08_.../expt_v27_data_size_seeds` trains the v4 recipe on the ladder's 12.5/25/50% subsets at two seeds each, scores them like expt_v16, and tests each data doubling against seed noise and experiment 17's curve.
