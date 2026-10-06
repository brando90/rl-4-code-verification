#!/usr/bin/env python3
"""Create a provenance-preserving 24-cell control reconciliation manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--failed-resume", type=Path, required=True)
    parser.add_argument("--retry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline = load(args.baseline)
    failed = load(args.failed_resume)
    retry = load(args.retry)
    resumed = {row["cell"]: row for row in retry["rows"]}
    rows = []
    for row in baseline["rows"]:
        cell = row["cell"]
        source = args.retry if cell in resumed else args.baseline
        selected = resumed.get(cell, row)
        rows.append(
            {
                "cell": cell,
                "status": selected["status"],
                "control_matches": selected.get("control_matches"),
                "immutable_row_source": str(source),
                "immutable_row_source_sha256": sha256(source),
                "row": selected,
            }
        )
    measured = [row for row in rows if row["status"] == "MEASURED"]
    output = {
        "schema": "e04_endpoint_control_reconciliation_v1",
        "scope": "authored_harness_validation_only",
        "declared_cells": baseline["declared_cells"],
        "reconciled_cells": len(rows),
        "measured_cells": len(measured),
        "matching_cells": sum(row["control_matches"] is True for row in measured),
        "baseline_receipt": {"path": str(args.baseline), "sha256": sha256(args.baseline)},
        "interrupted_resume_receipt": {
            "path": str(args.failed_resume),
            "sha256": sha256(args.failed_resume),
            "status": failed["status"],
            "executed_cells": failed.get("executed_cells", len(failed["rows"])),
            "note": "Preflight failed before any resumed cell measurement; preserved rather than overwritten.",
        },
        "identical_infrastructure_retry_receipt": {"path": str(args.retry), "sha256": sha256(args.retry)},
        "manifest_sha256": baseline["manifest_sha256"],
        "baseline_script_sha256": baseline["script_sha256"],
        "retry_script_sha256": retry["script_sha256"],
        "toolchain": retry["preflight"],
        "kernel": {"commit": retry["kernel_commit"], "sha256": retry["kernel_sha256"]},
        "rows": rows,
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    if len(rows) != baseline["declared_cells"] or len(measured) != baseline["declared_cells"]:
        return 2
    if output["matching_cells"] != baseline["declared_cells"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
