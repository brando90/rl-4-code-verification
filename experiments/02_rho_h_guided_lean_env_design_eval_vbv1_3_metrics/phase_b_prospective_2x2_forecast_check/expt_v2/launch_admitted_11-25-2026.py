"""11-25-2026: launch an admitted, hash-pinned Lean training command in bounded logged tmux, or print blockers and exit."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import socket
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--gpu-uuid")
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    if receipt["status"] != "ADMITTED":
        print(f"NOT LAUNCHED: {receipt['experiment']} ({receipt['date']})")
        for reason in receipt["blocking_reasons"]:
            print(f"- {reason}")
        return 2

    # Admission is a scientific artifact, not a CLI flag. No mock command or
    # generic math trainer is substituted when the real Lean command is absent.
    required = (
        "protocol", "training_entrypoint", "training_config", "frozen_forecast",
        "accepted_reference_receipt", "training_corpus_screen_receipt",
        "rollout_adapter_receipt", "precision_baseline_receipt", "published_claim_receipt",
    )
    verified = {}
    for name in required:
        artifact = receipt.get(name)
        if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("sha256"):
            raise ValueError(f"missing hash-pinned admission artifact: {name}")
        path = Path(artifact["path"]).resolve(strict=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError(f"changed admission artifact: {name}")
        verified[name] = path
    if receipt.get("model_route") != "self_hosted" or receipt.get("payer") != "included":
        raise ValueError("this launch permits only included self-hosted computation")
    if receipt.get("protected_corpus") != "all_VeriBench":
        raise ValueError("these older protocols protect all VeriBench tasks")
    if receipt.get("selected_host") != socket.gethostname().split(".")[0]:
        raise ValueError("host differs from the admitted inventory/placement")
    if not args.gpu_uuid or args.gpu_uuid not in receipt.get("selected_gpu_uuids", []):
        raise ValueError("pass one explicitly admitted --gpu-uuid; inherited visibility is ignored")
    gpu = subprocess.check_output([
        "nvidia-smi", f"--id={args.gpu_uuid}",
        "--query-gpu=memory.free,memory.used,utilization.gpu", "--format=csv,noheader,nounits",
    ], text=True)
    free, used, utilization = [int(x.strip()) for x in gpu.strip().split(",")]
    processes = subprocess.check_output([
        "nvidia-smi", f"--id={args.gpu_uuid}", "--query-compute-apps=pid", "--format=csv,noheader",
    ], text=True).strip()
    if processes or used > 1024 or utilization > 10 or free < receipt["minimum_free_memory_mib"]:
        print("NOT LAUNCHED: chosen GPU is occupied or lacks admitted memory; no wait/retry.")
        return 75
    hours = receipt.get("time_limit_hours")
    if not isinstance(hours, (int, float)) or not 0 < hours <= 24:
        raise ValueError("admit a positive bounded duration of at most 24 hours")
    log = Path(receipt["log_path"]).resolve()
    work = Path(receipt["work_root"]).resolve(strict=True)
    log.relative_to(work)
    entrypoint = verified["training_entrypoint"]
    entrypoint.relative_to(work)
    if log.exists():
        raise ValueError("log already exists; select a new dated run receipt, never overwrite")
    log.parent.mkdir(parents=True, exist_ok=True)
    session = receipt["tmux_session"]
    # The reviewed entrypoint owns its exact complete manifest and training
    # configuration. timeout bounds this one run; no GPU waiter or restart loop.
    command = shlex.join([
        "env", f"CUDA_VISIBLE_DEVICES={args.gpu_uuid}", "timeout", "--signal=TERM", "--kill-after=60s",
        f"{hours}h", "bash", str(entrypoint),
    ])
    command += f" >> {shlex.quote(str(log))} 2>&1; rc=$?; printf '\\nEXIT_CODE=%s\\n' \"$rc\" >> {shlex.quote(str(log))}; exit \"$rc\""
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session, "-c", str(work),
        "env", "-u", "BASH_ENV", "bash", "--noprofile", "--norc", "-c", command,
    ], check=True)
    print(f"STARTED tmux={session} log={log}; verify the first real rollout/scoring receipt next")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"NOT LAUNCHED: {error}", file=sys.stderr)
        raise SystemExit(2)
