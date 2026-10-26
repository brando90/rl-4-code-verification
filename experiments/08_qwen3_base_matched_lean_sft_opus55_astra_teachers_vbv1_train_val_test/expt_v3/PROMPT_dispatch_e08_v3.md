# Experiment 08 v3 dispatch prompt — Matched Replay (`R`) vs Admitted 2,585-File Expansion (`E`) SFT Continuation on SNAP GPUs (`[p 9/10]`)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/PROMPT_dispatch_e08_v3.md>

**TLDR:** Lock `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/PROTOCOL.md` with its recommended defaults, precompute the deterministic step schedules (`sft_schedule_v3_R.json` and `sft_schedule_v3_E.json`) and validation manifest (`ladder_manifest_v3.json`), freeze the prospective forecast (`forecasts/e08_v3_forecast.json`), run the 8-step 1.7B dry run on the Expansion (`E`) corpus, and execute the matched `+5,752,936`-loss-token supervised fine-tuning (SFT) continuations and `135 × 8` validation ladders on idle SNAP GPUs (`$0` Vals API spend).

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Binding rules, GPU etiquette & single-writer discipline

- Read `~/agents-config/INDEX_RULES.md`, the repository `CLAUDE.md`, and `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/{PROTOCOL.md,results.md,expt_v3/PROTOCOL.md,expt_v3/RESULTS_failure_taxonomy.md}`.
- **Zero paid model/judge calls (`$0` to Vals):** SFT training uses local NeMo RL 0.4.0 (`c751f811`) in `/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl`, local vLLM generation in `/lfs/skampere1/0/brando9/rl4cv_e08/venv_gen`, and local CPU Lean 4.22.0 kernel verification. Section 7 (`SCSC >= 0.25` hosted judge milestone) remains deferred until after validation gates (a)–(c) are evaluated.
- **GPU discipline (Trigger Rule 9):**
  - Check `nvidia-smi` and `/lfs/skampere1/0/brando9/rl4cv_e13v2` leases before claiming any GPU on `skampere1`.
  - Keep at least 1 idle GPU on `skampere1` free for Experiment 13 v2 (`codex-rl4cv-e13v2-owner-g0`).
  - Always export `CUDA_VISIBLE_DEVICES=<chosen_free_ids>` explicitly before every training or vLLM generation command.

## 1. Lock `expt_v3/PROTOCOL.md` with resolved `[decide at lock]` items

1. Verify the admitted corpus hashes on `skampere1` (`/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/s_v3_candidates.jsonl` SHA-256 `7fa02557…` and `expt_v3/results/admitted_corpus_manifest.csv` SHA-256 `3ed7cb7a…`: 2,585 admitted rows = 1,315 original `S` + 685 cached train teacher files + 585 Mostly Basic Python Problems (MBPP) pairs from Expt 02A v3; 0 duplicates, 0 held-out hits).
2. Resolve the `[decide at lock]` items in `expt_v3/PROTOCOL.md`:
   - **Section 2:** Confirm the exact counts and SHA-256 hashes from `expt_v3/results/admitted_corpus_stats.json`.
   - **Section 4:** Use the recommended learning-rate reset schedule: `LinearLR(start_factor=1/W, end_factor=1, total_iters=W)` with `W = ceil(0.03 * planned_steps)` followed by `CosineAnnealingLR(T_max = planned_steps - W, eta_min = 0)` at peak `lr = 2e-5` and fresh AdamW state from each size's `step_658` Hugging Face export (`ckpt/<size>/hf/step_658`).
   - **Section 6 (Decision rule):** Evaluate both the primary 4-size common checkpoint (`1.7B, 4B, 8B, 14B` all passing gates (a) `>= 972/1,080` extracted, (b) `<= 108/1,080` capped, (c) `>= 7/135` mixed tasks) AND the pre-registered 3-size sensitivity (`4B, 8B, 14B` common checkpoint, treating `1.7B` as a capacity floor), plus a zero-call post-processing diagnostic escaping digit-leading Lean `namespace` identifiers (per Experiment 01's 10-07 finding).
3. Precompute and commit:
   - `expt_v3/results/sft_schedule_v3_R.json` and `expt_v3/results/sft_schedule_v3_E.json` (deterministic `sha256("rl4cv-e08-v3-sft-order-v1:" + ...)` ordering, exact half-budget `2,876,468` and full-budget `5,752,936` loss-token step numbers).
   - `expt_v3/results/ladder_manifest_v3.json` (16 systems: `v3_<R|E>_<1p7b|4b|8b|14b>_<f0p5|f1p0>`, 135 validation tasks × 8 samples = 17,280 cells).
   - `expt_v3/forecasts/e08_v3_forecast.json` via `rl4cv.forecast.freeze_forecast`.
   - Update `expt_v3/PROTOCOL.md` status from `DRAFT, NOT LOCKED` to `LOCKED` with the lock commit hash and timestamp, create live `expt_v3/results.md` and `expt_v3/CKPT_e08_v3.md`, run `make test`, and push to `main`.

## 2. Dry run & SFT continuation execution order

1. Send `[RUN START] rl4cv-e08-v3-sft-continuation` To `brando.science@gmail.com` with CC `brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai`.
2. **Disposable 8-step dry run on 1.7B (`E` corpus):**
   - Run 8 steps (16 examples) on 1 idle GPU (`CUDA_VISIBLE_DEVICES=<1_free_gpu>`) to verify `global_valid_toks` matches `sft_schedule_v3_E.json` and checkpoint export works cleanly; delete the disposable dry-run weights afterward.
3. **Priority size order (`4B` and `1.7B` first — the two sizes that missed v1's formatting/cap gate! — then `8B` and `14B`):**
   - **Phase A (`1.7B` on 1 GPU + `4B` on 2 GPUs, conditions `E` and `R`):**
     - Train `v3_E_4b` and `v3_R_4b` (2 GPUs, ~107 min each) and `v3_E_1p7b` and `v3_R_1p7b` (1 GPU, ~66 min each), exporting checkpoints at `f0p5` and `f1p0` with `SHA256SUMS`.
     - Immediately run the `135 × 8` validation generation and Lean kernel scoring for the `1.7B` and `4B` rungs (`8 × 1,080 = 8,640` cells) and publish their gate (a)–(c) results and failure taxonomy in `expt_v3/results.md`!
   - **Phase B (`8B` on 4 GPUs + `14B` on 8 GPUs when idle devices permit, conditions `E` and `R`):**
     - Train `v3_E_8b`, `v3_R_8b`, `v3_E_14b`, `v3_R_14b`, run their `135 × 8` validation ladders, and publish the complete 4-size comparison table (`E` vs `R` paired task-bootstrap differences, 10,000 draws, seed 0) in `expt_v3/results.md` and `results.md`.
4. Send `[RUN DONE] rl4cv-e08-v3-sft-continuation: <status>` To `brando.science@gmail.com` with CC `brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai`.
