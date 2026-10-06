#!/usr/bin/env python3
"""Freeze the reconciled 8x2 official-control manifest without raw evaluator data."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


INERT_BASELINE_PATCH = """diff --git a/.e06_empty_control b/.e06_empty_control
new file mode 100644
index 0000000..e69de29
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    panel_bytes = args.panel.read_bytes()
    panel = json.loads(panel_bytes)
    cells = []
    for task in panel["tasks"]:
        identifier = task["instance_id"]
        gold = task["official_row"]["patch"]
        cells.extend(
            [
                {"instance_id": identifier, "condition": "gold", "patch_sha256": sha256(gold.encode()), "attempt": 1},
                {
                    "instance_id": identifier,
                    "condition": "empty_semantic_baseline",
                    "patch_sha256": sha256(INERT_BASELINE_PATCH.encode()),
                    "attempt": 2,
                    "supersedes": "attempt-1 literal empty patch, which the official harness filtered without evaluation",
                },
            ]
        )
    output = {
        "schema": "e06_official_control_manifest_v2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chronology": "Reconciliation manifest created after five gold and five literal-empty wrappers; it is not prospective for those observed wrappers.",
        "panel_manifest_sha256": sha256(panel_bytes),
        "harness_commit": "f7bbbb2ccdf479001d6467c9e34af59e44a840f9",
        "declared_cells": len(cells),
        "cells": cells,
    }
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
