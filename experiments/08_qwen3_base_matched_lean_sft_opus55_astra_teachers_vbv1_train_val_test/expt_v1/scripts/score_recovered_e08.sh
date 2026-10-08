#!/usr/bin/env bash
# TLDR: Score the cells recovered by the one allowed re-send (PROTOCOL § 3) as a separate small scorer job per run (`<teacher>_<sample>_rec1`),
# read them back, and replace their rows in that run's scored_cells file; then rebuild results/scored_cells.jsonl from all 8 runs.
set -uo pipefail
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
REPO="$WORK/rl-4-code-verification"; EXP="$REPO/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
S="$EXP/expt_v1/scripts/score_teacher_files.py"; PY="$REPO/.venv/bin/python"
ts() { date '+%m-%d-%Y %H:%M:%S'; }
for RUN in opus55:s1 opus55:s2 opus55:s3 opus55:s4 astra:s1 astra:s2 astra:s3 astra:s4; do
  T="${RUN%%:*}"; R="${RUN##*:}"; NAME="${T}_${R}"; CELLS="$WORK/raw/$T/$R/cells.jsonl"; REC="$WORK/raw/$T/$R/cells_recovered.jsonl"
  "$PY" - "$CELLS" "$REC" <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
rec = [r for r in rows if r.get("recovered")]
with open(sys.argv[2], "w") as fh:
    for r in rec:
        fh.write(json.dumps(r, sort_keys=True) + "\n")
print(len(rec))
EOF
  N=$(wc -l < "$REC")
  [ "$N" = 0 ] && { echo "[$(ts)] $NAME: no recovered cells"; continue; }
  MAIN="$WORK/scores/${NAME}_s0/scored_cells_${NAME}.jsonl"
  [ -f "$MAIN" ] || { echo "[$(ts)] $NAME: main readback missing ($MAIN); run score_teacher_runs.sh first" >&2; exit 1; }
  if ! ls "$WORK/scores/${NAME}_rec1_s0"/*_per_task.csv >/dev/null 2>&1; then
    echo "[$(ts)] $NAME: scoring $N recovered cells"
    rm -rf "$WORK/scores/${NAME}_rec1_s0" "$WORK/jobs/${NAME}_rec1_s0"
    "$PY" "$S" score --cells "$REC" --job-root "$WORK/jobs" --scores-root "$WORK/scores" --views-root "$WORK/pack_views/teachers" --name "${NAME}_rec1" > "$WORK/logs/score_${NAME}_rec1.log" 2>&1 || { echo "FAILED $NAME rec1" >&2; exit 1; }
  fi
  "$PY" "$S" readback --cells "$REC" --job-root "$WORK/jobs" --scores-root "$WORK/scores" --name "${NAME}_rec1" --out "$WORK/scores/${NAME}_rec1_s0/scored_cells_${NAME}_rec1.jsonl" || exit 1
  "$PY" - "$MAIN" "$WORK/scores/${NAME}_rec1_s0/scored_cells_${NAME}_rec1.jsonl" <<'EOF'
import json, sys
main = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
rec = {json.loads(l)["task_id"]: json.loads(l) for l in open(sys.argv[2]) if l.strip()}
n = 0
for i, r in enumerate(main):
    if r["task_id"] in rec:
        rec[r["task_id"]]["recovered"] = True
        main[i] = rec[r["task_id"]]; n += 1
with open(sys.argv[1], "w") as fh:
    for r in main:
        fh.write(json.dumps(r, sort_keys=True) + "\n")
print("merged", n, "recovered rows into", sys.argv[1])
EOF
done
OUT="$EXP/expt_v1/results/scored_cells.jsonl"; : > "$OUT.tmp"
for RUN in opus55:s1 opus55:s2 opus55:s3 opus55:s4 astra:s1 astra:s2 astra:s3 astra:s4; do T="${RUN%%:*}"; R="${RUN##*:}"; cat "$WORK/scores/${T}_${R}_s0/scored_cells_${T}_${R}.jsonl" >> "$OUT.tmp"; done
mv "$OUT.tmp" "$OUT"; echo "[$(ts)] wrote $OUT ($(wc -l < "$OUT") rows)"
