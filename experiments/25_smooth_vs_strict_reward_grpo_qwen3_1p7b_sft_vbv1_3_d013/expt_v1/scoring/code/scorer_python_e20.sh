#!/bin/bash
# TLDR: score_local.sh PYTHON hook (as Exp 20's scorer_python_e20.sh): forward the frozen scorer entry through D-109 durable
# compiler capture, pass every other interpreter call straight to the real python. G = E20_GRADING, not $SCRATCH (Sherlock).
set -euo pipefail
G=${E20_GRADING:?E20_GRADING not set}
SCORER="$G/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
if [ "${1:-}" = "$SCORER" ]; then
  shift
  exec "$E20_REAL_PYTHON" "$E20_D109_CODE/logged_scorer_e20.py" --scorer "$SCORER" \
    --evidence-root "$E20_D109_OUT" --lean-executable "$G/elan/toolchains/leanprover--lean4---v4.22.0/bin/lean" -- "$@"
fi
exec "$E20_REAL_PYTHON" "$@"
