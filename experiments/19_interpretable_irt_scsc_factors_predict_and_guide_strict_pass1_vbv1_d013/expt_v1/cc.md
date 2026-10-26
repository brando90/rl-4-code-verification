# Experiment 19 v1 runbook: locked offline IRT analysis

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/expt_v1/cc.md>

**TLDR:** Reproduce experiment 19's single locked analysis. It is CPU-only, makes zero model calls and costs $0. It reads only committed rl4cv inputs pinned in `input_pins_e19.json` and never touches the D-013 test split. Run it once from a checkout at the lock commit, then publish `results/analysis_e19.json` and `results.md` without changing any setting.

## Steps

1. Check out the lock commit recorded in `../CKPT_irt_lane.md`, and confirm `git status` is clean for this folder.
2. Use Python 3.11+ with NumPy ≥ 2.2 and SciPy ≥ 1.16.
3. Run `bash expt_v1/run_e19_snap.sh <lock commit>` from this experiment folder, in a named tmux session (SNAP: `cc-rl4cv-e19-irt-run`). `E19_WORKERS` sets the process count (default 32).
4. The log `results/run_e19.log` ends with `RUN_EXIT=<code>`. A nonzero exit or a failed numerical gate (`gates.all_primary_fits_converged` false) is reported as is. Never rerun with changed settings.
5. Publish: copy `results/` back, write `results.md` from `analysis_e19.json` (Hard Rule 11 statistics, verdicts exactly as `verdicts` prints them, frozen forecast scored), and update the experiment index row.

Synthetic check (no real data): `python3 expt_v1/analyze_e19.py --synthetic 7 --boot-refit 40 --workers 6 --out /tmp/e19_syn`.

**TL;DR:** One locked CPU run on SNAP, then publish exactly what it printed.
