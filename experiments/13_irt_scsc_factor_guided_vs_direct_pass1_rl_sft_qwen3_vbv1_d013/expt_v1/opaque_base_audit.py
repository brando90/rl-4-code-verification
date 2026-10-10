#!/usr/bin/env python3
"""Run the sealed 21,504-cell historical equality audit without disclosing test outcomes.

The private manifest contains cell identities and historical/new evidence.  Every public file
written by this program is deliberately limited to digests, completeness and PASS/FAIL state.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from declaration_adapter import AdapterError, inspect_source, sha256
MODELS = ("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base")


class AuditError(ValueError):
    """A malformed, missing, duplicate, or replaced cell blocks exact reproduction."""


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(canonical(value) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def public_receipt(path: Path, **values: Any) -> None:
    """Only sanitized audit state is public; no row, label, factor, or diagnostic escapes."""
    allowed = {
        "kind", "status", "expected_cells", "manifest_cells", "processed_cells",
        "complete", "equality", "manifest_sha256", "input_sha256", "binding_sha256",
        "sealed", "outcomes_disclosed", "updated_at", "failure_class",
    }
    unexpected = set(values) - allowed
    if unexpected:
        raise AuditError("attempted public sealed detail")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, {"kind": "opaque_complete_base_equality_audit", "sealed": True,
                       "outcomes_disclosed": False, "updated_at": now(), **values})


def _score_files(scored_dir: Path) -> list[Path]:
    paths = [scored_dir / f"scored_{model}_g8.jsonl" for model in MODELS]
    if any(not path.is_file() for path in paths):
        raise AuditError("required scored input is missing")
    return paths


def _split(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = {row.get("task_id", ""): row for row in csv.DictReader(handle)}
    if not rows or "" in rows or any(not row.get("group_id") or row.get("split") not in {"train", "validation", "test"}
                                      for row in rows.values()):
        raise AuditError("split manifest is malformed")
    return rows


def _historical_strict(row: dict[str, Any]) -> float:
    if not isinstance(row.get("rewards"), dict):
        raise AuditError("scored row lacks frozen strict evidence")
    stored = row["rewards"].get("kernel_binary")
    if type(stored) not in (int, float) or stored not in (0, 1):
        raise AuditError("invalid stored strict evidence")
    return float(stored)


def _vacuity_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("e13_frozen_vacuity", path)
    if spec is None or spec.loader is None:
        raise AuditError("cannot load frozen vacuity module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _job_sources(jobs_root: Path, expected_cells: int) -> dict[tuple[str, str, int], tuple[Path, str]]:
    """Bind source bytes to their own historical receipt, never to score-display metadata."""
    indexed: dict[tuple[str, str, int], tuple[Path, str]] = {}
    receipts = list(jobs_root.rglob("receipt.json"))
    if len(receipts) != expected_cells:
        raise AuditError("historical job receipt denominator is incomplete")
    folder_pattern = re.compile(r"^(qwen3-(?:1\.7b|4b|8b)-base)_g8_s([0-7])$")
    for receipt_path in receipts:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AuditError("historical job receipt malformed") from exc
        match = folder_pattern.fullmatch(receipt_path.relative_to(jobs_root).parts[0])
        task_id, sample_idx, expected_sha = receipt.get("task_id"), receipt.get("sample_idx"), receipt.get("solution_sha256")
        if (match is None or not isinstance(task_id, str) or not task_id or type(sample_idx) is not int
                or not 0 <= sample_idx < 8 or sample_idx != int(match.group(2))
                or expected_sha is not None and (not isinstance(expected_sha, str) or len(expected_sha) != 64)):
            raise AuditError("historical job receipt typed binding rejected")
        model = match.group(1)
        key = (model, task_id, sample_idx)
        if key in indexed:
            raise AuditError("duplicate historical source receipt")
        source = receipt_path.parent / "verifier" / "solution.lean"
        if not source.is_file() or expected_sha is not None and sha256(source) != expected_sha:
            raise AuditError("historical source is unavailable or replaced")
        indexed[key] = (source, sha256(source))
    return indexed


def build_manifest(*, scored_dir: Path, jobs_root: Path, split_manifest: Path, private_dir: Path,
                   expected_cells: int = 21504) -> dict[str, Any]:
    """Create a private, typed, source-bound manifest; reject every completeness defect."""
    split = _split(split_manifest)
    sources = _job_sources(jobs_root, expected_cells)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for score_path, model in zip(_score_files(scored_dir), MODELS, strict=True):
        with score_path.open(encoding="utf-8") as handle:
            for raw in handle:
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise AuditError("malformed scored JSONL") from exc
                # File identity is the frozen policy identity.  Historical display-model text is
                # not a stable identifier and is validated only as a typed provenance field.
                if not isinstance(row, dict) or not isinstance(row.get("model"), str) or not row["model"]:
                    raise AuditError("scored row model provenance is malformed")
                task_id, sample_idx = row.get("task_id"), row.get("sample_idx")
                if not isinstance(task_id, str) or not task_id or type(sample_idx) is not int or not 0 <= sample_idx < 8:
                    raise AuditError("scored row identity is malformed")
                if task_id not in split:
                    raise AuditError("scored task is absent from split manifest")
                cell_id = f"{model}/{task_id}/{sample_idx}"
                if cell_id in seen:
                    raise AuditError("duplicate historical cell")
                seen.add(cell_id)
                try:
                    source, actual_sha = sources[(model, task_id, sample_idx)]
                except KeyError as exc:
                    raise AuditError("scored cell lacks historical source receipt") from exc
                old_strict = _historical_strict(row)
                rows.append({"cell_id": cell_id, "model": model, "task_id": task_id, "sample_idx": sample_idx,
                             "group_id": split[task_id]["group_id"], "split": split[task_id]["split"],
                             "source_path": str(source), "source_sha256": actual_sha,
                             "truncated": bool(row["truncated"]), "old_kernel_binary": old_strict})
    if len(rows) != expected_cells or len(seen) != expected_cells:
        raise AuditError("historical cell denominator is incomplete")
    if set(sources) != {(r["model"], r["task_id"], r["sample_idx"]) for r in rows}:
        raise AuditError("historical source receipt has missing or replacement cell")
    private_dir.mkdir(parents=True, exist_ok=False)
    manifest = private_dir / "sealed_manifest.jsonl"
    with manifest.open("x", encoding="utf-8") as handle:
        for row in sorted(rows, key=lambda entry: entry["cell_id"]):
            handle.write(canonical(row) + "\n")
    input_hashes = {path.name: sha256(path) for path in _score_files(scored_dir)}
    input_hashes[split_manifest.name] = sha256(split_manifest)
    result = {"manifest_sha256": sha256(manifest), "cells": len(rows), "input_sha256": input_hashes}
    atomic_json(private_dir / "manifest_binding.json", result)
    return result


def _read_manifest(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    ids = [row.get("cell_id") for row in rows]
    if not rows or len(ids) != len(set(ids)):
        raise AuditError("sealed manifest malformed or duplicated")
    for row in rows:
        if (set(row) != {"cell_id", "model", "task_id", "sample_idx", "group_id", "split", "source_path", "source_sha256", "truncated", "old_kernel_binary"}
                or row["split"] not in {"train", "validation", "test"} or row["old_kernel_binary"] not in (0.0, 1.0)):
            raise AuditError("sealed manifest typed binding rejected")
    return rows


def reproduce(*, private_dir: Path, scorer_root: Path, lake_dir: Path, vacuity_source: Path,
              public_path: Path, state_path: Path, binding_sha256: str, heartbeat_every: int = 30) -> int:
    """Sequential pinned Lean reproduction; checkpointed private outcomes, sanitized public state."""
    manifest_path = private_dir / "sealed_manifest.jsonl"
    rows = _read_manifest(manifest_path)
    binding = json.loads((private_dir / "manifest_binding.json").read_text(encoding="utf-8"))
    if binding["manifest_sha256"] != sha256(manifest_path):
        raise AuditError("sealed manifest hash changed")
    result_path = private_dir / "sealed_results.jsonl"
    done: set[str] = set()
    if result_path.exists():
        for line in result_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("cell_id") in done:
                raise AuditError("duplicate sealed result")
            done.add(row.get("cell_id"))
    if not done.issubset({row["cell_id"] for row in rows}):
        raise AuditError("sealed results contain replacement cell")
    vacuity = _vacuity_module(vacuity_source)
    # The historical adapter was written inside experiment 08; bind its import root to
    # this audit's frozen scorer checkout instead of its checkout-local default.
    vacuity.SCORER = scorer_root
    public_receipt(public_path, status="RUNNING", expected_cells=len(rows), manifest_cells=len(rows),
                   processed_cells=len(done), complete=False, equality="PENDING", manifest_sha256=binding["manifest_sha256"],
                   input_sha256=binding["input_sha256"], binding_sha256=binding_sha256)
    atomic_json(state_path, {"status": "RUNNING", "processed_cells": len(done), "expected_cells": len(rows),
                             "manifest_sha256": binding["manifest_sha256"], "updated_at": now()})
    with result_path.open("a", encoding="utf-8") as result_file:
        for ordinal, row in enumerate(rows, 1):
            if row["cell_id"] in done:
                continue
            source = Path(row["source_path"])
            try:
                source_text = source.read_text(encoding="utf-8")
                vac = vacuity.vacuity(source_text) if source_text.strip() else {"n_vacuous": 0, "unparseable": []}
                if vac["unparseable"]:
                    raise AuditError("unparseable theorem type")
                measured = inspect_source(source, lake_dir=lake_dir, scorer_root=scorer_root,
                                          expected_sha256=row["source_sha256"], vacuous_count=vac["n_vacuous"],
                                          truncated=row["truncated"])
                private = {"cell_id": row["cell_id"], "strict_equal": measured["strict"] == row["old_kernel_binary"],
                           "strict": measured["strict"], "old_kernel_binary": row["old_kernel_binary"],
                           "d": measured["d"], "t": measured["t"], "p": measured["p"],
                           "factored_reward": measured["factored_reward"], "status": "measured"}
            except (AdapterError, AuditError, OSError, UnicodeError, ValueError):
                private = {"cell_id": row["cell_id"], "status": "unmeasured", "failure_class": "source_or_pinned_probe_rejected"}
            result_file.write(canonical(private) + "\n")
            result_file.flush()
            os.fsync(result_file.fileno())
            processed = ordinal
            if processed % heartbeat_every == 0 or processed == len(rows):
                atomic_json(state_path, {"status": "RUNNING", "processed_cells": processed, "expected_cells": len(rows),
                                         "manifest_sha256": binding["manifest_sha256"], "updated_at": now()})
                public_receipt(public_path, status="RUNNING", expected_cells=len(rows), manifest_cells=len(rows),
                               processed_cells=processed, complete=False, equality="PENDING",
                               manifest_sha256=binding["manifest_sha256"], input_sha256=binding["input_sha256"],
                               binding_sha256=binding_sha256)
    results = [json.loads(line) for line in result_path.read_text(encoding="utf-8").splitlines() if line]
    complete = len(results) == len(rows) and {r["cell_id"] for r in results} == {r["cell_id"] for r in rows}
    equality = complete and all(r.get("status") == "measured" and r.get("strict_equal") is True for r in results)
    status = "PASS" if equality else "FAIL"
    atomic_json(state_path, {"status": status, "processed_cells": len(results), "expected_cells": len(rows),
                             "manifest_sha256": binding["manifest_sha256"], "updated_at": now()})
    public_receipt(public_path, status=status, expected_cells=len(rows), manifest_cells=len(rows),
                   processed_cells=len(results), complete=complete, equality="PASS" if equality else "FAIL",
                   manifest_sha256=binding["manifest_sha256"], input_sha256=binding["input_sha256"], binding_sha256=binding_sha256)
    return 0 if equality else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("build", "reproduce"), required=True)
    parser.add_argument("--scored-dir", type=Path)
    parser.add_argument("--jobs-root", type=Path)
    parser.add_argument("--split-manifest", type=Path)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--scorer-root", type=Path)
    parser.add_argument("--lake-dir", type=Path)
    parser.add_argument("--vacuity-source", type=Path)
    parser.add_argument("--binding-sha256", default="UNFROZEN")
    parser.add_argument("--expected-cells", type=int, default=21504)
    parser.add_argument("--heartbeat-every", type=int, default=30)
    args = parser.parse_args()
    try:
        if args.mode == "build":
            if not all((args.scored_dir, args.jobs_root, args.split_manifest)):
                raise AuditError("build inputs required")
            built = build_manifest(scored_dir=args.scored_dir, jobs_root=args.jobs_root, split_manifest=args.split_manifest,
                                   private_dir=args.private_dir, expected_cells=args.expected_cells)
            public_receipt(args.public_receipt, status="MANIFEST_READY", expected_cells=args.expected_cells,
                           manifest_cells=built["cells"], processed_cells=0, complete=False, equality="PENDING",
                           manifest_sha256=built["manifest_sha256"], input_sha256=built["input_sha256"],
                           binding_sha256=args.binding_sha256)
            atomic_json(args.state, {"status": "MANIFEST_READY", "processed_cells": 0, "expected_cells": args.expected_cells,
                                     "manifest_sha256": built["manifest_sha256"], "updated_at": now()})
            return 0
        if not all((args.scorer_root, args.lake_dir, args.vacuity_source)):
            raise AuditError("reproduction inputs required")
        return reproduce(private_dir=args.private_dir, scorer_root=args.scorer_root, lake_dir=args.lake_dir,
                         vacuity_source=args.vacuity_source, public_path=args.public_receipt, state_path=args.state,
                         binding_sha256=args.binding_sha256, heartbeat_every=args.heartbeat_every)
    except AuditError:
        # Do not print sealed context.  Public receipt records the generic operational class only.
        public_receipt(args.public_receipt, status="FAIL", expected_cells=args.expected_cells, manifest_cells=0,
                       processed_cells=0, complete=False, equality="FAIL", manifest_sha256="UNAVAILABLE",
                       input_sha256={}, binding_sha256=args.binding_sha256, failure_class="typed_input_or_execution_rejected")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
