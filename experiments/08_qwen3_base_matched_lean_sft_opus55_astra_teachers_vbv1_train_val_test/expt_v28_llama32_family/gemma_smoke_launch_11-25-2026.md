# V28 Gemma-3 smoke: launched on Sherlock (11-25-2026 11:39 PST)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v28_llama32_family/gemma_smoke_launch_11-25-2026.md>

**TLDR:** The Gemma-3 smoke addendum in `PROTOCOL.md` (2026-11-02, prepared, not submitted) was submitted on Sherlock (account sanmi) on 11-25-2026 at 11:39 PST with `bash submit.sh gemma-smoke`, after Brando's 11-25-2026 10:38 "do experiments too ... start these GO". Nothing has run yet: prepare is pending on `normal`, the five GPU jobs wait on it (`Dependency`). No result is claimed here.

## What was launched
- **Harness and model:** custom PyTorch + Hugging Face SFT trainer `train_v28.py` (transformers 4.57.3, py-pytorch 2.9.1), vLLM 0.30.0 in the Apptainer image for the two smoke generations; no agent harness, no model API, no paid spend (included Sherlock usage, account sanmi). Models: `unsloth/gemma-3-1b-pt` and `unsloth/gemma-3-4b-pt`, pinned revisions in `train_v28.py`. **No DT** (local training and generation; nothing is graded against a frozen DT label).
- **Package:** this folder at main `fa1d4834` minus `results/` and `results.md`, extracted to `$SCRATCH/rl4cv_sherlock/expt_v28_gemma_smoke` (tarball sha256 `6b6e9e32143862719f88c6a5207d6b5463e074aa63eef3c6b0c6dff1013ea084`; `train_v28.py` sha256 `c666499a1dcf6bb87b44ba9ab724e9ead470b8a32397be2ffd3b6ca97ec7d1dc`). The Llama receipt in `$SCRATCH/rl4cv_sherlock/expt_v28` is untouched.
- **Slurm job ids** (receipt `jobs_v28_gemma_smoke.tsv` on Sherlock):

| phase | job id | resources |
|---|---|---|
| prepare | 53689003 | `normal`, 4 CPU, 48 GB, 3 h |
| smoke gemma1b sdpa (seed 20260830) | 53689013 | `gpu`, 1 GPU with 80 GB, 2 h |
| smoke gemma1b eager (seed 20260831) | 53689017 | same |
| smoke gemma4b sdpa (seed 20260830, host optimizer) | 53689021 | 1 GPU 80 GB, 16 CPU, 128 GB |
| smoke gemma4b eager (seed 20260831, host optimizer) | 53689024 | same |
| smoke generation gemma1b (sdpa) | 53689030 | after 53689013 |
| smoke generation gemma4b (sdpa) | 53689038 | after 53689021 |

## Smoke passes when (from PROTOCOL.md, unchanged)
Prepare is PASS; each smoke run ends with finite loss that falls over four updates, records peak GPU memory and exports files that load; each smoke generation finishes samples with `finish_reason` `stop` for at least some samples and writes the extraction fields. A failed model is diagnosed before any full Gemma chain; the full chain is a separate decision.

## Where results will go
`$SCRATCH/rl4cv_sherlock/expt_v28_gemma_smoke/{runs_smoke,gen,logs}`; I fetch them into this folder and write a dated results file when the jobs end. Slurm mail (BEGIN, END, FAIL) goes to Brando's two Gmail addresses.

## Why not run it now on skampere2
skampere2 had three idle H200s at 11:41 PST, but `train_v28.py` asserts a Slurm job id and the Sherlock-only chain inputs (vLLM image, grading directory), so the admitted smoke runs on Sherlock as the protocol says.

**TLDR-end:** [rl4cv Gemma smoke] submitted 11-25-2026 11:39 PST on Sherlock, jobs 53689003 to 53689038; not started yet; no result.

## Attempt 1 failed, attempt 2 submitted (11-25-2026 12:35 PST, AT-3571)
- **Attempt 1:** prepare 53689003 exited 1 after 1:13 at 11:45 PST, so the dependent jobs (53689013, 17, 21, 24, 30, 38) were cancelled. Cause (its log `logs/rl4cv-v28g-prepare_53689003.out` on Sherlock): the token gate `assert not over` in `train_v28.py` `prepare()`: with the Gemma-3 tokenizer 2 of the 1315 rows (index 1151 and 1249) are above `MAX_SEQ` 16384 tokens (longest 17221; Llama's longest was 16003). Download and hash checks had passed. Attempt 1's receipt is kept on Sherlock as `jobs_v28_gemma_smoke_attempt1_prepare_failed.tsv`.
- **Fix (smoke package only):** `MAX_SEQ` now reads `V28_MAX_SEQ` (default 16384, so the Llama chain is unchanged); `submit.sh gemma-smoke` exports `V28_MAX_SEQ=17408`; prepare writes `max_seq_gate` and `sequences_above_16384` per model into the receipt. The smoke trains on the longest rows first, so it now measures GPU memory at the 17221-token worst case. No row is dropped and no corpus change. `train_v28.py` sha256 on Sherlock `400366da70ccdb0689a6b9d50c84285c1902f275ebc2c259e7a6625b6065778b`.
- **Not decided here:** for a full Gemma chain, whether to keep all 1315 rows at a higher limit or drop the 2 long rows is a separate choice (its own dated protocol); the smoke result on memory at 17221 tokens informs it.
- **Attempt 2 job ids** (Sherlock `jobs_v28_gemma_smoke.tsv`, submitted 12:35 PST, `sanmi` account, no spend, no DT): prepare 53692824; smoke gemma1b sdpa 53692825; gemma1b eager 53692826; gemma4b sdpa 53692827; gemma4b eager 53692828; smoke generations gemma1b 53692830, gemma4b 53692831. At 12:37 prepare was pending on `normal`, the rest on `Dependency`.

**TLDR-end:** [rl4cv Gemma smoke] attempt 1 prepare failed on the 16384-token gate (2 Gemma-tokenized rows at up to 17221); gate raised to 17408 for the smoke only, resubmitted as jobs 53692824 to 53692831.
