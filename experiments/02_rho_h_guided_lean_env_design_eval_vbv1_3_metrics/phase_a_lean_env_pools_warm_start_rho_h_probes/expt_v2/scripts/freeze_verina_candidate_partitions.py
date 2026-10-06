#!/usr/bin/env python3
"""TLDR: Freeze outcome-blind disjoint VERINA candidate train, validation, and test partitions without admitting training."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact(record: dict) -> dict:
    return {key: record[key] for key in ("task_id", "upstream", "source_row_sha256", "file_sha256", "signature")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite frozen partition manifest: {args.out}")
    raw = args.candidate_manifest.read_bytes()
    manifest = json.loads(raw)
    if manifest.get("manifest_kind") != "VERINA_external24_screened_candidate_v1":
        raise ValueError("unexpected candidate manifest kind")
    clean_ids = set(manifest["screen"]["clean_ids"])
    eligible = [record for record in manifest["all_source_records"]
                if record["task_id"] in clean_ids and not record["lineage_excluded"]]
    ordered = sorted(eligible, key=lambda record: (record["source_row_sha256"], record["task_id"]))
    if len(ordered) < 72:
        raise RuntimeError(f"need at least 72 clean records for 24/24/nonempty partitions, found {len(ordered)}")
    expected_test = [task["task_id"] for task in manifest["tasks"]]
    actual_test = [record["task_id"] for record in ordered[:24]]
    if actual_test != expected_test:
        raise ValueError("candidate test panel is not the first 24 outcome-blind source-hash records")
    partitions = {"test": ordered[:24], "validation": ordered[24:48], "train": ordered[48:]}
    out = {
        "manifest_kind": "VERINA_candidate_train_validation_test_v1",
        "candidate_manifest_sha256": sha256(raw),
        "selection": "ascending source_row_sha256 then task_id; no compilation, model, judge, or repair outcome used",
        "partitions": {name: [compact(record) for record in records] for name, records in partitions.items()},
        "counts": {name: len(records) for name, records in partitions.items()},
        "training_admission": {
            "status": "NOT_ADMITTED",
            "reason": "candidate-only partitions: no accepted references, generic Lean endpoint adapter, Lean rollout reward path, or frozen numeric rho-H forecast",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "counts": out["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
