#!/usr/bin/env bash
# TLDR: Score harvested experiment 08 teacher runs with the frozen scorer (runbook § 6.1): for each harvested (teacher, sample) cells file,
# materialize the job, run `score_scsc.py --skip-tc` in the private grading project (SCORE_PAR jobs in parallel), read back per-cell
# kernel factors + non-vacuity + kernel_binary, and append to results/scored_cells.jsonl (rewritten from all per-run readbacks).
# Usage: bash score_teacher_runs.sh [phase=main] [runs="opus55:s1 opus55:s2 ... astra:s4"]
set -uo pipefail
PHASE="${1:-main}"; RUNS="${2:-opus55:s1 opus55:s2 opus55:s3 opus55:s4 astra:s1 astra:s2 astra:s3 astra:s4}"
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
REPO="$WORK/rl-4-code-verification"; EXP="$REPO/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
S="$EXP/expt_v1/scripts/score_teacher_files.py"; PY="$REPO/.venv/bin/python"
SCORE_PAR="${SCORE_PAR:-4}"
if [ "$PHASE" = main ]; then JOBS="$WORK/jobs"; SCORES="$WORK/scores"; VIEWS="$WORK/pack_views/teachers"; RAW="$WORK/raw"; else JOBS="$WORK/jobs_preflight"; SCORES="$WORK/scores_preflight"; VIEWS="$WORK/pack_views/preflight"; RAW="$WORK/raw/preflight"; fi
mkdir -p "$JOBS" "$SCORES" "$VIEWS" "$WORK/logs"
ts() { date '+%m-%d-%Y %H:%M:%S'; }
export S PY JOBS SCORES VIEWS RAW WORK
echo "$RUNS" | tr ' ' '\n' | xargs -P "$SCORE_PAR" -I{} bash -c '
  T="${1%%:*}"; R="${1##*:}"; NAME="${T}_${R}"; CELLS="$RAW/$T/$R/cells.jsonl"
  [ -f "$CELLS" ] || { echo "[$(date "+%m-%d-%Y %H:%M:%S")] no cells for $NAME ($CELLS); skipping"; exit 0; }
  if ls "$SCORES/${NAME}_s0"/*_per_task.csv >/dev/null 2>&1; then echo "already scored: $NAME"; exit 0; fi
  [ -d "$SCORES/${NAME}_s0" ] && mv "$SCORES/${NAME}_s0" "$SCORES/.interrupted_${NAME}_$(date +%Y%m%dT%H%M%S)"
  [ -d "$JOBS/${NAME}_s0" ] && mv "$JOBS/${NAME}_s0" "$JOBS/.interrupted_${NAME}_$(date +%Y%m%dT%H%M%S)"
  echo "[$(date "+%m-%d-%Y %H:%M:%S")] scoring $NAME"
  "$PY" "$S" score --cells "$CELLS" --job-root "$JOBS" --scores-root "$SCORES" --views-root "$VIEWS" --name "$NAME" > "$WORK/logs/score_${NAME}.log" 2>&1 && echo "scored: $NAME" || echo "FAILED: $NAME (see $WORK/logs/score_${NAME}.log)"
' _ {}
for RUN in $RUNS; do
  T="${RUN%%:*}"; R="${RUN##*:}"; NAME="${T}_${R}"; CELLS="$RAW/$T/$R/cells.jsonl"
  [ -f "$CELLS" ] || continue
  ls "$SCORES/${NAME}_s0"/*_per_task.csv >/dev/null 2>&1 || { echo "[$(ts)] $NAME not scored; aborting readback" >&2; exit 1; }
  "$PY" "$S" readback --cells "$CELLS" --job-root "$JOBS" --scores-root "$SCORES" --name "$NAME" --out "$SCORES/${NAME}_s0/scored_cells_${NAME}.jsonl" || exit 1
done
if [ "$PHASE" = main ]; then
  OUT="$EXP/expt_v1/results/scored_cells.jsonl"; : > "$OUT.tmp"
  for RUN in $RUNS; do T="${RUN%%:*}"; R="${RUN##*:}"; F="$SCORES/${T}_${R}_s0/scored_cells_${T}_${R}.jsonl"; [ -f "$F" ] && cat "$F" >> "$OUT.tmp"; done
  mv "$OUT.tmp" "$OUT"; echo "[$(ts)] wrote $OUT ($(wc -l < "$OUT") rows)"
fi
