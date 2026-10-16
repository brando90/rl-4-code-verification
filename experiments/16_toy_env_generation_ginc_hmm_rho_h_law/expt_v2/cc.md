# Runbook: 16_toy_env_generation_ginc_hmm_rho_h_law Night 2

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/cc.md>

**TLDR:** Complete the four-token CPU environment-generation test described in [the original dispatch](../PROMPT_dispatch_e16_night2.md) and [the prospective protocol](PROTOCOL.md). The declared matrix is four scales, sixteen environments, two training seeds and three budget observations, with the largest-scale forecast frozen before its training outcomes. Report the measured positive-transfer prevalence and the comparisons even if they fail the requested success criteria. Keep all compute on CPU at nice 10 with zero provider calls and $0 spend; preserve Night 1 evidence.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

From the dedicated repository root, `bash experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/preflight.sh` trains starting policies, freezes mixtures and checks the probe gate. The persistent session `rl4cv-e16-night2-cpu-sweep` runs `sweep.sh`: it waits for the gate, completes n1–n3, freezes forecasts, then runs n4 and generates the report. Both scripts leave logs under `expt_v2/results/pilot_v3/`. Inspect process liveness and exit codes as well as artifacts; never launch a duplicate writer for an active stage.

Run `.venv-test/bin/python -m pytest -q tests/test_e16_ginc_toy.py` and `PATH="$PWD/.venv-test/bin:$PATH" make test`. The training interpreter is `.venv/bin/python` (PyTorch 2.14.1+cpu); test environment `.venv-test` uses system Python 3.12 because managed Python 3.13 lacks the process-descriptor operation required by unrelated watchdog tests. Checkpoint tensors remain ignored locally; all probe and outcome tables used by analysis are committed.

Complete all authorized work, inspect the final artifacts and exact staged diff, run deterministic checks, push the requested branch, update pull request #15, and send the run-done email with verified status. No target-outcome tuning or selective reruns. A positive scientific verdict is not a condition for reporting an accurately completed run.

**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Finish the declared Night 2 matrix and publish its actual result with a prospective n4 forecast.
