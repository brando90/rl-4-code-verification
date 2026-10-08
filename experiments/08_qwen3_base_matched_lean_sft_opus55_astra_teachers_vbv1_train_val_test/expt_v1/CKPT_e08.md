# Experiment 08 checkpoint — matched Lean SFT warm start (master and SNAP worker)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/CKPT_e08.md>

**TLDR:** Resumable state of experiment 08. The master finished the zero-call design steps; the SNAP worker (tmux `rl4cv-e08-worker` on `skampere1`) has finished every zero-call lock-1 check (served pack, scorer adapter, tokenizer template, service, route identity) and is locking PROTOCOL §§ 1–7 before the 8-call live teacher preflight. `$WORK/CKPT_rl4cv-e08-worker.md` is a symlink to this file.

**Created:** 10-07-2026 16:35 PDT (master). **Last updated:** 10-07-2026 17:57 PDT (worker).

## State

| Item | Value |
|---|---|
| Current step | Runbook § 5: all 8 teacher main runs in flight (Astra since 17:44 PDT, Opus xhigh since ~17:58 PDT); Base 14B validation generation running; next: harvest + score as runs finish (§ 6) |
| Master | Claude Code (Opus 5.5) on Brando's laptop; private worktree `~/vb_worktrees/rl4cv-sft-warmstart-1007` |
| Worker | Claude Code `claude-fable-5-1`, effort `high`, on `skampere1`, tmux `rl4cv-e08-worker`, clone `/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification` (`main`) |
| Work root | `/lfs/skampere1/0/brando9/rl4cv_e08`: `env_e08.sh` (source in every shell), `.venv` (tests), `venv_gen` (vLLM 0.30.0 / torch 2.13.0+cu130 / transformers 5.18.0), `grading/lean_src` (private Lean v4.22.0 + Mathlib copy), `pack_train539/`, `cache/huggingface` (HF_HOME; 1.7B/4B/8B linked, 14B tokenizer), `private/` (0700), `logs/` |
| Status file | `/lfs/skampere1/0/brando9/rl4cv_e08/STATUS_e08` = RUNNING |
| Lock 1 / lock 2 | lock 1 LOCKED 2026-10-08T00:16:15Z at code commit `6e6890f`; the lock commit itself is `cc86ec0` (10-07-2026 17:16 PDT). **Amendment A1 (v1.1)** LOCKED 2026-10-08T00:55:51Z at `bc27e1c`: opus55 compute_effort xhigh. Lock 2 not locked |
| Valkyrie runs | preflight (8 cells, admitted 10-07-2026 17:17–17:19 PDT): opus55 p1 `67be268e-2560-4c6d-ae77-eb0448560508`, p2 `a3f8317d-3e9c-4f34-9d08-6f4cc4b85ccc`; astra p1 `68b86858-6af1-404e-ae1d-61d5c49da838`, p2 `62365cc4-5ff5-4ade-803f-320343716ca9` (`expt_v1/results/runs_state.json`); **Astra main** (admitted 17:44 PDT, 539 cells each, concurrency 24): s1 `e8ead92a-2839-41bd-8631-fe6b57e67747`, s2 `20362628-b046-4781-99a8-b3c7bd763d1f`, s3 `670496fd-932f-4ae9-af20-5d90106e046e`, s4 `3e4b9292-4da7-4db0-959a-26f582e9e3b2`; **Opus xhigh diagnostic preflight** (17:43 PDT): p1 `e4294309-0639-404c-b4f0-316437e4179c`, p2 `9ede472b-0200-47e6-98ab-8384b10fd5df`; **Opus main (xhigh, admitted 17:57 PDT, 539 cells each, concurrency 24)**: s1 `65dfef88-acc0-4bb3-9c32-88be333fccd2`, s2 `968f1080-e811-4736-865d-b728c333736b`, s3 `f26ab151-1a11-4afe-b576-276e73c6663e`, s4 `b267e358-bb10-4d66-981f-3ec730a9c367` |
| GPUs held | GPUs 1–2 (planned now): Base 14B validation generation, 2 vLLM shards (bf16 28 GB weights + KV cache each, gpu_memory_utilization 0.88, compute-bound, est. 1–3 h for 1,080 cells; then CPU scoring, 4 parallel); GPU 0 briefly for the smoke's vLLM load check, then none; smoke done (loss 2.73→2.15, export OK). Earlier plan: GPU 0 only, for the NeMo RL infrastructure smoke (tmux `rl4cv-e08-smoke-nemo`): Qwen3-1.7B-Base, 4 synthetic examples, 2 steps, est. 20–40 GB, compute bursts, < 15 min; freed when it ends. Production plan (PROTOCOL § 8 GPU layout, to be re-estimated after the dry run): 1.7B 1 GPU TP1, 4B 2 GPUs TP2, 8B 4 GPUs TP4, 14B 8 GPUs TP8 (after the others), all A100-80GB, full-parameter bf16 + fp32 AdamW, activation checkpointing |
| Services, ports, tunnels | service `rl4cv-e08-vbv1-train` on `127.0.0.1:9740` (uvicorn pid in `$WORK/private/service.pid`), cloudflared tunnel (pid in `$WORK/private/tunnel.pid`); port claim `/lfs/skampere1/0/brando9/valkyrie_port_claims/rl4cv-e08_9740-9759.txt`; private config `$WORK/private/valkyrie.yaml` (use `VALKYRIE_CONFIG_PATH`) |
| Health check | `snap_health.sh --node skampere1`: only `disk.dfs` FAIL (DFS 100% full), off this job's path |

## Log

- **10-07-2026 16:35 PDT (master).**
  - Built the D-013 split with `python -m rl4cv.splits` on VeriBench `c11b99ba`: 896 tasks, 664 groups, 539 / 135 / 222, manifest SHA-256 `157ce781…`. `tests/test_splits.py` passes, including the reproduction test (`VERIBENCH_ROOT` = an archive of the pin).
  - Computed Base baselines on the splits from experiment 05's receipts.
  - Ran `estimate_token_budget.py gold|e103` on `skampere1`; read-only on experiment 103's private receipts.
  - Wrote README, PROTOCOL (locks 1 and 2 pending), runbook and `results.md`. Recorded D-013 and D-015 and updated the `CLAUDE.md` held-out rule.

- **10-07-2026 16:39 PDT (Codex light review, local only).**
  - Reviewed `ab650c3` through the working tree at `4b66ca1`, only in the owned checkout; fixes remain unstaged and uncommitted. No model calls, Valkyrie runs, remote connections or GPU work.
  - Corrected lock order, data screens, deterministic SFT assembly, non-vacuity checks, matched training details, missing-cell gates, official aggregation, judge controls/audit, and worker path/environment isolation. Earlier experiment locks remain unchanged.
  - All seven split artifacts reproduce byte for byte; all 1,792 source-file hashes match. Base tables reproduce from experiment 05. Token-budget counts/rates/means and planning arithmetic agree; private teacher files and host toolchains were unavailable for direct verification.
  - Pinned archive: `python3 -m pytest -q` gives 89 passed, 2 skipped (experiment 103 adapters require source absent from the dataset-only archive). Without that archive: 88 passed, 3 skipped. `git diff --check` passes. Split parameters and manifest hash are unchanged.

- **10-07-2026 16:42 PDT (master).** Reviewed the Codex diff and committed it with the builder follow-ups listed in `results.md` (light QA section). Next: dispatch the SNAP worker.

- **10-07-2026 16:47 PDT — launch receipt (master).**
  - Host `skampere1`; tmux session `rl4cv-e08-worker`; client Claude Code via `/lfs/skampere1/0/brando9/bin/clauded_tok` (`claude --dangerously-skip-permissions`, node-local binary).
  - Model `claude-fable-5-1`, effort `high`, pid 461405, session `d3968eac-37d1-4b77-b339-a69389689c9c`. Effort `high` rather than `max` because this is long execution under a detailed runbook, sharing the personal subscription with the 02A v3 and 07 workers.
  - Clone `/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification` on `main` at `bae5929`. Launched with `deploy_cc.sh` (deployment identity `deploy_1a624de4…`); the master accepted the folder-trust prompt.
  - First observed action: refreshing agents-config and reading the runbook.
  - Preflight: `snap_health.sh --node skampere1` shows only `disk.dfs` FAIL (DFS 100% full), which is off this job's path. All 8 A100s were idle at 16:22 PDT.

- **10-07-2026 17:12 PDT — worker § 1–4 zero-call checks (all PASS; details in `results.md`).**
  - § 1: pulled `main` (818285a); `make external` at the three pins; `.venv` + `make install`; `make test` with `VERIBENCH_ROOT=external/veribench`: 112 passed, 1 skipped (experiment 07 `scipy`), all 13 split tests ran. `venv_gen` built with `uv` from `$WORK/env/gen_requirements.txt` (experiment 01's freeze recorded at `$WORK/env/e01_venv_freeze.txt`); `import vllm` and CUDA OK. Private grading project copied to `$WORK/grading/lean_src` (5.6 GB).
  - § 2: `scripts/build_train_pack.py` → `$WORK/pack_train539/` and `results/pack_check.json` PASS. `scripts/template_check.py control` → `results/template_check.json` PASS (4 sizes identical; assistant prefix `<think>\n\n</think>\n\n`).
  - § 3: `scripts/score_teacher_files.py adapter-check` → `results/scorer_adapter_check.json` PASS (14 files). First run exposed that 403/896 gold references use `native_decide` (2 of the first 3 train gold files score IC_proofs 0.5); gold selection now skips such references and scores two as diagnostics; `sorry` is classed `unproved_theorem`, `forbidden_axiom` is reserved for declared axioms / `native_decide`.
  - § 4.1: `scripts/deploy_service_e08.py deploy` → service + tunnel live (200/401 local and tunnel, limit 6,600 s), `results/deployment_e08.json`.
  - § 4.2–4.3: `scripts/identity_e08.py` with the 10-07 registry dump (read-only from the 02A v3 worker's private copy, SHA-256 `572c742f…`, 454 models; no key on this host) → `results/route_identity_e08.json` PASS: `anthropic/claude-opus-5-5-no-fallback` (fallbacks `[]`, compute_effort max), `openai/gpt-6-astra-max` (highest served); installed bundle = frozen hashes; retry bound 2 requests/cell; 0 prior runs. Decision (Rule 57): reuse that same-day dump instead of fetching the gateway key on this host.

- **10-07-2026 17:43 PDT — live preflight harvested; Opus 5.5 at max effort cannot complete (decision under Rule 57).**
  - Astra (`openai/gpt-6-astra-max`): 4 / 4 cells measured, finish `stop`, 2.3–3.8k output tokens with 17–33k reasoning tokens, 8–16 min each, charges 2.94 + 2.83 USD; Lean files collected by the service (`valk run results` returns "tracker returned a malformed response", as in 02A v3; the run-output benchmark JSON carries the rows and the harvest now reads it).
  - Opus 5.5 (`anthropic/claude-opus-5-5-no-fallback`, `compute_effort max`): 4 / 4 cells `model_error` / `MaxOutputTokensExceededError` after ~18 min, no usage or charge recorded. Zero-call evidence: the gateway caps this model's `max_tokens` at 128,000 (registry `properties`); experiment 103's Opus 5 max used a median 76,840 reasoning tokens (117 / 895 cells exceeded, the two preflight tasks did not); 02A v3's Fable 5.1 max preflight failed the same way. So the locked setting cannot yield files on most tasks and 2,156 main calls at max would be wasted.
  - Decision: do not admit Opus main runs at max. Run a tagged diagnostic preflight at `compute_effort xhigh` (same two train tasks, same labels + `-xhigh`, recorded in `runs_state.json` under `@xhigh`, excluded from S). If it completes and scores end to end, amend PROTOCOL § 3 for `opus55` to `xhigh` as a versioned lock-1 amendment (v1.1) before any Opus main call; if not, step to `high` once more, else report the Opus teacher as BLOCKED and continue with Astra only. Astra main runs are admitted under the unchanged lock once its preflight scores end to end. Flagged for Brando / the master in `results.md`.

- **10-07-2026 17:52 PDT — § 7 infrastructure verified (disposable smokes, synthetic data, GPU 0) and § 9 Base 14B generation launched.**
  - NeMo RL 0.4.0 `c751f811` (`$WORK/nemo_rl`, `uv`; torch 2.7.1+cu128, transformers 4.55.4; worker venvs built at first launch, Ray temp dir must be short: `/tmp/user/<uid>/e08ray*`). Smoke 1: 4 synthetic examples, 2 steps, loss 2.73 → 2.15, `step_2` checkpoint (weights + optimizer + scheduler + dataloader state) exported with `convert_dcp_to_hf.py` and loaded by vLLM 0.30.0 (`venv_gen`; CUDA 12.8 `nvcc` must be first on PATH for flashinfer's JIT, as experiment 01 found) → generation + extraction OK on the two preflight train tasks.
  - Smoke 2 (3 examples + the odd-|S| padding slot from `prepare_sft_nemo_e08.py`): TensorBoard `train/global_valid_toks` = 60 then 30, i.e. the padding slot contributes zero loss tokens and the cumulative log equals the precomputed schedule (`extract_train_logs_e08.py` → `matches_schedule true`). TensorBoard files live under `<log_dir>/exp_NNN/tensorboard/`.
  - Checkpoint mechanism for the token-fraction rungs: NeMo RL saves only every `save_period` steps or at the last step, so production runs as a chain of segments (`launch_sft_e08.sh`): each segment's `sft.max_num_steps` is the next rung step; the next segment resumes weights, optimizer, LR scheduler and dataloader state from it. Identical at every size.
  - Base 14B validation generation: `tmux rl4cv-e08-ladder-base14b`, `run_ladder_e08.sh validation base14b Qwen/Qwen3-14B-Base 0b0bd373… 1,2 1` (2 vLLM shards, 540 cells each; frozen manifest `results/ladder_manifest_base14b.json`); GPU 1 at 70 GB / 100 % four minutes after launch, GPU 2 shard staggered 180 s.

## Next command (worker)

```bash
source /lfs/skampere1/0/brando9/rl4cv_e08/env_e08.sh && cd $REPO && . .venv/bin/activate
# 1. commit + push this zero-call step; 2. set PROTOCOL lock-1 line to that commit, commit + push (record the lock commit here);
# 3. live preflight: python $EXP/expt_v1/scripts/run_teachers_e08.py admit --phase preflight --teacher opus55 --sample p1 (and p2; astra p1, p2)
```
