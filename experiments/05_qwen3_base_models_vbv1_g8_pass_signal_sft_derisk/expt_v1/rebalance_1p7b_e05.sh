#!/usr/bin/env bash
# TLDR: Speed up experiment 05's single-GPU Qwen3-1.7B-Base generation: freed GPUs generate its not-yet-started 128-task blocks (top down), shard 0 is stopped at a block boundary, then the pieces are merged and 1.7B scoring starts.
# Orchestration only (agents-config Trigger Rule 57): identical cells, prompt, decoding and per-sample seeds (91*100003 + k);
# PROTOCOL.md is unchanged. Shard 0 generates tasks in id-list order in batches of 1,024 cells = 128-task blocks, so block b
# = tasks [128b, 128b+128). A helper on each listed GPU waits until that GPU has no compute process, then atomically claims
# (mkdir) the highest unclaimed block above shard 0's current block and generates it into its own file. A watcher stops shard 0
# the moment it finishes a block whose successor is claimed, so no cell is generated twice (the merge still keeps the first
# copy of any duplicate and counts it). Finally the exact 896 x 8 manifest is checked, gen_qwen3-1.7b-base_g8.jsonl is
# written, and the qwen3-1.7b-base window is restarted for jobs, scoring (SCORE_PAR=8) and statistics.
# Usage (in tmux, after `source $WORK/env_e05.sh`): bash rebalance_1p7b_e05.sh 7,1,2,3,5,6,0     DRY=1 prints the plan only.
set -euo pipefail
GPUS="${1:?helper GPU csv}"; DRY="${DRY:-0}"
: "${OUT:?}" "${TASK_IDS:?}" "${PACK:?}"
WORK=/lfs/skampere1/0/brando9/rl4cv_e05
HERE=$WORK/rl-4-code-verification/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1
SESSION=rl4cv-e05-qwen3-base-g8
MODEL=Qwen/Qwen3-1.7B-Base; REV=ea980cb0a6c2ae4b936e82123acc929f1cec04c1; LABEL=qwen3-1.7b-base; NAME=${LABEL}_g8; K=8
S0="$OUT/raw/gen_${NAME}.shard0of1.jsonl"; S0PAT="^python[0-9.]* -m rl4cv[.]veribench[.]generate .*gen_${NAME}[.]shard0of1[.]jsonl"  # anchored: only the generator itself
CL="$OUT/claims_1p7b"; mkdir -p "$CL" "$OUT/logs"
BT=128; CPB=$((BT * K))
NT=$(awk 'NF && $0 !~ /^#/' "$TASK_IDS" | wc -l); NB=$(( (NT + BT - 1) / BT ))
GEN_ARGS=(--pack "$PACK" --model "$MODEL" --revision "$REV" --thinking on --seed 91 --stop-token '<|im_end|>'
  --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --batch 1024 --samples "$K" --label "$NAME")
ts() { date '+%m-%d-%Y %H:%M:%S'; }
rows() { if [ -f "$S0" ]; then wc -l < "$S0"; else echo 0; fi; }
current_block() {  # shard 0's block in progress; once shard 0 is stopped, the last block it completed
  if [ -f "$CL/shard0_stopped_rows" ]; then echo $(( $(cat "$CL/shard0_stopped_rows") / CPB - 1 )); else echo $(( $(rows) / CPB )); fi
}

if [ "$DRY" = 1 ]; then
  echo "tasks $NT, blocks $NB of $BT tasks; shard0 rows $(rows); shard0 current block $(current_block); claims: $(ls "$CL" | tr '\n' ' ')"
  echo "shard0 pids: $(pgrep -f "$S0PAT" | tr '\n' ' ')"
  for g in ${GPUS//,/ }; do echo "GPU $g compute pids: $(nvidia-smi -i "$g" --query-compute-apps=pid --format=csv,noheader | tr '\n' ' ')"; done
  exit 0
fi

descendants() { local p; for p in $(pgrep -P "$1" || true); do echo "$p"; descendants "$p"; done; }

watch_shard0() {
  while true; do
    local r; r=$(rows)
    if [ $((r % CPB)) -eq 0 ] && [ "$r" -gt 0 ] && [ -d "$CL/block$((r / CPB))" ]; then
      local pids; pids="$(for p in $(pgrep -f "$S0PAT" || true); do echo "$p"; descendants "$p"; done | sort -u | tr '\n' ' ')"
      echo "[$(ts)] shard0 completed blocks 0..$((r / CPB - 1)) ($r rows); block $((r / CPB)) belongs to a helper: stopping shard0 pids $pids"
      echo "$r" > "$CL/shard0_stopped_rows"
      [ -n "$pids" ] && kill $pids 2>/dev/null || true
      sleep 30
      for p in $pids; do kill -0 "$p" 2>/dev/null && kill -9 "$p" 2>/dev/null || true; done
      return 0
    fi
    if ! pgrep -f "$S0PAT" > /dev/null; then
      echo "[$(ts)] shard0 is not running (rows $r): recording where it stopped"
      echo "$r" > "$CL/shard0_stopped_rows"; return 0
    fi
    sleep 2
  done
}

run_block() {  # $1 = block, $2 = GPU
  local b="$1" g="$2" ids="$CL/block$1.ids" out="$OUT/raw/gen_${NAME}.block$1.jsonl" try
  awk 'NF && $0 !~ /^#/' "$TASK_IDS" | sed -n "$((b * BT + 1)),$(((b + 1) * BT))p" > "$ids"
  local want=$(( $(wc -l < "$ids") * K ))
  for try in 1 2 3; do  # infrastructure retries rerun the identical cells (generate.py resumes from its own file)
    echo "[$(ts)] GPU $g: block $b (tasks $((b * BT))..$((b * BT + $(wc -l < "$ids") - 1))), attempt $try -> $out"
    ( export CUDA_VISIBLE_DEVICES="$g"; python -m rl4cv.veribench.generate "${GEN_ARGS[@]}" --task-ids "$ids" --out "$out" ) \
      >> "$OUT/logs/gen_${NAME}.block$b.log" 2>&1 || true
    if [ -f "$out" ] && [ "$(wc -l < "$out")" -eq "$want" ]; then touch "$CL/block$b/done"; echo "[$(ts)] GPU $g: block $b done ($want cells)"; return 0; fi
    sleep 60
  done
  echo "[$(ts)] GPU $g: block $b FAILED after 3 attempts; see $OUT/logs/gen_${NAME}.block$b.log" >&2; return 1
}

helper() {  # $1 = GPU
  local g="$1" b cur claimed
  while true; do
    until [ -z "$(nvidia-smi -i "$g" --query-compute-apps=pid --format=csv,noheader)" ]; do sleep 60; done
    cur=$(current_block); claimed=""
    for ((b = NB - 1; b > cur; b--)); do
      if mkdir "$CL/block$b" 2>/dev/null; then claimed=$b; break; fi
    done
    if [ -z "$claimed" ]; then echo "[$(ts)] GPU $g: no unclaimed block above shard0's block $cur; helper exits"; return 0; fi
    run_block "$claimed" "$g" || return 1
  done
}

echo "[$(ts)] rebalance start: $NT tasks, $NB blocks; shard0 rows $(rows); helper GPUs $GPUS"
watch_shard0 & WPID=$!
HP=(); for g in ${GPUS//,/ }; do helper "$g" & HP+=($!); sleep 5; done
fail=0; for p in "${HP[@]}"; do wait "$p" || fail=1; done
# Helpers exit once no block above shard 0 is left; shard 0 then finishes its own block (or is stopped at a boundary).
wait "$WPID" || true
while pgrep -f "$S0PAT" > /dev/null; do sleep 30; done
[ "$fail" = 0 ] || { echo "[$(ts)] a helper failed; fix and rerun this script (claims and finished blocks are kept)" >&2; exit 1; }

python - "$TASK_IDS" "$K" "$S0" "$OUT/raw/gen_${NAME}" "$CL" "$NB" <<'EOF'
import json, os, sys
ids_path, k, s0, stem, cl, nb = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6])
ids = [l.strip() for l in open(ids_path) if l.strip() and not l.startswith("#")]
sources = [s0] + [f"{stem}.block{b}.jsonl" for b in range(nb) if os.path.isfile(f"{stem}.block{b}.jsonl")]
got, dups, per_source = {}, 0, {}
for src in sources:
    n = 0
    for line in open(src, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line); key = (r["task_id"], int(r["sample_idx"])); n += 1
        if key in got:
            dups += 1  # an infrastructure duplicate of the identical cell: keep the first copy, never choose by score
        else:
            got[key] = r
    per_source[os.path.basename(src)] = n
want = {(t, s) for t in ids for s in range(k)}
missing, extra = want - set(got), set(got) - want
receipt = {"sources": per_source, "cells_declared": len(want), "cells_merged": len(got), "missing": len(missing),
           "extra": len(extra), "duplicates_dropped_keep_first": dups}
print(json.dumps(receipt, indent=2))
json.dump(receipt, open(os.path.join(cl, "merge_receipt.json"), "w"), indent=2)
if missing or extra:
    sys.exit(1)
order = {t: i for i, t in enumerate(ids)}
with open(stem + ".jsonl.tmp", "w", encoding="utf-8") as fh:
    for key in sorted(got, key=lambda x: (order[x[0]], x[1])):
        fh.write(json.dumps(got[key], ensure_ascii=False) + "\n")
os.replace(stem + ".jsonl.tmp", stem + ".jsonl")
EOF

# Restart the 1.7B window for jobs, scoring and statistics (its generation stage is skipped now that the merged file exists).
LOG="$WORK/logs/driver_${LABEL}.log"
if tmux list-windows -t "$SESSION" -F '#W' | grep -qx "$LABEL"; then
  tail -n 3 "$LOG" | grep -q '^EXIT=' || { echo "[$(ts)] window $LABEL has no EXIT line yet; not replacing a live writer" >&2; exit 1; }
  tmux kill-window -t "$SESSION:$LABEL"
fi
tmux new-window -d -t "$SESSION" -n "$LABEL" \
  "bash -c 'source $WORK/env_e05.sh; set -o pipefail; SCORE_PAR=8 bash $HERE/run_model_e05.sh $MODEL $REV $LABEL 0 all 2>&1 | tee -a $LOG; echo EXIT=\$? >> $LOG; exec bash'"
echo "[$(ts)] merged; restarted window $LABEL for scoring with SCORE_PAR=8"
