# Dispatch brief: run experiment 01 (small Qwen models on VeriBench V1, single call + G=8 probe) on skampere1

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Dispatched:** 09-30-2026 by the master session on Brando's laptop (Claude Opus 5.5), after Brando said "run my experiments on snap!". Worker: `clauded` (personal profile), `claude-sonnet-5`, effort `high`, full access, tmux session `rl4cv-e01-qwen-vbv1-baseline` on `skampere1`, Remote Control name `rl4cv-e01-qwen-vbv1-baseline`.

## What to do

1. Read `~/agents-config/INDEX_RULES.md`, then clone the repo into the work root and read its `CLAUDE.md`, `experiments/01_small_open_models_veribench_v1_single_call_baseline/{README.md,PROTOCOL.md,results.md}` and GitHub issue #3 (`gh issue view 3 -R brando90/rl-4-code-verification --comments`).
2. Follow `scripts/cc_prompt_run_experiment_on_snap.md` (the launcher), then carry out `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md` end to end on this host. The protocol is locked. Never change the prompt, extraction, scorer or sampling settings.
3. Work root: `WORK=/lfs/skampere1/0/brando9/rl4cv_e01` (cc.md's name). Clone the repo to `$WORK/rl-4-code-verification`. Raw generations stay under `$WORK`; commit summaries only.

## Decisions already made (do not re-ask)

- **Host = skampere1, not the B200/H200 hosts.** Baseline at dispatch (09-30-2026):
  - skampere3 (8× B200): `/lfs` 100% full (21 GB free), and 7 of its 8 GPUs are busy with other users.
  - skampere2 (8× H200): `/lfs` 100% full (99 GB free), and GPUs are shared with 4 other users.
  - skampere1 (8× A100-SXM4-80GB): 15 TB free on `/lfs`, 128 cores, GPUs 3–7 idle (0 MiB, 0%); GPUs 0–2 belong to user `truongvo`, so never touch them. Experiment 103's v6 pack is also here.

  Record this in the inventory file as "GPU rule (B200 → H200 first) not met: disk full and GPUs busy". Re-verify free GPUs right before each launch.
- **Go is given.** Brando's "run my experiments on snap!" (09-30-2026) plus his earlier "just do the experiment ... Go" cover experiment 01's full GPU run.
  - Write the compute estimate into `results.md` → "Compute estimate", post it as a comment on issue #3, then launch without waiting.
  - This satisfies cc.md §5 "Ask".
- **Inputs for cc.md §3.** Experiment 103's gated v6 pack is `/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896`, and the id list is `.../private/task_ids_vbv1.txt` in the same `private/` folder.
  - Verify the SHA-256, the `agent-spec v6` stamp and the count of 896.
  - A candidate grading project is `/lfs/skampere1/0/brando9/veribench_vb103/veribench_dataset/lean_src`. Use it only if `lake env lean` on a gold file exits 0 with Lean v4.22.0. Otherwise build per cc.md §3.2 (`lake exe cache get`, never `lake build` of Mathlib).
  - Treat `veribench_vb103` as read-only.
- **GPUs.** Use one model per free GPU in parallel across GPUs 3–7, at most one GPU job per device (`export CUDA_VISIBLE_DEVICES=<id>` for each).
  - Admit models smallest to largest.
  - The Qwen3.6-27B route control may need `tp=2` on 80 GB. If so, record it as a deviation.
  - Check with `nvidia-smi` within minutes of each launch.
- **Durability.** Put the GPU work in a driver script (for example `$WORK/run_all_e01.sh`) that runs in its own tmux sessions (`rl4cv-e01-gen-<label>`) and keeps going without you.
  - Wait on it with a background command so you are re-invoked when it finishes.
  - Ending a turn while jobs run is fine. A watchdog (below) nudges you when jobs stop and your checkpoint goes stale.
- **Publishing.** The repo `CLAUDE.md` (09-30-2026) overrides cc.md §7.5's draft pull request (PR): commit summaries directly to `main` with explicit pathspecs after `make test` passes, pull `--ff-only` first, and never force-push.
  - Post the results and the gate G1 verdict as a comment on issue #3.
  - Commit this brief as `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/DISPATCH_e01.md` with your first commit.
- **FSC.** D-102 is still open. Report FSC as "unmeasured (D-102)" and do not run any judge.
- **Launcher Lean line.** Launcher §4 says `lake build`; use cc.md §3.2's cache method instead and leave the launcher file alone. Another session owns it.
- **Experiments 02/03/07 are out of scope.** They wait on gate G1 from this run and on Brando's decisions D-103–D-105. Report the G1 verdict with its numbers so he can decide.

## Full-set completion (agents-config Trigger Rule 61)

- **Every declared cell.** Run every declared model × task × sample cell:
  - 9 models × 896 tasks at G=1;
  - 8 models × ≤132 probe tasks × 8 samples.
- **Receipts and denominators.** Each cell needs a terminal receipt: generated/scored, or explicitly failed/unmeasured with the reason. Failed, truncated and unmeasured cells stay in the denominator.
- **When to stop.** Do not stop early because results look good or bad, or after one clean model. Do not re-sample on score.
- **Locked prompt.** Experiment 103's frozen single-call prompt does **not** contain the agents-config solver completion reminder. Adding it would create a new condition, so do not add it. Note this in `REPORT.md`.
- **Unrecoverable cells.** If a model cannot load or a cell cannot finish, record the deviation in `REPORT.md` → "Open questions for Brando" and continue with the unaffected cells (cc.md §0).

## State files the watchdog reads

- `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01.md`:
  - update it at every stage change (start time, current model/stage per GPU, tmux session names, next resume command);
  - timestamps in `MM-DD-YYYY HH:MM`.
- `$WORK/STATUS_e01` holds one word:
  - `RUNNING` while work remains;
  - `DONE` only after every cell is terminal, the results are committed and pushed, and your GPU processes are cleaned up (`nvidia-smi` shows none of yours);
  - `BLOCKED` only for a real blocker you cannot route around, written up in the checkpoint and on issue #3.

  Write `RUNNING` now.

## Watchdog

The master runs `$WORK/watchdog_e01.sh` in tmux session `rl4cv-e01-watchdog`, every 10 minutes:

- **Heartbeat.** It writes `$WORK/watchdog_e01.state`.
- **Dead worker.** If your process is gone, it relaunches you with a resume prompt, at most 3 times.
- **Idle worker.** If no GPU or scorer jobs are running and the checkpoint has not changed for 45 minutes, it types a nudge into your session, at most once an hour and at most 24 times.
- **Notifications.** It posts relaunches, stalls, `DONE` and `BLOCKED` to issue #3.
- **Stopping.** It stops on `DONE` or `BLOCKED`.

Do not kill it.

## Resume rule

If you were relaunched, read `CKPT_e01.md` first. Check `tmux ls` and `nvidia-smi`, and never start a second copy of a generation or scoring stage that is still running (one writer per job). Generation and scoring resume on their own; job and score directories are write-once.
