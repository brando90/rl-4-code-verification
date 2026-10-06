#!/usr/bin/env bash
# Finish report-backed gold cells and only empty baselines with retry allowance left.
set -euo pipefail

runtime=/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery
root=/lfs/skampere1/0/brando9/rl4cv_e06_swebench/rl-4-code-verification
gold="$root/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/scripts/run_official_control.py"
empty="$root/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/scripts/run_official_empty_baseline_adapter.py"
log="$runtime/evaluator_controls/eligible_panel_status.txt"
blocked_empty=(sqlfluff__sqlfluff-1763 pvlib__pvlib-python-1606)

rm_pause="$runtime/evaluator_controls/PAUSE_ADMISSION"
if [[ -f "$rm_pause" ]]; then
  echo "remove only after adapter preflight is recorded" >&2
  exit 65
fi
printf 'started=%s\n' "$(date --iso-8601=seconds)" > "$log"
for task in pvlib__pvlib-python-1154 pvlib__pvlib-python-1072 pydicom__pydicom-1139; do
  "$runtime/venv_v2_clean/bin/python" "$gold" --runtime "$runtime" --instance-id "$task" --kind gold --attempt 1
  printf '%s\t%s\tgold\t0\n' "$(date --iso-8601=seconds)" "$task" >> "$log"
done
for task in sqlfluff__sqlfluff-2419 marshmallow-code__marshmallow-1343 pvlib__pvlib-python-1707 pvlib__pvlib-python-1154 pvlib__pvlib-python-1072 pydicom__pydicom-1139; do
  attempt=1
  [[ "$task" == sqlfluff__sqlfluff-2419 || "$task" == marshmallow-code__marshmallow-1343 ]] && attempt=2
  "$runtime/venv_v2_clean/bin/python" "$empty" --runtime "$runtime" --instance-id "$task" --attempt "$attempt"
  printf '%s\t%s\texact_empty_patch_adapter\t0\n' "$(date --iso-8601=seconds)" "$task" >> "$log"
done
printf 'blocked_empty_retry_exhausted=%s\n' "${blocked_empty[*]}" >> "$log"
printf 'finished=%s\n' "$(date --iso-8601=seconds)" >> "$log"
