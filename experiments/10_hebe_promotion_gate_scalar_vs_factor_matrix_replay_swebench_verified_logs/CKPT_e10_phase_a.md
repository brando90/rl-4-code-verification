# CKPT: experiment 10 phase A replay (rl4cv-e10-phase-a-10-14)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/CKPT_e10_phase_a.md>

**TLDR:** Rule 44 checkpoint for running phase A of experiment 10 (`experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs`) on the real data under its LOCKED protocol revision 3, with zero model calls, on skampere1. Worker: Claude Code (`claude-fable-5-1`, effort max), dispatched 10-14-2026 by the master session `oct14-cc-rl4cv-master-ultracode-progress`. Outcome: primary replay DONE and scored (no gate recommendation under the frozen rules); matched-test-lists sensitivity BLOCKED by its own shape stop rule.

Created: 10-14-2026 13:05 PDT
Last updated: 10-14-2026 13:40 PDT

## Goal

Verify the lock (forecast `expt_v1/forecasts/e10_forecast.json`, SHA-256 `e4eccd8b…3c23`; pinned `analyze_e10.py`, `tests/test_e10_replay.py`, per-cell input, drift list), run the primary replay (`--sensitivity none`) and the matched-test-lists sensitivity, 1,000 splits × 1,000 draws each, score every frozen prediction exactly as `PROTOCOL.md` and the forecast define them, and publish `results.md`, the README status and this checkpoint. No pinned file is modified; a needed code change is reported as BLOCKED, never made under the old lock.

## What ran

- **Lock verification (Mac worktree and host, 10-14-2026 ~13:00 PDT):** `rl4cv.forecast.verify_forecast` → True (canonical hash `e4eccd8b…3c23`; raw bytes hash `9b1b4596…` because `freeze_forecast` appends a newline). `analyze_e10.py` `a1278349…`, `tests/test_e10_replay.py` `dc1ba2e1…`, `per_cell_e07.jsonl.gz` `f064c395…`, `test_list_drift_e07.json` `e1d34185…`: all equal to the forecast's pins. Lock commit `55d1c53` changed only PROTOCOL.md's Status line relative to the forecast's recorded protocol commit `fb756de`; no pinned file changed since.
- **Host setup:** clone `/lfs/skampere1/0/brando9/rl4cv_e10/rl-4-code-verification` at origin/main `57c3bb6` (12:59 PDT); venv `/lfs/skampere1/0/brando9/rl4cv_e10/env` (Python 3.12.3, numpy 2.5.4, pytest 9.1.1, built with uv; the experiment-08 environments have no pytest). `tests/test_e10_replay.py`: 15 passed on the host.
- **Primary run:** launched 13:02 PDT via `~/agents-config/scripts/snap_dispatch.sh run rl4cv-e10-phase-a-10-14 /lfs/skampere1/0/brando9/rl4cv_e10/run_primary.sh` (32 workers, `OMP_NUM_THREADS=1`, `/usr/bin/time -v`). Exit 0 at 13:04:56 PDT: wall 2 min 52.95 s, `runtime_s` 172.5, GNU time max RSS 2.36 GB (largest process), 21 GB summed RSS over 34 processes sampled at 13:03. Output `e10_primary.json` SHA-256 `0005a03e455ae22a92edfee1d2632a4a3d1246ddfc8159d7c738b47f60ed20b1` (106 KB), copied into `expt_v1/results/` with `run_e10_primary.log`. Dispatch log `/lfs/skampere1/0/brando9/snap_jobs/rl4cv-e10-phase-a-10-14_latest.log`; the tmux session remains (remain-on-exit) and may be killed.
- **Sensitivity run:** launched 13:02 PDT as `rl4cv-e10-phase-a-sens-10-14`; exited after 1.4 s with the protocol stop rule `STOP: expected (164, 420), got (164, 421)` (see Stuck / blocked). Log copied to `expt_v1/results/run_e10_sensitivity_matched_test_lists.log`.
- **Scoring:** `python3 expt_v1/score_e10.py --result expt_v1/results/e10_primary.json --out expt_v1/results/e10_primary_verdicts.json --tables` (new script, reads the output only; verifies `settings.expect_sha` = per-cell pin and 164 × 424).
- **Rule 70 email:** `[RUN START] rl4cv e10 phase A replay` sent 13:03 PDT through the Gmail connector (message id `1a13c036afbac1d9`); `[RUN DONE]` sent after the results push.
- **Commits on origin/main:** `52a08d6` (status, runbook `expt_v1/cc.md`, checkpoint, sensitivity log); the results commit follows (see Log).

## Results

Population P_near (1 ≤ net_V ≤ 10), q = 0.5, 1,000/1,000 splits admitted, 1,000/1,000 draws valid, median 2,382 pairs per split, 164 systems × 424 tasks; `x [lo, hi] p-val=n/a` with the dyadic system bootstrap (1,000 draws):

- H1: HPR 0.2580 [0.2410, 0.2821]; share with losses_E ≥ 1 0.9991 [0.9961, 1.0000]; mean losses_E/|E| 0.0754 [0.0690, 0.0820]; mean Δpass1_E 0.0245 [0.0223, 0.0262].
- H2a: 0.1265 [0.0840, 0.1675] → SUPPORTED (descriptive; null-sized per the frozen caveat). H2(c) ΔR²(M2 − M1) median −0.0017, share > 0 = 0.475.
- H3: C_fac 0.0046 [−0.0027, 0.0117] (includes 0); C_fac0 0.0210 [0.0017, 0.0403]; C_bin 0.0163 [−0.0014, 0.0355] (includes 0); guards R3 − R2 0.0007 [−0.0000, 0.0014], R3 − R0 0.0003 [−0.0014, 0.0023], R2 − R0 −0.0004 [−0.0020, 0.0014] all pass → **no recommendation, reason code `interval_includes_zero`**. Same decision at q = 0.25 and 0.75.
- Practical target: S0+ − R3 −0.0652 [−0.0838, −0.0443] (relative −0.379), S0+ − R2 −0.0698 [−0.0865, −0.0507]: not met; "just be stricter" is safer.
- Deployable zero-loss rule: acceptance 0.0008 [0.0000, 0.0038]; conditional HPR inconclusive (430/1,000 valid draws).
- Full tables and the plain-English reading: `results.md`.

## Stuck / blocked

- **Sensitivity (`--sensitivity matched_test_lists`) is BLOCKED under the lock.** Dropping the 4 declared drift tasks from the 424-task cohort leaves 421 tasks, not the 420 the protocol requires, so the pinned code's stop rule fires before any statistic. Cause: `django__django-10097` is not in the 164 × 424 common cohort (0 `common_cohort` cells; the other 3 drift tasks have 164 each). Fixing this needs a change to `analyze_e10.py`'s `EXPECTED_SHAPE` or to the protocol's declared sensitivity, which is a new `expt_v2` or a dated amendment, never an edit under the old lock. The primary analysis does not use the drift list and is unaffected.

## Next steps

1. Brando decides amendment versus `expt_v2` for the sensitivity (below); if amendment: add `AMENDMENT_A1_sensitivity_shape.md` dated before the rerun, declaring the 3 cohort-resident drift tasks and expected shape 164 × 421, then rerun only `--sensitivity matched_test_lists` with the host launcher `/lfs/skampere1/0/brando9/rl4cv_e10/run_sens.sh` after adjusting the expected shape in a new code revision with its own pin.
2. Experiment 11 proceeds without a gate claim; its design may use the exploratory C_agg (R1) result as a hypothesis only.
3. Phase B waits on the AlphaHebe team's export (AlphaHebe-dev issue #30).
4. Housekeeping on skampere1: `tmux kill-session -t rl4cv-e10-phase-a-10-14; tmux kill-session -t rl4cv-e10-phase-a-sens-10-14` (both finished; left for inspection).

## Brando to-do

- Decide how the matched-test-lists sensitivity is re-admitted: a dated amendment that declares the cohort-resident drift tasks (expected shape 164 × 421) and reruns only the sensitivity, or an `expt_v2`. The primary verdicts do not depend on it.
- Read the plain-English section of `results.md`: the cheapest safety improvement for AlphaHebe today is a larger promotion margin, not a per-item gate.

## Log

- 10-14-2026 13:05 PDT: lock verified, host prepared, primary running, sensitivity blocked by the 420-versus-421 stop rule, START email sent.
- 10-14-2026 13:16 PDT: primary finished 13:04:56 (exit 0), output copied and scored; results.md, README and this checkpoint written; status commit `52a08d6` pushed; results commit being pushed.
- 10-14-2026 13:40 PDT -- Results commit landed as `a2a10ef` (independent check PASS: lock pins verified, numbers match e10_primary.json). Finished host sessions rl4cv-e10-phase-a-10-14 and rl4cv-e10-phase-a-sens-10-14 closed by the master. Open: Brando's choice of a dated amendment (shape 164 x 421) or expt_v2 for the matched-test-lists sensitivity.
