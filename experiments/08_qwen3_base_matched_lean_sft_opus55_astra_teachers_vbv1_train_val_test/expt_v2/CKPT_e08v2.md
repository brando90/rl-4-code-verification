# Experiment 08 version 2 checkpoint — matched step-658 test evaluation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_e08v2.md>

**TLDR:** This is the resume record for version 2: a one-time test evaluation of 1.7B, 4B and 14B at step 658, so all four sizes are compared after identical SFT (same data, 658 updates, 5,752,936 tokens). The binding protocol is `PROTOCOL_v2.md` and the runbook is `cc.md`.

**Created:** 10-13-2026 17:02 PDT (Claude master). **Last updated:** 10-13-2026 17:49 PDT

## Goal
- Complete the matched step-658 evaluation; this attempt closed PARTIAL at the runbook route-controls gate.
## What ran
- Worker: tmux `codexv-rl4cv-e08v2-matched-test`, PID 2972470 (launcher 2972451), gpt-6-astra/high, full access/never; deployment deploy_e6c90b4a14374fbe81cb42a3fc065263.
- Manifest/admission published before generation at 25bbe01; all hashes verified; frozen judge bundle 3/3 exact.
- CUDA 12.4 startup failed without cells; identical environment-only resumes used CUDA 12.8. Real inference ran on GPUs 4 (1.7B), 1 (4B), 2/3 (14B).
- Two control admissions rejected unserved, zero tracker runs. Supported current CLI authenticates to BrandoMiranda-fellow but managed AWS is unavailable (HTTP 403), Daytona mapping absent.
- Runbook §§4/7 terminal partial closeout: stopped 14 owned processes, own service/tunnel, released leases/port claim, removed only two own cron lines. STATUS_e08v2=PARTIAL.
## Results
- 0/5,328 new generations persisted before the first batch returned; all 5,328 cells remain unknown. Reused matched 8,880 cells and diagnostic 1,776 retain original factors.
- All six reused summaries reproduce exact v1 scope fields; terminal independent 108 factor/score checks PASS; reused 8B paired metrics also exact.
- Control ratings 0/50; fixed-audit ratings 0/1,080; additional eligibility unknown for 5,328 cells. No model request admitted, no charge receipts. Forecasts unresolved.
- Terminal full make test: 338 passed / 4 skipped in 293.25 s; Python compilation and git diff --check PASS.
- START duplication discovered after upstream merge (master 17:09, worker 17:18); no further START. DONE not sent yet.
## Stuck / blocked
- Vals-side managed AWS/Daytona restoration needed for the existing organization; see `results/judge_route_blocker_v2.json`.
## Next steps
- [p 10/10] Terminal report/analysis verified; publish explicit paths, send one required PARTIAL DONE email, then commit its receipt.
- Resume only after route repair: reverify Vals payer/frozen bundle and supported CLI/service registration; archive positively unserved control entries before a bounded identical admission. Never replay a possibly served rating.
- Preserve the exact published generation manifest/protocol and shard layouts. Existing drivers resume with GPUs 4 / 1 / 2,3 only after rechecking idle devices and leases; do not take another owner's GPU.
- Canonical checkpoint here; local named copy `$WORK/v2/CKPT_codexv-rl4cv-e08v2-matched-test.md`; every failed attempt remains under `$WORK/v2`.
## Brando to-do
- Have Vals restore managed AWS access and the existing Daytona configuration for BrandoMiranda-fellow before resuming.

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

- 10-13-2026 17:37 PDT -- all four assigned GPUs doing inference; controls admission failed because server lacks a Daytona mapping after service migration. Preserved both failed entries; diagnosing supported CLI with existing credentials, no new judge call.

- 10-13-2026 17:45 PDT -- confirmed terminal Vals-side managed AWS blocker via supported CLI; zero admitted control runs. Followed runbook partial closeout, stopped only owned jobs/services, released resources, retained all unknowns and failed attempts; terminal analysis/tests/publication next.

- 10-13-2026 17:38 PDT -- master (Claude, laptop) handing off: Brando is moving computers, so the laptop watch ends. Verified at 17:37: STATUS RUNNING; drivers for 1.7B (GPU 4), 4B (GPU 1) and 14B (GPUs 2,3) fresh and at 99–100% utilization; host watchdog cron (*/15 + @reboot, tag e08v2-matched-test) live. Recovery now rests on the worker and that watchdog; any new master resumes from this file.

- 10-13-2026 17:49 PDT -- terminal analysis: all six reused summaries and 8B paired metrics exact; independent 108 checks PASS; full make test 338 passed / 4 skipped in 293.25 s. All new cells and 1,130 control/fixed-audit ratings listed missing; additional main eligibility unresolved. Publishing PARTIAL report next.
