#!/usr/bin/env bash
# TLDR: 11-25-2026, fail closed until experiment 02B has a real admitted training command; then launch one bounded logged tmux job.
set -euo pipefail
TASK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$TASK_DIR/launch_admitted_11-25-2026.py" "$TASK_DIR/launch_admission_11-25-2026.json" "$@"
