"""Run the frozen 16-cell control plan with durable bounds and fail-closed backend evidence.

The shared version-budget ledger (including setup and later stages) is an explicit
execution-integration blocker; this module accounts for the control stage only.
The separately hashed backend must enforce Docker/build and owned-storage limits;
process-group termination cannot stop daemon-owned containers. This runner will
not launch a control without that backend's run-matched enforcement evidence.
See ``validate_manifest`` and ``validate_observation`` for the input contract.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

GIB = 1024 ** 3
HARNESS = "f7bbbb2ccdf479001d6467c9e34af59e44a840f9"
DATASET = "6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2"
PANEL = "68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46"
TASKS = (
    "sqlfluff__sqlfluff-1763", "pvlib__pvlib-python-1606",
    "sqlfluff__sqlfluff-2419", "marshmallow-code__marshmallow-1343",
    "pvlib__pvlib-python-1707", "pvlib__pvlib-python-1154",
    "pvlib__pvlib-python-1072", "pydicom__pydicom-1139",
)
EMPTY_HASH = hashlib.sha256(b"").hexdigest()
REQUIRED_ROLES = {"backend", "grading", "official_tests", "dataset", "environment", "empty_adapter", "enforcement"}
DEFAULT_LIMITS = {
    "build_seconds": 900, "evaluate_seconds": 1920, "teardown_seconds": 60,
    "test_timeout_seconds": 1800, "processor_hours": 160,
    "container_cpus": 4, "container_memory_bytes": 8 * GIB,
    "max_containers": 2, "owned_docker_bytes": 120 * GIB,
    "owned_scratch_bytes": 120 * GIB, "min_docker_free_bytes": 100 * GIB,
    "min_scratch_free_bytes": 1024 * GIB,
}
INFRASTRUCTURE = {"BUILD_FAILED", "EVALUATE_FAILED", "PHASE_TIMEOUT", "PROCESS_START_FAILED",
                  "REPORT_INVALID", "OBSERVER_FAILED"}


class ObservationError(RuntimeError):
    """A bounded infrastructure observation failed without measuring an outcome."""


class GateError(ValueError):
    """An immutable input or resource gate does not permit execution."""


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def utc_time(value: str) -> float:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise GateError("timestamps must include a timezone")
    return parsed.timestamp()


def stamp(now: float) -> str:
    return datetime.fromtimestamp(now, timezone.utc).isoformat()


def check_hash(value: object) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise GateError("expected a SHA-256 hexadecimal identity")


def validate_manifest(manifest: dict) -> dict:
    """Check the full frozen panel before inspecting or running any cell.

    ``files`` pins every execution/grade/test dependency (absolute path, sha256,
    role). ``commands`` contains argv templates for build/evaluate/observe/cleanup.
    A template receives run_id, instance_id, kind, patch_path, patch_sha256,
    output_dir and test_timeout_seconds. Each task supplies its base_commit,
    gold_patch_path/gold_patch_sha256 and official_test_sha256. No shell is used.
    """
    if manifest.get("schema_version") != 3 or not re.fullmatch(r"e06v3-[a-z0-9-]{6,80}", manifest.get("run_id", "")):
        raise GateError("expected a unique e06v3 run identity")
    for key, expected in (("harness_commit", HARNESS), ("dataset_revision", DATASET), ("public_panel_sha256", PANEL)):
        if manifest.get(key) != expected:
            raise GateError(f"frozen {key} does not match")
    start, deadline = utc_time(manifest["started_at_utc"]), utc_time(manifest["deadline_utc"])
    if not 0 < deadline - start <= 18 * 3600:
        raise GateError("absolute run interval must be positive and at most 18 hours")
    limits = DEFAULT_LIMITS | manifest.get("limits", {})
    if set(limits) != set(DEFAULT_LIMITS):
        raise GateError("unknown resource limit")
    for key, value in limits.items():
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise GateError(f"invalid limit {key}")
        if not key.startswith("min_") and value > DEFAULT_LIMITS[key]:
            raise GateError(f"limit exceeds declared ceiling: {key}")
        if key.startswith("min_") and value < DEFAULT_LIMITS[key] :
            raise GateError("headroom cannot be lowered within this protocol")
    if limits["evaluate_seconds"] <= limits["test_timeout_seconds"] or limits["teardown_seconds"] < 30:
        raise GateError("test execution needs capture/teardown reserve")
    tasks = manifest.get("tasks", [])
    if len(tasks) != 8 or {t["instance_id"] for t in tasks} != set(TASKS):
        raise GateError("must freeze the unchanged eight-task panel exactly once")
    for task in tasks:
        if not re.fullmatch(r"[0-9a-f]{40}", task.get("base_commit", "")):
            raise GateError("missing exact base commit")
        for key in ("gold_patch_sha256", "official_test_sha256"):
            check_hash(task[key])
        if task["gold_patch_sha256"] == EMPTY_HASH or not Path(task["gold_patch_path"]).is_absolute():
            raise GateError("gold patch must have a nonempty identity and absolute path")
    cells = manifest.get("cells", [])
    expected = {(task, kind) for task in TASKS for kind in ("gold", "empty")}
    if len(cells) != 16 or {(c["instance_id"], c["kind"]) for c in cells} != expected:
        raise GateError("must predeclare exactly sixteen gold/empty cells")
    files = manifest.get("files", [])
    if not REQUIRED_ROLES.issubset({f["role"] for f in files}):
        raise GateError("missing frozen backend/grading/test/dataset/environment/empty-adapter dependency")
    if len({f["path"] for f in files}) != len(files):
        raise GateError("duplicate frozen dependency")
    for item in files:
        if not Path(item["path"]).is_absolute():
            raise GateError("frozen dependency path must be absolute")
        check_hash(item["sha256"])
    check_hash(manifest["runner_sha256"])
    if set(manifest.get("commands", {})) != {"build", "evaluate", "observe", "cleanup"}:
        raise GateError("need all four bounded backend commands")
    for argv in manifest["commands"].values():
        if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a or "\0" in a for a in argv):
            raise GateError("backend commands must be nonempty argument arrays")
    for key in ("cwd", "docker_root", "scratch_root"):
        if not Path(manifest[key]).is_absolute():
            raise GateError(f"{key} must be absolute")
    return limits


def verify_files(manifest: dict) -> None:
    if file_digest(Path(__file__)) != manifest["runner_sha256"]:
        raise GateError("runner source changed after freeze")
    for item in manifest["files"]:
        if file_digest(Path(item["path"])) != item["sha256"]:
            raise GateError(f"frozen {item['role']} changed")
    for task in manifest["tasks"]:
        if file_digest(Path(task["gold_patch_path"])) != task["gold_patch_sha256"]:
            raise GateError("gold patch changed after freeze")


def cell_identity(manifest: dict, task: dict, kind: str, attempt: int) -> dict:
    patch_hash = task["gold_patch_sha256"] if kind == "gold" else EMPTY_HASH
    run_id = f"{manifest['run_id']}-{digest(task['instance_id'].encode())[:12]}-{kind}-{patch_hash[:12]}-a{attempt}"
    return {"run_id": run_id, "instance_id": task["instance_id"], "kind": kind,
            "patch_sha256": patch_hash, "attempt": attempt}


def validate_observation(observed: dict, identity: dict, limits: dict, manifest: dict) -> None:
    """Fail closed without run-bound backend enforcement and measured usage.

    The backend itself is frozen and must be reviewed before execution; this is
    an interface check, not proof that an arbitrary backend implements quotas.
    Evidence paths identify the host/container quota observations it captured.
    """
    if observed.get("run_id") != identity["run_id"]:
        raise GateError("resource observation belongs to a different run")
    enforcement = observed.get("enforcement", {})
    expected = {k: limits[k] for k in ("container_cpus", "container_memory_bytes", "max_containers", "owned_docker_bytes", "owned_scratch_bytes")}
    if enforcement.get("limits") != expected or not enforcement.get("evidence_sha256"):
        raise GateError("backend has not supplied frozen hard-bound enforcement evidence")
    check_hash(enforcement["evidence_sha256"])
    frozen = [f for f in manifest["files"] if f["role"] == "enforcement"]
    if len(frozen) != 1 or enforcement["evidence_sha256"] != frozen[0]["sha256"]:
        raise GateError("enforcement evidence does not match the frozen evidence file")
    if file_digest(Path(frozen[0]["path"])) != frozen[0]["sha256"]:
        raise GateError("frozen enforcement evidence changed")
    for key, ceiling in (("active_containers", limits["max_containers"]),
                         ("max_container_cpus", limits["container_cpus"]),
                         ("max_container_memory_bytes", limits["container_memory_bytes"]),
                         ("owned_docker_bytes", limits["owned_docker_bytes"]),
                         ("owned_scratch_bytes", limits["owned_scratch_bytes"])):
        value = observed.get(key)
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= ceiling:
            raise GateError(f"missing or exceeded measured resource: {key}")


def endpoint(output: Path, identity: dict, task: dict, manifest: dict) -> tuple[str, bool | None, dict]:
    """Require matching report identity, unchanged grading/tests and actual execution."""
    evidence = {}
    try:
        paths = {name: output / name for name in ("report.json", "test_output.txt", "evidence.json")}
        evidence["artifact_sha256"] = {name: file_digest(path) for name, path in paths.items()}
        raw = json.loads(paths["report.json"].read_text())
        attestation = json.loads(paths["evidence.json"].read_text())
        if set(raw) != {identity["instance_id"]}:
            return "IDENTITY_INVALID", None, evidence
        report = raw[identity["instance_id"]]
        evidence["raw_resolved"] = report.get("resolved")
        for key in ("run_id", "instance_id", "kind", "patch_sha256"):
            if attestation.get(key) != identity[key]:
                return "IDENTITY_INVALID", None, evidence
        grading_hashes = sorted(f["sha256"] for f in manifest["files"] if f["role"] == "grading")
        if attestation.get("grading_sha256") != grading_hashes or attestation.get("official_test_sha256") != task["official_test_sha256"]:
            return "IDENTITY_INVALID", None, evidence
        before, after = attestation.get("base_tree_before"), attestation.get("base_tree_after")
        if not isinstance(before, str) or not re.fullmatch(r"[0-9a-f]{40}", before):
            return "IDENTITY_INVALID", None, evidence
        if not isinstance(after, str) or not re.fullmatch(r"[0-9a-f]{40}", after):
            return "IDENTITY_INVALID", None, evidence
        if (identity["kind"] == "empty" and before != after) or (identity["kind"] == "gold" and before == after):
            return "IDENTITY_INVALID", None, evidence
        if attestation.get("base_commit") != task["base_commit"]:
            return "IDENTITY_INVALID", None, evidence
        if attestation.get("environment_valid") is not True:
            return "ENVIRONMENT_INVALID", None, evidence
        log = paths["test_output.txt"].read_text(errors="replace")
        # ImportError inside a completed test call may be the issue itself.
        # Collection/setup failures and interrupted runs are never endpoints.
        if re.search(r"ERROR collecting|ERROR at setup|ERROR at teardown|fixture .+ not found|Interrupted:|KeyboardInterrupt|INTERNALERROR", log):
            return "ENVIRONMENT_INVALID", None, evidence
        if re.search(r"AttributeError:\s*['\"]Test[^'\"]*['\"] object has no attribute", log):
            return "ENVIRONMENT_INVALID", None, evidence
        if not re.search(r"\b[1-9]\d* (?:passed|failed|xfailed|xpassed)\b", log):
            return "REPORT_INVALID", None, evidence
        execution = attestation.get("test_execution", {})
        if (execution.get("completed") is not True or execution.get("collection_errors") != 0
                or execution.get("setup_errors") != 0 or execution.get("terminated") is not False):
            return "ENVIRONMENT_INVALID", None, evidence
        if report.get("patch_successfully_applied") is not True or type(report.get("resolved")) is not bool:
            return "REPORT_INVALID", None, evidence
        return "COMPLETE", report["resolved"], evidence
    except (OSError, ValueError, KeyError, TypeError):
        return "REPORT_INVALID", None, evidence


def terminate_process_group(process: subprocess.Popen) -> None:
    """Kill descendants even when the group's original leader already exited."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=3)


def bounded_run(command, *, timeout, **kwargs):
    """Apply the timeout to a new process group, including cleanup/observers."""
    capture = kwargs.pop("capture_output", False)
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    finally:
        terminate_process_group(process)


class Runner:
    """Single-writer sequential scheduler; backend may use at most two containers."""

    def __init__(self, manifest: dict, state_dir: Path, *, wall=time.time, monotonic=time.monotonic,
                 sleep=time.sleep, popen=subprocess.Popen, run=bounded_run, disk_usage=shutil.disk_usage,
                 device=lambda path: os.stat(path).st_dev):
        self.manifest, self.root = manifest, state_dir
        self.limits = validate_manifest(manifest)
        self.wall, self.monotonic, self.sleep = wall, monotonic, sleep
        self.popen, self.run, self.disk_usage, self.device = popen, run, disk_usage, device
        self.manifest_hash = digest(canonical(manifest))
        self.deadline = utc_time(manifest["deadline_utc"])
        self.start = utc_time(manifest["started_at_utc"])
        self.reservation_seconds = sum(self.limits[k] for k in ("build_seconds", "evaluate_seconds", "teardown_seconds"))
        self.reservation_hours = self.reservation_seconds * self.limits["container_cpus"] * self.limits["max_containers"] / 3600
        self.state = None

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.root / "state.json"
        if path.exists():
            self.state = json.loads(path.read_text())
            if self.state["manifest_sha256"] != self.manifest_hash:
                raise GateError("resume manifest differs from frozen state")
        else:
            self.state = {"schema_version": 3, "manifest_sha256": self.manifest_hash,
                          "run_id": self.manifest["run_id"], "reserved_processor_hours": 0,
                          "accounting": "conservative allocation reservation, not measured processor use; reservations are never released",
                          "cells": [{**c, "status": "PENDING", "endpoint_value": None, "attempts": []} for c in self.manifest["cells"]]}
            atomic_json(self.root / "manifest.json", self.manifest)
            self.save()

    def save(self) -> None:
        atomic_json(self.root / "state.json", self.state)

    def admission(self) -> None:
        verify_files(self.manifest)
        if self.wall() < self.start:
            raise GateError("run has not reached its frozen start time")
        if self.wall() + self.reservation_seconds > self.deadline:
            raise GateError("worst-case cell plus teardown does not fit absolute deadline")
        if self.state["reserved_processor_hours"] + self.reservation_hours > self.limits["processor_hours"]:
            raise GateError("worst-case reservation exceeds processor-hour ceiling")
        self.headroom(reserve=True)

    def headroom(self, *, reserve: bool = False) -> None:
        devices = {}
        for path, key, owned in (("docker_root", "min_docker_free_bytes", "owned_docker_bytes"),
                                 ("scratch_root", "min_scratch_free_bytes", "owned_scratch_bytes")):
            root = self.manifest[path]
            entry = devices.setdefault(self.device(root), {"free": self.disk_usage(root).free, "floor": 0, "growth": 0})
            entry["free"] = min(entry["free"], self.disk_usage(root).free)
            entry["floor"] = max(entry["floor"], self.limits[key])
            entry["growth"] += self.limits[owned] if reserve else 0
        if any(d["free"] < d["floor"] + d["growth"] for d in devices.values()):
            raise GateError("filesystem free-space gate failed (including combined worst-case owned storage at admission)")

    def command(self, phase: str, identity: dict, output: Path, task: dict) -> list[str]:
        fields = identity | {"output_dir": str(output), "test_timeout_seconds": str(self.limits["test_timeout_seconds"]),
                             "patch_path": task["gold_patch_path"] if identity["kind"] == "gold" else str(output / "empty.patch")}
        try:
            return [arg.format_map(fields) for arg in self.manifest["commands"][phase]]
        except (KeyError, ValueError) as error:
            raise GateError("unsupported backend command placeholder") from error

    def environment(self) -> dict:
        # Evaluator phases need no language-model credentials or Python startup hooks.
        allowed = ("PATH", "HOME", "USER", "TMPDIR", "DOCKER_HOST", "DOCKER_CONTEXT", "XDG_RUNTIME_DIR")
        return {key: os.environ[key] for key in allowed if key in os.environ} | {"PYTHONNOUSERSITE": "1", "PYTHONUNBUFFERED": "1", "PYTHONOPTIMIZE": "0"}

    def observe(self, identity: dict, output: Path, task: dict) -> None:
        try:
            completed = self.run(self.command("observe", identity, output, task), cwd=self.manifest["cwd"],
                                 env=self.environment(), shell=False, capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ObservationError("bounded backend observation failed") from error
        if completed.returncode:
            raise ObservationError("backend resource observation failed")
        try:
            observed = json.loads(completed.stdout)
        except ValueError as error:
            raise ObservationError("backend observation was not JSON") from error
        validate_observation(observed, identity, self.limits, self.manifest)
        atomic_json(output / "resource_observation.json", observed)
        self.headroom()

    def phase(self, name: str, identity: dict, output: Path, task: dict) -> tuple[str, int | None]:
        command = self.command(name, identity, output, task)
        deadline = min(self.monotonic() + self.limits[f"{name}_seconds"],
                       self.monotonic() + self.deadline - self.wall() - self.limits["teardown_seconds"])
        process = None
        next_observation = self.monotonic() + 15
        try:
            with (output / f"{name}.stdout.log").open("wb") as stdout, (output / f"{name}.stderr.log").open("wb") as stderr:
                process = self.popen(command, cwd=self.manifest["cwd"], env=self.environment(), shell=False,
                                     start_new_session=True, stdout=stdout, stderr=stderr)
                while process.poll() is None:
                    if self.monotonic() >= deadline or self.wall() >= self.deadline - self.limits["teardown_seconds"]:
                        return "PHASE_TIMEOUT", None
                    # A five-second observation cannot consume the phase deadline.
                    if self.monotonic() >= next_observation and deadline - self.monotonic() > 5:
                        self.observe(identity, output, task)
                        next_observation = self.monotonic() + 15
                    self.sleep(min(1, max(0, deadline - self.monotonic())))
                return ("COMPLETE" if process.returncode == 0 else f"{name.upper()}_FAILED"), process.returncode
        except OSError:
            return "PROCESS_START_FAILED", None
        finally:
            if process is not None:
                terminate_process_group(process)

    def cleanup(self, identity: dict, output: Path, task: dict) -> bool:
        try:
            with (output / "cleanup.stdout.log").open("wb") as stdout, (output / "cleanup.stderr.log").open("wb") as stderr:
                completed = self.run(self.command("cleanup", identity, output, task), cwd=self.manifest["cwd"],
                                     env=self.environment(), shell=False, stdout=stdout, stderr=stderr,
                                     timeout=self.limits["teardown_seconds"] - 10, start_new_session=True)
            if completed.returncode:
                return False
            self.observe(identity, output, task)
            observed = json.loads((output / "resource_observation.json").read_text())
            return observed["active_containers"] == 0
        except (OSError, ValueError, subprocess.SubprocessError, ObservationError):
            return False

    def run_cell(self, cell: dict) -> bool:
        """Run one attempt; the panel scheduler admits retries only after all firsts."""
        if len(cell["attempts"]) >= 2:
            raise GateError("attempt ceiling reached")
        task = next(t for t in self.manifest["tasks"] if t["instance_id"] == cell["instance_id"])
        identity = cell_identity(self.manifest, task, cell["kind"], len(cell["attempts"]) + 1)
        output = self.root / identity["run_id"]
        receipt = identity | {"status": "PRELAUNCH", "endpoint_value": None, "started_at": stamp(self.wall()),
                              "manifest_sha256": self.manifest_hash, "reserved_processor_hours": 0}
        cell["attempts"].append(receipt)
        self.save()
        attempt_started = self.monotonic()
        launched, safe, own_output = False, True, False
        try:
            try:
                output.mkdir(mode=0o700)
                own_output = True
            except FileExistsError:
                receipt.update(status="STALE_ATTEMPT_DIRECTORY", reason="existing evidence preserved; owned resources require reconciliation")
                safe = False
                return False
            (output / "empty.patch").write_bytes(b"")
            atomic_json(output / "receipt.json", receipt)
            self.admission()
            self.observe(identity, output, task)
            # Reserve durably before starting either phase; crashes retain the full charge.
            self.state["reserved_processor_hours"] += self.reservation_hours
            receipt.update(status="RUNNING", reserved_processor_hours=self.reservation_hours,
                           commands={phase: self.command(phase, identity, output, task) for phase in ("build", "evaluate", "cleanup")})
            self.save()
            atomic_json(output / "receipt.json", receipt)
            launched = True
            for name in ("build", "evaluate"):
                status, returncode = self.phase(name, identity, output, task)
                receipt[f"{name}_returncode"] = returncode
                if status != "COMPLETE":
                    break
            if status == "COMPLETE":
                verify_files(self.manifest)
                self.observe(identity, output, task)
                status, value, evidence = endpoint(output, identity, task, self.manifest)
                receipt.update(endpoint_value=value, evidence=evidence)
            receipt["status"] = status
        except ObservationError as error:
            receipt.update(status="OBSERVER_FAILED", reason=str(error), endpoint_value=None)
        except (GateError, OSError, ValueError, subprocess.SubprocessError) as error:
            receipt.update(status="GATE_FAILED", reason=str(error), endpoint_value=None)
        finally:
            if launched:
                safe = self.cleanup(identity, output, task)
                receipt["cleanup_verified"] = safe
                if not safe:
                    receipt.update(outcome_status=receipt["status"], status="CLEANUP_FAILED")
            receipt["finished_at"] = stamp(self.wall())
            receipt["elapsed_seconds"] = max(0, self.monotonic() - attempt_started)
            # Never overwrite a stale directory or its old receipt.
            destination = output / "receipt.json" if own_output else self.root / (identity["run_id"] + ".blocked.json")
            atomic_json(destination, receipt)
            cell.update(status=receipt["status"], endpoint_value=receipt["endpoint_value"])
            self.save()
        return safe

    def execute(self) -> dict:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.root / "writer.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.initialize()
            # Unknown live work cannot be rescheduled from a stale RUNNING receipt.
            if any(a["status"] in {"PRELAUNCH", "RUNNING"} for c in self.state["cells"] for a in c["attempts"]):
                raise GateError("interrupted attempt requires explicit owned-resource reconciliation before resume")
            stopped = False
            for attempt in (1, 2):
                for cell in self.state["cells"]:
                    eligible = (attempt == 1 and cell["status"] == "PENDING") or (
                        attempt == 2 and len(cell["attempts"]) == 1 and cell["status"] in INFRASTRUCTURE)
                    if not eligible:
                        continue
                    if stopped:
                        if attempt == 1:
                            cell.update(status="BLOCKED_AFTER_CLEANUP_FAILURE", endpoint_value=None)
                            self.save()
                    else:
                        stopped = not self.run_cell(cell)
                if stopped:
                    break
            pairs = {task: {c["kind"]: c["endpoint_value"] for c in self.state["cells"] if c["instance_id"] == task} for task in TASKS}
            valid = sum(p["gold"] is True and p["empty"] is False for p in pairs.values())
            self.state["summary"] = {"declared_cells": 16, "measured_cells": sum(c["endpoint_value"] is not None for c in self.state["cells"]),
                                     "valid_control_pairs": valid, "declared_tasks": 8, "required_pairs": 6, "admission_blocked": stopped, "gate_passed": valid >= 6 and not stopped}
            self.save()
            return self.state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--execute", action="store_true", help="otherwise validate only; no backend commands")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    runner = Runner(manifest, args.state_dir.resolve())
    if not args.execute:
        verify_files(manifest)
        print(json.dumps({"status": "PLAN_VALIDATED_ONLY", "declared_cells": 16, "reservation_per_attempt_processor_hours": runner.reservation_hours}))
        return 0
    state = runner.execute()
    print(json.dumps(state["summary"], sort_keys=True))
    return 0 if state["summary"]["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
