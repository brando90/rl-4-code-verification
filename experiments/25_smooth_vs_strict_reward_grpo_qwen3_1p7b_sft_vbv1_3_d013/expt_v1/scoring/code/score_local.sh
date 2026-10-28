#!/bin/bash
# TLDR: Local replacement for Sherlock's score_sherlock.sh: runs the frozen VeriBench scorer (pin 59059a20, score_scsc.py --skip-tc)
# on one rollout job dir with the grading tree's own Lean v4.22.0 + Mathlib, exactly as Exp 8's run_validation.sh called it.
# usage: PYTHON=<python or hook> E20_GRADING=<grading tree> score_local.sh <job-dir> <pack> <out-dir>
set -euo pipefail
G=${E20_GRADING:?E20_GRADING not set}
export PATH="$G/bin:$PATH"          # `lake` for `lake env lean` (the old 'lake: No such file or directory' failure)
export ELAN_HOME="$G/elan"
if [ $# -ne 3 ]; then echo "usage: $0 <job-dir> <pack> <out-dir>" >&2; exit 64; fi
command -v lake >/dev/null || { echo "lake not on PATH ($G/bin)" >&2; exit 127; }
exec "${PYTHON:-python3}" "$G/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py" \
  --job-dir "$1" --pack "$2" --name "$(basename "$1")" --gold-dir "$G/veribench_scorer/veribench_dataset/lean_src/veribench" \
  --lake-dir "$G/lean_src" --skip-tc --out-dir "$3"
