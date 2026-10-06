"""Freeze eight hash-selected SWE-bench Lite tasks without exposing evaluator metadata to solvers."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

PREFIX = "rl4cv-e06-v1:"
PANEL_SIZE = 8
CONDITIONS = ("ordinary", "scalar", "vector")
SOLVER_FIELDS = ("instance_id", "repo", "base_commit", "problem_statement")
EVALUATOR_FIELDS = ("patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(value):
    return json.loads(value, object_pairs_hook=_unique_object, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"invalid JSON constant: {token}")))


def read_rows(path):
    """Read arrays, a rows wrapper, or JSON Lines, rejecting ambiguous JSON."""
    raw = Path(path).read_bytes()
    if Path(path).suffix.lower() == ".jsonl":
        rows = [strict_json(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    else:
        rows = strict_json(raw)
        if isinstance(rows, dict):
            rows = rows.get("rows")
    if not isinstance(rows, list):
        raise ValueError("input must contain a JSON row array or JSON Lines")
    return rows, hashlib.sha256(raw).hexdigest()


def declared_cells(task_ids, models):
    cells = []
    for model in models:
        for task_id in task_ids:
            for condition, step in [("shared_initial", 0)] + [(c, s) for c in CONDITIONS for s in (1, 2)]:
                cell = {"model": model, "instance_id": task_id, "condition": condition, "step": step}
                cell["cell_id"] = digest(cell)
                cells.append(cell)
    return cells


def build_panel(rows, source_sha256, dataset_id, revision, split, models):
    if not dataset_id or not isinstance(dataset_id, str):
        raise ValueError("dataset ID is required")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        raise ValueError("revision must be an exact 40-character commit hash")
    if split not in ("dev", "validation"):
        raise ValueError("only the upstream development/validation split is permitted")
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("source SHA-256 must be a 64-character lowercase hash")
    if not models or any(not isinstance(m, str) or not m.strip() for m in models) or len(set(models)) != len(models):
        raise ValueError("models must be distinct nonempty exact identifiers")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each input row must be an object")
        for field in SOLVER_FIELDS:
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"missing or empty required field: {field}")
        task_id = row["instance_id"]
        if task_id in seen:
            raise ValueError(f"duplicate instance_id: {task_id}")
        seen.add(task_id)
        for field in EVALUATOR_FIELDS:
            if field not in row:
                raise ValueError(f"missing official evaluator metadata: {field}")
        for field in ("patch", "test_patch"):
            if not isinstance(row[field], str):
                raise ValueError(f"{field} must be a string")
        for field in ("FAIL_TO_PASS", "PASS_TO_PASS"):
            tests = row[field]
            if isinstance(tests, str):
                tests = strict_json(tests)
            if not isinstance(tests, list) or any(not isinstance(test, str) for test in tests):
                raise ValueError(f"{field} must contain a list of test identifiers")
        canonical(row)
    if len(rows) < PANEL_SIZE:
        raise ValueError(f"need at least {PANEL_SIZE} distinct rows")
    selected = sorted(rows, key=lambda row: (hashlib.sha256((PREFIX + row["instance_id"]).encode()).hexdigest(), row["instance_id"]))[:PANEL_SIZE]
    task_ids = [row["instance_id"] for row in selected]
    source = {"dataset_id": dataset_id, "revision": revision.lower(), "upstream_split": split, "logical_split": "validation", "source_sha256": source_sha256, "source_row_count": len(rows)}
    public = {"schema_version": 1, "experiment": "06_swebench_lite_factor_feedback_matched_budget", "selection": {"method": "ascending_sha256_of_prefix_plus_instance_id", "prefix": PREFIX, "panel_size": PANEL_SIZE}, "source": source, "models": list(models), "conditions": list(CONDITIONS), "task_ids": task_ids, "tasks": [{"instance_id": row["instance_id"], "row_sha256": digest(row)} for row in selected], "cells": declared_cells(task_ids, models)}
    public["design_sha256"] = digest(public)
    manifest_sha256 = hashlib.sha256(canonical(public) + b"\n").hexdigest()
    solver = [{field: row[field] for field in SOLVER_FIELDS} for row in selected]
    evaluator = {"schema_version": 1, "manifest_sha256": manifest_sha256, "source": source, "tasks": [{"instance_id": row["instance_id"], "row_sha256": digest(row), "official_row": row} for row in selected]}
    return public, solver, evaluator


def write_bundle(public_path, solver_path, evaluator_path, public, solver, evaluator, input_path=None):
    paths = [Path(p) for p in (public_path, solver_path, evaluator_path)]
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(paths) or (input_path is not None and Path(input_path).resolve() in resolved):
        raise ValueError("input and all output paths must be distinct")
    if any(p.exists() or p.is_symlink() for p in paths):
        raise FileExistsError("refusing to overwrite an existing frozen output")
    created = []
    try:
        for path, value, mode in zip(paths, (public, solver, evaluator), (0o644, 0o600, 0o600)):
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
            created.append(path)
            with os.fdopen(fd, "wb") as stream:
                stream.write(canonical(value) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
    except BaseException:
        for path in created:
            path.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--split", required=True, choices=("dev", "validation"))
    parser.add_argument("--models", required=True, nargs="+")
    parser.add_argument("--public-manifest", required=True, type=Path)
    parser.add_argument("--solver-view", required=True, type=Path)
    parser.add_argument("--evaluator-manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        rows, source_hash = read_rows(args.input)
        bundle = build_panel(rows, source_hash, args.dataset_id, args.revision, args.split, args.models)
        write_bundle(args.public_manifest, args.solver_view, args.evaluator_manifest, *bundle, input_path=args.input)
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(2, f"preparation failed: {exc}\n")
    print(json.dumps({"manifest_sha256": bundle[2]["manifest_sha256"], "tasks": PANEL_SIZE, "declared_cells": len(bundle[0]["cells"])}))


if __name__ == "__main__":
    main()
