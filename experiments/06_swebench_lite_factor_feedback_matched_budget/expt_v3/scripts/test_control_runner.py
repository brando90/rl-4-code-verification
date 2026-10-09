"""Exercise control-plan identity, null receipts, bounded scheduling and process cleanup."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("control_runner", Path(__file__).with_name("control_runner.py"))
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


@pytest.fixture
def manifest(tmp_path):
    frozen = []
    for role in sorted(m.REQUIRED_ROLES):
        path = tmp_path / role
        path.write_text(role)
        frozen.append({"path": str(path), "sha256": m.file_digest(path), "role": role})
    tasks = []
    for index, task in enumerate(m.TASKS):
        patch = tmp_path / f"patch{index}"
        patch.write_text(f"patch {task}")
        tasks.append({"instance_id": task, "base_commit": "a" * 40,
                      "gold_patch_path": str(patch), "gold_patch_sha256": m.file_digest(patch),
                      "official_test_sha256": "b" * 64})
    return {"schema_version": 3, "run_id": "e06v3-test-001",
            "started_at_utc": "2026-10-08T00:00:00+00:00", "deadline_utc": "2026-10-08T18:00:00+00:00",
            "harness_commit": m.HARNESS, "dataset_revision": m.DATASET, "public_panel_sha256": m.PANEL,
            "runner_sha256": m.file_digest(Path(m.__file__)), "files": frozen, "tasks": tasks,
            "cells": [{"instance_id": t, "kind": kind} for t in m.TASKS for kind in ("gold", "empty")],
            "commands": {phase: ["/backend", phase, "{run_id}", "{output_dir}", "{patch_path}"] for phase in ("build", "evaluate", "observe", "cleanup")},
            "cwd": str(tmp_path), "docker_root": str(tmp_path), "scratch_root": str(tmp_path)}


def observation(identity, limits, manifest):
    return {"run_id": identity["run_id"], "enforcement": {
        "limits": {k: limits[k] for k in ("container_cpus", "container_memory_bytes", "max_containers", "owned_docker_bytes", "owned_scratch_bytes")},
        "evidence_sha256": next(f["sha256"] for f in manifest["files"] if f["role"] == "enforcement")}, "active_containers": 0, "max_container_cpus": 0,
        "max_container_memory_bytes": 0, "owned_docker_bytes": 1, "owned_scratch_bytes": 1}


def runner(manifest, tmp_path, **kwargs):
    return m.Runner(manifest, tmp_path / "state", wall=lambda: m.utc_time(manifest["started_at_utc"]),
                    disk_usage=lambda _: SimpleNamespace(free=2000 * m.GIB), **kwargs)


def artifacts(output, identity, task, manifest, *, resolved=True, log="2 passed in 0.3s"):
    output.mkdir(exist_ok=True)
    (output / "report.json").write_text(json.dumps({task["instance_id"]: {"resolved": resolved, "patch_successfully_applied": True}}))
    (output / "test_output.txt").write_text(log)
    attestation = {k: identity[k] for k in ("run_id", "instance_id", "kind", "patch_sha256")}
    attestation.update(grading_sha256=sorted(f["sha256"] for f in manifest["files"] if f["role"] == "grading"),
                       official_test_sha256=task["official_test_sha256"], base_commit=task["base_commit"],
                       base_tree_before="e" * 40, base_tree_after=("e" if identity["kind"] == "empty" else "f") * 40, environment_valid=True,
                       test_execution={"completed": True, "collection_errors": 0, "setup_errors": 0, "terminated": False})
    (output / "evidence.json").write_text(json.dumps(attestation))
    return attestation


def test_valid_full_frozen_plan(manifest):
    assert m.validate_manifest(manifest) == m.DEFAULT_LIMITS
    m.verify_files(manifest)


@pytest.mark.parametrize("change", [
    lambda x: x["cells"].pop(),
    lambda x: x["cells"].__setitem__(0, x["cells"][1]),
    lambda x: x["tasks"].pop(),
    lambda x: x.update(harness_commit="f" * 40),
    lambda x: x.update(deadline_utc="2026-10-09T00:00:00Z"),
    lambda x: x.update(started_at_utc="2026-10-08T00:00:00"),
    lambda x: x.update(limits={"max_containers": 3}),
    lambda x: x.update(limits={"processor_hours": float("nan")}),
    lambda x: x.update(limits={"min_scratch_free_bytes": 1}),
    lambda x: x.update(limits={"test_timeout_seconds": 1800, "evaluate_seconds": 1800}),
    lambda x: x["commands"].update(build="shell command"),
    lambda x: x["files"].pop(),
])
def test_invalid_manifest_is_rejected(manifest, change):
    change(manifest)
    with pytest.raises((m.GateError, KeyError)):
        m.validate_manifest(manifest)


def test_prospective_explicit_headroom_change(manifest):
    manifest["limits"] = {"min_scratch_free_bytes": 500 * m.GIB}
    manifest["prospective_headroom_change"] = "Dedicated filesystem lower bound recorded before controls."
    with pytest.raises(m.GateError, match="headroom cannot be lowered"):
        m.validate_manifest(manifest)


def test_source_and_gold_are_reverified(manifest):
    Path(manifest["tasks"][0]["gold_patch_path"]).write_text("changed")
    with pytest.raises(m.GateError, match="gold patch changed"):
        m.verify_files(manifest)


def test_unique_task_kind_patch_attempt_identity(manifest):
    task = manifest["tasks"][0]
    ids = [m.cell_identity(manifest, task, kind, attempt)["run_id"] for kind in ("gold", "empty") for attempt in (1, 2)]
    assert len(set(ids)) == 4
    assert all(value.startswith("e06v3-") for value in ids)
    assert m.cell_identity(manifest, task, "empty", 1)["patch_sha256"] == m.EMPTY_HASH


def test_initial_receipts_keep_all_null_cells(manifest, tmp_path):
    r = runner(manifest, tmp_path)
    r.initialize()
    assert len(r.state["cells"]) == 16
    assert all(c["endpoint_value"] is None for c in r.state["cells"])


def test_expired_run_records_every_prelaunch_null(manifest, tmp_path):
    r = runner(manifest, tmp_path)
    r.wall = lambda: m.utc_time(manifest["deadline_utc"])
    state = r.execute()
    assert state["summary"]["measured_cells"] == 0
    assert len(list(r.root.glob("*/receipt.json"))) == 16
    assert all(c["status"] == "GATE_FAILED" for c in state["cells"])
    assert state["reserved_processor_hours"] == 0


def test_worst_case_plus_teardown_admission(manifest, tmp_path):
    r = runner(manifest, tmp_path)
    r.initialize()
    r.wall = lambda: r.deadline - r.reservation_seconds + 1
    with pytest.raises(m.GateError, match="plus teardown"):
        r.admission()
    r.wall = lambda: r.start
    r.state["reserved_processor_hours"] = 159
    with pytest.raises(m.GateError, match="processor-hour"):
        r.admission()


def test_missing_enforcement_or_overspend_fails_closed(manifest):
    limits = m.validate_manifest(manifest)
    identity = m.cell_identity(manifest, manifest["tasks"][0], "gold", 1)
    observed = observation(identity, limits, manifest)
    m.validate_observation(observed, identity, limits, manifest)
    for field, invalid in (("run_id", "other"), ("active_containers", 3), ("max_container_cpus", 5),
                           ("owned_docker_bytes", 121 * m.GIB), ("owned_scratch_bytes", -1),
                           ("max_container_memory_bytes", float("nan")), ("enforcement", {})):
        changed = copy.deepcopy(observed)
        changed[field] = invalid
        with pytest.raises(m.GateError):
            m.validate_observation(changed, identity, limits, manifest)


@pytest.mark.parametrize("log,status", [("2 passed", "COMPLETE"), ("1 failed, 1 passed", "COMPLETE"),
    ("ImportError: broken\n1 failed, 1 passed", "COMPLETE"),
    ("fixture 'example' not found\n1 error", "ENVIRONMENT_INVALID"), ("nothing ran", "REPORT_INVALID")])
def test_endpoint_requires_observed_tests(manifest, tmp_path, log, status):
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "empty", 1)
    artifacts(tmp_path, identity, task, manifest, resolved=False, log=log)
    result, value, evidence = m.endpoint(tmp_path, identity, task, manifest)
    assert result == status
    assert value is (False if status == "COMPLETE" else None)
    assert evidence["raw_resolved"] is False


@pytest.mark.parametrize("field,value", [("base_tree_after", "f" * 40), ("run_id", "stale"),
    ("base_commit", "0" * 40), ("official_test_sha256", "a" * 64), ("grading_sha256", [])])
def test_empty_adapter_or_grading_mutation_stays_null(manifest, tmp_path, field, value):
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "empty", 1)
    attestation = artifacts(tmp_path, identity, task, manifest)
    attestation[field] = value
    (tmp_path / "evidence.json").write_text(json.dumps(attestation))
    status, value, _ = m.endpoint(tmp_path, identity, task, manifest)
    assert (status, value) == ("IDENTITY_INVALID", None)


def test_one_identical_infrastructure_retry_and_no_score_retry(manifest, tmp_path, monkeypatch):
    r = runner(manifest, tmp_path)
    r.initialize()
    monkeypatch.setattr(r, "observe", lambda *a: None)
    monkeypatch.setattr(r, "cleanup", lambda *a: True)
    commands = []
    def phase(name, identity, output, task):
        commands.append((name, identity["patch_sha256"], identity["attempt"]))
        return "BUILD_FAILED", 1
    monkeypatch.setattr(r, "phase", phase)
    assert r.run_cell(r.state["cells"][0])
    assert len(r.state["cells"][0]["attempts"]) == 1
    assert r.run_cell(r.state["cells"][0])
    assert len(r.state["cells"][0]["attempts"]) == 2
    assert commands[0][1] == commands[1][1]
    assert r.state["reserved_processor_hours"] == 2 * r.reservation_hours
    def successful_phase(name, identity, output, task):
        artifacts(output, identity, task, manifest, resolved=False)
        return "COMPLETE", 0
    monkeypatch.setattr(r, "phase", successful_phase)
    assert r.run_cell(r.state["cells"][2])
    assert len(r.state["cells"][2]["attempts"]) == 1  # Incorrect gold is data, never a retry trigger.
    assert r.state["cells"][2]["endpoint_value"] is False


def test_cleanup_failure_halts_and_keeps_remaining_denominator(manifest, tmp_path, monkeypatch):
    r = runner(manifest, tmp_path)
    monkeypatch.setattr(r, "observe", lambda *a: None)
    monkeypatch.setattr(r, "phase", lambda *a: ("BUILD_FAILED", 1))
    monkeypatch.setattr(r, "cleanup", lambda *a: False)
    state = r.execute()
    assert state["cells"][0]["status"] == "CLEANUP_FAILED"
    assert all(c["status"] == "BLOCKED_AFTER_CLEANUP_FAILURE" for c in state["cells"][1:])
    assert state["summary"]["declared_cells"] == 16
    assert state["summary"]["measured_cells"] == 0


def test_crashed_reservation_not_released_or_automatically_retried(manifest, tmp_path):
    r = runner(manifest, tmp_path)
    r.initialize()
    r.state["reserved_processor_hours"] = r.reservation_hours
    r.state["cells"][0]["attempts"] = [{"status": "RUNNING"}]
    r.save()
    with pytest.raises(m.GateError, match="reconciliation"):
        r.execute()
    assert json.loads((r.root / "state.json").read_text())["reserved_processor_hours"] == r.reservation_hours


def test_phase_timeout_kills_group_and_uses_no_shell(manifest, tmp_path, monkeypatch):
    now = [0.0]
    killed, options = [], []
    process = SimpleNamespace(pid=1234, poll=lambda: None)
    def popen(command, **kwargs):
        options.append(kwargs)
        return process
    r = runner(manifest, tmp_path, monotonic=lambda: now[0], sleep=lambda t: now.__setitem__(0, now[0] + 1000), popen=popen)
    monkeypatch.setattr(r, "observe", lambda *a: None)
    monkeypatch.setattr(m, "terminate_process_group", lambda p: killed.append(p.pid))
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "gold", 1)
    status, code = r.phase("build", identity, tmp_path, task)
    assert (status, code) == ("PHASE_TIMEOUT", None)
    assert killed == [1234]
    assert options[0]["shell"] is False and options[0]["start_new_session"] is True


def test_process_group_killed_when_leader_already_finished(monkeypatch):
    calls = []
    monkeypatch.setattr(m.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    process = SimpleNamespace(pid=999, wait=lambda timeout: 0)
    m.terminate_process_group(process)
    assert [sig for _, sig in calls] == [m.signal.SIGTERM, m.signal.SIGKILL]


def test_every_first_attempt_precedes_retry_under_budget_pressure(manifest, tmp_path, monkeypatch):
    r = runner(manifest, tmp_path)
    order = []
    monkeypatch.setattr(r, "observe", lambda *args: None)
    monkeypatch.setattr(r, "cleanup", lambda *args: True)
    def phase(name, identity, output, task):
        order.append((identity["instance_id"], identity["kind"], identity["attempt"]))
        return "BUILD_FAILED", 1
    monkeypatch.setattr(r, "phase", phase)
    state = r.execute()
    assert len(order) >= 16
    assert [row[2] for row in order[:16]] == [1] * 16
    assert len({row[:2] for row in order[:16]}) == 16
    assert all(row[2] == 2 for row in order[16:])
    assert state["reserved_processor_hours"] <= 160


@pytest.mark.parametrize("status", ["ENVIRONMENT_INVALID", "IDENTITY_INVALID"])
def test_deterministic_invalidity_is_not_retried(manifest, tmp_path, monkeypatch, status):
    r = runner(manifest, tmp_path)
    monkeypatch.setattr(r, "observe", lambda *args: None)
    monkeypatch.setattr(r, "cleanup", lambda *args: True)
    monkeypatch.setattr(r, "phase", lambda *args: ("COMPLETE", 0))
    monkeypatch.setattr(m, "endpoint", lambda *args: (status, None, {}))
    state = r.execute()
    assert all(len(c["attempts"]) == 1 for c in state["cells"])
    assert all(c["status"] == status for c in state["cells"])


def test_observer_timeout_is_bounded_and_retryable(manifest, tmp_path, monkeypatch):
    timeout_values = []
    def stalled(command, **kwargs):
        timeout_values.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])
    r = runner(manifest, tmp_path, run=stalled)
    state = r.execute()
    assert set(timeout_values) == {5}
    assert len(timeout_values) == 32  # Full first-attempt panel, then one identical retry each.
    assert all(c["status"] == "OBSERVER_FAILED" and len(c["attempts"]) == 2 for c in state["cells"])
    assert state["reserved_processor_hours"] == 0  # No container phase was admitted.


def test_phase_observer_cadence_and_failure_stop_process_group(manifest, tmp_path, monkeypatch):
    now, observed, killed = [0.0], [], []
    process = SimpleNamespace(pid=2345, poll=lambda: None)
    r = runner(manifest, tmp_path, monotonic=lambda: now[0], sleep=lambda t: now.__setitem__(0, now[0] + t),
               popen=lambda *args, **kwargs: process)
    def fail(*args):
        observed.append(now[0])
        raise m.ObservationError("timeout")
    monkeypatch.setattr(r, "observe", fail)
    monkeypatch.setattr(m, "terminate_process_group", lambda p: killed.append(p.pid))
    task = manifest["tasks"][0]
    with pytest.raises(m.ObservationError):
        r.phase("build", m.cell_identity(manifest, task, "gold", 1), tmp_path, task)
    assert observed == [15]
    assert killed == [2345]


def test_cleanup_failure_preserves_measured_endpoint(manifest, tmp_path, monkeypatch):
    r = runner(manifest, tmp_path)
    monkeypatch.setattr(r, "observe", lambda *args: None)
    monkeypatch.setattr(r, "cleanup", lambda *args: False)
    def phase(name, identity, output, task):
        artifacts(output, identity, task, manifest, resolved=True)
        return "COMPLETE", 0
    monkeypatch.setattr(r, "phase", phase)
    state = r.execute()
    cell = state["cells"][0]
    assert cell["status"] == "CLEANUP_FAILED"
    assert cell["endpoint_value"] is True
    assert cell["attempts"][0]["outcome_status"] == "COMPLETE"
    assert cell["attempts"][0]["cleanup_verified"] is False
    assert state["summary"]["measured_cells"] == 1
    assert all(c["status"] == "BLOCKED_AFTER_CLEANUP_FAILURE" for c in state["cells"][1:])


def test_stale_attempt_directory_records_null_without_overwrite(manifest, tmp_path):
    r = runner(manifest, tmp_path)
    r.initialize()
    identity = m.cell_identity(manifest, manifest["tasks"][0], "gold", 1)
    output = r.root / identity["run_id"]
    output.mkdir()
    prior = b'{"prior": "preserve"}\n'
    (output / "receipt.json").write_bytes(prior)
    state = r.execute()
    assert (output / "receipt.json").read_bytes() == prior
    assert state["cells"][0]["status"] == "STALE_ATTEMPT_DIRECTORY"
    assert state["cells"][0]["endpoint_value"] is None
    blocked = json.loads((r.root / (identity["run_id"] + ".blocked.json")).read_text())
    assert blocked["status"] == "STALE_ATTEMPT_DIRECTORY"
    assert blocked["finished_at"]


def test_shared_storage_reserves_combined_growth(manifest, tmp_path):
    r = runner(manifest, tmp_path)
    r.disk_usage = lambda _: SimpleNamespace(free=(1024 + 239) * m.GIB)
    r.device = lambda _: 9
    r.headroom()  # Existing headroom is adequate; worst-case growth is not.
    with pytest.raises(m.GateError, match="combined worst-case"):
        r.headroom(reserve=True)
    r.disk_usage = lambda _: SimpleNamespace(free=(1024 + 240) * m.GIB)
    r.headroom(reserve=True)


def test_separate_storage_reservations_use_each_device(manifest, tmp_path):
    manifest["docker_root"] = str(tmp_path / "docker")
    manifest["scratch_root"] = str(tmp_path / "scratch")
    r = runner(manifest, tmp_path)
    r.device = lambda path: 1 if path.endswith("docker") else 2
    r.disk_usage = lambda path: SimpleNamespace(free=(220 if path.endswith("docker") else 1144) * m.GIB)
    r.headroom(reserve=True)
    r.disk_usage = lambda path: SimpleNamespace(free=(219 if path.endswith("docker") else 1144) * m.GIB)
    with pytest.raises(m.GateError):
        r.headroom(reserve=True)


def test_enforcement_evidence_must_match_verified_frozen_bytes(manifest):
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "gold", 1)
    limits = m.validate_manifest(manifest)
    observed = observation(identity, limits, manifest)
    m.validate_observation(observed, identity, limits, manifest)
    changed = copy.deepcopy(observed)
    changed["enforcement"]["evidence_sha256"] = "c" * 64
    with pytest.raises(m.GateError, match="does not match"):
        m.validate_observation(changed, identity, limits, manifest)
    frozen = next(f for f in manifest["files"] if f["role"] == "enforcement")
    Path(frozen["path"]).write_text("changed quota evidence")
    with pytest.raises(m.GateError, match="changed"):
        m.validate_observation(observed, identity, limits, manifest)


def test_gold_control_requires_changed_tree(manifest, tmp_path):
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "gold", 1)
    attestation = artifacts(tmp_path, identity, task, manifest)
    attestation["base_tree_after"] = attestation["base_tree_before"]
    (tmp_path / "evidence.json").write_text(json.dumps(attestation))
    assert m.endpoint(tmp_path, identity, task, manifest)[:2] == ("IDENTITY_INVALID", None)


@pytest.mark.parametrize("field,value", [("completed", False), ("collection_errors", 1), ("setup_errors", 1), ("terminated", True)])
def test_test_stage_evidence_cannot_hide_failed_collection_or_setup(manifest, tmp_path, field, value):
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "empty", 1)
    attestation = artifacts(tmp_path, identity, task, manifest, resolved=False, log="ImportError inside test call\n1 failed, 3 passed")
    attestation["test_execution"][field] = value
    (tmp_path / "evidence.json").write_text(json.dumps(attestation))
    assert m.endpoint(tmp_path, identity, task, manifest)[:2] == ("ENVIRONMENT_INVALID", None)


@pytest.mark.parametrize("log", ["ERROR collecting example.py\n1 failed, 3 passed", "ERROR at setup of test_case\n1 failed, 3 passed", "Interrupted: timeout\n1 failed, 3 passed", "4 skipped"])
def test_partial_summary_does_not_hide_invalid_execution(manifest, tmp_path, log):
    task = manifest["tasks"][0]
    identity = m.cell_identity(manifest, task, "empty", 1)
    artifacts(tmp_path, identity, task, manifest, resolved=False, log=log)
    assert m.endpoint(tmp_path, identity, task, manifest)[1] is None
