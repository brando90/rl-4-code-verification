"""Exercise coordinator fencing and finite recovery using disposable processes and fixtures."""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

SCRIPT = Path(__file__).parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/coordinator_monitor_e08.py"
spec = importlib.util.spec_from_file_location("e08_monitor", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.fixture
def process_identity(monkeypatch):
    """Supply identity evidence to logic tests without consulting the host's /proc."""
    current = {"pid": os.getpid(), "start_ticks": 100, "boot_id": "fixture-boot",
               "ppid": os.getppid(), "session": os.getpid()}
    monkeypatch.setattr(m, "boot", lambda: current["boot_id"])
    monkeypatch.setattr(m, "identity", lambda pid: dict(current) if pid == current["pid"] else None)
    return current


@pytest.fixture
def root(tmp_path, monkeypatch, process_identity):
    (tmp_path / "owner_recovery").mkdir()
    (tmp_path / "pipeline").mkdir()
    monkeypatch.setattr(m, "WORK", tmp_path)
    monkeypatch.setattr(m, "EXP", tmp_path / "experiment")
    return tmp_path


def pipeline(root, **changes):
    obj = {"pid": os.getpid(), "boot_id": m.boot(), "last_tick": m.now(),
           "stages": {}, "summary": {"sft_14B": "waiting_gpu", "selection": "pending (15/20 rungs valid)"}}
    obj.update(changes)
    m.write(root / "pipeline/state.json", obj)
    return obj


def test_native_errors_ignore_injected_tool_text(tmp_path):
    path = tmp_path / "events"
    path.write_text(json.dumps({"type": "item.completed", "item": {"text": "quota; rm -rf /"}}) + "\n"
                    + json.dumps({"type": "turn.failed", "error": {"message": "usage limit exceeded"}}) + "\n")
    _, errors = m.native_events(path)
    assert len(errors) == 1
    assert m.classify(errors) == "allowance"


@pytest.mark.parametrize("error,kind", [
    ("401 unauthorized", "authentication"), ("rate limit 429", "rate_limit"),
    ("context window exceeded", "context"), ("model not found", "model_entitlement"),
    ("managed approval is not supported", "managed_permissions"),
    ("administrator spending limit", "spending_limit"), ("connection closed", "transport"),
])
def test_failure_classification(error, kind):
    assert m.classify([error]) == kind


def test_process_identity_fencing_logic(process_identity):
    assert m.alive(process_identity)
    assert not m.alive(dict(process_identity, start_ticks=process_identity["start_ticks"] + 1))
    assert not m.alive(dict(process_identity, boot_id="old-boot"))
    assert not m.alive(dict(process_identity, pid=process_identity["pid"] + 1))
    assert not m.alive(None)


@pytest.mark.skipif(sys.platform != "linux", reason="integration requires Linux /proc process identity")
def test_process_identity_fences_pid_reuse():
    actual = m.identity(os.getpid())
    assert m.alive(actual)
    assert not m.alive(dict(actual, start_ticks=actual["start_ticks"] + 1))
    assert not m.alive(dict(actual, boot_id="old-boot"))


def test_model_not_woken_for_device_churn_or_idle_ticks(root):
    p = pipeline(root)
    first = m.event_snapshot(root)["key"]
    p["last_tick"] = m.now()
    p["summary"]["e09_admission"] = "open [5, 6]"
    p["stages"]["sft_14B"] = {"devices": {"free": [5, 6]}, "retries": 0}
    m.write(root / "pipeline/state.json", p)
    assert m.event_snapshot(root)["key"] == first
    p["summary"]["sft_14B"] = "running"
    m.write(root / "pipeline/state.json", p)
    assert m.event_snapshot(root)["key"] != first


def test_inherited_owner_lock_defers_without_deadlock(root, monkeypatch):
    pipeline(root)
    store = root / "owner_recovery"
    m.write(store / "monitor_state.json", {"status": "ARMED", "serviced_key": "previous", "owner": None})
    calls = []
    monkeypatch.setattr(m, "drive", lambda *args: calls.append(args))
    with m.locked(store / "owner.lock") as acquired:
        assert acquired
        assert m.tick({"enabled": True}, store) == "WAITING_OWNER_LOCK"
    assert not calls
    m.tick({"enabled": True}, store)
    assert len(calls) == 1


def test_live_owner_and_children_prevent_replacement(root, monkeypatch):
    pipeline(root)
    store = root / "owner_recovery"
    m.write(store / "monitor_state.json", {"status": "ARMED", "serviced_key": "old",
                                         "owner": m.identity(os.getpid())})
    child = dict(m.identity(os.getpid()), pid=os.getpid() + 1, ppid=os.getpid())
    monkeypatch.setattr(m, "descendants", lambda owner: [child])
    monkeypatch.setattr(m, "drive", lambda *a: pytest.fail("duplicate coordinator"))
    assert m.tick({"enabled": True}, store) == "OWNER_ACTIVE"
    assert m.read(store / "monitor_state.json")["survivors"] == [child]


def test_stop_blocks_launch(root, monkeypatch):
    pipeline(root)
    store = root / "owner_recovery"
    m.write(store / "monitor_state.json", {"status": "ARMED", "serviced_key": "old", "owner": None})
    (store / "STOP").touch()
    monkeypatch.setattr(m, "drive", lambda *a: pytest.fail("STOP ignored"))
    assert m.tick({"enabled": True}, store) == "STOPPED"


def responses():
    return {"account/read": {"account": {"type": "chatgpt", "email": "expected"}},
            "configRequirements/read": {"requirements": None},
            "account/rateLimits/read": {"rateLimits": {"primary": {"usedPercent": 35}}},
            "model/list": {"data": [{"id": "gpt-6-astra",
                                     "supportedReasoningEfforts": [{"reasoningEffort": "ultra"}]}]}}


def test_eligibility_rejects_restricted_profile_and_low_balance():
    c = {"account_email": "expected", "model": "gpt-6-astra", "effort": "ultra"}
    r = responses()
    assert m.eligible(c, r)[0]
    r["configRequirements/read"]["requirements"] = {"allowedApprovalPolicies": ["on-request"]}
    assert m.eligible(c, r) == (False, "managed_permissions")
    r["configRequirements/read"]["requirements"] = None
    r["account/rateLimits/read"]["rateLimits"]["primary"]["usedPercent"] = 75
    assert m.eligible(c, r) == (False, "included_allowance_reserve")


def test_native_account_probe_harmless_fake_server(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    script = tmp_path / "fake_server.py"
    script.write_text("import sys,json\nfor line in sys.stdin:\n x=json.loads(line)\n"
                      " if 'id' in x: print(json.dumps({'id':x['id'],'result':{'ok':True}}),flush=True)\n")
    result = m.account_probe({"prefix": [sys.executable, str(script)]}, tmp_path, timeout=5)
    assert set(result) == {"account/read", "account/rateLimits/read", "configRequirements/read", "model/list"}


@pytest.mark.parametrize("completed_key", [None, "updated-owner-event"])
def test_finite_failover_uses_next_candidate_and_keeps_attempts(root, monkeypatch, completed_key):
    store = root / "owner_recovery"
    pipeline(root)
    monkeypatch.setattr(m, "REPO", root)
    monkeypatch.setattr(m, "account_probe", lambda *a: responses())
    monkeypatch.setattr(m, "eligible", lambda *a: (True, "included"))
    def prepare(config, state, directory, snapshot):
        (directory / "prompt.md").write_text("fixed")
        result = {"status": "COMPLETE", "incident_id": "fixture"}
        if completed_key is not None:
            result["serviced_event_key"] = completed_key
        m.write(directory / "phase_result.json", result)
        return "hash"
    monkeypatch.setattr(m, "prepare_handoff", prepare)
    monkeypatch.setattr(m, "receipt_valid", lambda attempt, directory, candidate: candidate["id"] == "vals_codex")
    fail = root / "fail.py"
    fail.write_text("import json\nprint(json.dumps({'type':'turn.failed','error':{'message':'usage limit'}}))\n")
    success = root / "success.py"
    success.write_text("print('harmless first useful action')\n")
    candidates = [{"id": profile, "prefix": [sys.executable, str(script)],
                   "model": "gpt-6-astra", "effort": "ultra", "file_sha256": {str(script): m.digest(script)}}
                  for profile, script in [("personal_codex", fail), ("vals_codex", success)]]
    state = {"incident": {"id": "fixture", "deadline_utc": (
        dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=40)).isoformat(), "attempts": []}}
    incident = state["incident"]
    # A long-lived monitor can still compute the old schema after its owner updates the source.
    current = {"key": "event"}
    monkeypatch.setattr(m, "event_snapshot", lambda *args: dict(current))
    m.drive({"candidates": candidates}, state, {"key": "event"}, store)
    assert state["status"] == "ARMED"
    assert state["serviced_key"] == (completed_key or "event")
    assert len(incident["attempts"]) == 2
    assert incident["attempts"][0]["failure_class"] == "allowance"
    assert incident["attempts"][1]["status"] == "VERIFIED_COMPLETE"
    archived = store / "incidents/fixture/receipt.json"
    assert m.read(archived)["attempts"] == incident["attempts"]
    archive_hash = m.digest(archived)

    # The next cron invocation sees the owner's schema: exact completion must stay idle.
    current["key"] = completed_key or "event"
    calls = []
    monkeypatch.setattr(m, "drive", lambda config, state, snapshot, storage: calls.append(snapshot))
    assert m.tick({"enabled": True}, store) == "ARMED"
    assert not calls

    # A later unseen semantic state still creates a new incident; prior accounting is intact.
    current["key"] = "genuinely-new-event"
    m.tick({"enabled": True}, store)
    assert calls == [{"key": "genuinely-new-event"}]
    assert m.read(store / "monitor_state.json")["incident"]["event_key"] == "genuinely-new-event"
    assert m.digest(archived) == archive_hash


def test_expired_incident_does_not_reset_or_probe(root, monkeypatch):
    store = root / "owner_recovery"
    state = {"incident": {"id": "old", "deadline_utc": "2000-01-01T00:00:00+00:00",
                         "attempts": [{"profile": "personal_codex"}]}}
    monkeypatch.setattr(m, "account_probe", lambda *a: pytest.fail("expired budget"))
    m.drive({"candidates": [{"id": "vals_codex"}]}, state, {"key": "event"}, store)
    assert state["status"] == "INCIDENT_DEADLINE"
    assert len(state["incident"]["attempts"]) == 1


def test_changed_prompt_or_executable_is_rejected(tmp_path):
    p = tmp_path / "fixed"
    p.write_text("verified")
    config = {"schema": 1, "candidates": [{"id": "personal_codex", "model": "gpt-6-astra",
        "effort": "ultra", "file_sha256": {str(p): m.digest(p)}}],
        "prompt": str(p), "prompt_sha256": m.digest(p)}
    assert m.verify_manifest(config) == config
    p.write_text("changed")
    assert m.candidate_integrity(config["candidates"][0])[0] is False
    with pytest.raises(ValueError, match="prompt changed"):
        m.verify_manifest(config)


def test_exited_owner_clears_old_status_and_services_next_event(root, monkeypatch):
    pipeline(root)
    store = root / "owner_recovery"
    m.write(store / "monitor_state.json", {"status": "OWNER_ACTIVE", "serviced_key": "old",
                                         "owner": None, "adopted_initial": False})
    calls = []
    monkeypatch.setattr(m, "drive", lambda *args: calls.append(args))
    m.tick({"enabled": True}, store)
    assert len(calls) == 1


def test_finished_initial_phase_disarms_recovery_until_new_event(root, monkeypatch):
    pipeline(root)
    store = root / "owner_recovery"
    key = m.event_snapshot(root)["key"]
    m.write(store / "monitor_state.json", {"status": "OWNER_ACTIVE", "serviced_key": "old",
                                         "owner": None, "adopted_initial": True})
    m.write(store / "launch_receipt.json", {"incident_id": "original"})
    m.write(store / "phase_result.json", {"status": "COMPLETE", "incident_id": "original",
                                        "serviced_event_key": key})
    monkeypatch.setattr(m, "drive", lambda *args: pytest.fail("idle model wake"))
    assert m.tick({"enabled": True}, store) == "ARMED"
    assert not m.read(store / "monitor_state.json")["adopted_initial"]


def test_initial_failure_preserves_deadline_and_consumed_profiles(root, monkeypatch):
    pipeline(root)
    store = root / "owner_recovery"
    m.write(store / "monitor_state.json", {"status": "OWNER_ACTIVE", "serviced_key": "old",
                                         "owner": None, "adopted_initial": True})
    deadline = "2000-01-01T00:00:00+00:00"
    m.write(store / "launch_receipt.json", {"incident_id": "original",
        "coordinator_incident_deadline_utc": deadline,
        "attempts": [{"profile": "stanford_codex", "status": "EXITED"},
                     {"profile": "personal_codex", "status": "EXITED"}]})
    calls = []
    monkeypatch.setattr(m, "drive", lambda config, state, *args: calls.append(state["incident"]))
    m.tick({"enabled": True}, store)
    assert calls[0]["deadline_utc"] == deadline
    assert [a["profile"] for a in calls[0]["attempts"]] == ["stanford_codex", "personal_codex"]


def test_receipt_requires_native_permissions_hash_ack_and_fresh_output(root):
    directory = root / "owner_recovery" / "fixture"
    directory.mkdir()
    profile = root / "profile"
    native = profile / "sessions/2026/10/09"
    native.mkdir(parents=True)
    session = "synthetic-native-session"
    candidate = {"model": "gpt-6-astra", "effort": "ultra", "profile_directory": str(profile)}
    started = m.now()
    (directory / "prompt.md").write_text("fixed handoff")
    (directory / "events.jsonl").write_text(json.dumps({"type": "thread.started", "thread_id": session}) + "\n")
    context = {"model": "gpt-6-astra", "effort": "ultra", "approval_policy": "never",
               "sandbox_policy": {"type": "danger-full-access"}}
    rollout = native / f"rollout-{session}.jsonl"
    rollout.write_text(json.dumps({"type": "turn_context", "payload": context}) + "\n")
    output = directory / "useful_check.json"
    output.write_text('{"checked": true}\n')
    attempt = {"incident_id": "fixture", "started_utc": started,
               "handoff_sha256": m.digest(directory / "prompt.md")}
    m.write(directory / "ack.json", {"native_session_id": session, "incident_id": "fixture",
                                    "handoff_sha256": attempt["handoff_sha256"]})
    m.write(directory / "first_action.json", {"native_session_id": session,
            "outputs": [{"path": str(output), "sha256": m.digest(output)}]})
    m.write(directory / "phase_result.json", {"status": "COMPLETE", "incident_id": "fixture"})
    assert m.receipt_valid(attempt, directory, candidate)
    context["sandbox_policy"] = {"type": "read-only"}
    rollout.write_text(json.dumps({"type": "turn_context", "payload": context}) + "\n")
    assert not m.receipt_valid(attempt, directory, candidate)
    context["sandbox_policy"] = {"type": "danger-full-access"}
    rollout.write_text(json.dumps({"type": "turn_context", "payload": context}) + "\n")
    output.write_text("changed")
    assert not m.receipt_valid(attempt, directory, candidate)
