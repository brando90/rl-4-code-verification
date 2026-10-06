#!/usr/bin/env python3
"""TLDR: Freeze an outcome-blind, contamination-screened FVAPPS external-24 candidate manifest without treating stub specs as accepted references."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rl4cv.screens import screen  # noqa: E402

FVAPPS_REVISION = "3552a173e74837dd0017d72431c6ede8fa903bb7"
FVAPPS_TRAIN_SHA256 = "e0874ed37ab4c0a1e727cc2e11fdc9d4add5f34316ddc726b1f3922d60146bc1"
ROW_FIELDS = ("apps_id", "apps_question", "spec", "units", "assurance_level", "apps_difficulty", "sorries")


def canonical_row_hash(row: dict) -> str:
    payload = {key: row[key] for key in ROW_FIELDS}
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_corpus(veribench_root: Path) -> dict[str, str]:
    dataset = veribench_root / "veribench_dataset"
    py_root, lean_root = dataset / "py_src", dataset / "lean_src"
    if not py_root.is_dir() or not lean_root.is_dir():
        raise FileNotFoundError("expected VeriBench veribench_dataset/{py_src,lean_src}")
    files = [p for p in py_root.rglob("*.py") if "__pycache__" not in p.parts]
    files += [p for p in lean_root.rglob("*.lean") if ".lake" not in p.parts and "lean-playground" not in p.parts]
    corpus = {
        str(path.relative_to(dataset)): path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(files)
    }
    if not corpus:
        raise RuntimeError("protected VeriBench corpus is empty; contamination screening fails closed")
    return corpus


def git_evidence(root: Path) -> dict[str, object]:
    def call(*argv: str) -> str:
        return subprocess.run(argv, cwd=root, text=True, capture_output=True, check=True).stdout.strip()
    return {"git_head": call("git", "rev-parse", "HEAD"), "dirty_paths": call("git", "status", "--porcelain").splitlines()}


def task_text(row: dict) -> str:
    return "\n".join((row["apps_question"], row["spec"], row["units"]))


def load_json_records(path: Path) -> list[dict]:
    """Read newline-delimited JSON robustly when a source string contains a literal line break."""
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict] = []
    offset = 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            break
        row, offset = decoder.raw_decode(text, offset)
        if not isinstance(row, dict):
            raise ValueError("FVAPPS source contains a non-object JSON record")
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fvapps-train", type=Path, required=True)
    parser.add_argument("--veribench-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite frozen candidate manifest: {args.out}")

    observed_file_sha = source_sha256(args.fvapps_train)
    if observed_file_sha != FVAPPS_TRAIN_SHA256:
        raise ValueError(f"FVAPPS train SHA-256 mismatch: {observed_file_sha}")
    rows = load_json_records(args.fvapps_train)
    for row in rows:
        missing = set(ROW_FIELDS) - set(row)
        if missing:
            raise ValueError(f"FVAPPS row missing fields: {sorted(missing)}")
    curated = [row for row in rows if row["assurance_level"] == "guarded_and_plausible"]
    eligible = [
        row for row in rows
        if row["assurance_level"] == "guarded_and_plausible" and row["spec"].strip() and row["units"].strip()
    ]
    ids = [row["apps_id"] for row in eligible]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate FVAPPS apps_id in eligible rows would invalidate screening")
    protected = protected_corpus(args.veribench_root)
    report = screen({row["apps_id"]: task_text(row) for row in eligible}, protected)
    clean_ids = set(report["clean_ids"])
    clean_rows = sorted((row for row in eligible if row["apps_id"] in clean_ids), key=lambda row: (canonical_row_hash(row), row["apps_id"]))
    selected = clean_rows[:24]
    if len(selected) != 24:
        raise RuntimeError(f"need 24 screened candidates, found {len(selected)}")
    if any("sorry" not in row["spec"] for row in selected):
        raise RuntimeError("selection contract expects FVAPPS stub specifications; inspect schema before changing status")

    manifest = {
        "manifest_kind": "FVAPPS_external24_screened_candidate_v1",
        "selection_is_outcome_blind": True,
        "source": {
            "dataset": "quinn-dougherty/fvapps",
            "revision": FVAPPS_REVISION,
            "split": "train",
            "train_jsonl_sha256": observed_file_sha,
            "schema_fields": list(ROW_FIELDS),
            "n_rows": len(rows),
            "n_guarded_and_plausible": len(curated),
            "n_guarded_and_plausible_nonempty_spec_and_units": len(eligible),
        },
        "protected_corpus": {
            "veribench_root": str(args.veribench_root.resolve()),
            "n_files": len(protected),
            "file_sha256": {name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in protected.items()},
            "checkout": git_evidence(args.veribench_root),
            "exact_hash_normalization": "rl4cv.screens.normalize",
            "word_shingle_n": 5,
            "near_duplicate_threshold": 0.7,
        },
        "screen": report,
        "reference_gate": {
            "status": "BLOCKED_PENDING_ACCEPTED_REFERENCES",
            "reason": "FVAPPS `spec` defines executable symbols and theorem bodies with `sorry`; its `units` use #eval on those symbols. A syntactic Lean compile is not an accepted reference: `sorry` violates the allowed-axiom policy and the units cannot evaluate through sorryAx.",
            "required_before_fixed_reference_or_repair_use": [
                "compile a materialized implementation/reference under Lean 4.22.0",
                "prove every named obligation with only propext, Classical.choice, Quot.sound",
                "rerun the exact-hash and word-5-gram screens at the execution checkout",
                "freeze a disjoint train/validation/test allocation before model outcomes",
            ],
        },
        "tasks": [
            {
                "task_id": f"fvapps_train_{row['apps_id']}",
                "apps_id": row["apps_id"],
                "source_row_sha256": canonical_row_hash(row),
                "assurance_level": row["assurance_level"],
                "difficulty": row["apps_difficulty"],
                "declared_sorries": row["sorries"],
                "reference_status": "SCREENED_CANDIDATE_PENDING_REFERENCE_ACCEPTANCE",
            }
            for row in selected
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "n_selected": len(selected), "screen": {k: report[k] for k in ("n_exact", "n_near")}}, sort_keys=True))


if __name__ == "__main__":
    main()
