#!/usr/bin/env python3
"""Observe experiment 08 and recover its coordinator through fixed, verified subscription clients."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import uuid

WORK = Path("/lfs/skampere1/0/brando9/rl4cv_e08")
REPO = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[2]
SECRET_ENV = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY",
              "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
              "MODEL_GATEWAY_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boot():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def identity(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return None
        return {"pid": int(pid), "start_ticks": int(fields[19]), "boot_id": boot(),
                "ppid": int(fields[1]), "session": int(fields[3])}
    except (FileNotFoundError, ProcessLookupError):
        return None


def alive(expected):
    if not expected:
        return False
    current = identity(expected["pid"])
    return bool(current and all(current[k] == expected[k] for k in ("pid", "start_ticks", "boot_id")))


def descendants(parent):
    if not alive(parent):
        return []
    procs = {}
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            with contextlib.suppress(FileNotFoundError, ProcessLookupError, PermissionError):
                v = identity(int(p.name))
                if v:
                    procs[v["pid"]] = v
    seen = {parent["pid"]}
    while True:
        added = {pid for pid, v in procs.items() if v["ppid"] in seen} - seen
        if not added:
            break
        seen |= added
    return [procs[p] for p in seen - {parent["pid"]}]


def session_survivors(expected):
    if not expected or expected["boot_id"] != boot():
        return []
    result = []
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            with contextlib.suppress(FileNotFoundError, ProcessLookupError, PermissionError):
                info = identity(int(p.name))
                if info and info["session"] == expected["pid"] and info["pid"] != expected["pid"]:
                    result.append(info)
    return result


@contextlib.contextmanager
def locked(path):
    with path.open("a") as fd:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def native_events(path):
    """Only structured native error records classify failures; tool/model text is not executable."""
    session, failures = None, []
    if path.exists():
        for line in path.open(errors="replace"):
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if not isinstance(item, dict):
                continue
            if item.get("type") == "thread.started":
                session = item.get("thread_id")
            if item.get("type") in ("error", "turn.failed"):
                failures.append(item.get("message", item.get("error", "")))
    return session, failures


def classify(errors):
    text = json.dumps(errors).lower()
    for category, terms in (
        ("managed_permissions", ("managed", "approval is not supported", "allowed sandbox")),
        ("spending_limit", ("spend control", "spending limit", "insufficient credit", "out of credits")),
        ("allowance", ("usage limit", "quota", "exceeded your", "usage_limit")),
        ("authentication", ("unauthorized", "authentication", "token expired", "401")),
        ("model_entitlement", ("model not found", "not have access", "unsupported model")),
        ("context", ("context window", "context length", "context limit", "turn limit")),
        ("rate_limit", ("rate limit", "429")),
        ("transport", ("connection", "timed out", "timeout", "disconnected")),
    ):
        if any(term in text for term in terms):
            return category
    return "unverified_exit"


def event_snapshot(work):
    p = read(work / "pipeline/state.json", {})
    # Device numbers, timestamps, e09 availability and stale historical child counters do not wake a model.
    summary = {k: v for k, v in p.get("summary", {}).items() if k != "e09_admission"}
    stages = p.get("stages", {})
    errors = {k: v for k, v in summary.items()
              if any(t in str(v).lower() for t in ("error", "critical", "fail", "unavailable", "incomplete"))}
    if (work / "pipeline/DONE").exists():
        phase = "pipeline_terminal"
    elif "judge" in summary:
        value = str(summary["judge"])
        phase = "judge:done" if value == "done" else ("judge:controls" if "control" in value.lower() else "judge:test")
    elif "test_generation" in summary or any(k.startswith("ladder_test_") for k in summary):
        phase = "test"
    elif summary.get("selection") in ("RL-READY", "PARTIAL", "NOT READY"):
        phase = "selection:" + summary["selection"]
    elif summary.get("sft_14B") == "done":
        phase = "14b_validation"
    elif summary.get("sft_14B") in ("running", "launched"):
        phase = "14b_training"
    else:
        phase = "device_wait"
    # Keep one event per semantic state; growing progress counts and error timestamps are omitted.
    health = "unknown"
    pid = p.get("pid")
    current = identity(pid) if pid else None
    if current and current["boot_id"] == p.get("boot_id"):
        age = time.time() - dt.datetime.fromisoformat(p["last_tick"]).timestamp()
        health = "fresh" if age <= 900 else "stale"
    elif p:
        health = "exited"
    judge_state = read(EXP / "expt_v1/results/judge/state.json", {})
    for key, entry in judge_state.get("runs", {}).items():
        if (str(entry.get("benchmark", "")).startswith("veribench-rl4cv-e08")
                and entry.get("phase") in ("admission_failed", "admitting") and not entry.get("run_id")):
            errors["judge_admission:" + key] = entry["phase"]
    retry = {k: s.get("retries", 0) for k, s in stages.items() if s.get("retries", 0)}
    event = {"phase": phase, "errors": errors, "pipeline_health": health, "stage_retries": retry}
    layout = EXP / "expt_v1/results/sft_layout_admission_14B.json"
    if layout.exists():
        event["sft_layout_admission_sha256"] = digest(layout)
    key = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
    return {"key": key, "event": event, "observed_utc": now(), "pipeline": current,
            "last_tick": p.get("last_tick"), "summary": summary}


def clean_env():
    env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
    # Profile wrappers choose their own existing home; an inherited override is not silently changed.
    if env.get("CODEX_HOME"):
        raise RuntimeError("unexpected inherited CODEX_HOME; profile identity unverified")
    return env


def account_probe(candidate, cwd, timeout=40):
    """Read-only native app-server requests; never starts a thread or inference turn."""
    reqs = [
        ("account/read", {"refreshToken": False}),
        ("account/rateLimits/read", {}),
        ("configRequirements/read", {}),
        ("model/list", {"limit": 100, "includeHidden": False}),
    ]
    p = subprocess.Popen(candidate["prefix"] + ["app-server", "--stdio"], cwd=cwd,
                         env=clean_env(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(p.stdout, selectors.EVENT_READ)
    responses = {}
    def send(obj):
        p.stdin.write((json.dumps(obj) + "\n").encode())
        p.stdin.flush()
    deadline = time.monotonic() + timeout
    try:
        send({"id": 0, "method": "initialize", "params": {"clientInfo": {
            "name": "e08_coordinator_monitor", "version": "1.0"}}})
        initialized = False
        buffer = b""
        while time.monotonic() < deadline and len(responses) < len(reqs):
            if not selector.select(min(1, max(0, deadline - time.monotonic()))):
                continue
            data = os.read(p.stdout.fileno(), 65536)
            if not data:
                raise RuntimeError("native account probe exited")
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                item = json.loads(line)
                if item.get("id") == 0:
                    if item.get("error"):
                        raise RuntimeError("native initialization failed")
                    send({"method": "initialized", "params": {}})
                    for i, (method, params) in enumerate(reqs, 1):
                        send({"id": i, "method": method, "params": params})
                    initialized = True
                elif initialized and isinstance(item.get("id"), int) and 1 <= item["id"] <= len(reqs):
                    if item.get("error"):
                        raise RuntimeError("native read failed: " + reqs[item["id"] - 1][0])
                    responses[reqs[item["id"] - 1][0]] = item.get("result", {})
        if len(responses) != len(reqs):
            raise RuntimeError("native account read timeout")
        return responses
    finally:
        selector.close()
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()


def eligible(candidate, response):
    account = response["account/read"].get("account") or {}
    if account.get("type") != "chatgpt" or account.get("email") != candidate["account_email"]:
        return False, "account_identity"
    requirements = response["configRequirements/read"].get("requirements")
    if requirements:
        policies = requirements.get("allowedApprovalPolicies")
        modes = requirements.get("allowedSandboxModes")
        if policies is not None and "never" not in policies:
            return False, "managed_permissions"
        if modes is not None and not set(modes) & {"dangerFullAccess", "danger-full-access"}:
            return False, "managed_permissions"
    limits = response["account/rateLimits/read"]
    buckets = limits.get("rateLimitsByLimitId") or {"codex": limits.get("rateLimits", {})}
    observed = False
    for limit in buckets.values():
        if limit.get("spendControlReached") or limit.get("rateLimitReachedType"):
            return False, "spending_or_allowance_limit"
        for window in ("primary", "secondary"):
            row = limit.get(window)
            if row:
                observed = True
                if row.get("usedPercent", 100) >= 75:
                    return False, "included_allowance_reserve"
    if not observed:
        return False, "allowance_unknown"
    models = response["model/list"].get("data", [])
    model = next((m for m in models if m.get("model") == candidate["model"]
                  or m.get("id") == candidate["model"]), None)
    if not model:
        return False, "model_catalog"
    efforts = {e.get("reasoningEffort") for e in model.get("supportedReasoningEfforts", [])}
    if candidate["effort"] not in efforts:
        return False, "effort_catalog"
    return True, "included_allowance"


def verify_manifest(config):
    if config.get("schema") != 1 or not 1 <= len(config["candidates"]) <= 2:
        raise ValueError("finite candidate manifest required")
    if {c["id"] for c in config["candidates"]} - {"personal_codex", "vals_codex"}:
        raise ValueError("unverified candidate")
    for c in config["candidates"]:
        if c["model"] != "gpt-6-astra" or c["effort"] != "ultra":
            raise ValueError("coordinator pin changed")
    if digest(Path(config["prompt"])) != config["prompt_sha256"]:
        raise ValueError("continuation prompt changed")
    return config



def candidate_integrity(candidate):
    for name, expected in candidate["file_sha256"].items():
        if not Path(name).is_file() or digest(Path(name)) != expected:
            return False, "candidate executable changed: " + name
    return True, "verified executable hashes"


def runtime_context(candidate, session):
    if not session:
        return None
    for p in (Path(candidate["profile_directory"]) / "sessions").glob(f"*/*/*/*{session}.jsonl"):
        for line in p.open(errors="replace"):
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("type") == "turn_context":
                v = row["payload"]
                return {"session_id": session, "model": v.get("model"), "effort": v.get("effort"),
                        "approval_policy": v.get("approval_policy"),
                        "sandbox_mode": (v.get("sandbox_policy") or {}).get("type")}
    return None


def receipt_valid(attempt, directory, candidate):
    ack = read(directory / "ack.json", {})
    action = read(directory / "first_action.json", {})
    result = read(directory / "phase_result.json", {})
    session, _ = native_events(directory / "events.jsonl")
    ctx = runtime_context(candidate, session)
    expected = {"session_id": session, "model": candidate["model"], "effort": candidate["effort"],
                "approval_policy": "never", "sandbox_mode": "danger-full-access"}
    if not session or ctx != expected:
        return False
    if not (directory / "prompt.md").exists() or digest(directory / "prompt.md") != attempt["handoff_sha256"]:
        return False
    if ack.get("handoff_sha256") != attempt["handoff_sha256"] or ack.get("native_session_id") != session:
        return False
    if ack.get("incident_id") != attempt["incident_id"] or action.get("native_session_id") != session:
        return False
    outputs = action.get("outputs", [])
    if not outputs:
        return False
    for item in outputs:
        p = Path(item["path"])
        if (not p.resolve().is_relative_to(directory.resolve()) or not p.is_file()
                # Filesystem timestamps may trail wall-clock time by a tick; the directory is unique per attempt.
                or p.stat().st_mtime + 1 < dt.datetime.fromisoformat(attempt["started_utc"]).timestamp()
                or digest(p) != item["sha256"]):
            return False
    return result.get("status") == "COMPLETE" and result.get("incident_id") == attempt["incident_id"]


def prepare_handoff(config, state, directory, snapshot):
    files = [EXP / "PROTOCOL.md", EXP / "expt_v1/cc.md", EXP / "expt_v1/CKPT_e08.md",
             EXP / "results.md", WORK / "pipeline/state.json", WORK / "pipeline/leases.json"]
    packet = {"incident_id": state["incident"]["id"], "event": snapshot,
              "deadline_utc": state["incident"]["deadline_utc"],
              "project_revision": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
              "policy_revision": subprocess.check_output(["git", "-C", str(Path.home() / "agents-config"), "rev-parse", "HEAD"], text=True).strip(),
              "file_sha256": {str(p): digest(p) for p in files},
              "original_launch_receipt_sha256": digest(WORK / "owner_recovery/launch_receipt.json"),
              "scientific_accounting": "All existing cells, calls, retries, gates, locks and funding route persist."}
    write(directory / "handoff.json", packet)
    text = Path(config["prompt"]).read_text() + (
        "\nThis invocation's receipt directory: " + str(directory) +
        "\nRead handoff.json there, verify its stable input hashes; runtime state may advance."
        "\nIncident: " + packet["incident_id"] + "\nDeadline: " + packet["deadline_utc"] + "\n")
    (directory / "prompt.md").write_text(text)
    return digest(directory / "prompt.md")



def archive_incident(storage, state, incident, status):
    incident = dict(incident, status=status, ended_utc=now())
    path = storage / "incidents" / incident["id"] / "receipt.json"
    write(path, incident)
    state.setdefault("completed_incidents", []).append(
        {"id": incident["id"], "path": str(path), "sha256": digest(path), "status": status})


def drive(config, state, snapshot, storage):
    """Called only while both monitor.lock and owner.lock are held; neither is the pipeline lock."""
    incident = state["incident"]
    for candidate in config["candidates"]:
        if time.time() >= dt.datetime.fromisoformat(incident["deadline_utc"]).timestamp():
            state["status"] = "INCIDENT_DEADLINE"
            break
        if any(a["profile"] == candidate["id"] for a in incident["attempts"]):
            continue
        number = len(incident["attempts"]) + 1
        directory = storage / "incidents" / incident["id"] / str(number)
        directory.mkdir(parents=True, exist_ok=True)
        attempt = {"profile": candidate["id"], "number": number, "incident_id": incident["id"],
                   "started_utc": now(), "receipt_directory": str(directory), "status": "PROBING"}
        incident["attempts"].append(attempt)
        write(storage / "monitor_state.json", state)
        try:
            intact, integrity_reason = candidate_integrity(candidate)
            if not intact:
                raise RuntimeError(integrity_reason)
            response = account_probe(candidate, REPO)
            allowed, reason = eligible(candidate, response)
            # Only nonsecret account/usage/config/model metadata from read methods.
            write(directory / "account_check.json", response)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            allowed, reason = False, type(exc).__name__ + ":" + str(exc)
        if not allowed:
            attempt.update(status="INELIGIBLE", reason=reason, ended_utc=now())
            write(storage / "monitor_state.json", state)
            continue
        with locked(WORK / "pipeline/lock") as acquired:
            if not acquired:
                # No model call attempted: preserve candidate availability, defer snapshot atomically.
                incident["attempts"].pop()
                state["status"] = "WAITING_PIPELINE_LOCK"
                write(storage / "monitor_state.json", state)
                return
            attempt["handoff_sha256"] = prepare_handoff(config, state, directory, snapshot)
        cmd = candidate["prefix"] + ["exec", "--dangerously-bypass-approvals-and-sandbox",
              "-m", candidate["model"], "-c", 'model_reasoning_effort="ultra"', "--json",
              "-o", str(directory / "last_message.txt"), "-"]
        attempt["command"] = cmd
        with (directory / "prompt.md").open() as inp, (directory / "events.jsonl").open("w") as out, (directory / "stderr.log").open("w") as err:
            child = subprocess.Popen(cmd, cwd=REPO, env=clean_env(), stdin=inp, stdout=out,
                                     stderr=err, start_new_session=True, close_fds=True)
            attempt.update(status="RUNNING_UNVERIFIED", process=identity(child.pid))
            state["owner"] = attempt["process"]
            state["last_owner"] = attempt["process"]
            state.pop("orphan_deadline_signal_epoch", None)
            write(storage / "monitor_state.json", state)
            observed_children, signaled = {}, None
            while child.poll() is None:
                for item in descendants(attempt["process"]):
                    observed_children[item["pid"]] = item
                _, errors = native_events(directory / "events.jsonl")
                expired = time.time() >= dt.datetime.fromisoformat(incident["deadline_utc"]).timestamp()
                # Terminate only the exact coordinator on a native terminal failure/deadline.
                if (expired or errors) and signaled is None and alive(attempt["process"]):
                    child.send_signal(signal.SIGINT)
                    signaled = time.monotonic()
                elif signaled is not None and time.monotonic() - signaled > 30 and alive(attempt["process"]):
                    child.terminate()
                state["observed_utc"] = now()
                attempt["observed_descendants"] = list(observed_children.values())
                write(storage / "monitor_state.json", state)
                time.sleep(5)
            child.wait()
        _, errors = native_events(directory / "events.jsonl")
        attempt.update(status="EXITED", exit_code=child.returncode, ended_utc=now(),
                       failure_class=classify(errors), native_errors=errors)
        survivors = [v for v in observed_children.values() if alive(v)]
        state["owner"] = None
        if survivors:
            state.update(status="CHILD_ADOPTION_REQUIRED", survivors=survivors)
            break
        if receipt_valid(attempt, directory, candidate):
            attempt["status"] = "VERIFIED_COMPLETE"
            archive_incident(storage, state, incident, "VERIFIED_COMPLETE")
            completed = read(directory / "phase_result.json", {})
            # Honor the verified result even if this long-lived monitor uses an older event schema.
            # The next tick compares its current snapshot, so an unseen event still stays pending.
            state.update(status="ARMED", incident=None,
                         serviced_key=completed.get("serviced_event_key") or snapshot["key"])
            break
        write(storage / "monitor_state.json", state)
    else:
        state["status"] = "CANDIDATES_EXHAUSTED_REQUIRES_INVENTORY"
    write(storage / "monitor_state.json", state)


def tick(config, storage):
    with locked(storage / "monitor.lock") as acquired:
        if not acquired:
            return "MONITOR_BUSY"
        state = read(storage / "monitor_state.json")
        if state is None:
            raise RuntimeError("monitor must be explicitly initialized from the owned handoff")
        snapshot = event_snapshot(WORK)
        state.update(observed_utc=now(), snapshot=snapshot, status="OBSERVING")
        if not config.get("enabled"):
            state["status"] = "DISABLED"
        elif alive(state.get("owner")):
            state["last_owner"] = state["owner"]
            state["survivors"] = descendants(state["owner"])
            state["status"] = "OWNER_ACTIVE"
            deadline = (state.get("incident") or {}).get("deadline_utc")
            if deadline and time.time() >= dt.datetime.fromisoformat(deadline).timestamp():
                first = state.setdefault("orphan_deadline_signal_epoch", time.time())
                os.kill(state["owner"]["pid"], signal.SIGTERM if time.time() - first > 30 else signal.SIGINT)
                state["status"] = "OWNER_DEADLINE_SIGNALLED"
        elif session_survivors(state.get("last_owner")) or any(alive(v) for v in state.get("survivors", [])):
            state["status"] = "CHILD_ADOPTION_REQUIRED"
        elif state.get("adopted_initial"):
            # The original launch guard owns candidate attempts/deadline until it exits.
            initial = read(storage / "phase_result.json", {})
            launch = read(storage / "launch_receipt.json", {})
            if initial.get("status") == "COMPLETE" and initial.get("incident_id") == launch.get("incident_id"):
                state.update(adopted_initial=False, owner=None, status="ARMED",
                             serviced_key=initial.get("serviced_event_key", state["serviced_key"]))
            else:
                state["status"] = "INITIAL_PHASE_UNFINISHED"
                state["incident"] = {"id": launch["incident_id"],
                                     "deadline_utc": launch["coordinator_incident_deadline_utc"],
                                     "attempts": [{"profile": a["profile"], "status": a["status"],
                                                   "source": "original_launch_receipt"} for a in launch["attempts"]]}
                state["adopted_initial"] = False
        if state["status"] in ("OWNER_ACTIVE", "OWNER_DEADLINE_SIGNALLED", "DISABLED", "CHILD_ADOPTION_REQUIRED"):
            write(storage / "monitor_state.json", state)
            return state["status"]
        incident = state.get("incident")
        if incident and incident["attempts"]:
            previous = incident["attempts"][-1]
            if previous.get("receipt_directory"):
                candidate = next(c for c in config["candidates"] if c["id"] == previous["profile"])
                directory = Path(previous["receipt_directory"])
                if receipt_valid(previous, directory, candidate):
                    result = read(directory / "phase_result.json")
                    archive_incident(storage, state, incident, "VERIFIED_COMPLETE_AFTER_MONITOR_EXIT")
                    state.update(incident=None, owner=None, status="ARMED",
                                 serviced_key=result.get("serviced_event_key", incident.get("event_key")))
        # An exited driver may have left a native child; never infer all writers exited from its PID alone.
        old_attempts = (state.get("incident") or {}).get("attempts", [])
        survivors = [v for a in old_attempts for v in a.get("observed_descendants", []) if alive(v)]
        if survivors:
            state.update(status="CHILD_ADOPTION_REQUIRED", survivors=survivors)
            write(storage / "monitor_state.json", state)
            return state["status"]
        if (storage / "STOP").exists():
            state["status"] = "STOPPED"
        elif not state.get("incident") and snapshot["key"] == state.get("serviced_key"):
            state["status"] = "ARMED"
        else:
            with locked(storage / "owner.lock") as owner_acquired:
                if not owner_acquired:
                    state["status"] = "WAITING_OWNER_LOCK"
                else:
                    if not state.get("incident"):
                        state["incident"] = {"id": str(uuid.uuid4()), "created_utc": now(),
                            "deadline_utc": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=70)).isoformat(),
                            "attempts": [], "event_key": snapshot["key"]}
                    write(storage / "monitor_state.json", state)
                    drive(config, state, snapshot, storage)
        write(storage / "monitor_state.json", state)
        return state["status"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, default=WORK)
    ap.add_argument("--probe", choices=("personal_codex", "vals_codex"))
    ap.add_argument("--observe", action="store_true")
    args = ap.parse_args()
    global_work(args.work)
    storage = WORK / "owner_recovery"
    config = verify_manifest(read(storage / "monitor_manifest.json"))
    if args.observe:
        print(json.dumps(event_snapshot(WORK), indent=2))
    elif args.probe:
        candidate = next(c for c in config["candidates"] if c["id"] == args.probe)
        response = account_probe(candidate, REPO)
        write(storage / f"probe_{args.probe}.json", response)
        print(json.dumps({"profile": args.probe, "eligibility": eligible(candidate, response)}))
    else:
        print(tick(config, storage))


def global_work(path):
    global WORK
    WORK = path


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write(WORK / "owner_recovery/monitor_error.json",
              {"observed_utc": now(), "error_type": type(exc).__name__, "message": str(exc)[:500]})
        raise
