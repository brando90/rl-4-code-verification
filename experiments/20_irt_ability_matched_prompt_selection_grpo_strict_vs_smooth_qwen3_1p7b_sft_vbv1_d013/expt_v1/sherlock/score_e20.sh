#!/bin/bash
# TLDR: Score one materialized job directory (rl4cv.veribench.jobs layout) with VeriBench's frozen scorer (pin 59059a2,
# --skip-tc) through experiment 20's D-109 logged entry (logged_scorer_e20.py): same scorer, same gold dir, same Lean
# v4.22.0 + Mathlib project and `lake env lean` shim as $SCRATCH/rl4cv_sherlock/grading/score_sherlock.sh, plus durable
# compiler evidence under <out>/compiler_diagnostics/. CPU only; run inside a Slurm job.  usage: score_e20.sh <jobs-dir> <pack> <out>
set -euo pipefail
G=$SCRATCH/rl4cv_sherlock/grading; C=$SCRATCH/rl4cv_sherlock/e20/code
if [ $# -ne 3 ]; then echo "usage: $0 <jobs-dir> <pack> <out>" >&2; exit 64; fi
JOB="$(realpath "$1")"; PACK="$(realpath "$2")"; OUT="$(realpath -m "$3")"
[ -d "$JOB" ] || { echo "no job dir $JOB" >&2; exit 66; }
[ -d "$PACK" ] || { echo "no pack dir $PACK" >&2; exit 66; }
[ -f "$G/READY" ] || { echo "grading project not built ($G/READY missing)" >&2; exit 69; }
if [ -z "${PYTHON:-}" ]; then
  type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1 || true
  module load python/3.12.1 >/dev/null 2>&1 || true
  PYTHON="$(command -v python3.12 || command -v python3)"
fi
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN|OAUTH_TOKEN' || true); do unset "$k"; done
export CUDA_VISIBLE_DEVICES="" PYTHONPATH="$G/rl4cv/src" PATH="$G/bin:$PATH" TOKENIZERS_PARALLELISM=false
SCORER="$G/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
LEAN="$G/elan/toolchains/leanprover--lean4---v4.22.0/bin/lean"
mkdir -p "$OUT"
exec "$PYTHON" "$C/logged_scorer_e20.py" --scorer "$SCORER" --evidence-root "$OUT/compiler_diagnostics" --lean-executable "$LEAN" -- \
  --job-dir "$JOB" --pack "$PACK" --name "$(basename "$JOB")" \
  --gold-dir "$G/veribench_scorer/veribench_dataset/lean_src/veribench" --lake-dir "$G/lean_src" --skip-tc --out-dir "$OUT"
