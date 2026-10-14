# Experiment 08 version 2 worker runbook — matched step-658 test evaluation (SNAP, skampere1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/cc.md>

**TLDR:** You are the only writer for experiment 08 version 2 on skampere1. Run a one-time test evaluation of the 1.7B, 4B and 14B step-658 checkpoints on the VeriBench V1 test split: 222 tasks × 8 samples each, with version 1's exact generation, kernel scorer and validated judge. Then publish one matched table with all four sizes at the same 5,752,936 SFT tokens next to their Base models. Success means all 5,328 new cells and all their judge ratings are known (or explicitly listed as missing), the analysis is published on `main`, and you have sent the `[RUN DONE]` email. Version 1's files stay byte-identical.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

Solve the entire assigned task, including every required file, question and subtask. Produce the complete required deliverable in the specified output location or response format; an outline, partial draft, progress report or claim of completion is not a substitute. Write/save the output, inspect the actual saved artifact or final response, and run the allowed checks, tests or compilation required by the task. Within the declared time, token, call and tool limits, continue working and fixing errors until the requirements are met or a declared terminal condition is reached. Follow the fixed continuation procedure without resetting budgets. If anything remains unresolved, preserve the best current deliverable and report the exact remaining failures and checks that did not pass; never claim success or invent verification.

## Binding inputs

- `expt_v2/PROTOCOL_v2.md` (LOCKED; binding) and the frozen forecast `expt_v2/forecasts/e08v2_matched_step658_test.json`. Its SHA-256 is `cb6661ddce51b9cc4df7746cac19043d0e535bea406fe4aa94d583eeea8a592d`; check it with `rl4cv.forecast.verify_forecast`.
- `../PROTOCOL.md` §§ 3, 9, 10 and 14; version 1 reuses these rules unchanged.
- Version 1's code under `../expt_v1/scripts/` is the reference implementation. Its final runtime record is `../expt_v1/CKPT_e08.md`, and `../results.md` (top section) has the final numbers and transport fixes.
- Work root `WORK=/lfs/skampere1/0/brando9/rl4cv_e08`: `env_e08.sh`, `venv_gen`, `grading/lean_src`, `cache/huggingface`, `private/`, `ckpt/`. The repository clone is `$WORK/rl-4-code-verification`. Put all version 2 runtime state under `$WORK/v2/`.
- The binding limits are listed at the end of this file.

## 0. Start

1. Run `git -C ~/agents-config pull --ff-only`, then read `~/agents-config/INDEX_RULES.md`, the repository `CLAUDE.md`, `PROTOCOL_v2.md` and this file.
2. Confirm that nothing from version 1 is still writing. Run `tmux ls | grep -i e08`, `pgrep -af 'pipeline_e08|run_ladder_e08|judge_rl4cv_e08'` and `cat $WORK/STATUS_e08`, which should say `DONE`. If any version 1 writer is alive, record it in the checkpoint and stop.
3. Experiment 13 v2 runs on this node under a separate owner (`codex-rl4cv-e13v2-owner`). Never touch its processes, files, ports, GPUs or cron lines. The same applies to every other user's work.
4. In the clone, run `git pull --ff-only` until `HEAD` contains this runbook. Then `source $WORK/env_e08.sh` and run `make test` with the clone's `.venv` and `VERIBENCH_ROOT=external/veribench`. Fix only environment problems, and record them.
   - Current tests need `scipy` and `psutil`: `uv pip install --python .venv/bin/python scipy psutil`.
   - Known failure you inherit: on skampere1 at `origin/main` `6174f02`, before any version 2 change, `make test` gives 330 passed, 4 skipped, 2 failed. Both failures are experiment 13 v2's live owner's tests: `tests/test_e13_v2_watchdog.py::test_concurrent_recovery_starts_one_process` and `::test_orphaned_child_is_adopted_without_relaunch`. Do not edit experiment 13's code. Treat `make test` as passing when exactly those tests fail (or they pass) and everything else passes. Record the counts with every push.
5. Update `expt_v2/CKPT_e08v2.md`: edit the state block and append one log line. It should give your session name, PID, the effective model and effort, the permission mode and your first action. Commit and push it.

## 1. Check the inputs (no model calls)

- Recompute the weight-manifest SHA-256 for the three new exports, using the same method version 1 used to write `weights_sha256_manifest` in `../expt_v1/results/ladder_manifest.json` (see `make_ladder_manifest_e08.py`). Each must equal its value in PROTOCOL_v2 § 3.
- Check that the test task list hashes to `303a6c66…` and that the forecast's hash verifies.
- Write `expt_v2/results/inputs_check.json`. If any check fails, that is a real blocker: record it and stop without generating.

## 2. Freeze the manifest and the admission check before any generation

- Write `expt_v2/results/test_manifest_v2.json`. It lists the three new systems (label, `hf_path`, step 658, 5,752,936 tokens, weight hash) and the reused systems, each with a pointer to its version 1 artifacts. It also records 5,328 new declared cells, 14,208 matched declared cells, the task-id hash, the protocol file's SHA-256 and the forecast's SHA-256.
- Add `expt_v2/scripts/test_admission_e08v2.py`. It must verify that `PROTOCOL_v2.md` and `test_manifest_v2.json` are the exact published files on `origin/main`, that the label and model path are in the manifest, and that the weight hash matches. It must reject everything else.
- Add `expt_v2/scripts/run_test_e08v2.sh`, a copy of `run_ladder_e08.sh` that changes only the admission call. Record the change in `expt_v2/scripts/run_test_e08v2.diff`. Do not edit version 1 scripts.
- Add tests under `tests/` for the admission check: it rejects a label outside the manifest, a hash mismatch and an unpublished manifest. Run `make test`, then commit and push the manifest, scripts and tests. Generation may start only after that push.

## 3. Generation and kernel scoring (identical to version 1)

- **GPU plan (record it in the checkpoint before launching).**
  - Read `nvidia-smi` and `$WORK/pipeline/leases.json`, and use `gpu_lease_e08.py`-style leases.
  - Give 1.7B one idle device, 4B one, and 14B one or two (data-parallel shards).
  - Use idle devices only. Never take a device that another user's process is on.
  - Export `CUDA_VISIBLE_DEVICES` explicitly, and confirm real utilization with `nvidia-smi` within five minutes.
- **Launching.** Run each system in its own named tmux session, `rl4cv-e08v2-test-<label>`:

  ```bash
  SCORE_PAR=4 bash expt_v2/scripts/run_test_e08v2.sh test <label> <hf_path> local <gpu_csv> 1
  ```

  These are ordinary-code drivers that keep running if you die, and they resume. Run the systems concurrently if devices allow; otherwise run them in sequence.
- **Releasing devices.** Release each device as soon as its merged generation file exists.
- **Completion per system:** 1,776 of 1,776 generated cells joined exactly to the manifest (no missing, duplicate or extra cells), 8 of 8 score shards, and the scored file collected. Infrastructure failures re-run the identical cell; never re-sample.
- **Kernel analysis.** Run `analyze_ladder.py --manifest expt_v2/results/test_manifest_v2.json --split test --out expt_v2/results/test_ladder_kernel_v2.json --no-selection`, adapting paths only. Publish it, and update `expt_v2/results.md` as each system lands.

## 4. Judge: formal specification coverage (version 1's route and settings)

- **Before the first call (D-108):** verify the Vals route on this host (organization, credential source, payer) and that the three `vb103_judge` bundle files match version 1's frozen hashes. Record only non-secret evidence in the checkpoint and in `expt_v2/results/route_identity_v2.json`.
- **Judge script.** Copy `judge_rl4cv_e08.py` to `expt_v2/scripts/judge_rl4cv_e08v2.py`, keeping its state under `expt_v2/results/judge/`.
  - Suites: `rl4cv-e08v2-controls` and `rl4cv-e08v2:<system>`. Benchmarks: `veribench-rl4cv-e08v2-controls` and `veribench-rl4cv-e08v2-test`.
  - Keep version 1's transport fixes: the interpreter directory and `valk` on `PATH`, the `lean`/`lake` launchers, and task-ID slicing so admission URLs stay under the transport limit.
- **Ports.** Claim a free port block (check with `ss -ltn` and existing claims) and record it.
- **Route controls first.** Use the same train-file control pack and thresholds as version 1. If the controls fail, judging is not admitted: record the blocker and go to § 7 with status `partial`.
- **Test pack.** Build it from every new cell with IC_tests = 1, plus the same 60 audit cells per system (the `rl4cv-e08-audit-v1:` ranking), with 3 ratings × 2 members each. Freeze and publish the pack manifest before admission.
- **Running it.** Admit, poll, harvest and compute `fsc` per system.
  - Every declared rating must end terminal. Reconcile identities as (system, task_id, sample_idx, rating_idx).
  - Keep failed attempts. Follow the two-request limit and never resend a request that was possibly served.
  - Record the reported charges.

## 5. Analysis (PROTOCOL_v2 § 6)

- Write `expt_v2/scripts/analyze_test_v2.py`, adapted from `analyze_test.py`. It reads the new cells plus version 1's reused cells and ratings without altering them. It writes:
  - `expt_v2/results/test_eval_v2.json`;
  - `expt_v2/results/test_factor_cells_v2.csv`, covering the eight matched systems plus the flagged 14B step-334 diagnostic.
- **Regression check:** recomputing the reused systems must reproduce version 1's `test_eval.json` values exactly.
- **Independent check:** a separate small summarizer must reproduce every factor mean and SCSC.
- **Forecasts:** run `verify_forecast` first, then score F1–F3 into `expt_v2/results/forecast_evaluation_v2.json`. Report failed forecasts exactly like passing ones.
- **Reporting:** use Hard Rule 11 form, `x [lo, hi]` with `p-val=n/a`, and give measured/declared counts, all/core/IndustrySet, and every unknown cell.

## 6. Publish

- Write the final section of `expt_v2/results.md`. Lead with one setup/status sentence, then the matched table (four trained sizes at step 658 and four Base, with all three factors and n), the SFT − Base paired differences, the scaling table, the version 1 14B step-334 diagnostic, the forecast scores, charges and counts.
- Add a short pointer section at the top of `../results.md`, leaving every version 1 section unchanged. Update the status lines in `../README.md`, row 08 of `experiments/README.md` and `expt_v2/CKPT_e08v2.md`.
- Run `make test` and `git diff --check`. Confirm `git diff origin/main -- experiments/08_*/expt_v1/` is empty. Stage explicit paths only, commit to `main`, pull with `--ff-only` and push.

## 7. `[RUN DONE]` email — you send exactly one

- **When.** Send it after § 6 is pushed and verified, or at any terminal failure or block (status `failed` or `partial`, with the blocker). Skip it if the marker `$WORK/v2/DONE_EMAIL_SENT` exists; write that marker right after a successful send.
- **Sending.** Use `uutils.emailing.send_email_smtp(..., from_addr="brandojazz@gmail.com", smtp_pass_file="~/keys/gmail_app_password.txt")`. If `uutils` is missing, install `ultimate-utils` into `$WORK/v2/venv_mail`. Never print the password file.
  - If SMTP fails, try SNAP `mail` to the same recipients.
  - If that fails too, save the email with `get_notifier(dry_run=True)` and record it in the checkpoint.
- **Recipients.** To: `brando.science@gmail.com`. CC: `brandojazz@gmail.com, brando9@stanford.edu, brando@vals.ai, vmadan@stanford.edu, rakshitk@stanford.edu, emxia18@stanford.edu, eth127@stanford.edu`.
- **Subject:** `[RUN DONE] e08v2 matched step-658 test (1.7B/4B/8B/14B): <success|partial|failed>`.
- **Body.** Plain text in Brando's first-person voice, kept short:
  1. what ran and its wall time;
  2. all-task SCSC [95%] for each size at step 658 with n = 1,776, next to its Base;
  3. the SFT − Base differences and whether the forecasts passed;
  4. the commit URL of `expt_v2/results.md`;
  5. any failure, with the next step.

  Because the team is CC'd, end with "Please keep my CC'd inboxes on replies so my agents can follow the thread.", then `Brando (drafted with Codex)` and the signature from `~/agents-config/email-signature.md`.

## 8. Watchdog and continuation (Rules 44, 48 and 69)

- **Host watchdog (no model calls).** Install one with cron every 15 minutes plus `@reboot`, tagged `e08v2`. It checks:
  - your tmux session and the per-system sessions;
  - progress freshness (log and partial-score modification times);
  - disk space.

  When a generation or scoring driver dies, it relaunches the identical resumable command once per incident. When your session dies or blocks, or nothing progresses for more than 2 hours, it emails `brando.science@gmail.com` only (no CC), deduplicated. When `$WORK/v2/STATUS_e08v2` says `DONE`, it removes its own cron lines.
- **Test the watchdog** with a fake mailer and one harmless simulated failure before relying on it. `../expt_v1/scripts/watchdog_e08.sh` is the pattern to copy.
- **Near a context or usage limit,** update the checkpoint with the exact next command and stop cleanly. The master relaunches from the checkpoint. Keep one writer.

## 9. Teardown

Stop your judge services and tunnels, free your ports, release every lease and GPU, and remove only your own cron lines. Check `pgrep` for leftover children, then write `$WORK/v2/STATUS_e08v2` = `DONE` (or the terminal status). Update the checkpoint, then commit and push.

## Binding limits

- Version 1 files stay byte-identical. Each new checkpoint gets exactly one test evaluation. No test outcome may change training, selection, sampling, settings or the manifest.
- Never loosen the verifier or scorer: axioms only within {`propext`, `Classical.choice`, `Quot.sound`}, and `--skip-tc`. FSC comes only from `vb103_judge` and is compile-gated.
- Model calls go only through the Vals-funded Valkyrie judge route. No personal credits, provider keys or `.env` copies. Never print or commit secrets.
- Preserve every failed attempt, retry and receipt. Unknown cells stay in the denominator.
- Leave other users' and other experiments' work alone.

TL;DR: Freeze the version 2 manifest and admission check, then generate and kernel-score 1.7B, 4B and 14B at step 658 on the 222 test tasks × 8 with version 1's exact settings. Judge them with the validated Vals route, publish the matched four-size table on `main`, and send the one `[RUN DONE]` email with the team CC'd.
