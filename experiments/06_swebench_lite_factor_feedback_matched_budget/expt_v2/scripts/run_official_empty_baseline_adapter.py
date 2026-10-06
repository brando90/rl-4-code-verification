#!/usr/bin/env python3
"""Evaluate an exact empty patch by skipping only absent patch application in an adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import time


HARNESS_COMMIT = "f7bbbb2ccdf479001d6467c9e34af59e44a840f9"
CPUS, MEMORY_GIB, MAX_WORKERS, TIMEOUT_SECONDS = 4, 8, 2, 1800
MIN_DOCKER_FREE_GIB, MIN_SCRATCH_FREE_GIB, MAX_PROCESSOR_HOURS = 100, 1024, 160
DEADLINE = datetime(2026, 10, 7, 0, 7, tzinfo=timezone.utc)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"


def free_gib(path: Path) -> float:
    return shutil.disk_usage(path).free / (1024 ** 3)


def processor_hours(controls: Path) -> float:
    seconds = 0.0
    for receipt_path in controls.glob("*/receipt.json"):
        try:
            seconds += float(json.loads(receipt_path.read_text()).get("elapsed_seconds", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return seconds * CPUS / 3600


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    controls = runtime / "evaluator_controls"
    adapter = runtime / "evaluator_sources" / "SWE-bench-f7bbbb2-empty-baseline-adapter"
    source = runtime / "evaluator_sources" / "SWE-bench-f7bbbb2"
    python = runtime / "venv_v2_clean" / "bin" / "python"
    manifest_path = runtime / "evaluator_inputs" / "panel_evaluator_manifest.json"
    if not all((adapter.is_dir(), source.is_dir(), python.is_file(), manifest_path.is_file())):
        raise SystemExit("missing frozen evaluator adapter inputs")
    if free_gib(Path("/var/lib/docker")) < MIN_DOCKER_FREE_GIB or free_gib(runtime) < MIN_SCRATCH_FREE_GIB:
        raise SystemExit("storage free-space gate failed")
    if datetime.now(timezone.utc) >= DEADLINE or processor_hours(controls) >= MAX_PROCESSOR_HOURS:
        raise SystemExit("time or cumulative processor-hour gate failed")
    if len(subprocess.check_output(["docker", "ps", "-q", "--filter", "name=sweb.eval"], text=True).splitlines()) >= 2:
        raise SystemExit("two-container gate failed")
    panel_bytes = manifest_path.read_bytes()
    panel = json.loads(panel_bytes)
    if args.instance_id not in {task["instance_id"] for task in panel["tasks"]}:
        raise SystemExit("instance id is outside frozen panel")
    empty_patch = ""
    patch_hash = sha256(empty_patch.encode())
    task_hash = sha256(args.instance_id.encode())[:12]
    run_id = f"e06-empty-adapter-{task_hash}-{patch_hash[:12]}-a{args.attempt}"
    output = controls / f"empty_adapter_{args.instance_id}_{patch_hash[:16]}_a{args.attempt}"
    if output.exists():
        raise SystemExit("refusing to overwrite an existing adapter control")
    output.mkdir(mode=0o700)
    prediction = {"instance_id": args.instance_id, "model_name_or_path": "control-empty-adapter", "model_patch": empty_patch}
    prediction_path = output / "predictions.jsonl"
    prediction_bytes = canonical(prediction)
    prediction_path.write_bytes(prediction_bytes)
    command = [str(python), "-m", "swebench.harness.run_evaluation", "--dataset_name", str(runtime / "evaluator_inputs" / "lite_dev_rows.jsonl"), "--split", "dev", "--instance_ids", args.instance_id, "--predictions_path", str(prediction_path), "--max_workers", str(MAX_WORKERS), "--timeout", str(TIMEOUT_SECONDS), "--namespace", "none", "--run_id", run_id, "--cache_level", "env", "--clean", "false"]
    before = processor_hours(controls)
    receipt = {"schema_version": 1, "status": "RUNNING", "condition": "exact_empty_patch_adapter", "started_at": datetime.now(timezone.utc).isoformat(), "instance_id": args.instance_id, "attempt": args.attempt, "harness_commit": HARNESS_COMMIT, "panel_manifest_sha256": sha256(panel_bytes), "patch_sha256": patch_hash, "run_id": run_id, "command": command, "adapter": {"original_run_evaluation_sha256": sha256((source / "swebench/harness/run_evaluation.py").read_bytes()), "adapter_run_evaluation_sha256": sha256((adapter / "swebench/harness/run_evaluation.py").read_bytes()), "adapter_docker_build_sha256": sha256((adapter / "swebench/harness/docker_build.py").read_bytes()), "semantics": "same harness/test/grading; bypass only absent candidate-patch application on the unchanged base tree"}, "limits": {"max_workers": MAX_WORKERS, "container_cpus": CPUS, "container_memory_gib": MEMORY_GIB, "timeout_seconds": TIMEOUT_SECONDS, "deadline_utc": DEADLINE.isoformat()}, "cumulative_processor_hours_before": before, "free_space_gib_before": {"docker": free_gib(Path("/var/lib/docker")), "scratch": free_gib(runtime)}}
    receipt_path = output / "receipt.json"
    receipt_path.write_bytes(canonical(receipt))
    environment = os.environ | {"PYTHONPATH": str(adapter), "E06_EMPTY_BASELINE_ADAPTER": "1"}
    started = time.monotonic()
    completed = subprocess.run(command, cwd=adapter, capture_output=True, text=True, env=environment)
    (output / "stdout.log").write_text(completed.stdout)
    (output / "stderr.log").write_text(completed.stderr)
    report_path = adapter / "logs/run_evaluation" / run_id / "control-empty-adapter" / args.instance_id / "report.json"
    try:
        report = json.loads(report_path.read_text())
    except (OSError, json.JSONDecodeError):
        report = None
    valid = isinstance(report, dict) and args.instance_id in report and report[args.instance_id].get("patch_successfully_applied") is True
    elapsed = round(time.monotonic() - started, 3)
    receipt.update(status="COMPLETE" if completed.returncode == 0 and valid else "EVALUATOR_AMBIGUOUS", finished_at=datetime.now(timezone.utc).isoformat(), returncode=completed.returncode, elapsed_seconds=elapsed, stdout_sha256=sha256(completed.stdout.encode()), stderr_sha256=sha256(completed.stderr.encode()), report_path=str(report_path), report_sha256=sha256(report_path.read_bytes()) if report_path.is_file() else None, report_outcome=report[args.instance_id].get("resolved") if valid else None, cumulative_processor_hours_after=before + elapsed * CPUS / 3600, free_space_gib_after={"docker": free_gib(Path("/var/lib/docker")), "scratch": free_gib(runtime)})
    receipt_path.write_bytes(canonical(receipt))
    print(json.dumps({"status": receipt["status"], "output": str(output)}, sort_keys=True))
    return 0 if receipt["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
