# Experiment 14 run instructions (agent prompt)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1/cc.md>

**TLDR:** Run the locked experiment 14 analysis once, on `skampere1`, from a `/lfs` checkout at the lock commit, with zero model calls. The analyzer refuses to start unless the frozen forecast verifies. It stops by itself if experiment 07's splits or the Rasch rank check do not reproduce. Then publish `expt_v1/results/` and update `results.md` with counts, intervals, threshold sources and the verdict.

## Steps

1. Check out the lock commit (the commit that adds `expt_v1/forecasts/e14_forecast.json`) in `/lfs/skampere1/0/brando9/rl4cv_e14`. Confirm that `git rev-parse HEAD` matches the lock in `results.md`.
2. Use `PY=/lfs/skampere1/0/brando9/uv_envs/rl4cv_e14/bin/python` (Python 3.12 with numpy 2.2.6, scipy 1.16.3, pytest and pyyaml; created 10-12-2026 with `uv`). Export `HOME=/lfs/skampere1/0/brando9`, because non-interactive ssh has no AFS token.
3. In tmux session `ccv-rl4cv14-irt-q1-run`, run:
   ```bash
   cd /lfs/skampere1/0/brando9/rl4cv_e14
   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
     $PY experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1/analyze_e14.py \
     --workers 64 2>&1 | tee experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1/results/run_e14.log
   ```
4. **Stop rules (the analyzer enforces them):**
   - input hashes;
   - the 164 × 424 cohort with one inconsistent cell;
   - an exact reproduction of experiment 07's H2;
   - Rasch common-parameter Δ = 0 in every split;
   - the frozen forecast verifies.

   On a STOP, publish the log and the status, and do not rerun with changed settings.
5. Copy `expt_v1/results/` back to the private worktree. Commit it with explicit pathspecs together with `results.md` (verdict, counts, intervals, threshold sources, forecast versus outcome, deviations), then push to `main` after `make test`.

**TL;DR:** One locked CPU run (64 processes) on `skampere1`; the analyzer enforces the stop rules; publish everything, including failures.
