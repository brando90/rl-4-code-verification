#!/usr/bin/env bash
# TLDR: Run experiment 01 for one model end to end (generate, materialize, kernel-score, collect, summarize) for the G=1 evaluation or the G=8 probe.
# Usage: bash run_model.sh <eval|probe> <hf_model_id> <revision> <label> [tp]
# Required env: PACK (experiment 103's gated v6 pack dir), TASK_IDS (its 896-id list), LAKE_DIR (grading Lean project,
# Lean v4.22.0 + Mathlib v4.22.0 built), OUT (results dir on /lfs, not DFS), SCORER (external/veribench_scorer checkout).
# Optional env: STAGE=gen|score|all (default all; orchestration only, never loads a model in the score stage),
# BATCH=<n> (generate.py --batch; default 64, unrelated to PROTOCOL.md's sampling parameters or per-request seeds).
# Resumable: generation skips finished cells; job and score directories are write-once, so delete a failed stage's dir
# only after recording why in the checkpoint file.
set -euo pipefail
MODE="$1"; MODEL="$2"; REV="$3"; LABEL="$4"; TP="${5:-1}"
STAGE="${STAGE:-all}"; BATCH="${BATCH:-64}"
: "${PACK:?}" "${TASK_IDS:?}" "${LAKE_DIR:?}" "${OUT:?}" "${SCORER:?}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT/raw" "$OUT/jobs" "$OUT/scores" "$OUT/scored" "$OUT/summaries"

if [ "$MODE" = eval ]; then
  NAME="${LABEL}_g1"; IDS="$TASK_IDS"
  GEN_ARGS=(--samples 1 --max-tokens 65536 --temperature 1.0 --top-p 0.95 --top-k 20)
elif [ "$MODE" = probe ]; then
  NAME="${LABEL}_g8"; IDS="$OUT/probe_task_ids.txt"
  [ -f "$IDS" ] || python -m rl4cv.veribench.pack --task-ids "$TASK_IDS" --per-split 4 --salt rl4cv-probe-v1 --out "$IDS"
  GEN_ARGS=(--samples 8 --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20)
else
  echo "mode must be eval or probe" >&2; exit 2
fi

if [ "$STAGE" = gen ] || [ "$STAGE" = all ]; then
  python -m rl4cv.veribench.generate --pack "$PACK" --task-ids "$IDS" --model "$MODEL" --revision "$REV" \
    --label "$NAME" --thinking on --seed 91 --tensor-parallel-size "$TP" --batch "$BATCH" "${GEN_ARGS[@]}" \
    --out "$OUT/raw/gen_${NAME}.jsonl"

  # Every declared cell must have a generation row before scoring (one-to-one manifest check).
  python - "$OUT/raw/gen_${NAME}.jsonl" "$IDS" "$MODE" <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
ids = [l.strip() for l in open(sys.argv[2]) if l.strip()]
k = 8 if sys.argv[3] == "probe" else 1
want = {(t, s) for t in ids for s in range(k)}
got = {(r["task_id"], r["sample_idx"]) for r in rows}
missing, extra = want - got, got - want
print(f"cells declared {len(want)}, generated {len(got)}, missing {len(missing)}, extra {len(extra)}")
sys.exit(1 if missing or extra or len(rows) != len(got) else 0)
EOF

  [ -d "$OUT/jobs/${NAME}_s0" ] || python -m rl4cv.veribench.jobs --gen "$OUT/raw/gen_${NAME}.jsonl" --out-root "$OUT/jobs" --name "$NAME"
  echo "gen done: $NAME"
fi

if [ "$STAGE" = score ] || [ "$STAGE" = all ]; then
  for JOB in "$OUT"/jobs/"${NAME}"_s*; do
    J="$(basename "$JOB")"
    [ -d "$OUT/scores/$J" ] && continue
    # Experiment 103's frozen scorer; --skip-tc because its built-in FSC is the retired Sonnet 4.6 judge.
    python "$SCORER/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py" \
      --job-dir "$(realpath "$JOB")" --pack "$PACK" --name "$J" --lake-dir "$LAKE_DIR" --skip-tc \
      --out-dir "$OUT/scores/$J"
  done

  FSC_ARGS=()
  [ -d "$OUT/fsc" ] && FSC_ARGS=(--fsc-root "$OUT/fsc")
  python -m rl4cv.veribench.collect --gen "$OUT/raw/gen_${NAME}.jsonl" --scores-root "$OUT/scores" --job-name "$NAME" \
    ${FSC_ARGS[@]+"${FSC_ARGS[@]}"} --out "$OUT/scored/scored_${NAME}.jsonl"
  python -m rl4cv.veribench.summarize --scored "$OUT/scored/scored_${NAME}.jsonl" --out "$OUT/summaries/summary_${NAME}.json"
  if [ "$MODE" = probe ]; then
    for CH in kernel_binary proof_fraction; do
      python -m rl4cv.probe --scored "$OUT/scored/scored_${NAME}.jsonl" --channel "$CH" --group-by split \
        --out "$OUT/summaries/rho_h_${NAME}_${CH}.json"
    done
  fi
  echo "done: $NAME"
fi
