# Experiment 10, expt_v1 runbook: verify the lock, replay, score, publish

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/expt_v1/cc.md>

**TLDR:** Phase A of experiment 10 (`experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs`) replays AlphaHebe-style promotion policies on experiment 07's 164 × 424 SWE-bench Verified factor matrix with zero model calls. The protocol is LOCKED (revision 3, commit `55d1c53`, 10-09-2026 16:43 PDT) and the forecast is frozen (`forecasts/e10_forecast.json`, SHA-256 `e4eccd8b…3c23`), so the agent's job is mechanical: verify every pin, run the pinned `analyze_e10.py` twice (primary and the matched-test-lists sensitivity), score the frozen predictions exactly as `PROTOCOL.md` defines them, and publish. Any pinned hash that differs stops the run; a code change is a new `expt_v2`, never an edit under the old lock. Runs go on a SNAP (Stanford Network Analysis Project) node inside tmux so they survive the laptop sleeping.

## 1. Verify the lock (stop rule)

Run from the repository root. Every line must match before anything else is run.

```bash
E=experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs
python3 -c "import sys; sys.path.insert(0,'src'); from rl4cv.forecast import verify_forecast; print(verify_forecast('$E/expt_v1/forecasts/e10_forecast.json'))"   # True
shasum -a 256 $E/expt_v1/analyze_e10.py                       # a1278349f95d6d07fc4783b79f7c14e4593fda06b7f083de92c953149ad79f0c
shasum -a 256 tests/test_e10_replay.py                        # dc1ba2e1b1fb54c81510775d1c763936d164f655e52a0312d7a57bc447eabae6
shasum -a 256 experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz   # f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d
shasum -a 256 $E/expt_v1/inputs/test_list_drift_e07.json      # e1d341855f04c4d6120444e58af840a39ca446ffa6764748240268452188f6c8
python -m pytest -q tests/test_e10_replay.py                  # 15 passed
```

Notes:

- `verify_forecast` hashes the canonical JSON text without the trailing newline; the raw file bytes hash to `9b1b4596…`, which is expected.
- The forecast records `PROTOCOL.md` at commit `fb756de` (SHA-256 `eaaad9f6…`); the lock commit `55d1c53` changed only the Status line.
- If any pin differs: do not run. Publish the discrepancy in `results.md` and report BLOCKED.

## 2. Run phase A (primary and sensitivity)

Both runs are deterministic given the seeds; the worker count only changes wall time. Use one BLAS thread per worker (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`) and GNU time for peak memory.

```bash
/usr/bin/time -v python $E/expt_v1/analyze_e10.py --sensitivity none --splits 1000 --draws 1000 \
  --split-seed 20261009 --boot-seed 20261010 --q 0.5 0.25 0.75 --min-pairs 200 --workers 32 \
  --out $E/expt_v1/results/e10_primary.json > $E/expt_v1/results/run_e10_primary.log 2>&1
/usr/bin/time -v python $E/expt_v1/analyze_e10.py --sensitivity matched_test_lists --splits 1000 --draws 1000 \
  --split-seed 20261009 --boot-seed 20261010 --q 0.5 0.25 0.75 --min-pairs 200 --workers 32 \
  --out $E/expt_v1/results/e10_sensitivity_matched_test_lists.json > $E/expt_v1/results/run_e10_sensitivity_matched_test_lists.log 2>&1
```

On SNAP: clone at the verified commit under `/lfs/skampere1/0/brando9/rl4cv_e10/rl-4-code-verification`, use the venv `/lfs/skampere1/0/brando9/rl4cv_e10/env` (numpy, pytest), and launch each run with `~/agents-config/scripts/snap_dispatch.sh run <job-name> '<command>'` (sessions `rl4cv-e10-phase-a-10-14` and `rl4cv-e10-phase-a-sens-10-14` on 10-14-2026). The script itself prints nothing until it finishes; liveness is the tmux session and the process list. A run that dies from an infrastructure cause (memory, paths, environment) may be relaunched once unchanged; a traceback inside the pinned code is reported as BLOCKED.

## 3. Score the frozen predictions

Read `e10_forecast.json` and `PROTOCOL.md` first; score only what they define, from `populations.near` unless stated.

| Prediction | Where in the JSON | Verdict rule |
|---|---|---|
| H1 (descriptive) | `H1.members.{hpr, share_any_loss, mean_lossfrac, mean_dpass_t}` | Report `x [lo, hi] p-val=n/a` with splits admitted / considered and valid draws / 1,000 |
| H2(a) | `H2.hrm.members.hrm` | Supported iff estimate > 0 and `lo` > 0; `krm`, `hrm_with_marginals`, `trm_given_gain_p1` are sensitivities; `H2_predictive` gives M0/M1/M2 and M2 − M1 |
| H3 factor gate | `H3["0.5"].main.members` | `R2-R3.hpr_abs_reduction` (C_fac) and `R0-R3.hpr_abs_reduction` (C_fac0) both with estimate > 0 and `lo` > 0, and utility guard: `R2-R3.dpass_gain_of_second.lo` > −0.01 and `R0-R3.dpass_gain_of_second.lo` > −0.01 |
| H3 binary gate | same | Otherwise: `R0-R2.hpr_abs_reduction` (C_bin) estimate > 0 and `lo` > 0, and `R0-R2.dpass_gain_of_second.lo` > −0.01 |
| No recommendation | same | Otherwise, with reason codes `interval_includes_zero`, `utility_guard_failed`, `undefined_or_inconclusive_support` (the family `status` is not `ok`, or a member is missing) |
| Practical target | `*.hpr_rel_reduction` for `S0plus-R3` and `S0plus-R2` | Relative HPR reduction ≥ 0.20 versus S0+ (reported, not a decision rule) |

Also report: `splits_degenerate` (more than 10% makes P_near inconclusive), `pairs_per_split_median`, every family's `status`, the q = 0.25 and 0.75 tables, the deployable zero-loss rule's acceptance and conditional HPR (undefined stays undefined), `runtime_s`, and the GNU time wall clock and maximum resident set size. The sensitivity run is reported beside the primary; it never replaces it.

## 4. Publish

1. Copy the JSON outputs into `expt_v1/results/` (gzip above about 5 MB; above about 20 MB keep them on the host and commit the SHA-256 plus a compact extract) and verify that `settings.expect_sha` in each output equals the per-cell pin.
2. Write `results.md` (verdict table, intervals, support counts, sensitivities, cost, plain-English reading), update `README.md` Status, and keep `CKPT_e10_phase_a.md` current.
3. `make test`, commit with explicit pathspecs, `git fetch origin && git rebase origin/main && git push origin HEAD:main`.
4. Send the `[RUN DONE]` email (Rule 70) and hand the index-row text for `experiments/README.md` to the master.

## TL;DR

Verify five hashes and 15 tests, run the pinned script twice on SNAP, score H1/H2/H3 exactly as frozen, publish with intervals and support counts, and never touch the pinned files.
