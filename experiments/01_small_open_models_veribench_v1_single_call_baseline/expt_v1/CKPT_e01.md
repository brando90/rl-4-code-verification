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
  - Model preflight: Qwen3.5-0.8B on 5 tasks, GPU 3 — **in progress / see next resume command**.
- **Current stage:** preflight generation (step 4 of cc.md), GPU 3, PID varies per launch — check `tmux ls`/`nvidia-smi`/`ps aux | grep rl4cv.veribench.generate` before relaunching (jobs are write-once/resumable).
- **Next resume command** (if relaunched):
  ```bash
  cd /lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification && source .venv/bin/activate
  export WORK=/lfs/skampere1/0/brando9/rl4cv_e01
  export PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
  export TASK_IDS=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/task_ids_vbv1.txt
  export LAKE_DIR=$PWD/external/veribench_scorer/veribench_dataset/lean_src
  export SCORER=$PWD/external/veribench_scorer
  export OUT=$WORK/out
  # then: bash expt_v1/run_model.sh eval <hf_id> <revision> <label> [tp]  per model/GPU (see model_revisions.json)
  ```
- **State files:** `$WORK/STATUS_e01` = `RUNNING`.
