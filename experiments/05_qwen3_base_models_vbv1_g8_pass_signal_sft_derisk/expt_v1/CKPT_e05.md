# Checkpoint — experiment 05 (Qwen3 Base 1.7B/4B/8B, VeriBench V1, G=8)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1/CKPT_e05.md>

**TLDR:** Resumable state for experiment 05's SNAP run: who owns it, what is running where, and the exact commands to resume or land it.

**Last updated:** 10-05-2026 18:20 (master)

## Ownership

- **Master:** Claude Code (Opus 5.5) on Brando's laptop, session `https://claude.ai/code/session_019RBgi9yaHeBPu5urmhn8qN`; wrote the design, opened draft PR #4, ran the preflight and launched the run.
- **Worker (sole writer of the branch after dispatch):** Claude Code on `skampere1`, tmux session `rl4cv-e05-worker`, launched with `/lfs/skampere1/0/brando9/bin/clauded_tok` (full access, long-lived SNAP OAuth token), model `claude-sonnet-5`, prompt `expt_v1/cc.md`. Launch receipt below once verified.
- **Branch / PR:** `e05-qwen3-base-vbv1-g8-sft-derisk`, <https://github.com/brando90/rl-4-code-verification/pull/4> (draft until every cell is terminal).
- **Host:** `skampere1`; work root `/lfs/skampere1/0/brando9/rl4cv_e05`; clone `$WORK/rl-4-code-verification`; status file `$WORK/STATUS_e05` (`RUNNING` / `DONE` / `BLOCKED`).
- **Health check (10-05-2026 17:58, `snap_health.sh --node skampere1`):** all job-relevant checks PASS; `disk.dfs` FAIL (DFS 100% used, 570 GiB free) is not on this job's path (all outputs on `/lfs`, 11.5 TiB free). WARNs: stale alternate `claude`/`codex` binaries (unused here).

## Timeline

- **10-05-2026 17:41** — baseline: `skampere1` GPUs 0–3, 5–7 idle; GPU 4 another user's (never touched). `skampere2`/`skampere3` unusable (disk full, GPUs busy).
- **10-05-2026 17:58** — design, protocol and code pushed as `b519487`; draft PR #4 opened.
- **10-05-2026 18:02–18:09** — preflight on GPU 7 (Qwen3-1.7B-Base, 5 tasks × 2 samples): **PASS**. Locked prompt hashes match; Base rendering byte-identical to post-trained Qwen3-1.7B on all 5 prompts; finish reasons 5 `stop` / 5 `length`; 10/10 scored; IC_tests and IC_proofs 0 on all 10. Receipt `expt_v1/results/preflight_qwen3-1.7b-base.json`.
- **10-05-2026 18:10** — full run launched (`launch_e05.sh all`): 1.7B on GPU 0 at once, 4B on GPUs 1,2 after 240 s, 8B on GPUs 3,5,6 after 480 s (shards staggered 180 s). 4B and 8B weights prefetched into the Hugging Face cache beforehand. GPU 0 confirmed at 100% utilization, 72 GB, at 18:12.
- **10-05-2026 18:15 (worker launch receipt)** — worker dispatched: client Claude Code (`clauded_tok`), host `skampere1`, model `claude-sonnet-5`, effort `high`, permission mode `--dangerously-skip-permissions`, tmux session `rl4cv-e05-worker`. Verified on arrival: `tmux list-windows -t rl4cv-e05-qwen3-base-g8` shows all 4 windows (`control`, `qwen3-1.7b-base`, `qwen3-4b-base`, `qwen3-8b-base`) alive; `qwen3-1.7b-base` generating on GPU 0 (100% util, 72 GB) at ~144/1,024 prompts of shard0of1; `qwen3-4b-base` shard0of2 generating on GPU 1 (started 18:14:17 per driver log); `qwen3-4b-base` shard1of2 (GPU 2) and `qwen3-8b-base` (GPUs 3, 5, 6) not yet started — expected, per the launcher's 180 s/240 s/480 s stagger, not a failure. GPU 4's 45–47 GB in use is another user's job (confirmed at the 17:58 health check), never touched. Taking over supervision now per `expt_v1/cc.md` §1.
- **10-05-2026 18:47** — routine check: all 6 generation shards across the 3 models running at 100% GPU utilization on GPUs 0,1,2,3,5,6 (GPU 4 still another user's, GPU 7 idle); 1.7B-base shard0of1 43% through its first 1,024-cell batch, 4B-base shards 86–88%, 8B-base shards 39–49%. No milestones or failures; no checkpoint-worthy event.
- **10-05-2026 19:07 (orchestration deviation, agents-config Trigger Rule 57; PROTOCOL.md unchanged)** — Qwen3-1.7B-Base on its single GPU (0) is the long pole (~9 h) while 4B/8B are on track to finish generating around 20:45. Master instructed a rebalance: freed GPUs (7 first, then 1,2,3,5,6 as 4B/8B finish, then 0 once shard 0 stops) generate 1.7B-base's not-yet-started 128-task blocks (= 1,024-cell batches) top-down, using the identical pack, prompt, decoding and per-sample seed formula (`91·100003 + k`, independent of task order, so reordering tasks across GPUs is bit-for-bit equivalent). Shard 0 is stopped by a watcher only once it finishes a block whose successor block is already claimed by a helper (anchored `pgrep` kills only shard 0's own `rl4cv.veribench.generate` process and descendants; never touches GPU 4 or another user's process); an exact 896 × 8 manifest merge follows (duplicates keep the first copy, never chosen by score), then the `qwen3-1.7b-base` window is restarted with `SCORE_PAR=8` for jobs/scoring/statistics (its generation stage is skipped once the merged file exists). Script reviewed line-by-line before running (anchoring, kill scope, block-claim races, merge correctness) and dry-run (`DRY=1`) first: `tasks 896, blocks 7 of 128 tasks; shard0 rows 0, current block 0; shard0 pid 615483; GPU 7 free; GPUs 1,2,3,5,6,0 busy with our own processes`, matching expectations. Committed as `expt_v1/rebalance_1p7b_e05.sh` and launched in tmux window `rebalance-1p7b` (session `rl4cv-e05-qwen3-base-g8`) on helper GPUs `7,1,2,3,5,6,0`. **Expected and not a failure:** the `qwen3-1.7b-base` window will end with `EXIT=1` when the watcher stops shard 0 at its block boundary — do not relaunch it; the rebalancer's own script restarts that window after the merge. Log `$WORK/logs/rebalance_1p7b.log`; claims under `$OUT/claims_1p7b/`.
- **10-05-2026 20:10 — Qwen3-4B-Base generation DONE.** `gen done: qwen3-4b-base_g8` at 20:09:57; merge exact (cells declared 7,168, generated 7,168, missing 0, extra 0, duplicate rows 0). Scoring started immediately (4 concurrent scorers, `qwen3-4b-base_g8_s0..s7` jobs). GPUs 1 and 2 freed and were claimed within seconds by the 1.7B-base rebalancer: GPU 1 → block 5 (tasks 640–767) at 20:09:50, GPU 2 → block 4 (tasks 512–639) at 20:09:56 (claims: `block4`, `block5`, `block6` under `$OUT/claims_1p7b/`). 1.7B-base shard 0 (GPU 0) has completed block 0 (1,024/1,024 rows) and is working its own block 1; no scorer errors or tracebacks found in any `gen_*`/`score_*` log.
- **10-05-2026 20:23 — Qwen3-8B-Base generation DONE.** `gen done: qwen3-8b-base_g8` at 20:23:02; merge exact (7,168 declared = generated, 0 missing/extra/dup). Scoring started immediately (4 concurrent scorers). GPUs 3 and 6 (freed by 8B-base's shard0of3/shard2of3) were claimed by the rebalancer for 1.7B-base blocks 2 (20:20:03) and 3 (20:13:11); GPU 5 (freed earlier by shard1of3) found no unclaimed block above shard 0's current block and exited cleanly at 20:23:07 — **by design**, not a failure: blocks 2–6 are now all claimed/running (block 6 at 86%, block 5 16%, block 4 14%, block 3 12%, block 2 12% of their 1,024-cell batches), leaving only blocks 0 (done) and 1 (shard 0, in progress on GPU 0) outstanding. Helper GPU 0 will join once shard 0 is stopped at the block-1→2 boundary, but by then every block will already be claimed, so it is expected to find nothing and exit immediately. No scorer errors or tracebacks in any log; `$OUT/scores/` still empty for 4B/8B (kernel scoring just started, CPU/Lean-compile-bound, ~2 h/job per PROTOCOL.md estimate).

## Running now

| tmux window (session `rl4cv-e05-qwen3-base-g8`) | GPUs | Job | Log |
|---|---|---|---|
| `qwen3-1.7b-base` | 0 | generate 7,168 cells → merge → jobs → score (4 concurrent) → collect/summarize/ρ-H | `$W/logs/driver_qwen3-1.7b-base.log`, `$W/out/logs/gen_qwen3-1.7b-base_g8.shard0of1.log` |
| `qwen3-4b-base` | 1, 2 | same, 2 shards | `$W/logs/driver_qwen3-4b-base.log`, `$W/out/logs/gen_qwen3-4b-base_g8.shard{0,1}of2.log` |
| `qwen3-8b-base` | 3, 5, 6 | same, 3 shards | `$W/logs/driver_qwen3-8b-base.log`, `$W/out/logs/gen_qwen3-8b-base_g8.shard{0,1,2}of3.log` |

## Resume

```bash
ssh skampere1
W=/lfs/skampere1/0/brando9/rl4cv_e05; cd $W/rl-4-code-verification
tmux list-windows -t rl4cv-e05-qwen3-base-g8; nvidia-smi; tail -n 5 $W/logs/driver_*.log
wc -l $W/out/raw/gen_*_g8.shard*.jsonl; ls $W/out/scores
# a window that ended with EXIT!=0: fix the cause, tmux kill-window -t rl4cv-e05-qwen3-base-g8:<name>, then:
bash experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1/launch_e05.sh all   # resumes; same GPU counts per model
```

Landing: `expt_v1/cc.md` §2–§3.
