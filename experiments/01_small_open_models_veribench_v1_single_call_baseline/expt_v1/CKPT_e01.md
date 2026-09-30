# Checkpoint — experiment 01 (skampere1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01.md>

**TLDR:** Live checkpoint for the GPU worker running experiment 01 on `skampere1`. Updated at every stage change.

- **Start time:** 09-30-2026 11:49 (dispatch); GPU work started 09-30-2026 12:05.
- **Host/session:** `skampere1`, tmux `rl4cv-e01-qwen-vbv1-baseline` (worker), `rl4cv-e01-watchdog` (watchdog, restarted 12:15 after fixing an `$USER` unbound-variable bug in `watchdog_e01.sh` line 32).
- **Work root:** `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification` (venv `.venv`, CUDA 12.8 prepended to PATH in `.venv/bin/activate` — CUDA 12.4's `nvcc` lacks `--compress-mode=size`, needed by flashinfer's JIT sampling kernel; without this fix vLLM's engine core crashes on startup).
- **Done so far:**
  - `make external` (veribench @ c11b99b, veribench_scorer @ 59059a20d, rl_env_scaling @ c75755c) — pin match confirmed.
  - venv + `pip install -e ".[dev,gen]"` (vLLM 0.30.0, torch 2.13.0+cu130) — needed extra explicit installs (pygments, packaging, typing_extensions, pydantic, requests, six, watchfiles, httpx, anyio, rich, uvicorn, python-multipart, sse-starlette, typing-inspection, attrs, cachetools, jsonschema, pyjwt, pyyaml) because `pip install -q` silently dropped several transitive deps.
  - `make test` / `pytest`: 34 passed.
  - Scorer hashes verified exactly (`run_real_eval.py` 6e82b3d1cd6d…, `kernel_axioms.py` 5dbbdcae75ba…, `score_scsc.py` b3713c48e0fd…).
  - Prompt hashes verified exactly: addendum `a7a0fc1b7be6…`, system prompt `dc051963de11…`.
  - Extraction bundle diff (committed `c7cbe3e6…` vs. experiment 103's pushed `6e1a9b0d…`): differs only by VBV2 multi-file path-policy code that is inert under `--addendum vbv1` (root=None, max_files=1); functionally identical for this experiment.
  - Pack verified: experiment 103's v6 pack at `/lfs/skampere1/0/brando9/veribench_vb103/.../private/packs/vbv1_896`, 896 tasks, all `agent-spec v6`; task-id list SHA-256 of content-without-trailing-newline = `5d4e64e4…` (matches PROTOCOL.md exactly).
  - Lean grading project: `veribench_vb103`'s candidate (`veribench_dataset/lean_src`) is NOT built (empty `.lake`, "no previous manifest") and was left untouched (still `git status` clean) — never ran `lake build`/cache there. Built our own instead at `$REPO/external/veribench_scorer/veribench_dataset/lean_src` via `lake exe cache get` (Mathlib prebuilt cache, "Completed successfully!"); `lake env lean` on a gold file exits 0. `LAKE_DIR` = that path.
  - Probe subset written: `$WORK/out/probe_task_ids.txt`, 128 tasks (4/split × 32 splits present; SHA-256 `59b8775653…`).
  - Model revisions resolved for all 9 models via `HfApi().model_info(...).sha`; written to `expt_v1/results/model_revisions.json` (pending write — see next step).
  - Web search 09-30-2026: newer small Qwen releases exist (Qwen3.8 Omni Flash 09-23-2026; Qwen3.8-27B / Qwen3.5-27B multimodal 09-02-2026) — **not added**, per cc.md ("a new model is a new condition"); noted for `REPORT.md`.
  - Compute estimate written to `results.md` → "Compute estimate" (~15–44 GPU-hours generation, ~4–12h wall-clock on GPUs 3–7) and posted; dispatch brief committed. Commit `3852a47`, pushed.
  - Scorer controls (hand-built job, real gold/empty/sorry on 4 distinct tasks — `easy_set__1_myadd`, `cs_set__binary_search` gold 1.0/1.0 each; a 3rd task emptied 0.0/0.0; `aerospace_set_real__my_fprime_crc_match` gold-with-first-proof-sorry'd 1.0/0.833 (<1)) — **all pass**. (First attempt used 4 arbitrary probe-subset tasks; one gold file legitimately fails IC_proofs=1 because its pack-provided gold uses `native_decide` inside a named theorem (`witness_thm`), tainting it and its dependent `correctness_thm` under this project's kernel-axiom rule — not a scorer bug. Switched to CPU-pilot-validated clean tasks.)
  - Model preflight: Qwen3.5-0.8B on 5 tasks, GPU 3 — **passed** (0/5 compile, 3/5 cut off at cap; consistent with README hypothesis, not a smoke failure). Evidence: `expt_v1/results/preflight.json`. Committed `4bf4a8c`, pushed.
- **Current stage: full launch (cc.md §5), 09-30-2026 12:31.** All 9 eval jobs (G=1, 896 tasks) + 8 probe jobs (G=8, 128 tasks) running now, one model at a time per GPU, across GPUs 3–7 (re-verified idle immediately before launch), smallest→largest within each GPU's queue:
  - `rl4cv-e01-gen-gpu3`: qwen3.5-0.8b → qwen3-1.7b → qwen3.5-2b (eval then probe each)
  - `rl4cv-e01-gen-gpu4`: qwen3.5-4b → qwen3-4b (eval then probe each)
  - `rl4cv-e01-gen-gpu5`: qwen3-8b → qwen3.5-9b (eval then probe each)
  - `rl4cv-e01-gen-gpu6`: qwen3-14b (eval then probe)
  - `rl4cv-e01-gen-gpu7`: qwen3.6-27b-local — **OOM'd at `tp=1`** at 12:49 (16.32 GiB KV cache needed vs. 15.44 GiB available after ~54 GB bf16 weights). Deviation recorded in `expt_v1/results/REPORT.md`. `jobs_gpu7.txt` updated to `tp=2`; `wait_and_launch_gpu7_tp2.sh` running in the same tmux session, polling every 60s for GPU 6, 5 or 4 to go fully idle (never 0-2), then launches `CUDA_VISIBLE_DEVICES=7,<partner>` tp=2.
  - Driver: `$WORK/run_all_e01.sh <jobs-file> <log>`, one manifest per GPU (`$WORK/jobs_gpu{3,4,5,6,7}.txt`), logs at `$WORK/run_all_e01_gpu{3,4,5,6,7}.log`. Each line is resumable (`run_model.sh` skips finished generation cells; job/score dirs write-once); a failed line is logged and the driver continues to the next job rather than stopping the GPU's whole queue.
  - `OUT=$WORK/out` (shared across all jobs; per-label subdirs).
- **Next resume command** (if relaunched or a GPU's tmux session died): check `tmux ls` for `rl4cv-e01-gen-gpu{3,4,5,6,7}` and `ps aux | grep rl4cv.veribench.generate` first — never start a second copy of a job still running. To resume a dead GPU queue:
  ```bash
  export CUDA_VISIBLE_DEVICES=<3|4|5|6|7>
  bash /lfs/skampere1/0/brando9/rl4cv_e01/run_all_e01.sh /lfs/skampere1/0/brando9/rl4cv_e01/jobs_gpu<N>.txt /lfs/skampere1/0/brando9/rl4cv_e01/run_all_e01_gpu<N>.log
  ```
  (Re-running is safe: already-finished lines' `run_model.sh` calls no-op past the manifest check since generation/scoring resume.)
- **State files:** `$WORK/STATUS_e01` = `RUNNING`.
