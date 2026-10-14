# CKPT: experiment 10 phase A replay (rl4cv-e10-phase-a-10-14)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/CKPT_e10_phase_a.md>

**TLDR:** Rule 44 checkpoint for running phase A of experiment 10 (`experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs`) on the real data under its LOCKED protocol revision 3, with zero model calls, on skampere1. Worker: Claude Code (`claude-fable-5-1`, effort max), dispatched 10-14-2026 by the master session `oct14-cc-rl4cv-master-ultracode-progress`.

Created: 10-14-2026 13:05 PDT
Last updated: 10-14-2026 13:05 PDT

## Goal

Verify the lock (forecast `expt_v1/forecasts/e10_forecast.json`, SHA-256 `e4eccd8b…3c23`; pinned `analyze_e10.py`, `tests/test_e10_replay.py`, per-cell input, drift list), run the primary replay (`--sensitivity none`) and the matched-test-lists sensitivity, 1,000 splits × 1,000 draws each, score every frozen prediction exactly as `PROTOCOL.md` and the forecast define them, and publish `results.md`, the README status and this checkpoint. No pinned file is modified; a needed code change is reported as BLOCKED, never made under the old lock.

## What ran

- **Lock verification (Mac worktree and host, 10-14-2026 ~13:00 PDT):** `rl4cv.forecast.verify_forecast` → True (canonical hash `e4eccd8b…3c23`; raw bytes hash `9b1b4596…` because `freeze_forecast` appends a newline). `analyze_e10.py` `a1278349…`, `tests/test_e10_replay.py` `dc1ba2e1…`, `per_cell_e07.jsonl.gz` `f064c395…`, `test_list_drift_e07.json` `e1d34185…`: all equal to the forecast's pins. Lock commit `55d1c53` changed only PROTOCOL.md's Status line relative to the forecast's recorded protocol commit `fb756de`; no pinned file changed since.
- **Host setup:** clone `/lfs/skampere1/0/brando9/rl4cv_e10/rl-4-code-verification` at origin/main `57c3bb6` (12:59 PDT); venv `/lfs/skampere1/0/brando9/rl4cv_e10/env` (Python 3.12.3, numpy 2.5.4, pytest 9.1.1, built with uv; the experiment-08 environments have no pytest). `tests/test_e10_replay.py`: 15 passed on the host.
- **Primary run:** launched 13:02 PDT via `~/agents-config/scripts/snap_dispatch.sh run rl4cv-e10-phase-a-10-14 /lfs/skampere1/0/brando9/rl4cv_e10/run_primary.sh` (32 workers, `OMP_NUM_THREADS=1`, `/usr/bin/time -v`). Log: `<clone>/experiments/10_…/expt_v1/results/run_e10_primary.log`; dispatch log `/lfs/skampere1/0/brando9/snap_jobs/rl4cv-e10-phase-a-10-14_latest.log`; done marker `/lfs/skampere1/0/brando9/rl4cv_e10/done_primary.rc<code>`. At 13:03 PDT: 34 processes, 21 GB summed RSS, ~32 cores busy.
- **Sensitivity run:** launched 13:02 PDT as `rl4cv-e10-phase-a-sens-10-14`; exited after 1.4 s with the protocol stop rule `STOP: expected (164, 420), got (164, 421)` (see Stuck / blocked).
- **Rule 70 email:** `[RUN START] rl4cv e10 phase A replay` sent 13:03 PDT through the Gmail connector (message id `1a13c036afbac1d9`).

## Results

None read yet. The primary output `e10_primary.json` does not exist until the run finishes; no real-data statistic has been seen.

## Stuck / blocked

- **Sensitivity (`--sensitivity matched_test_lists`) is BLOCKED under the lock.** Dropping the 4 declared drift tasks from the 424-task cohort leaves 421 tasks, not the 420 the protocol requires, so the pinned code's stop rule fires before any statistic. Cause: one declared drift task is not in the 164 × 424 common cohort (cohort membership check in results.md). Fixing this needs a change to `analyze_e10.py`'s `EXPECTED_SHAPE` or to the protocol's declared sensitivity, which is a new `expt_v2` or a dated amendment, never an edit under the old lock. The primary analysis does not use the drift list and is unaffected.

## Next steps

1. Poll the primary run every 3-5 minutes: `ssh brando9@skampere1.stanford.edu 'tmux ls | grep rl4cv-e10; tail -3 /lfs/skampere1/0/brando9/snap_jobs/rl4cv-e10-phase-a-10-14_latest.log; ls /lfs/skampere1/0/brando9/rl4cv_e10/'`.
2. When `done_primary.rc0` exists: copy `e10_primary.json` and `run_e10_primary.log` into `expt_v1/results/`, verify `settings.expect_sha` equals `f064c395…`, score H1/H2a/H3 per `expt_v1/cc.md` section 3, write `results.md`, update the README status, commit, push, send `[RUN DONE]`.
3. Hand the master the index-row text and the sensitivity amendment decision (Brando to-do).

## Brando to-do

- Decide how the matched-test-lists sensitivity is re-admitted: a dated amendment that declares the cohort-resident drift tasks (expected shape 164 × 421) and reruns only the sensitivity, or an `expt_v2`. The primary verdicts do not depend on it.

## Log

- 10-14-2026 13:05 PDT: lock verified, host prepared, primary running, sensitivity blocked by the 420-versus-421 stop rule, START email sent.
