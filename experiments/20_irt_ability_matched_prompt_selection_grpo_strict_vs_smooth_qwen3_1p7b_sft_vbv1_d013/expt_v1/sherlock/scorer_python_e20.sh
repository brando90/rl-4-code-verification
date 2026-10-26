#!/bin/bash
# TLDR: score_sherlock.sh PYTHON hook: preserve its interpreter probe and scorer arguments, instrument compiler I/O only.
set -euo pipefail
G=$SCRATCH/rl4cv_sherlock/grading
SCORER="$G/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
if [ "${1:-}" = "$SCORER" ]; then
  shift
  exec "$E20_REAL_PYTHON" "$E20_D109_CODE/logged_scorer_e20.py" --scorer "$SCORER" \
    --evidence-root "$E20_D109_OUT" --lean-executable "$G/elan/toolchains/leanprover--lean4---v4.22.0/bin/lean" -- "$@"
fi
exec "$E20_REAL_PYTHON" "$@"
