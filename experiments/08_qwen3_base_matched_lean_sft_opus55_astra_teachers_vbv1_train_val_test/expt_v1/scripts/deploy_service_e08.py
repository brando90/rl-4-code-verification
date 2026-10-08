#!/usr/bin/env python3
"""TLDR: Deploy, inspect and tear down experiment 08's collect-only single-call VeriBench service (experiment 103's `vb_service_single_call`, imported unmodified from this clone's pinned checkout) serving the 539-task train pack on claimed port 9740 behind a bearer-protected cloudflared tunnel, registered as benchmark `rl4cv-e08-vbv1-train` in a private copy of the host Valkyrie configuration (PROTOCOL § 3, runbook § 4.1; zero model calls). Adapted from experiment 02A v3's `deploy_service_e02a.py`."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
PRIVATE = WORK / "private"
E103 = REPO_ROOT / "external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
SERVICE_DIR = E103 / "scripts" / "vb_service_single_call"
KERNEL_AXIOMS = REPO_ROOT / "external/veribench/scripts/scsc/kernel_axioms.py"
LAKE_DIR = WORK / "grading" / "lean_src"                      # never compiled by the collect-only service; the path must merely exist
UVICORN = Path("/lfs/skampere1/0/brando9/vb103_venv/bin/uvicorn")   # shared service interpreter (benchmark_service installed), used read-only
CLOUDFLARED = Path("/lfs/skampere1/0/brando9/vb-e2-service-20260916/bin/cloudflared")
HOST_CONFIG = Path.home() / ".config/valkyrie/valkyrie.yaml"
BENCHMARK, PORT, PORT_CLAIM = "rl4cv-e08-vbv1-train", 9740, "9740-9759"   # /lfs/skampere1/0/brando9/valkyrie_port_claims/rl4cv-e08_9740-9759.txt
PACK = WORK / "pack_train539"
NAME = "teachers"   # receipt name; judge instances override BENCHMARK / PORT / PACK / NAME / EXPECTED_TASKS from the command line
# Agent client timeout (vb103_single_call VB103_CALL_TIMEOUT_S default 3000 s): the per-task limit must be >= 2 x 3000 + 600 (PROTOCOL § 12.3).
AGENT_CLIENT_TIMEOUT_S = 3000
AGENT_TIMEOUT_S = 2 * AGENT_CLIENT_TIMEOUT_S + 600
PROVIDER_ENV = ("AUTH_DISABLED", "PYTHONPATH", "PYTHONHOME", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                "MODEL_GATEWAY_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN", "VALKYRIE_API_KEY")
PUBLIC_RECEIPT = EXP / "results" / "deployment_e08.json"
EXPECTED_TASKS = 539


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (TypeError, ValueError, OSError):
        return False


def probe(url: str, bearer: str | None, timeout: float = 20) -> int:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"} if bearer else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001 - not reachable yet
        return 0


def get_json(url: str, bearer: str, timeout: float = 120):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def wait_for(check, what: str, tries: int = 90, delay: float = 2.0):
    for _ in range(tries):
        result = check()
        if result:
            return result
        time.sleep(delay)
    raise SystemExit(f"{what} timed out")


def listening(port: int) -> bool:
    out = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True).stdout
    return bool(re.search(rf":{port}\s", out))


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def task_limits(url: str, bearer: str) -> dict:
    """Read the per-task limit back from the service itself (`/retrieve-task/` carries `agent_timeout`)."""
    ids = sorted(p.name for p in PACK.iterdir() if p.is_dir())
    sample = [ids[0], ids[len(ids) // 2], ids[-1]]
    timeouts = {}
    for tid in sample:
        data = get_json(url + f"/retrieve-task/?task_id={tid}", bearer)
        timeouts[tid] = data.get("agent_timeout") if isinstance(data, dict) else None
    verify = get_json(url + "/verify-task-ids?" + "&".join(f"task_ids={tid}" for tid in sample), bearer)
    vals = sorted({float(v) for v in timeouts.values() if v is not None})
    return {"sampled_task_ids": sample, "agent_timeout_s": timeouts, "verify_task_ids_response": verify, "required_min_s": AGENT_TIMEOUT_S,
            "limit_ok": bool(vals) and len(vals) == 1 and vals[0] >= AGENT_TIMEOUT_S}


def cmd_deploy(a) -> int:
    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    os.chmod(PRIVATE, 0o700)
    receipt_path = PRIVATE / ("deployment.json" if NAME == "teachers" else f"deployment_{NAME}.json")
    old = read_json(receipt_path, {})
    if alive(old.get("service_pid")) or alive(old.get("tunnel_pid")):
        raise SystemExit("a live deployment is recorded; run teardown first (a new tunnel URL orphans a running run)")
    if listening(PORT):
        raise SystemExit(f"port {PORT} is already listening; refusing to bind (check ss -tlnp and valkyrie_port_claims)")
    for p, what in ((PACK, "pack"), (SERVICE_DIR, "service dir"), (KERNEL_AXIOMS, "kernel axiom checker"), (LAKE_DIR, "lake dir"),
                    (UVICORN, "uvicorn"), (CLOUDFLARED, "cloudflared"), (HOST_CONFIG, "host Valkyrie config")):
        if not p.exists():
            raise SystemExit(f"{what} missing: {p}")
    n_pack = len([p for p in PACK.iterdir() if p.is_dir()])
    if EXPECTED_TASKS and n_pack != EXPECTED_TASKS:
        raise SystemExit(f"pack holds {n_pack} task dirs, expected {EXPECTED_TASKS}")
    bearer_path = PRIVATE / ("service_bearer" if NAME == "teachers" else f"service_bearer_{NAME}")
    if not bearer_path.exists():
        bearer_path.write_text(secrets.token_urlsafe(36))
    os.chmod(bearer_path, 0o600)
    bearer = bearer_path.read_text().strip()
    env = {k: v for k, v in os.environ.items() if k not in PROVIDER_ENV}
    env.update(VB_SERVICE_KEY_FILE=str(bearer_path), VB_TASK_PACK=str(PACK), VB_CONTROL_PACK="1", VB_NO_COMPILER="1", VB_COLLECT_ONLY="1",
               VB_LAKE_DIR=str(LAKE_DIR), VB_KERNEL_AXIOMS=str(KERNEL_AXIOMS), VB_GRADE_SCRATCH=str(PRIVATE / "grade_scratch"),
               VB_GRADE_NETNS="off", VB_IC_PP="offline", VB_AGENT_TIMEOUT_S=str(AGENT_TIMEOUT_S), VB_SETUP_TIMEOUT_S="900",
               VB_RESOURCES_VCPU="2", VB_RESOURCES_MEMORY="4", VB_RESOURCES_DISK="20")
    local = f"http://127.0.0.1:{PORT}"
    service_log = open(PRIVATE / ("service.log" if NAME == "teachers" else f"service_{NAME}.log"), "ab", buffering=0)
    service = subprocess.Popen([str(UVICORN), "main:app", "--host", "127.0.0.1", "--port", str(PORT)], cwd=str(SERVICE_DIR), env=env,
                               stdin=subprocess.DEVNULL, stdout=service_log, stderr=service_log, start_new_session=True)
    (PRIVATE / ("service.pid" if NAME == "teachers" else f"service_{NAME}.pid")).write_text(str(service.pid))
    wait_for(lambda: probe(local + "/health", bearer) == 200 or service.poll() is not None, "local health")
    if service.poll() is not None:
        raise SystemExit("service exited during startup; see private/service.log")
    if probe(local + "/health", None) != 401:
        os.killpg(service.pid, signal.SIGTERM)
        raise SystemExit("local service answered an unauthenticated probe; refusing to expose it")
    limits = task_limits(local, bearer)
    tunnel_log = PRIVATE / ("tunnel.log" if NAME == "teachers" else f"tunnel_{NAME}.log")
    tunnel_log.write_bytes(b"")
    tunnel = subprocess.Popen([str(CLOUDFLARED), "tunnel", "--no-autoupdate", "--url", local], stdin=subprocess.DEVNULL,
                              stdout=open(tunnel_log, "ab", buffering=0), stderr=subprocess.STDOUT, start_new_session=True)
    (PRIVATE / ("tunnel.pid" if NAME == "teachers" else f"tunnel_{NAME}.pid")).write_text(str(tunnel.pid))
    url = wait_for(lambda: (re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", tunnel_log.read_text()) or [None])[-1], "tunnel hostname")
    wait_for(lambda: probe(url + "/health", bearer) == 200, "tunnel health", tries=60)
    unauth = probe(url + "/health", None)
    if unauth != 401:
        for proc in (service, tunnel):
            os.killpg(proc.pid, signal.SIGTERM)
        raise SystemExit(f"tunnel answered an unauthenticated probe with {unauth}; refusing")
    tunnel_limits = task_limits(url, bearer)
    import yaml
    target = PRIVATE / "valkyrie.yaml"
    cfg = yaml.safe_load(target.read_text()) if target.exists() else yaml.safe_load(HOST_CONFIG.read_text())   # keep earlier instances registered
    cfg.setdefault("custom_benchmark_services", {})[BENCHMARK] = url
    cfg.setdefault("benchmark_auth", {})[BENCHMARK] = "Bearer " + bearer
    target.write_text(yaml.safe_dump(cfg))
    os.chmod(target, 0o600)
    service_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SERVICE_DIR.glob("*.py"))}
    veribench_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT / "external/veribench", capture_output=True, text=True).stdout.strip()
    receipt = {"deployed_utc": stamp(), "host": os.uname().nodename, "benchmark": BENCHMARK, "port": PORT, "port_claim": PORT_CLAIM,
               "tunnel_url": url, "service_pid": service.pid, "tunnel_pid": tunnel.pid,
               "local_health": 200, "local_unauthenticated_health": 401, "tunnel_health": 200, "tunnel_unauthenticated_health": unauth,
               "tunnel_version_status": probe(url + "/version", bearer), "service_dir": str(SERVICE_DIR), "service_files_sha256": service_hashes,
               "veribench_checkout": veribench_head, "pack_dir": str(PACK), "pack_task_count": n_pack,
               "control_pack": True, "grade_mode": "collect_only (VB_COLLECT_ONLY=1)", "sandbox_lean": "none (VB_NO_COMPILER=1)",
               "agent_timeout_s": AGENT_TIMEOUT_S, "agent_client_timeout_s": AGENT_CLIENT_TIMEOUT_S, "per_task_limit_local": limits,
               "per_task_limit_tunnel": tunnel_limits, "valkyrie_config": str(target), "inference_calls": 0}
    write_json(receipt_path, receipt)
    public = {k: v for k, v in receipt.items() if k not in ("tunnel_url",)}
    public["tunnel_url"] = "recorded in $WORK/private/deployment.json (not published)"
    write_json(PUBLIC_RECEIPT if NAME == "teachers" else PUBLIC_RECEIPT.with_name(f"deployment_e08_{NAME}.json"), public)
    print(json.dumps({k: public[k] for k in ("benchmark", "port", "pack_task_count", "local_health", "local_unauthenticated_health", "tunnel_health",
                                             "tunnel_unauthenticated_health", "per_task_limit_tunnel")}))
    return 0


def cmd_status(a) -> int:
    r = read_json(PRIVATE / ("deployment.json" if NAME == "teachers" else f"deployment_{NAME}.json"), {})
    if not r:
        print(json.dumps({"deployed": False}))
        return 1
    bearer = (PRIVATE / ("service_bearer" if NAME == "teachers" else f"service_bearer_{NAME}")).read_text().strip()
    out = {"checked_utc": stamp(), "service_alive": alive(r.get("service_pid")), "tunnel_alive": alive(r.get("tunnel_pid")),
           "local_health_now": probe(f"http://127.0.0.1:{PORT}/health", bearer), "tunnel_health_now": probe(r["tunnel_url"] + "/health", bearer),
           "port_listening": listening(PORT)}
    print(json.dumps(out))
    return 0 if out["service_alive"] and out["tunnel_alive"] and out["tunnel_health_now"] == 200 else 1


def cmd_teardown(a) -> int:
    r = read_json(PRIVATE / ("deployment.json" if NAME == "teachers" else f"deployment_{NAME}.json"), {})
    for key in ("tunnel_pid", "service_pid"):
        if alive(r.get(key)):
            try:
                os.killpg(int(r[key]), signal.SIGTERM)
            except ProcessLookupError:
                pass
    time.sleep(3)
    still = [k for k in ("tunnel_pid", "service_pid") if alive(r.get(k))]
    for k in still:
        os.killpg(int(r[k]), signal.SIGKILL)
    time.sleep(1)
    still = [k for k in ("tunnel_pid", "service_pid") if alive(r.get(k))]
    r.update(torn_down_utc=stamp(), still_alive=still, port_free=not listening(PORT))
    write_json(PRIVATE / ("deployment.json" if NAME == "teachers" else f"deployment_{NAME}.json"), r)
    pub_path = PUBLIC_RECEIPT if NAME == "teachers" else PUBLIC_RECEIPT.with_name(f"deployment_e08_{NAME}.json")
    pub = read_json(pub_path, {})
    pub.update(torn_down_utc=r["torn_down_utc"], still_alive=still, port_free=r["port_free"])
    write_json(pub_path, pub)
    print(json.dumps({"torn_down_utc": r["torn_down_utc"], "still_alive": still, "port_free": r["port_free"]}))
    return 0 if not still and r["port_free"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["deploy", "status", "teardown"])
    ap.add_argument("--name", default=None, help="judge instance name (default: the teacher service)")
    ap.add_argument("--benchmark", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--pack", type=Path, default=None)
    ap.add_argument("--expected-tasks", type=int, default=None)
    a = ap.parse_args()
    global BENCHMARK, PORT, PACK, NAME, EXPECTED_TASKS
    if a.name:
        NAME = a.name
        BENCHMARK, PORT, PACK = a.benchmark or BENCHMARK, a.port or PORT, a.pack or PACK
        EXPECTED_TASKS = a.expected_tasks if a.expected_tasks is not None else 0
        if PORT == 9740 or BENCHMARK == "rl4cv-e08-vbv1-train":
            raise SystemExit("a judge instance needs its own --benchmark and --port in the claimed block 9741-9759")
    return {"deploy": cmd_deploy, "status": cmd_status, "teardown": cmd_teardown}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
