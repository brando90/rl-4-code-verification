#!/usr/bin/env bash
# TLDR: 11-25-2026, fail closed until experiment 03 has its required protocol, probes, forecast and real training entrypoint.
set -euo pipefail
TASK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(git -C "$TASK_DIR" rev-parse --show-toplevel)
LAUNCHER="$REPO_ROOT/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/launch_admitted_11-25-2026.py"
exec python3 "$LAUNCHER" "$TASK_DIR/launch_admission_11-25-2026.json" "$@"
