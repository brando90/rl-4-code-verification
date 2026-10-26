#!/bin/bash
# TLDR: Invoke the shared score_sherlock.sh unchanged, with its PYTHON hook forwarding only the frozen scorer entry
# through D-109 durable compiler capture. CPU only, in a Slurm job. usage: score_e20.sh <jobs-dir> <pack> <out>
set -euo pipefail
G=$SCRATCH/rl4cv_sherlock/grading; C=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [ $# -ne 3 ]; then echo "usage: $0 <jobs-dir> <pack> <out>" >&2; exit 64; fi
if [ -z "${PYTHON:-}" ]; then
  type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1 || true
  module load python/3.12.1 >/dev/null 2>&1 || true
  PYTHON="$(command -v python3.12 || command -v python3)"
fi
export E20_REAL_PYTHON="$PYTHON" E20_D109_OUT="$(realpath -m "$3")/compiler_diagnostics" E20_D109_CODE="$C"
export PYTHON="$C/scorer_python_e20.sh"
exec bash "$G/score_sherlock.sh" "$@"
