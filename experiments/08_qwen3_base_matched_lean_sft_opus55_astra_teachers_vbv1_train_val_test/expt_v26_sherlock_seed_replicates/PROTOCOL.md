# V26: Sherlock seed replicates — a third v4 seed at 1.7B and the v4 recipe at Qwen3-4B-Base (2 seeds)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/08-v26-sherlock-seeds/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v26_sherlock_seed_replicates/PROTOCOL.md>

**TLDR:** Train three new checkpoints on Sherlock with the exact [expt_v4](../expt_v4/PROTOCOL.md) recipe and data — Qwen3-1.7B-Base seed 20260832, and Qwen3-4B-Base seeds 20260830 and 20260831 — then generate 135 validation tasks x 8 samples each with the frozen v12 settings and score them with the Lean kernel, all on Sherlock. The 1.7B seed gives a three-seed noise bar for single-seed 1.7B comparisons; the 4B pair tests whether the recipe's size gain (SNAP 4.91% -> 9.26% pass@1) reproduces on Sherlock and how large 4B seed noise is. The test split stays unopened.

**Status:** LOCKED 10-20-2026 19:30 PDT, before any job of this version is submitted. Changes after this point go in a dated addendum below; nothing above it is edited.

## Why this version (and why it is the fallback)

The request was to retrain the newest SNAP 1.7B exp-08 condition (V25, else V23, else V20) with two new seeds. That needs the condition's full training data in this repository. It is not here:

| Condition | Training file needed | Where it is | SHA-256 (receipt) |
|---|---|---|---|
| V25 | `corpus_training_v25/base/data/training.jsonl` | SNAP only: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v25/base/data/training.jsonl` | `0882a889…` |
| V23 | `corpus_training_v23/base/data/training.jsonl` | SNAP only: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v23/base/data/training.jsonl` | `215cd07d…` |
| V20 | `corpus_training_v20/base/data/training.jsonl` | SNAP only: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/data/training.jsonl` | `6dad28a9…` |

None of the three hashes matches any blob on `main` (19ba81ff); only their `row_results.csv` decision tables are committed. SNAP is not reachable from this work. So the pre-agreed fallback runs: the expt_v4 corpus, which is on Sherlock with a verified hash, at a third 1.7B seed and at 4B.

## Question

1. **Seed noise at 1.7B.** With a third seed, how large is the seed-to-seed spread of the v4 recipe on validation pass@1 and pass@8? The two v4 seeds differ by 0.56 pts pass@1 and 4.4 pts pass@8 ([expt_v16](https://github.com/brando90/rl-4-code-verification/pull/16)).
2. **Size at a fixed recipe.** Does the v4 recipe at Qwen3-4B-Base beat 1.7B on Sherlock as on SNAP, and is the 4B result within noise of SNAP's `sft_4B_f1p0`?

## Arms

| Arm | Model (revision) | Seed(s) | Run name(s) | Label(s) |
|---|---|---|---|---|
| A: 1.7B third seed | `Qwen/Qwen3-1.7B-Base` (`ea980cb0a6c2ae4b936e82123acc929f1cec04c1`) | 20260832 | `1p7b_s20260832` | `v26_1p7b_s20260832` |
| B: 4B, v4 recipe | `Qwen/Qwen3-4B-Base` (`906bfd4b4dc7f14ee4320094d8b41684abff8539`) | 20260830, 20260831 | `4b_s20260830`, `4b_s20260831` | `v26_4b_s20260830`, `v26_4b_s20260831` |

No Base 4B generation: Base 1.7B scored 0/1080 on both clusters and SNAP's Base 4B scored 3/1080 (`base_4B_e05`); the committed SNAP cells serve as the Base reference.

## Inputs (identical to expt_v4)

- Corpus: the 1,315 admitted examples, `s_v1.jsonl`, SHA-256 `885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354`, copied from the Sherlock expt_v4 package.
- Token gate: every example's prompt and assistant token ids must hash to the committed `../expt_v4/token_manifest.jsonl` values (5,752,936 loss tokens, no sequence above 16,384), for **each** model's tokenizer. The 4B tokenizer files are byte-identical to 1.7B's on the Hub (same blob ids), and the manifest records `identical_across_sizes: true`; a mismatch stops all training.
- Weights: Hub snapshots at the pinned revisions; every file's SHA-256 is recorded in the preparation receipt and the safetensors shards are checked against the Hub's LFS SHA-256 values pinned in `train_v26.py`.

## Training recipe

Exactly expt_v4: one GPU, global batch 2 as two serial microbatches of 1, token-normalized assistant-only loss, AdamW lr 2e-5, betas (0.9, 0.98), eps 1e-5, weight decay 0.1, clip 1.0, 20-step linear warmup from 5% then 638-step cosine to 0, 658 updates, one epoch in the order `random.Random(seed).shuffle`, activation checkpointing, float32 parameters, bfloat16 autocast, SDPA attention, TF32 off, Sherlock modules python/3.14.2, py-pytorch/2.9.1_py314, py-transformers/4.57.3_py314. Checkpoints at every 100 updates and at 658; final Hugging Face export with a SHA-256 manifest.

Arm A runs the expt_v4 training loop unchanged (only the seed table differs).

**Arm B deviation (memory).** At 4.02B parameters, float32 parameters + gradients are ~32 GB and AdamW's two float32 moments another ~32 GB; with activations (1.7B peaked at 47.85 GiB with ~32 GB of states) this exceeds one 80 GB H100. Multi-GPU sharding or lower-precision states would change the numerics more. Arm B therefore keeps the float32 parameters, gradients, forward/backward, autocast and gradient clipping on the GPU exactly as expt_v4, and runs the **same** `torch.optim.AdamW` (same hyperparameters, `fused=False, foreach=False`) and the same scheduler on a float32 CPU master copy of the parameters and the CPU moments. After every update the master values are copied back to the GPU parameters, so GPU and CPU copies are equal. The update formula and the precision of every state are unchanged; only CPU vs CUDA elementwise rounding (e.g. `sqrt`, division) can differ in the last bit. A local unit test (`tests/test_offload_equivalence.py`) checks that the offload bookkeeping gives bit-identical parameters to the in-place optimizer on the same device over many steps. Arm B jobs ask for 16 CPU cores and 128 GB host memory and a 12 h wall (expected ~4–5 h: ~2x the 1.7B forward/backward time plus a CPU optimizer step).

## Pipeline (one dependency chain)

1. **prep** (`normal`, CPU): copy + hash the corpus; download both models at the pinned revisions and record every file's hash; token gate for both tokenizers; write `data/tokens.pt` and `prepare_receipt.json`; check the generation image, validation pack and Lean grading directory exist. Uses Sherlock modules only (no pip builds).
2. **train** x3 (`gpu`, one 80 GB H100 each, `afterok:prep`), in parallel.
3. **gen** x3 (`gpu`, L40S or H100, `afterok:train`): AT-476's vLLM 0.30.0 Apptainer command with the frozen v12 settings — 135 validation tasks x 8 samples, thinking on, seed 91, temperature 0.6, top-p 0.95, top-k 20, 12,288-token cap, stop `<|im_end|>`; 6 h wall at 1.7B, 10 h at 4B (resumable). Then materialize the 8 per-sample Lean job directories. The job fails unless all 1,080 cells exist.
4. **score** x3 arrays of 8 (`normal`, `-c 1 --mem 16G`, `afterok:gen`): AT-477's `score_one.sh` (veribench `score_scsc.py --skip-tc` at 59059a2, Lean 4.22, Mathlib 79e94a09).
5. **collect** (`normal`, `afterany` on everything): one tarball of receipts, step tables, raw generations, scores and logs (no weights) at `$SCRATCH/rl4cv_sherlock/expt_v26_results.tgz`.

All jobs mail BEGIN, END and FAIL to brandojazz@gmail.com and brando.science@gmail.com; job ids go to `jobs_v26.tsv`. A failed step cancels its dependents (`--kill-on-invalid-dep=yes`); there is no automatic retry, seed substitution or data resampling. A generation that hits its wall may be resubmitted with the same command (it resumes and re-draws nothing already written); that is recorded in an addendum.

## Metrics and analysis (`analyze_v26.py`)

Per-attempt binary success = `kernel_binary` with the inherited non-vacuity gate (expt_v6 `analyze.evaluate`), exactly as expt_v16.

- **pass@1** = mean success over 1,080 cells; **pass@8** = share of the 135 tasks solved by at least one of 8 samples.
- **95% CIs**: task bootstrap, 10,000 draws, numpy seed 0, all samples of a task resampled together; paired differences on the same draws.
- **Seed spread**: per size, mean, SD and range of pass@1 and pass@8 across seeds — 1.7B: v4 20260830, v4 20260831 (Sherlock, expt_v16 scores) and v26 20260832; 4B: v26 20260830 and 20260831.
- **Comparisons (paired)**: new 1.7B seed vs each v4 seed and vs SNAP `sft_1p7B_f1p0`; each 4B seed vs SNAP `sft_4B_f1p0`; 4B seed pool vs 1.7B three-seed pool (pass@1); 4B seed 20260830 vs 20260831.

No model selection happens here, so no multiplicity correction; all intervals are reported.

## Predictions (written before any job)

- 1.7B seed 20260832: pass@1 between 3.5% and 6.5%, i.e. inside the band of the two v4 seeds (4.81%, 5.37%) and SNAP (4.91%); pass@8 between 10% and 21%. The three-seed pass@1 SD stays under 1 pt.
- 4B: pass@1 per seed between 6.5% and 12% (SNAP `sft_4B_f1p0` 9.26%, 100/1080; pass@8 33/135 = 24.4%), with both paired differences vs SNAP 4B inside their CIs.
- 4B pool minus 1.7B pool: pass@1 about +4 pts, CI excluding 0.
- 4B seed spread similar to or larger than 1.7B's in absolute pass@1 points.

## Scope, resources, stopping

Validation split only; the test split is not loaded. No paid API calls ($0 provider spend). GPU estimate: train ~1.1 h (1.7B) + 2 x ~5 h (4B); gen ~1.6 h (1.7B) + 2 x ~3.5 h (4B); about 19 GPU-hours on public `gpu` nodes, within QOS and fair use (Brando dropped the 8 GPU-hour cap on 10-20-2026). Scoring 24 x ~1 h on `normal` single cores. Canonical remote home: `$SCRATCH/rl4cv_sherlock/expt_v26`. Other people's runs (SNAP, Ethan Lee's folders, `sherlock-agent-bridge` jobs) are never touched.

**TLDR-end:** [rl4cv: Sherlock seed replicates] `08_.../expt_v26_sherlock_seed_replicates` adds a third 1.7B seed and two 4B seeds of the v4 recipe, trained, generated and Lean-scored on Sherlock, to put a seed-noise bar under single-seed 08 comparisons.
