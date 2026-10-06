#!/usr/bin/env bash
# TLDR: Run experiment 05 for one Qwen3 Base model: G=8 generation sharded across GPUs, merge + manifest check, jobs, frozen-scorer kernel scoring, collect, summarize and rho/H.
# Usage: bash run_model_e05.sh <hf_model_id> <revision> <label> <gpu_ids_csv> [all|gen|score|preflight]
# Required env (launch_e05.sh exports them): PACK, TASK_IDS, LAKE_DIR, OUT, SCORER, VERIBENCH_ROOT, and PYTHONPATH/venv for rl4cv + vLLM.
# Optional env: BATCH (generate.py --batch, default 1024; orchestration only), SCORE_PAR (concurrent scorers for this model,
# default 4), STAGGER_S (seconds between shard launches, default 180, avoids the flashinfer JIT-cache race seen in experiment 01).
# Resumable: generation skips finished cells per shard file; the shard count is fixed per model at first launch; a scored job is
# never rescored; an interrupted scorer's partial output is moved aside (kept), and the identical job is rerun.
set -euo pipefail
MODEL="$1"; REV="$2"; LABEL="$3"; GPUS="$4"; STAGE="${5:-all}"
BATCH="${BATCH:-1024}"; SCORE_PAR="${SCORE_PAR:-4}"; STAGGER_S="${STAGGER_S:-180}"
: "${PACK:?}" "${TASK_IDS:?}" "${LAKE_DIR:?}" "${OUT:?}" "${SCORER:?}" "${VERIBENCH_ROOT:?}"
export PACK TASK_IDS LAKE_DIR OUT SCORER VERIBENCH_ROOT
SCORE_PY="$SCORER/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
NAME="${LABEL}_g8"; K=8
IFS=, read -ra G <<< "$GPUS"; N=${#G[@]}
mkdir -p "$OUT/raw" "$OUT/jobs" "$OUT/scores" "$OUT/scored" "$OUT/summaries" "$OUT/ids" "$OUT/logs"
ts() { date '+%m-%d-%Y %H:%M:%S'; }
# Locked decoding (PROTOCOL.md): experiment 01's probe contract plus the Base-model stop token.
GEN_ARGS=(--pack "$PACK" --model "$MODEL" --revision "$REV" --thinking on --seed 91 --stop-token '<|im_end|>'
  --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --batch "$BATCH")

gen_shards() {  # $1 = id list, $2 = samples, $3 = output stem, $4 = condition label
  local ids_all="$1" k="$2" stem="$3" lab="$4" pids=() j
  for j in "${!G[@]}"; do
    local ids="${stem}.shard${j}of${N}.ids" out="${stem}.shard${j}of${N}.jsonl"
    awk -v n="$N" -v j="$j" 'NF && $0 !~ /^#/ { if ((c++ % n) == j) print }' "$ids_all" > "$ids"
    echo "[$(ts)] gen $lab shard $j/$N on GPU ${G[$j]} -> $out"
    ( export CUDA_VISIBLE_DEVICES="${G[$j]}"
      python -m rl4cv.veribench.generate "${GEN_ARGS[@]}" --samples "$k" --task-ids "$ids" --label "$lab" --out "$out"
    ) >> "$OUT/logs/$(basename "$stem").shard${j}of${N}.log" 2>&1 &
    pids+=($!)
    if [ "$j" -lt $((N - 1)) ]; then sleep "$STAGGER_S"; fi
  done
  local fail=0 p
  for p in "${pids[@]}"; do wait "$p" || fail=1; done
  [ "$fail" = 0 ] || { echo "[$(ts)] a generation shard of $lab failed; see $OUT/logs" >&2; return 1; }
}

merge_and_check() {  # $1 = id list, $2 = samples, $3 = output stem -> writes ${stem}.jsonl only if the manifest is exact
  python - "$1" "$2" "$3" "$N" <<'EOF'
import json, os, sys
ids_path, k, stem, n = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
ids = [l.strip() for l in open(ids_path) if l.strip() and not l.startswith("#")]
rows = [json.loads(l) for j in range(n) for l in open(f"{stem}.shard{j}of{n}.jsonl") if l.strip()]
got = {}
for r in rows:
    got.setdefault((r["task_id"], int(r["sample_idx"])), r)
want = {(t, s) for t in ids for s in range(k)}
missing, extra, dups = want - set(got), set(got) - want, len(rows) - len(got)
print(f"cells declared {len(want)}, generated {len(got)}, missing {len(missing)}, extra {len(extra)}, duplicate rows {dups}")
if missing or extra or dups:
    sys.exit(1)
order = {t: i for i, t in enumerate(ids)}
with open(stem + ".jsonl.tmp", "w", encoding="utf-8") as fh:
    for key in sorted(got, key=lambda x: (order[x[0]], x[1])):
        fh.write(json.dumps(got[key], ensure_ascii=False) + "\n")
os.replace(stem + ".jsonl.tmp", stem + ".jsonl")
EOF
}

make_jobs() {  # $1 = merged gen jsonl, $2 = job name, $3 = jobs root; atomic: build in a temp root, then move
  local gen="$1" name="$2" root="$3"
  [ -f "$root/.done_$name" ] && return 0
  local tmp="$root/.tmp_$name"; rm -rf "$tmp"
  python -m rl4cv.veribench.jobs --gen "$gen" --out-root "$tmp" --name "$name"
  mv "$tmp"/"${name}"_s* "$root"/ && rmdir "$tmp" && touch "$root/.done_$name"
}

score_jobs() {  # $1 = job name, $2 = jobs root, $3 = scores root
  local name="$1" jroot="$2" sroot="$3"
  export JROOT="$jroot" SROOT="$sroot" SCORE_PY
  ls -d "$jroot"/"${name}"_s* | xargs -n1 basename | xargs -P "$SCORE_PAR" -I{} bash -c '
    J={}; D="$SROOT/$J"
    if ls "$D"/*_per_task.csv >/dev/null 2>&1; then echo "already scored: $J"; exit 0; fi
    P="$SROOT/.partial_$J"
    [ -e "$P" ] && mv "$P" "$SROOT/.interrupted_${J}_$(date +%Y%m%dT%H%M%S)"
    echo "[$(date "+%m-%d-%Y %H:%M:%S")] scoring $J"
    # Experiment 103 frozen scorer; --skip-tc because its built-in FSC is the retired Sonnet 4.6 judge.
    python "$SCORE_PY" --job-dir "$(realpath "$JROOT/$J")" --pack "$PACK" --name "$J" --lake-dir "$LAKE_DIR" \
      --skip-tc --out-dir "$P" > "$OUT/logs/score_$J.log" 2>&1 && mv "$P" "$D" && echo "scored: $J"'
  local s; for s in $(seq 0 $((K - 1))); do
    ls "$sroot/${name}_s$s"/*_per_task.csv >/dev/null 2>&1 || { echo "[$(ts)] scoring incomplete: ${name}_s$s" >&2; return 1; }
  done
}

finish_stats() {  # collect -> summarize -> rho/H per split
  python -m rl4cv.veribench.collect --gen "$OUT/raw/gen_${NAME}.jsonl" --scores-root "$OUT/scores" --job-name "$NAME" \
    --out "$OUT/scored/scored_${NAME}.jsonl"
  python -m rl4cv.veribench.summarize --scored "$OUT/scored/scored_${NAME}.jsonl" --out "$OUT/summaries/summary_${NAME}.json" > /dev/null
  for CH in kernel_binary proof_fraction; do
    python -m rl4cv.probe --scored "$OUT/scored/scored_${NAME}.jsonl" --channel "$CH" --group-by split \
      --out "$OUT/summaries/rho_h_${NAME}_${CH}.json" > /dev/null
  done
}

if [ "$STAGE" = preflight ]; then
  # 5 tasks x 2 samples on the given GPU(s): prompt hashes, Base-vs-post-trained rendering, stop token, scorer path.
  PF="$OUT/preflight"; mkdir -p "$PF/jobs" "$PF/scores"
  head -5 "$TASK_IDS" > "$PF/preflight_ids.txt"
  [ -f "$PF/gen_${LABEL}_pf.jsonl" ] || { gen_shards "$PF/preflight_ids.txt" 2 "$PF/gen_${LABEL}_pf" "${LABEL}_pf"
    merge_and_check "$PF/preflight_ids.txt" 2 "$PF/gen_${LABEL}_pf"; }
  make_jobs "$PF/gen_${LABEL}_pf.jsonl" "${LABEL}_pf" "$PF/jobs"
  K=2 score_jobs "${LABEL}_pf" "$PF/jobs" "$PF/scores"
  python -m rl4cv.veribench.collect --gen "$PF/gen_${LABEL}_pf.jsonl" --scores-root "$PF/scores" --job-name "${LABEL}_pf" \
    --out "$PF/scored_${LABEL}_pf.jsonl"
  python "$(dirname "$0")/preflight_check_e05.py" --model "$MODEL" --revision "$REV" --gen "$PF/gen_${LABEL}_pf.jsonl" \
    --scored "$PF/scored_${LABEL}_pf.jsonl" --pack "$PACK" --ids "$PF/preflight_ids.txt" --out "$PF/preflight_${LABEL}.json"
  exit 0
fi

if [ "$STAGE" = gen ] || [ "$STAGE" = all ]; then
  NFILE="$OUT/ids/${LABEL}.nshards"
  if [ -f "$NFILE" ] && [ "$(cat "$NFILE")" != "$N" ]; then
    echo "$LABEL was started with $(cat "$NFILE") shards; resume with that many GPUs (got $N)" >&2; exit 2
  fi
  echo "$N" > "$NFILE"
  if [ ! -f "$OUT/raw/gen_${NAME}.jsonl" ]; then
    gen_shards "$TASK_IDS" "$K" "$OUT/raw/gen_${NAME}" "$NAME"
    merge_and_check "$TASK_IDS" "$K" "$OUT/raw/gen_${NAME}"
  fi
  make_jobs "$OUT/raw/gen_${NAME}.jsonl" "$NAME" "$OUT/jobs"
  echo "[$(ts)] gen done: $NAME"
fi

if [ "$STAGE" = score ] || [ "$STAGE" = all ]; then
  score_jobs "$NAME" "$OUT/jobs" "$OUT/scores"
  finish_stats
  echo "[$(ts)] done: $NAME"
fi
