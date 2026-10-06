#!/usr/bin/env python3
"""TLDR: Freeze a screened VERINA 24-task candidate panel before Lean 4.22 compilation or any model outcome."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rl4cv.screens import screen  # noqa: E402

VERINA_COMMIT = "66b3ce5014edafb20cb26b87c681e7f31847249f"
DISALLOWED_LINEAGE = {"humaneval", "verisoftbench", "verisoft"}
SOURCE_FILES = ("task.json", "description.txt", "task.lean", "test.json", "reject_inputs.json")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"required VERINA task file missing: {path}")
    return path.read_bytes()


def protected_corpus(veribench_root: Path) -> dict[str, str]:
    dataset = veribench_root / "veribench_dataset"
    paths = []
    for root in (dataset / "py_src", dataset / "lean_src"):
        if not root.is_dir():
            raise FileNotFoundError(f"missing protected corpus root: {root}")
        paths.extend(p for p in root.rglob("*") if p.is_file() and p.suffix in {".py", ".lean"}
                     and ".lake" not in p.parts and "lean-playground" not in p.parts)
    result = {str(p.relative_to(dataset)): p.read_text(encoding="utf-8", errors="replace") for p in sorted(paths)}
    if not result:
        raise RuntimeError("protected corpus is empty; contamination screen fails closed")
    return result


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], text=True, check=True,
                          capture_output=True).stdout.strip()


def task_record(task_dir: Path) -> dict:
    raw = {name: read_bytes(task_dir / name) for name in SOURCE_FILES}
    metadata = json.loads(raw["task.json"])
    task_id = metadata.get("id")
    if not isinstance(task_id, str) or task_id != task_dir.name:
        raise ValueError(f"task id/path mismatch: {task_dir}")
    upstream = metadata.get("metadata", {}).get("upstream", {}).get("name")
    if not isinstance(upstream, str) or not upstream:
        raise ValueError(f"missing upstream lineage: {task_id}")
    lineage = upstream.lower().replace("-", "").replace("_", "")
    excluded = any(token in lineage for token in DISALLOWED_LINEAGE)
    source_blob = b"".join(name.encode("utf-8") + b"\0" + raw[name] + b"\0" for name in SOURCE_FILES)
    return {
        "task_id": task_id,
        "upstream": upstream,
        "lineage_excluded": excluded,
        "source_row_sha256": sha256(source_blob),
        "file_sha256": {name: sha256(data) for name, data in raw.items()},
        "lean_text": raw["task.lean"].decode("utf-8", errors="replace"),
        "signature": metadata.get("signature"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verina-root", type=Path, required=True)
    parser.add_argument("--veribench-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite frozen candidate manifest: {args.out}")
    if git(args.verina_root, "rev-parse", "HEAD") != VERINA_COMMIT:
        raise ValueError("VERINA source commit mismatch")
    dataset = args.verina_root / "datasets" / "verina"
    records = [task_record(path) for path in sorted(dataset.iterdir()) if path.is_dir()]
    if not records:
        raise RuntimeError("VERINA dataset has no task directories")
    lineage_clean = [r for r in records if not r["lineage_excluded"]]
    protected = protected_corpus(args.veribench_root)
    screening = screen({r["task_id"]: r["lean_text"] for r in lineage_clean}, protected)
    clean_ids = set(screening["clean_ids"])
    clean = sorted((r for r in lineage_clean if r["task_id"] in clean_ids),
                   key=lambda r: (r["source_row_sha256"], r["task_id"]))
    selected = clean[:24]
    if len(selected) != 24:
        raise RuntimeError(f"need 24 source-lineage-clean candidates, found {len(selected)}")
    for record in records:
        record.pop("lean_text")
    manifest = {
        "manifest_kind": "VERINA_external24_screened_candidate_v1",
        "selection_is_outcome_blind": True,
        "source": {
            "repository": "https://github.com/sunblaze-ucb/verina",
            "commit": VERINA_COMMIT,
            "tree": git(args.verina_root, "rev-parse", "HEAD^{tree}"),
            "license": "Apache-2.0",
            "source_lean_toolchain": (args.verina_root / "lean-toolchain").read_text().strip(),
            "schema": {"task_files": list(SOURCE_FILES), "required_task_json_keys": ["id", "signature", "metadata", "test_file", "reject_inputs_file"]},
            "n_total": len(records),
            "n_lineage_excluded": len(records) - len(lineage_clean),
            "lineage_exclusion_tokens": sorted(DISALLOWED_LINEAGE),
        },
        "protected_corpus": {
            "veribench_root": str(args.veribench_root.resolve()),
            "checkout": {"git_head": git(args.veribench_root, "rev-parse", "HEAD")},
            "n_files": len(protected),
            "exact_hash_normalization": "rl4cv.screens.normalize",
            "word_shingle_n": 5,
            "near_duplicate_threshold": 0.7,
        },
        "screen": screening,
        "all_source_records": records,
        "tasks": [{
            "task_id": r["task_id"], "upstream": r["upstream"], "source_row_sha256": r["source_row_sha256"],
            "file_sha256": r["file_sha256"], "signature": r["signature"],
            "reference_status": "FROZEN_PENDING_LEAN422_APPLICABILITY",
        } for r in selected],
        "reference_gate": {
            "status": "PENDING_LEAN422_COMPILATION_AND_ENDPOINT_ADAPTER",
            "required_before_repair_or_training_use": [
                "compile each original source byte sequence under the pinned Lean 4.22 workspace",
                "verify accepted reference theorems have only propext, Classical.choice, Quot.sound",
                "materialize fixed tests and requirements through a mechanical, reviewed callable adapter",
                "preserve unsupported cases and freeze disjoint train/validation/test allocations",
            ],
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "n_total": len(records), "n_selected": len(selected),
                      "n_exact": screening["n_exact"], "n_near": screening["n_near"]}, sort_keys=True))


if __name__ == "__main__":
    main()
