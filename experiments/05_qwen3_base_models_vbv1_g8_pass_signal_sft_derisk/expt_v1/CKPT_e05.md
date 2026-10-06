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
