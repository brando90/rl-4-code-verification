#!/usr/bin/env bash
# TLDR: Run the experiment-13 version-2 fenced watchdog from cron or at reboot.
set -euo pipefail
WR="${E13_WORK_ROOT:-/lfs/skampere1/0/brando9/rl4cv_e13v2}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == --reboot ]]; then shift; fi
exec "$WR/venv/bin/python" "$HERE/watchdog_e13v2.py" "$@" check
