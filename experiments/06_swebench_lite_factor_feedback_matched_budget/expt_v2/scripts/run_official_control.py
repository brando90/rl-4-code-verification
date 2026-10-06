"""Run one sealed SWE-bench control with report-backed completion and fixed limits."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


HARNESS_COMMIT = "f7bbbb2ccdf479001d6467c9e34af59e44a840f9"
CPUS = 4
MEMORY_GIB = 8
MAX_WORKERS = 2
TIMEOUT_SECONDS = 1800
MIN_DOCKER_FREE_GIB = 100
MIN_SCRATCH_FREE_GIB = 1024
MAX_PROCESSOR_HOURS = 160
DEADLINE = datetime(2026, 10, 7, 0, 7, tzinfo=timezone.utc)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"


def exclusive_json(path: Path, value: object) -> None:
    payload = canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def free_gib(path: Path) -> float:
    return shutil.disk_usage(path).free / (1024 ** 3)


def previous_processor_hours(controls: Path) -> float:
    total_seconds = 0.0
    for receipt_path in controls.glob("*/receipt.json"):
        try:
            receipt = json.loads(receipt_path.read_text())
            total_seconds += float(receipt.get("elapsed_seconds", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return total_seconds * CPUS / 3600


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--kind", choices=("gold", "empty"), required=True)
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    if args.kind == "empty":
        raise SystemExit("literal empty patches are filtered by this harness; use the audited empty-baseline adapter")

    runtime = args.runtime.resolve()
    if (runtime / "evaluator_controls" / "PAUSE_ADMISSION").exists():
        raise SystemExit("control admission paused pending deterministic reconciliation")
    evaluator = runtime / "evaluator_sources" / "SWE-bench-f7bbbb2"
    python = runtime / "venv_v2_clean" / "bin" / "python"
    manifest_path = runtime / "evaluator_inputs" / "panel_evaluator_manifest.json"
    if not python.is_file() or not manifest_path.is_file() or not evaluator.is_dir():
        raise SystemExit("missing sealed evaluator inputs")
    if free_gib(Path("/var/lib/docker")) < MIN_DOCKER_FREE_GIB:
        raise SystemExit("Docker free-space gate failed")
    if free_gib(runtime) < MIN_SCRATCH_FREE_GIB:
        raise SystemExit("scratch free-space gate failed")
    if datetime.now(timezone.utc) >= DEADLINE:
        raise SystemExit("18-hour deadline gate failed")

    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    task = next((x for x in manifest["tasks"] if x["instance_id"] == args.instance_id), None)
    if task is None:
        raise SystemExit("instance id is outside the frozen eight-task panel")
    patch = task["official_row"]["patch"]
    patch_hash = sha256(patch.encode())
    task_token = hashlib.sha256(args.instance_id.encode()).hexdigest()[:12]
    run_id = f"e06-{args.kind}-{task_token}-{patch_hash[:12]}-a{args.attempt}"
    controls = runtime / "evaluator_controls"
    controls.mkdir(mode=0o700, exist_ok=True)
    if previous_processor_hours(controls) >= MAX_PROCESSOR_HOURS:
        raise SystemExit("cumulative 160 processor-hour gate failed")
    if len([line for line in subprocess.check_output(["docker", "ps", "-q", "--filter", "name=sweb.eval"], text=True).splitlines() if line]) >= 2:
        raise SystemExit("two-container gate failed")
    output = controls / f"{args.kind}_{args.instance_id}_{patch_hash[:16]}_a{args.attempt}"
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing control: {output}")
    output.mkdir(mode=0o700)
    prediction = {"instance_id": args.instance_id, "model_name_or_path": f"control-{args.kind}", "model_patch": patch}
    prediction_bytes = canonical(prediction)
    prediction_path = output / "predictions.jsonl"
    prediction_path.write_bytes(prediction_bytes)
    command = [str(python), "-m", "swebench.harness.run_evaluation", "--dataset_name",
               str(runtime / "evaluator_inputs" / "lite_dev_rows.jsonl"), "--split", "dev",
               "--instance_ids", args.instance_id, "--predictions_path", str(prediction_path),
               "--max_workers", str(MAX_WORKERS), "--timeout", str(TIMEOUT_SECONDS), "--namespace",
               "none", "--run_id", run_id, "--cache_level", "env", "--clean", "false",
               "--report_dir", str(output / "reports")]
    receipt = {"schema_version": 2, "status": "RUNNING", "started_at": datetime.now(timezone.utc).isoformat(),
               "instance_id": args.instance_id, "kind": args.kind, "harness_commit": HARNESS_COMMIT,
               "panel_manifest_sha256": sha256(manifest_bytes), "prediction_sha256": sha256(prediction_bytes),
               "patch_sha256": patch_hash, "run_id": run_id, "command": command,
               "limits": {"max_workers": MAX_WORKERS, "container_cpus": CPUS,
                          "container_memory_gib": MEMORY_GIB, "timeout_seconds": TIMEOUT_SECONDS},
               "cumulative_processor_hours_before": previous_processor_hours(controls),
               "deadline_utc": DEADLINE.isoformat(),
               "free_space_gib_before": {"docker": free_gib(Path("/var/lib/docker")), "scratch": free_gib(runtime)}}
    receipt_path = output / "receipt.json"
    exclusive_json(receipt_path, receipt)
    started = time.monotonic()
    completed = subprocess.run(command, cwd=evaluator, capture_output=True, text=True)
    (output / "stdout.log").write_text(completed.stdout)
    (output / "stderr.log").write_text(completed.stderr)
    report_path = evaluator / "logs" / "run_evaluation" / run_id / prediction["model_name_or_path"] / args.instance_id / "report.json"
    report = None
    if report_path.is_file():
        try:
            report = json.loads(report_path.read_text())
        except json.JSONDecodeError:
            pass
    if completed.returncode != 0:
        status = "EVALUATOR_FAILURE"
    elif not isinstance(report, dict) or args.instance_id not in report:
        status = "EVALUATOR_AMBIGUOUS"
    elif report[args.instance_id].get("patch_successfully_applied") is not True:
        status = "EVALUATOR_AMBIGUOUS"
    else:
        status = "COMPLETE"
    receipt.update(status=status,
                   finished_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=round(time.monotonic() - started, 3),
                   returncode=completed.returncode, stdout_sha256=sha256(completed.stdout.encode()),
                   stderr_sha256=sha256(completed.stderr.encode()),
                   report_path=str(report_path), report_sha256=sha256(report_path.read_bytes()) if report_path.is_file() else None,
                   report_outcome=report[args.instance_id].get("resolved") if isinstance(report, dict) and args.instance_id in report else None,
                   free_space_gib_after={"docker": free_gib(Path("/var/lib/docker")), "scratch": free_gib(runtime)},
                   cumulative_processor_hours_after=previous_processor_hours(controls) + (time.monotonic() - started) * CPUS / 3600)
    receipt_path.write_bytes(canonical(receipt))
    print(json.dumps({"output": str(output), "status": receipt["status"]}, sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
