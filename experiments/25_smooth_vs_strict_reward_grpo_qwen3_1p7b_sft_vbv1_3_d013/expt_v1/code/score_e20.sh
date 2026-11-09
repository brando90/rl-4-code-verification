#!/bin/bash
# TLDR: Local (no Slurm, no Sherlock) strict scorer entry for Experiment 25's train_e25.py score(): the same CLI as Exp 20's
# score_e20.sh (<job-dir> <pack> <out>), with Exp 20's D-109 durable compiler capture, calling score_local.sh in place of the
# Sherlock-only score_sherlock.sh. Needs E20_GRADING (set by train_e25.py) = the grading tree that setup_local_grading.sh built.
set -euo pipefail
C=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
G=${E20_GRADING:-$(cd "$C/../grading" && pwd)}
if [ $# -ne 3 ]; then echo "usage: $0 <jobs-dir> <pack> <out>" >&2; exit 64; fi
export E20_GRADING="$G"
if [ -z "${PYTHON:-}" ]; then PYTHON="$(command -v python3.12 || command -v python3)"; fi
export E20_REAL_PYTHON="$PYTHON" E20_D109_OUT="$(realpath -m "$3")/compiler_diagnostics" E20_D109_CODE="$C"
export PYTHON="$C/scorer_python_e20.sh"
exec bash "$C/score_local.sh" "$@"
