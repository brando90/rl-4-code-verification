# Experiment 08 version 2 checkpoint — matched step-658 test evaluation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_e08v2.md>

**TLDR:** This is the resume record for version 2: a one-time test evaluation of 1.7B, 4B and 14B at step 658, so all four sizes are compared after identical SFT (same data, 658 updates, 5,752,936 tokens). The binding protocol is `PROTOCOL_v2.md` and the runbook is `cc.md`.

**Created:** 10-13-2026 17:02 PDT (Claude master). **Last updated:** 10-13-2026 17:30 PDT

## Goal
- Finish experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2: 5,328 new test cells, all ratings, matched four-size report and one DONE email.
## What ran
- One writer: tmux `codexv-rl4cv-e08v2-matched-test`, PID 2972470 (launcher 2972451), gpt-6-astra/high, full access/never, deployment deploy_e6c90b4a14374fbe81cb42a3fc065263.
- Published admission `25bbe01`; all inputs and fresh judge bundle hashes match. Full make test: 338 passed / 4 skipped in 293.84 s; command uses env -u CODEX_HOME and node-local Lean.
- GPU plan: 1.7B=4, 4B=1, 14B=2,3, ~70–75 GB/device, compute-bound, estimated 1–4 h/system; explicit CUDA_VISIBLE_DEVICES; shared leases released at merged generation. Devices 0/7 belong to others.
- Resumable drivers named `rl4cv-e08v2-test-<label>`; runtime `$WORK/v2`. Cron every 15 min + reboot; child-aware recovery and idle nudge self-tests PASS.
- Controls service: port 9860, claimed block 9860–9869; health/authentication verified, exact 25 control prompts; no judge calls yet.
## Results
- 0/5,328 new cells so far. All six reused-system summaries reproduce original values exactly; independent 108 factor/score checks PASS.
- Master START email 17:09 and worker START 17:18 (duplicate discovered only after upstream merge); START marker prevents another. DONE not sent.
## Stuck / blocked
- Initial generators failed before outputs: inherited CUDA_HOME=12.4. Environment-only recovery pins 12.8/private caches; all failed logs and identities retained. Verify live utilization next.
## Next steps
- [p 10/10] Publish prepared controls/scripts, then `.venv/bin/python expt_v2/scripts/judge_rl4cv_e08v2.py admit --suite rl4cv-e08v2-controls` (from experiment directory; repo-relative path otherwise).
- Supervise generation/scoring; after controls pass and 3/3 score files exist, build/freeze/publish test judge pack before admission, then run cc.md §§ 4–9.
- Local named resume copy: `$WORK/v2/CKPT_codexv-rl4cv-e08v2-matched-test.md`. Fallbacks from master: personal Codex, Vals Claude, personal Claude; allowance unknown. Judge ~$225 + ~$3 controls, Vals only.
## Brando to-do
- None.

## Log

- 10-13-2026 17:02 PDT -- master created the protocol, forecast, runbook and this checkpoint; dispatch next.

- 10-13-2026 17:12 PDT -- worker accepted deployment; version 1 writer check clear; baseline tests and input verification started.

- 10-13-2026 17:21 PDT -- inputs verified; full corrected make test 338 passed / 4 skipped; admission tests and fake-mail watchdog self-test pass; START email delivered.

- 10-13-2026 17:11 PDT -- master dispatched the worker (codex-vals gpt-6-astra high, full access verified, PID 2972451) and sent [RUN START]; runbook § 8 now adds the idle-nudge watchdog and the checkpoint location.

- 10-13-2026 17:22 PDT -- integrated master launch receipt/runbook update; preserving both logs. Master START email at 17:09 was learned after worker START at 17:18; no further START email. Canonical checkpoint here; launch-named local copy lives in $WORK/v2.

- 10-13-2026 17:23 PDT -- admission published at 25bbe01; GPU plan recorded before launch; idle-nudge self-test PASS; six reused-system summaries reproduce every original scope field exactly and independent 108 factor/score checks PASS (new cells still unknown).

- 10-13-2026 17:23 PDT -- launch recheck found other users on GPUs 0 and 7; 1.7B guard rejected GPU 0, so its zero-cell launch is moved to idle GPU 4. Other users untouched.

- 10-13-2026 17:28 PDT -- initial generators failed before any output (nvcc 12.4 rejects --compress-mode); environment corrected to CUDA 12.8, fixed sampling unchanged. Resume 1.7B/4B now; let 14B initialization finish/fail before identical resume.

- 10-13-2026 17:30 PDT -- controls deployed with exact prompts; full make test 338 passed / 4 skipped in 293.84 s; all three CUDA-environment resumes initiated, failed attempts retained. Publishing controls/scripts before the first judge call.
