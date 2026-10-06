#!/usr/bin/env bash
# Run only genuinely unmeasured gold cells plus audited semantic-empty baselines.
set -euo pipefail

echo "obsolete: marker-file baseline was rejected by supervision; use run_official_eligible_controls.sh" >&2
exit 65

runtime=/lfs/skampere1/0/brando9/rl4cv_e06_swebench/runtime_vals_recovery
root=/lfs/skampere1/0/brando9/rl4cv_e06_swebench/rl-4-code-verification
runner="$root/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/scripts/run_official_control.py"
manifest="$runtime/evaluator_controls/control_manifest_v2.json"
rm_pause="$runtime/evaluator_controls/PAUSE_ADMISSION"

if [[ ! -f "$manifest" ]]; then
  echo "missing reconciled control manifest" >&2
  exit 64
fi
if [[ -f "$rm_pause" ]]; then
  echo "admission remains paused" >&2
  exit 65
fi

mapfile -t task_ids < <("$runtime/venv_v2_clean/bin/python" - "$manifest" <<'PY'
import json, sys
seen = set()
for cell in json.load(open(sys.argv[1]))["cells"]:
    if cell["instance_id"] not in seen:
        seen.add(cell["instance_id"])
        print(cell["instance_id"])
PY
)

log="$runtime/evaluator_controls/reconciled_panel_status.txt"
printf 'started=%s\n' "$(date --iso-8601=seconds)" > "$log"
for task_id in "${task_ids[@]}"; do
  if ! find "$runtime/evaluator_controls" -path "*/gold_${task_id}_*/receipt.json" -exec jq -e '.status == "COMPLETE"' {} \; -quit | grep -q true; then
    "$runtime/venv_v2_clean/bin/python" "$runner" --runtime "$runtime" --instance-id "$task_id" --kind gold --attempt 1
    printf '%s\t%s\tgold\t%s\n' "$(date --iso-8601=seconds)" "$task_id" "$?" >> "$log"
  fi
  "$runtime/venv_v2_clean/bin/python" "$runner" --runtime "$runtime" --instance-id "$task_id" --kind empty --attempt 2
  printf '%s\t%s\tempty_semantic_baseline\t%s\n' "$(date --iso-8601=seconds)" "$task_id" "$?" >> "$log"
done
printf 'finished=%s\n' "$(date --iso-8601=seconds)" >> "$log"
