#!/usr/bin/env python3
"""TLDR: Compile every frozen VERINA panel source unchanged under the pinned Lean 4.22 workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LEAN_TOOLCHAIN = "leanprover/lean4:v4.22.0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verina-root", type=Path, required=True)
    parser.add_argument("--lake-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 60:
        parser.error("timeout must be in [1, 60]")
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite receipt directory: {args.out}")
    if (args.lake_dir / "lean-toolchain").read_text().strip() != LEAN_TOOLCHAIN:
        raise ValueError("Lean workspace toolchain does not match required Lean 4.22 pin")
    version = subprocess.run(["lake", "env", "lean", "--version"], cwd=args.lake_dir,
                             capture_output=True, text=True, check=True, timeout=60).stdout.strip()
    if "Lean (version 4.22.0" not in version:
        raise ValueError(f"unexpected Lean runtime: {version}")
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("manifest_kind") != "VERINA_external24_screened_candidate_v1" or len(manifest.get("tasks", [])) != 24:
        raise ValueError("expected a frozen 24-task VERINA candidate manifest")
    args.out.mkdir(parents=True)
    logs = args.out / "logs"
    logs.mkdir()
    receipt = {
        "status": "RUNNING", "started_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256(manifest_bytes), "lake_dir": str(args.lake_dir.resolve()),
        "lean_version": version, "timeout_seconds": args.timeout_seconds, "rows": [],
        "scope": "original_VERINA_source_bytes_only_no_compatibility_edits",
    }
    out_path = args.out / "results.json"
    def save() -> None:
        out_path.write_text(json.dumps(receipt, indent=2) + "\n")
    save()
    for task in manifest["tasks"]:
        task_id = task["task_id"]
        expected = task["file_sha256"]
        task_dir = args.verina_root / "datasets" / "verina" / task_id
        actual = {name: sha256((task_dir / name).read_bytes()) for name in expected}
        if actual != expected:
            raise ValueError(f"source changed after panel freeze: {task_id}")
        source = task_dir / "task.lean"
        log_base = logs / task_id
        try:
            completed = run(["lake", "env", "lean", str(source.resolve())], cwd=args.lake_dir,
                            timeout=args.timeout_seconds)
            status = "pass" if completed.returncode == 0 else "fail"
            error = None
            return_code = completed.returncode
            stdout, stderr = completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            status, error, return_code = "unknown", "timeout", None
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
        (log_base.with_suffix(".stdout.txt")).write_bytes(stdout)
        (log_base.with_suffix(".stderr.txt")).write_bytes(stderr)
        receipt["rows"].append({
            "task_id": task_id, "source_row_sha256": task["source_row_sha256"],
            "task_lean_sha256": actual["task.lean"], "compile_status": status,
            "return_code": return_code, "reason": error,
            "stdout_sha256": sha256(stdout), "stderr_sha256": sha256(stderr),
            "stdout_path": str(log_base.with_suffix(".stdout.txt")),
            "stderr_path": str(log_base.with_suffix(".stderr.txt")),
        })
        save()
    receipt["status"] = "COMPLETE"
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps({"status": receipt["status"], "n_rows": len(receipt["rows"]),
                      "n_pass": sum(row["compile_status"] == "pass" for row in receipt["rows"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
