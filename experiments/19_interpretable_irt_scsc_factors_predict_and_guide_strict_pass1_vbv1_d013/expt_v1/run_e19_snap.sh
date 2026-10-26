#!/usr/bin/env bash
# TLDR: Run experiment 19's locked real-data analysis once (CPU only, zero model calls) from a checkout at the lock commit; refuses to start if HEAD differs, and ends its log with RUN_EXIT=<code>.
set -euo pipefail
LOCK="${1:?usage: run_e19_snap.sh <lock commit>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
cd "$ROOT"
HEAD_NOW="$(git rev-parse HEAD)"
if [ "$HEAD_NOW" != "$LOCK" ]; then
  echo "refusing: HEAD $HEAD_NOW is not the lock commit $LOCK" >&2
  exit 3
fi
if [ -n "$(git status --porcelain -- "$HERE")" ]; then
  echo "refusing: the experiment folder has uncommitted changes" >&2
  exit 3
fi
PY="${E19_PY:-python3}"
OUT="$HERE/results"
LOG="$OUT/run_e19.log"
mkdir -p "$OUT"
{
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) host $(hostname) lock $LOCK"
  "$PY" -c 'import sys, numpy, scipy; print("python", sys.version.split()[0], "numpy", numpy.__version__, "scipy", scipy.__version__)'
} | tee "$LOG"
set +e
"$PY" -u "$HERE/analyze_e19.py" --workers "${E19_WORKERS:-32}" --out "$OUT" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
set -e
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ) RUN_EXIT=$rc" | tee -a "$LOG"
exit "$rc"
