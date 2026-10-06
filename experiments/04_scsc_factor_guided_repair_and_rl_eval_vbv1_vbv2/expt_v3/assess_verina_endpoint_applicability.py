#!/usr/bin/env python3
"""TLDR: Record every frozen VERINA panel task's Lean 4.22 and endpoint-adapter applicability without altering its source."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCORER_COMMIT = "59059a20d40adf3289869e58302169ad78102877"
KERNEL_PATH = "scripts/scsc/kernel_axioms.py"
KERNEL_SHA256 = "5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
REQUIRED_MARKERS = ("precond", "code", "postcond", "proof")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_kernel(scorer_repo: Path, out: Path):
    import subprocess
    data = subprocess.run(["git", "-C", str(scorer_repo), "show", f"{SCORER_COMMIT}:{KERNEL_PATH}"],
                          check=True, capture_output=True).stdout
    if sha256(data) != KERNEL_SHA256:
        raise ValueError("pinned kernel inspector bytes do not match the scorer lock")
    path = out / "kernel_axioms_pinned.py"
    path.write_bytes(data)
    spec = importlib.util.spec_from_file_location("verina_endpoint_kernel", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if set(module.ALLOWED_AXIOMS) != ALLOWED_AXIOMS:
        raise ValueError("pinned kernel inspector axiom policy mismatch")
    return module


def source_markers(text: str) -> dict[str, int]:
    return {name: len(re.findall(rf"-- !benchmark @start {re.escape(name)}(?:\s|$)", text)) for name in REQUIRED_MARKERS}


def ref_status(module, source: Path, theorem: str, lake_dir: Path, evidence: Path) -> dict:
    evidence.mkdir(parents=True, exist_ok=False)
    try:
        report = module.check_file(str(source), str(lake_dir), timeout=30, allow_native_decide=False,
                                   keep_dir=str(evidence)).to_dict()
    except Exception as exc:  # The checker's own report treats infrastructure as unknown; preserve it.
        return {"status": "unknown", "reason": "kernel_inspector_infrastructure_failure", "detail": str(exc)}
    (evidence / "kernel_report.json").write_text(json.dumps(report, indent=2) + "\n")
    if report.get("probe_ok") is not True or report.get("compile_rc") != 0:
        return {"status": "unknown", "reason": "original_source_compile_or_inspection_failed", "report_sha256": sha256(json.dumps(report, sort_keys=True).encode())}
    matches = [row for row in report.get("theorems", []) if row.get("name") == theorem]
    if len(matches) != 1 or matches[0].get("resolution") != "source_position":
        return {"status": "unknown", "reason": "reference_theorem_not_resolved_exactly", "report_sha256": sha256(json.dumps(report, sort_keys=True).encode())}
    row = matches[0]
    axioms = row.get("axioms")
    if not isinstance(axioms, list) or set(axioms) - ALLOWED_AXIOMS:
        return {"status": "fail", "reason": "forbidden_transitive_axioms", "axioms": axioms, "report_sha256": sha256(json.dumps(report, sort_keys=True).encode())}
    if row.get("category") != "honest" or row.get("kernel_honest") is not True:
        return {"status": "fail", "reason": "reference_theorem_not_kernel_honest", "category": row.get("category"), "report_sha256": sha256(json.dumps(report, sort_keys=True).encode())}
    return {"status": "pass", "reason": "original_reference_proof_kernel_honest", "axioms": axioms,
            "report_sha256": sha256(json.dumps(report, sort_keys=True).encode())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--compile-receipt", type=Path, required=True)
    parser.add_argument("--verina-root", type=Path, required=True)
    parser.add_argument("--lake-dir", type=Path, required=True)
    parser.add_argument("--scorer-repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite applicability receipt: {args.out}")
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    compiled = json.loads(args.compile_receipt.read_text())
    compiled_by_id = {row["task_id"]: row for row in compiled["rows"]}
    if len(manifest.get("tasks", [])) != 24 or set(compiled_by_id) != {task["task_id"] for task in manifest["tasks"]}:
        raise ValueError("candidate and compilation manifests do not describe the same frozen 24 tasks")
    args.out.mkdir(parents=True)
    kernel = load_kernel(args.scorer_repo, args.out)
    receipt = {
        "status": "RUNNING", "started_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256(manifest_bytes), "compile_receipt_sha256": sha256(args.compile_receipt.read_bytes()),
        "endpoint_contract": "restricted_authored_control_endpoint_accepts_only_bounded_JSON_Nat_to_Nat_AST_candidates",
        "rows": [],
    }
    result_path = args.out / "results.json"
    def save() -> None:
        result_path.write_text(json.dumps(receipt, indent=2) + "\n")
    save()
    for task in manifest["tasks"]:
        task_id = task["task_id"]
        task_dir = args.verina_root / "datasets" / "verina" / task_id
        source = task_dir / "task.lean"
        actual_hashes = {name: sha256((task_dir / name).read_bytes()) for name in task["file_sha256"]}
        if actual_hashes != task["file_sha256"]:
            raise ValueError(f"source changed after panel freeze: {task_id}")
        metadata = json.loads((task_dir / "task.json").read_text())
        name = metadata["signature"]["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"unsafe/noncanonical callable name: {task_id}")
        text = source.read_text(encoding="utf-8", errors="replace")
        markers = source_markers(text)
        proof = ref_status(kernel, source, name + "_spec_satisfied", args.lake_dir,
                           args.out / "evidence" / task_id)
        compile_row = compiled_by_id[task_id]
        parser = {"status": "pass" if all(markers.values()) else "fail", "markers": markers,
                  "reason": "VERINA benchmark sections found" if all(markers.values()) else "missing_required_benchmark_section"}
        interface = {
            "status": "unsupported",
            "reason": "no audited mechanical adapter from arbitrary VERINA Lean source/callable signatures to the restricted JSON Nat-to-Nat endpoint",
            "candidate_hash_status": "unavailable_without_adapter",
            "fixed_requirement_identity_status": "unavailable_without_adapter",
        }
        receipt["rows"].append({
            "task_id": task_id, "source_row_sha256": task["source_row_sha256"],
            "source_compile_lean422": {"status": compile_row["compile_status"], "return_code": compile_row["return_code"]},
            "original_reference_proof": proof, "parser": parser, "callable_interface": interface,
            "endpoint_applicable": False,
            "endpoint_status": "unsupported_adapter",
        })
        save()
    n_applicable = sum(row["endpoint_applicable"] for row in receipt["rows"])
    receipt.update({
        "status": "COMPLETE", "finished_at": datetime.now(timezone.utc).isoformat(),
        "n_declared": len(receipt["rows"]), "n_endpoint_applicable": n_applicable,
        "practical_gate": {"threshold": "20/24", "verdict": "FAIL", "reason": "0/24 tasks have an audited adapter satisfying candidate-hash and fixed-requirement-identity requirements"},
        "next_action": "do not admit repair or judge calls; a new version would need an independently validated generic Lean endpoint adapter",
    })
    save()
    print(json.dumps({"status": receipt["status"], "n_declared": len(receipt["rows"]), "n_endpoint_applicable": n_applicable}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
