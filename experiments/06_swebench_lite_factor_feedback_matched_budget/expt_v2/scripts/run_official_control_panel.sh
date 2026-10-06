#!/usr/bin/env bash
# TLDR: Run every frozen gold/empty official control serially, retaining a receipt for every admitted cell.
set -u -o pipefail

runtime=/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery
root=/lfs/skampere1/0/brando9/rl4cv_e06_swebench/rl-4-code-verification
runner="$root/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/scripts/run_official_control.py"
log_dir="$runtime/evaluator_controls"
mkdir -p "$log_dir"

mapfile -t task_ids < <("$runtime/venv_v2_clean/bin/python" - "$runtime/evaluator_inputs/panel_evaluator_manifest.json" <<'PY'
import json, sys
for task in json.load(open(sys.argv[1]))["tasks"]:
    print(task["instance_id"])
PY
)

started=$(date --iso-8601=seconds)
printf 'started=%s\n' "$started" > "$log_dir/panel_driver_status.txt"
for task_id in "${task_ids[@]}"; do
  for kind in gold empty; do
    stamp=$(date +%s)
    "$runtime/venv_v2_clean/bin/python" "$runner" --runtime "$runtime" --instance-id "$task_id" --kind "$kind" \
      >"$log_dir/${kind}_${task_id}_${stamp}.driver.stdout" 2>"$log_dir/${kind}_${task_id}_${stamp}.driver.stderr"
    rc=$?
    printf '%s\t%s\t%s\t%s\n' "$(date --iso-8601=seconds)" "$task_id" "$kind" "$rc" \
      >> "$log_dir/panel_driver_status.txt"
  done
done
printf 'finished=%s\n' "$(date --iso-8601=seconds)" >> "$log_dir/panel_driver_status.txt"
