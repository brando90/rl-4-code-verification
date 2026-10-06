# Run and land experiment 05 (Qwen3 Base 1.7B/4B/8B, VeriBench V1, G=8) on skampere1

**TLDR:** You supervise experiment 05 on `skampere1` until every one of its 21,504 declared cells (3 Qwen3 Base models × 896 VeriBench V1 tasks × 8 samples) is generated and kernel-scored, then run the analysis, publish `results.md` with the per-model verdict ("SFT warm start needed" if the `kernel_binary` mixed-group share is below 0.05, "RL from Base viable" at 0.20 or more, otherwise "marginal"; Qwen3-1.7B-Base decides), and land the work. The deliverable is the merged pull request on branch `e05-qwen3-base-vbv1-g8-sft-derisk` plus an email to brando.science@gmail.com. Never change the locked protocol (prompt, decoding, scorer, thresholds), never re-sample a cell because of its score, and never touch another user's GPU or experiment 01's files (read-only). Read `~/agents-config/INDEX_RULES.md` first.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Context

- **Why.** At the 10-05-2026 meeting Varun asked for this de-risking run before any RL: sample G=8 from Qwen3 Base 1.7B/4B/8B on VeriBench V1 and check whether tasks pass "more than 0 out of 8 but not 8 out of 8". Read the experiment's `README.md` and `PROTOCOL.md` (locked) before acting.
- **Work root.** `WORK=/lfs/skampere1/0/brando9/rl4cv_e05`; repository clone `$WORK/rl-4-code-verification` on branch `e05-qwen3-base-vbv1-g8-sft-derisk` (you are its only writer). Experiment folder `EXP=$WORK/rl-4-code-verification/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk`.
- **Environment.** `source $WORK/env_e05.sh` (written by `launch_e05.sh`): experiment 01's vLLM venv, pack, Lean project and scorer, all read-only. Raw outputs go to `$WORK/out`, logs to `$WORK/logs`. Raw generations and scored JSONL stay on the host; commit only summaries.
- **Execution.** `bash $EXP/expt_v1/launch_e05.sh all` runs tmux session `rl4cv-e05-qwen3-base-g8` with one window per model (`qwen3-1.7b-base` on GPU 0, `qwen3-4b-base` on GPUs 1,2, `qwen3-8b-base` on GPUs 3,5,6). Each window runs `run_model_e05.sh`: sharded generation → merge with an exact 896 × 8 manifest check → scorer jobs → frozen-scorer kernel scoring (4 concurrent per model) → collect → summarize → ρ/H. Re-running the launcher resumes; it refuses to start a second writer for a live window. GPU 4 belongs to another user: never use it.
- **State on dispatch.** `$EXP/expt_v1/CKPT_e05.md` says what the master already did (preflight, launch time). Read it first, then `tmux list-windows -t rl4cv-e05-qwen3-base-g8`, `nvidia-smi` and `tail -n 20 $WORK/logs/driver_*.log`.

## 1. Supervise until every cell is terminal

Check every 20–30 minutes (use a background wait or `sleep` loop so you are re-invoked; do not end the task while work remains):

- **Progress:** rows per shard (`wc -l $WORK/out/raw/gen_*_g8.shard*.jsonl`), finished jobs (`ls $WORK/out/scores`), driver log tails, `nvidia-smi` (our processes only on GPUs 0–3, 5–7).
- **Failures:** a window whose log ends in `EXIT=` non-zero needs diagnosis. Infrastructure retries rerun the identical cells (generation resumes from its shard file; an interrupted scorer's partial directory is moved aside, never deleted, and the identical job reruns): fix the cause, close the dead window (`tmux kill-window`), and re-run `launch_e05.sh all`. Keep the shard count per model unchanged (the script enforces it). If a GPU process dies and leaves memory allocated, kill only our orphaned `EngineCore` PIDs (`nvidia-smi --query-compute-apps=pid,used_memory --format=csv`) and confirm the memory is freed before relaunching.
- **Abort rule (PROTOCOL.md):** stop new generation and diagnose if more than 20% of a model's first 500 cells show an extraction or transport error not explained by the model's own output, or a scorer crash repeats on retry. Record it; keep every affected cell in the denominator as unmeasured.
- **Ledger:** at every milestone (a model's generation done, a model's scoring done, any incident) update `$EXP/expt_v1/CKPT_e05.md` (timestamps `MM-DD-YYYY HH:MM`, current stage per model, tmux names, exact resume command) and `$EXP/results.md` (`**Last updated:**`, phase table, numbers so far), then commit with explicit pathspecs and push the branch.

## 2. Analyze and publish

When all three windows report `done: <label>_g8`:

1. Copy the small summaries into the repository: `cp $WORK/out/summaries/{summary,rho_h}_qwen3-*-base_g8*.json $EXP/expt_v1/results/` and the preflight receipt `$WORK/out/preflight/preflight_qwen3-1.7b-base.json`.
2. Run the analysis (experiment 01's post-trained G=8 rows give the paired comparison on its 128-task subset):

   ```bash
   source $WORK/env_e05.sh; E01OUT=/lfs/skampere1/0/brando9/rl4cv_e01/out
   python $EXP/expt_v1/analyze_e05.py --task-ids $TASK_IDS --probe-ids $E01OUT/probe_task_ids.txt \
     --base qwen3-1.7b-base=$OUT/scored/scored_qwen3-1.7b-base_g8.jsonl qwen3-4b-base=$OUT/scored/scored_qwen3-4b-base_g8.jsonl qwen3-8b-base=$OUT/scored/scored_qwen3-8b-base_g8.jsonl \
     --post-trained qwen3-1.7b-base=$E01OUT/scored/scored_qwen3-1.7b_g8.jsonl qwen3-4b-base=$E01OUT/scored/scored_qwen3-4b_g8.jsonl qwen3-8b-base=$E01OUT/scored/scored_qwen3-8b_g8.jsonl \
     --out-dir $EXP/expt_v1/results
   ```
3. Write `results.md`: status DONE, the headline table from `analysis_e05_table.md`, the execution table per model (declared/scored cells, cut off at 12,288, no Lean extracted, compiling cells, mean generated tokens, IC_tests and IC_proofs means, SCSC exact or the listed unmeasured cells), the pass-count histograms, core 614 and IndustrySet 282 separately, ρ/H, the paired comparison with experiment 01 (Base minus post-trained mixed share with its interval and exact McNemar p-value), and the verdicts read against the locked thresholds. Report every prespecified statistic, flattering or not; write `x [lo, hi] p-val=Z` with the test named. Quote two or three representative completions (first 15 lines) to show what the Base models actually write. End with `**TLDR-end:** [rl4cv: 05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk] …`.
4. Update the README status table and the experiment 05 row in `experiments/README.md` (state and next action: Varun's warm starts as `expt_v2` once D-105 resolves, if the verdict is "SFT warm start needed").

## 3. Land (agents-config Trigger Rule 46; no QA tier was requested)

1. `make test` must pass (`source $WORK/env_e05.sh; cd $WORK/rl-4-code-verification; python -m pytest -q`). Inspect `git diff --cached` and the file list before every commit (no secrets, no raw generations); stage explicit pathspecs only.
2. Push the branch, `gh pr ready <n>`, then fetch `origin/main`. If `main` moved: record the backup branch name, old merge base and fetched main commit in the checkpoint, `git branch <backup> HEAD`, rebase onto `origin/main`, review `git range-diff` and `git diff <backup> HEAD -- experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk`, re-run `make test`, and publish with `git push --force-with-lease=refs/heads/<branch>:<previous-remote-commit> origin HEAD:refs/heads/<branch>` (never force `main`).
3. Merge only the verified commit: `gh pr merge <n> --rebase --match-head-commit <verified-sha>`; confirm `gh pr view <n> --json state,mergeCommit,url` says `MERGED`. Then delete the remote branch with `git push --force-with-lease=refs/heads/<branch>:<verified-sha> origin :refs/heads/<branch>` and verify with `git ls-remote --exit-code --heads origin refs/heads/<branch>` (exit 2 = gone).
4. Email one message to `brando.science@gmail.com` (no CC), subject `[rl4cv] PR #<n> merged: <title>`, body = PR URL, the TLDR with the three verdicts, `git diff --stat` of the PR, and the ledger and CKPT paths — sent with `uutils.emailing.send_email_smtp(..., smtp_pass_file="~/keys/gmail_app_password.txt")`. No interpreter on `skampere1` imports `uutils` yet: create one (`uv venv $WORK/mail_venv && uv pip install --python $WORK/mail_venv/bin/python ultimate-utils`, or put a local `ultimate-utils` checkout's source on `PYTHONPATH`), verify `python -c 'from uutils.emailing import send_email_smtp'` (sends nothing), then send. If delivery fails, record the error and the pending receipt in the checkpoint; never report an email as sent without a successful send.
5. Signal the master through git: on `main`, append `LANDED <merged-commit> <PR URL> <MM-DD-YYYY HH:MM>` to `CKPT_e05.md`, set `results.md` status DONE, commit (docs only) and push to `main` after `git pull --ff-only` (the repository allows direct pushes to `main`; never force-push).
6. Clean up: no process of ours on any GPU (`nvidia-smi`), close the tmux windows, write `DONE` to `$WORK/STATUS_e05`.

If the task is blocked (a real blocker you cannot route around), write `BLOCKED` to `$WORK/STATUS_e05`, describe it in the checkpoint and the PR, email `[rl4cv] PR #<n> blocked: <title>`, and stop; the PR stays open.

## 4. Full-set completion (agents-config Trigger Rule 61)

- Every declared cell needs a terminal receipt: generated and scored, or explicitly failed/unmeasured with its reason. Failed, cut-off and unmeasured cells stay in the denominator.
- Do not stop because results look good or bad, after one model, or because the GPUs look idle during scoring. A smoke pass is not a completed evaluation.
- The frozen single-call prompt does not contain the agents-config solver completion reminder; adding it would create a new condition, so do not add it (as in experiment 01).
- Solve the entire assigned task, including every required file, question and subtask. Produce the complete required deliverable in the specified output location or response format; an outline, partial draft, progress report or claim of completion is not a substitute. Write/save the output, inspect the actual saved artifact or final response, and run the allowed checks, tests or compilation required by the task. Within the declared time, token, call and tool limits, continue working and fixing errors until the requirements are met or a declared terminal condition is reached. Follow the fixed continuation procedure without resetting budgets. If anything remains unresolved, preserve the best current deliverable and report the exact remaining failures and checks that did not pass; never claim success or invent verification.

## 5. Guardrails

- VeriBench is held out: nothing here trains, tunes or selects on it. No FSC judge, no provider API calls, no spend.
- Never edit `PROTOCOL.md`; deviations go to `results.md` → "Deviations and open questions".
- Never modify experiment 01's work root or `veribench_vb103`; never touch GPU 4 or other users' processes.
- Expand acronyms on first use in `results.md`; dates `MM-DD-YYYY`.

TL;DR: Supervises the three-model vLLM generation and frozen-scorer Lean kernel scoring already running in tmux on `skampere1`, runs `analyze_e05.py`, publishes `results.md` with the SFT-warm-start verdicts, merges the experiment 05 pull request and emails brando.science@gmail.com.
