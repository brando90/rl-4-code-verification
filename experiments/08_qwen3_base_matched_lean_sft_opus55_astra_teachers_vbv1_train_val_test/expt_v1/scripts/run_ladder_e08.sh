#!/usr/bin/env bash
# TLDR: Generate and kernel-score one system (a trained checkpoint or Base 14B) on one D-013 split for experiment 08 with experiment 05's exact
# command (G = 8, T = 0.6, top-p 0.95, top-k 20, 12,288-token cap, thinking template on, seed 91, stop <|im_end|>), the frozen scorer
# (`score_scsc.py --skip-tc`) in experiment 08's private grading project, then `collect` and `summarize` as diagnostics (PROTOCOL §§ 9–10).
# Usage: bash run_ladder_e08.sh <split: validation|test> <label> <model_path_or_hub_id> <revision_or_local> <gpu_ids_csv> [tp]
#   tp > 1 runs one vLLM process with --tensor-parallel-size tp over all listed GPUs; tp = 1 shards the task list across the GPUs.
# Env: E08_WORK (default /lfs/skampere1/0/brando9/rl4cv_e08); BATCH (default 1024), SCORE_PAR (default 4), STAGGER_S (default 180).
# Resumable: generation skips finished cells; scored jobs are never rescored; the shard count is fixed per label at first launch.
set -euo pipefail
SPLIT="${1:?validation|test}"; LABEL="${2:?label}"; MODEL="${3:?model}"; REV="${4:?revision or local}"; GPUS="${5:?gpu ids}"; TP="${6:-1}"
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
REPO="$WORK/rl-4-code-verification"
EXP="$REPO/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
E103_PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
SCORER="$REPO/external/veribench_scorer"
SCORE_PY="$SCORER/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
LAKE_DIR="$WORK/grading/lean_src"
GOLD_DIR="$SCORER/veribench_dataset/lean_src/veribench"
case "$SPLIT" in validation) IDS="$EXP/expt_v1/results/split/vbv1_validation_task_ids.txt"; N_TASKS=135 ;; test) IDS="$EXP/expt_v1/results/split/vbv1_test_task_ids.txt"; N_TASKS=222 ;; *) echo "bad split" >&2; exit 2 ;; esac
OUT="$WORK/ladder/$SPLIT"; mkdir -p "$OUT/raw" "$OUT/jobs" "$OUT/scores" "$OUT/scored" "$OUT/summaries" "$OUT/ids" "$OUT/logs"
BATCH="${BATCH:-1024}"; SCORE_PAR="${SCORE_PAR:-4}"; STAGGER_S="${STAGGER_S:-180}"
export PYTHONPATH="$REPO/src" VERIBENCH_ROOT="$REPO/external/veribench" HF_HOME="$WORK/cache/huggingface" HF_HUB_OFFLINE=1 PATH="$HOME/.elan/bin:$PATH"
PY="$WORK/venv_gen/bin/python"
NAME="${LABEL}_g8"; K=8
IFS=, read -ra G <<< "$GPUS"; N=${#G[@]}
ts() { date '+%m-%d-%Y %H:%M:%S'; }
# Pack view for the split (symlinks into experiment 103's pack; the scorer reads task.toml for its fixed denominator and the trials' config.json for identity).
VIEW="$WORK/pack_views/$SPLIT"; mkdir -p "$VIEW"
while read -r tid; do [ -n "$tid" ] && [ ! -e "$VIEW/$tid" ] && ln -s "$E103_PACK/$tid" "$VIEW/$tid"; done < "$IDS"
[ "$(ls "$VIEW" | wc -l)" = "$N_TASKS" ] || { echo "pack view has $(ls "$VIEW" | wc -l) tasks, expected $N_TASKS" >&2; exit 2; }
GEN_ARGS=(--pack "$E103_PACK" --model "$MODEL" --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --batch "$BATCH")
[ "$REV" != local ] && GEN_ARGS+=(--revision "$REV")

gen_tp() {  # one vLLM process over all GPUs
  local out="$OUT/raw/gen_${NAME}.shard0of1.jsonl"
  echo "$IDS" > /dev/null; cp "$IDS" "$OUT/raw/gen_${NAME}.shard0of1.ids"
  echo "[$(ts)] gen $NAME (tp=$TP) on GPUs $GPUS -> $out"
  CUDA_VISIBLE_DEVICES="$GPUS" "$PY" -m rl4cv.veribench.generate "${GEN_ARGS[@]}" --tensor-parallel-size "$TP" --samples "$K" --task-ids "$IDS" --label "$NAME" --out "$out" \
    >> "$OUT/logs/gen_${NAME}.shard0of1.log" 2>&1
}

gen_shards() {  # data-parallel shards, one vLLM process per GPU, staggered (flashinfer JIT-cache race seen in experiment 01)
  local pids=() j
  for j in "${!G[@]}"; do
    local ids="$OUT/raw/gen_${NAME}.shard${j}of${N}.ids" out="$OUT/raw/gen_${NAME}.shard${j}of${N}.jsonl"
    awk -v n="$N" -v j="$j" 'NF && $0 !~ /^#/ { if ((c++ % n) == j) print }' "$IDS" > "$ids"
    echo "[$(ts)] gen $NAME shard $j/$N on GPU ${G[$j]} -> $out"
    ( export CUDA_VISIBLE_DEVICES="${G[$j]}"
      "$PY" -m rl4cv.veribench.generate "${GEN_ARGS[@]}" --samples "$K" --task-ids "$ids" --label "$NAME" --out "$out"
    ) >> "$OUT/logs/gen_${NAME}.shard${j}of${N}.log" 2>&1 &
    pids+=($!)
    if [ "$j" -lt $((N - 1)) ]; then sleep "$STAGGER_S"; fi
  done
  local fail=0 p; for p in "${pids[@]}"; do wait "$p" || fail=1; done
  [ "$fail" = 0 ] || { echo "[$(ts)] a generation shard of $NAME failed; see $OUT/logs" >&2; return 1; }
}

merge_and_check() {  # writes gen_${NAME}.jsonl only if the manifest is exact (all tasks x 8 samples, no extras, no duplicates)
  local n="$1"
  "$PY" - "$IDS" "$K" "$OUT/raw/gen_${NAME}" "$n" <<'EOF'
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

if [ ! -f "$OUT/raw/gen_${NAME}.jsonl" ]; then
  if [ "$TP" -gt 1 ]; then NSH=1; gen_tp; else
    NFILE="$OUT/ids/${LABEL}.nshards"
    if [ -f "$NFILE" ] && [ "$(cat "$NFILE")" != "$N" ]; then echo "$LABEL was started with $(cat "$NFILE") shards; resume with that many GPUs (got $N)" >&2; exit 2; fi
    echo "$N" > "$NFILE"; NSH=$N; gen_shards
  fi
  merge_and_check "$NSH"
fi
echo "[$(ts)] gen done: $NAME"

if [ ! -f "$OUT/jobs/.done_$NAME" ]; then
  tmp="$OUT/jobs/.tmp_$NAME"; rm -rf "$tmp"
  "$PY" -m rl4cv.veribench.jobs --gen "$OUT/raw/gen_${NAME}.jsonl" --out-root "$tmp" --name "$NAME"
  mv "$tmp"/"${NAME}"_s* "$OUT/jobs"/ && rmdir "$tmp" && touch "$OUT/jobs/.done_$NAME"
fi

export JROOT="$OUT/jobs" SROOT="$OUT/scores" SCORE_PY VIEW LAKE_DIR GOLD_DIR OUT PY
ls -d "$OUT/jobs"/"${NAME}"_s* | xargs -n1 basename | xargs -P "$SCORE_PAR" -I{} bash -c '
  J={}; D="$SROOT/$J"
  if ls "$D"/*_per_task.csv >/dev/null 2>&1; then echo "already scored: $J"; exit 0; fi
  P="$SROOT/.partial_$J"; [ -e "$P" ] && mv "$P" "$SROOT/.interrupted_${J}_$(date +%Y%m%dT%H%M%S)"
  echo "[$(date "+%m-%d-%Y %H:%M:%S")] scoring $J"
  "$PY" "$SCORE_PY" --job-dir "$(realpath "$JROOT/$J")" --pack "$VIEW" --name "$J" --gold-dir "$GOLD_DIR" --lake-dir "$LAKE_DIR" --skip-tc --out-dir "$P" \
    > "$OUT/logs/score_$J.log" 2>&1 && mv "$P" "$D" && echo "scored: $J"'
for s in $(seq 0 $((K - 1))); do ls "$OUT/scores/${NAME}_s$s"/*_per_task.csv >/dev/null 2>&1 || { echo "[$(ts)] scoring incomplete: ${NAME}_s$s" >&2; exit 1; }; done
"$PY" -m rl4cv.veribench.collect --gen "$OUT/raw/gen_${NAME}.jsonl" --scores-root "$OUT/scores" --job-name "$NAME" --out "$OUT/scored/scored_${NAME}.jsonl"
"$PY" -m rl4cv.veribench.summarize --scored "$OUT/scored/scored_${NAME}.jsonl" --out "$OUT/summaries/summary_${NAME}.json" > /dev/null
echo "[$(ts)] done: $NAME"
