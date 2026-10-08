#!/usr/bin/env python3
# TLDR: Deploy a new Valkyrie judge benchmark service for experiment 01 (uvicorn + cloudflared),
# reusing experiment 103's deploy_service.py UNMODIFIED (imported from this repo's own pinned
# external/veribench checkout, so every write lands under E = that checkout's own 103 folder,
# never veribench_vb103). Only adds new INSTANCES entries in memory, in a claimed port block
# (9700-9719, see /lfs/skampere1/0/brando9/valkyrie_port_claims/rl4cv-e01_9700-9719.txt); never
# touches or restarts any existing (8923-8998, etc.) service.
# Usage: python3 deploy_rl4cv_e01_judge_service.py --instance controls
#        python3 deploy_rl4cv_e01_judge_service.py --instance <label> --status
#        python3 deploy_rl4cv_e01_judge_service.py --instance <label> --part r23   # repeats 2-3 pack
#        python3 deploy_rl4cv_e01_judge_service.py --instance <label> --part r23 --stop
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
E103 = (REPO / "external/veribench/experiments"
        "/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge")
sys.path.insert(0, str(E103 / "scripts"))
import deploy_service  # noqa: E402  reused unmodified; E/PRIVATE resolve inside THIS checkout

PORT_BASE = 9700
PORT_MAX = 9719
CONTROLS_KEY = "rl4cv-e01-controls"


def _port_for(key: str) -> int:
    if key == CONTROLS_KEY:
        return PORT_BASE
    # one port per model label, stable order via a small local registry file
    registry = E103 / "private" / "rl4cv_e01_port_registry.txt"
    registry.parent.mkdir(parents=True, exist_ok=True)
    lines = registry.read_text().splitlines() if registry.exists() else []
    if key in lines:
        return PORT_BASE + 1 + lines.index(key)
    lines.append(key)
    assert PORT_BASE + len(lines) <= PORT_MAX + 1, "out of claimed ports (9700-9719)"
    registry.write_text("\n".join(lines) + "\n")
    return PORT_BASE + len(lines)


def register(instance_key: str, benchmark: str, pack: Path) -> int:
    port = _port_for(instance_key)
    ss = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True).stdout
    if f":{port} " in ss:
        raise SystemExit(f"port {port} is already listening; refusing to bind (re-check "
                          f"valkyrie_port_claims and ss -tlnp)")
    deploy_service.INSTANCES[instance_key] = {
        "benchmark": benchmark, "pack": pack, "port": port, "control_pack": True,
        "service_dir": deploy_service.SERVICE_DIR, "family": "vbv1",
    }
    sys.argv = ["deploy_service.py", "--instance", instance_key]
    return deploy_service.main()


def status(instance_key: str) -> int:
    sys.argv = ["deploy_service.py", "--instance", instance_key, "--status"]
    return deploy_service.main()


def stop(instance_key: str) -> int:
    """Stop ONLY the service and tunnel this wrapper deployed for `instance_key` (PIDs from its own
    deployment receipt), then confirm the port is free. Never touches any other instance."""
    receipt = deploy_service.PRIVATE / f"deployment_{instance_key}.json"
    if not receipt.exists():
        print(json.dumps({"instance": instance_key, "stopped": False, "reason": "no deployment receipt"}))
        return 1
    state = json.loads(receipt.read_text())
    killed = {}
    for role in ("service_pid", "tunnel_pid"):
        pid = state.get(role)
        if deploy_service.alive(pid):
            os.kill(int(pid), signal.SIGTERM)
            killed[role] = pid
    for _ in range(30):
        if not any(deploy_service.alive(state.get(r)) for r in ("service_pid", "tunnel_pid")):
            break
        time.sleep(1)
    for role in ("service_pid", "tunnel_pid"):
        pid = state.get(role)
        if deploy_service.alive(pid):
            os.kill(int(pid), signal.SIGKILL)
    ss = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True).stdout
    port_free = f":{state['port']} " not in ss
    print(json.dumps({"instance": instance_key, "port": state["port"], "killed": killed,
                      "port_free_after": port_free}))
    return 0 if port_free else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True, help="'controls' or a model label")
    ap.add_argument("--part", choices=["gate", "r23"], default="gate",
                    help="r23 serves the repeats-2-3 pack on its own instance/benchmark/port")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--stop", action="store_true", help="stop this wrapper's own service+tunnel for the instance")
    args = ap.parse_args()
    key = CONTROLS_KEY if args.instance == "controls" else f"rl4cv-e01-{args.instance}"
    if args.part == "r23":
        assert args.instance != "controls", "controls have no repeats (reference design: controls are __r1 only)"
        key = f"{key}-r23"
    if args.stop:
        return stop(key)
    if args.status:
        # register a throwaway entry first only if needed for --status to resolve the instance;
        # normal status calls happen after register() already added it to INSTANCES this run.
        if key not in deploy_service.INSTANCES:
            print("not deployed in this process; re-run without --status right after deploying, "
                  "or use deploy_service.py --instance <key> --status directly")
            return 1
        return status(key)
    judge_priv = E103 / "private" / "judge" / "rl4cv_e01"
    if key == CONTROLS_KEY:
        pack = judge_priv / "packs" / "judge_rl4cv_e01_controls"
        benchmark = "veribench-rl4cv-e01-controls"
    elif args.part == "r23":
        label = args.instance
        pack = judge_priv / "packs" / f"judge_rl4cv_e01_{label}_r23"
        benchmark = f"veribench-rl4cv-e01-{label}-r23".replace(".", "-")
    else:
        label = args.instance
        pack = judge_priv / "packs" / f"judge_rl4cv_e01_{label}"
        benchmark = f"veribench-rl4cv-e01-{label}".replace(".", "-")
    if not pack.is_dir():
        raise SystemExit(f"pack not built yet: {pack} (run judge_rl4cv_e01.py build-controls/build-model first)")
    return register(key, benchmark, pack)


if __name__ == "__main__":
    raise SystemExit(main())
