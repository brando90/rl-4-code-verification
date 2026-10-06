#!/usr/bin/env python3
"""Freeze the post-audit 16-cell reconciliation, including two null empty controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    panel_bytes = args.panel.read_bytes()
    panel = json.loads(panel_bytes)
    blocked = {"sqlfluff__sqlfluff-1763", "pvlib__pvlib-python-1606"}
    cells = []
    for task in panel["tasks"]:
        task_id = task["instance_id"]
        cells.append({"instance_id": task_id, "condition": "gold", "planned_execution": "report_backed_official_harness"})
        cells.append({"instance_id": task_id, "condition": "exact_empty_patch", "planned_execution": "null_retry_exhausted" if task_id in blocked else "adapter_skips_only_absent_patch_application", "original_patch_sha256": digest(b"")})
    manifest = {"schema": "e06_official_control_reconciliation_manifest_v3", "created_at": datetime.now(timezone.utc).isoformat(), "chronology": "Created after literal-empty filtering and two unadmitted marker attempts; no claim of prospective freeze for earlier wrappers.", "harness_commit": "f7bbbb2ccdf479001d6467c9e34af59e44a840f9", "panel_manifest_sha256": digest(panel_bytes), "declared_cells": len(cells), "eligible_cells": sum(cell["planned_execution"] != "null_retry_exhausted" for cell in cells), "null_cells": sorted(blocked), "cells": cells}
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
