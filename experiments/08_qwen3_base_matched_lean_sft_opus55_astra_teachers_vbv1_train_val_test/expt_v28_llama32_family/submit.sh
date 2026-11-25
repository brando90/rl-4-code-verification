#!/usr/bin/env bash
# TLDR: Submit the V28 smoke chain (prepare, short trainings, one smoke generation) or the full chain (6 trainings -> 6 generations
# -> 6x8 scoring -> collector); ids in jobs_v28.tsv (full) / jobs_v28_smoke.tsv (smoke).
# usage: cd $SCRATCH/rl4cv_sherlock/expt_v28 && bash submit.sh smoke    # first; read the smoke logs
#        cd $SCRATCH/rl4cv_sherlock/expt_v28 && bash submit.sh full     # after the smoke passed and prepare_receipt.json exists
#        cd $SCRATCH/rl4cv_sherlock/expt_v28_gemma_smoke && bash submit.sh gemma-smoke   # Gemma-3 smoke only, in its own copy of this folder
set -euo pipefail
cd "$(dirname "$0")"
MODE=${1:?smoke or full}
mkdir -p logs
MAIL=(--mail-type=BEGIN,END,FAIL --mail-user=brandojazz@gmail.com,brando.science@gmail.com)
DEP=(--kill-on-invalid-dep=yes)
sb() { sbatch --parsable --account=sanmi -D "$PWD" "${MAIL[@]}" "$@"; }
if [ "$MODE" = smoke ]; then
  T=jobs_v28_smoke.tsv
  test ! -e $T || { echo "Existing receipt $T" >&2; exit 2; }
  rec() { printf '%s\t%s\n' "$1" "$2" >> $T; }
  printf 'phase\tjob_id\n' > $T
  PREP=$(sb -p normal -c 4 --mem=32G -t 02:00:00 -J rl4cv-v28-prepare -o "$PWD/logs/%x_%j.out" run_job.sh prepare); rec prepare "$PREP"
  # 4 updates on the 4 longest examples: peak GPU memory at the worst case + export check. 3B: host optimizer (as configured) and,
  # as a second probe on another seed, the optimizer on the GPU, to learn whether the host optimizer is needed on an 80 GB card.
  S1=$(sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c 4 --mem=64G -t 01:00:00 --dependency="afterok:$PREP" "${DEP[@]}" \
    -J rl4cv-v28-smoke-llama1b -o "$PWD/logs/%x_%j.out" run_job.sh smoke llama1b 20260830 4 auto); rec smoke_llama1b "$S1"
  S3=$(sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c 16 --mem=128G -t 02:00:00 --dependency="afterok:$PREP" "${DEP[@]}" \
    -J rl4cv-v28-smoke-llama3b-host -o "$PWD/logs/%x_%j.out" run_job.sh smoke llama3b 20260830 4 auto); rec smoke_llama3b_host "$S3"
  S3D=$(sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c 4 --mem=64G -t 01:00:00 --dependency="afterok:$PREP" "${DEP[@]}" \
    -J rl4cv-v28-smoke-llama3b-dev -o "$PWD/logs/%x_%j.out" run_job.sh smoke llama3b 20260831 4 off); rec smoke_llama3b_device "$S3D"
  G1=$(SMOKE=1 sb -t 01:00:00 --export=ALL,SMOKE=1 --dependency="afterok:$S1" "${DEP[@]}" -J rl4cv-v28-smokegen-llama1b \
    -o "$PWD/logs/%x_%j.out" gen_v28.sbatch llama1b_s20260830 v28smoke_llama1b_s20260830); rec smokegen_llama1b "$G1"
  cat $T; squeue -u "$USER" -o '%.10i %.34j %.9P %.8T %.20R' | grep -E 'JOBID|rl4cv-v28' || true
  exit 0
fi
if [ "$MODE" = gemma-smoke ]; then
  # Separate package directory (own prepare_receipt.json, data/, cache/): the Llama receipt is never touched. Arms: gemma1b, gemma4b only.
  T=jobs_v28_gemma_smoke.tsv
  test ! -e $T || { echo "Existing receipt $T" >&2; exit 2; }
  rec() { printf '%s\t%s\n' "$1" "$2" >> $T; }
  printf 'phase\tjob_id\n' > $T
  export V28_MAX_SEQ=17408   # Gemma tokenizer: 2 of 1315 rows are 16385..17221 tokens (prepare 53689003 failed the 16384 gate); the smoke trains the longest rows first, so it measures that worst case
  export V28_ARMS=gemma1b,gemma4b   # sbatch passes the environment on (--export=ALL), so every job below sees it
  PREP=$(sb -p normal -c 4 --mem=48G -t 03:00:00 -J rl4cv-v28g-prepare -o "$PWD/logs/%x_%j.out" run_job.sh prepare); rec prepare "$PREP"
  # 4 updates on the 4 longest examples. 1B sdpa (as Llama) and 1B eager on another seed; 4B (multimodal checkpoint, text weights) with the
  # host optimizer under sdpa and under eager. Each records peak GPU memory and exports; the smoke generations check the vLLM load of the export.
  g() { V28_ATTN="$1" sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c "$2" --mem="$3" -t 02:00:00 \
        --dependency="afterok:$PREP" "${DEP[@]}" -J "rl4cv-v28g-smoke-$4" -o "$PWD/logs/%x_%j.out" run_job.sh smoke "$5" "$6" 4 auto; }
  S1=$(g sdpa 4 64G g1b-sdpa gemma1b 20260830); rec smoke_gemma1b_sdpa "$S1"
  S2=$(g eager 4 64G g1b-eager gemma1b 20260831); rec smoke_gemma1b_eager "$S2"
  S3=$(g sdpa 16 128G g4b-sdpa gemma4b 20260830); rec smoke_gemma4b_sdpa "$S3"
  S4=$(g eager 16 128G g4b-eager gemma4b 20260831); rec smoke_gemma4b_eager "$S4"
  gg() { SMOKE=1 sb -t 01:00:00 --export=ALL,SMOKE=1 --dependency="afterok:$1" "${DEP[@]}" -J "rl4cv-v28g-smokegen-$2" \
         -o "$PWD/logs/%x_%j.out" gen_v28.sbatch "$3" "v28smoke_$3"; }
  G1=$(gg "$S1" g1b gemma1b_s20260830); rec smokegen_gemma1b_sdpa "$G1"
  G4=$(gg "$S3" g4b gemma4b_s20260830); rec smokegen_gemma4b_sdpa "$G4"
  cat $T; squeue -u "$USER" -o '%.10i %.34j %.9P %.8T %.20R' | grep -E 'JOBID|rl4cv-v28g' || true
  exit 0
fi
test "$MODE" = full
test -f prepare_receipt.json || { echo "run the smoke chain first (prepare_receipt.json missing)" >&2; exit 2; }
test ! -e jobs_v28.tsv || { echo 'Existing submission receipt: inspect jobs_v28.tsv before another launch.' >&2; exit 2; }
rec() { printf '%s\t%s\n' "$1" "$2" >> jobs_v28.tsv; }
printf 'phase\tjob_id\n' > jobs_v28.tsv
ALL=""
# arm seed train-cpus train-mem train-wall gen-wall (llama1b: expt_v4's resources; llama3b: host optimizer, see PROTOCOL.md)
for spec in "llama1b 20260830 4 64G 04:00:00 05:00:00" "llama1b 20260831 4 64G 04:00:00 05:00:00" "llama1b 20260832 4 64G 04:00:00 05:00:00" \
            "llama3b 20260830 16 128G 12:00:00 08:00:00" "llama3b 20260831 16 128G 12:00:00 08:00:00" "llama3b 20260832 16 128G 12:00:00 08:00:00"; do
  read -r ARM SEED CPUS MEM TWALL GWALL <<< "$spec"
  RUN=${ARM}_s$SEED; L=v28_$RUN
  TR=$(sb -p gpu --gres=gpu:1 --constraint='GPU_MEM:80GB' -c "$CPUS" --mem="$MEM" -t "$TWALL" "${DEP[@]}" \
    -J "rl4cv-v28-train-$RUN" -o "$PWD/logs/%x_%j.out" run_job.sh train "$ARM" "$SEED")
  rec "train_$RUN" "$TR"
  GEN=$(sb -t "$GWALL" --dependency="afterok:$TR" "${DEP[@]}" -J "rl4cv-v28-gen-$RUN" -o "$PWD/logs/%x_%j.out" gen_v28.sbatch "$RUN" "$L")
  rec "gen_$RUN" "$GEN"
  SC=$(sb -t 03:00:00 --dependency="afterok:$GEN" "${DEP[@]}" -J "rl4cv-v28-score-$RUN" -o "$PWD/logs/%x_%A_%a.out" score_v28.sbatch "$L")
  rec "score_$RUN" "$SC"
  ALL="$ALL:$TR:$GEN:$SC"
done
COL=$(sb -p normal -c 1 --mem=4G -t 01:00:00 --dependency="afterany${ALL}" -J rl4cv-v28-collect -o "$PWD/logs/%x_%j.out" collect_v28.sh)
rec collect "$COL"
cat jobs_v28.tsv
squeue -u "$USER" -o '%.10i %.34j %.9P %.8T %.20R' | grep -E 'JOBID|rl4cv-v28' || true
