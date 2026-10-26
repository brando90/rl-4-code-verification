"""Run three independently isolated training/validation pipelines with persistent logs and terminal receipts."""
from __future__ import annotations

import argparse
import concurrent.futures
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path(os.environ["TINY_RUN_ROOT"])
PYTHON = "/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python"
GEN_SITE = "/lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/lib/python3.12/site-packages"
SCORER = REPO / "external/veribench_scorer"


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def run_stage(label, stage, command, env, timeout):
    out = RUN / "execution" / label
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / f"{stage}.json"
    assert not receipt_path.exists(), f"existing attempt {receipt_path}; preserve and reconcile"
    started = time.time()
    record = {"label": label, "stage": stage, "command": command, "started_unix": started,
        "host": socket.gethostname(), "cuda_visible_devices": env["CUDA_VISIBLE_DEVICES"], "status": "RUNNING"}
    with (out / f"{stage}.log").open("x") as stream:
        process = subprocess.Popen(command, env=env, cwd=REPO, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        record["pid"] = process.pid
        try:
            record["start_ticks"] = Path(f"/proc/{process.pid}/stat").read_text().rsplit(") ", 1)[1].split()[19]
            record["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        except OSError:
            pass
        write(receipt_path, record)
        print(json.dumps({"label": label, "stage": stage, "status": "RUNNING", "pid": process.pid}), flush=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            record["stop_reason"] = "declared stage time boundary"
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    record.update(ended_unix=time.time(), exit_code=code, status="DONE" if code == 0 else "FAILED")
    write(receipt_path, record)
    print(json.dumps({"label": label, "stage": stage, "status": record["status"], "exit_code": code}), flush=True)
    if code:
        raise RuntimeError(f"{label} {stage} exited {code}; see {out / (stage + '.log')}")
    return record


def device_inventory():
    output = subprocess.check_output(["nvidia-smi", "--query-gpu=index,uuid,memory.total,memory.used",
        "--format=csv,noheader,nounits"], text=True)
    devices = {}
    for line in output.splitlines():
        index, uuid, total, used = [x.strip() for x in line.split(",")]
        devices[index] = {"uuid": uuid, "total_mib": int(total), "used_mib": int(used)}
    busy = set(subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid",
        "--format=csv,noheader"], text=True).split())
    return devices, busy


def gpu_pipeline(label, gpu):
    size = "4B" if label == "4b_mixed" else "1.7B"
    condition = "control" if label.endswith("control") else "mixed"
    root = RUN / ("four" if size == "4B" else "onep7")
    assert json.loads((root / "prepare_receipt.json").read_text())["status"] == "PASS"
    lock = (RUN / f"device_{gpu}.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    devices, busy = device_inventory()
    assert devices[gpu]["uuid"] not in busy and devices[gpu]["used_mib"] < 64
    assert devices[gpu]["total_mib"] >= 79000
    write(RUN / "execution" / label / "allocation.json", {"gpu": gpu, **devices[gpu],
        "allocated_unix": time.time(), "pid": os.getpid(), "owner": "eth127", "foreign_processes_preserved": True})
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES=gpu, TINY_TRAIN_ROOT=str(root), TINY_RUN_ROOT=str(RUN),
        PYTHONPATH=str(REPO / "src"), HF_HUB_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
        OMP_NUM_THREADS="4", MKL_NUM_THREADS="4")
    for key in list(env):
        if any(word in key for word in ("API_KEY", "AUTH_TOKEN", "ACCESS_TOKEN", "BEARER_TOKEN")):
            env.pop(key)
    try:
        run_stage(label, "smoke", [PYTHON, str(HERE / "experiment.py"), "smoke", "--condition", condition], env, 900)
        run_stage(label, "training", [PYTHON, str(HERE / "experiment.py"), "train", "--condition", condition], env, 8 * 3600)
        preflight = json.loads((RUN / "validation_preflight.json").read_text())
        assert preflight["status"] == "PASS" and preflight["tasks"] == 135
        model = root / "runs" / condition / "hf"
        env["PYTHONPATH"] = str(REPO / "src") + ":" + GEN_SITE
        env["VERIBENCH_ROOT"] = str(REPO / "external/veribench")
        env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        env["FLASHINFER_WORKSPACE_BASE"] = str(RUN / "flashinfer" / label)
        ids = HERE.parent / "expt_v1/results/split/vbv1_validation_task_ids.txt"
        output = RUN / "validation" / label / "raw.jsonl"
        command = ["/usr/bin/python3", "-m", "rl4cv.veribench.generate", "--pack", str(RUN / "validation_pack"),
            "--task-ids", str(ids), "--model", str(model), "--label", label,
            "--samples", "8", "--thinking", "on", "--seed", "91", "--stop-token", "<|im_end|>",
            "--max-tokens", "12288", "--temperature", "0.6", "--top-p", "0.95", "--top-k", "20",
            "--batch", "128", "--tensor-parallel-size", "1", "--gpu-memory-utilization", "0.85", "--out", str(output)]
        run_stage(label, "generation", command, env, 8 * 3600)
        raw = [json.loads(line) for line in output.read_text().splitlines()]
        expected = {(tid, k) for tid in ids.read_text().splitlines() for k in range(8)}
        assert len(raw) == len({(r["task_id"], r["sample_idx"]) for r in raw}) == len(expected) == 1080
        assert {(r["task_id"], r["sample_idx"]) for r in raw} == expected
        for row in raw:
            assert all(row[k] == v for k, v in preflight["prompts"][row["task_id"]].items())
        write(RUN / "validation" / label / "generation_verified.json", {"cells": 1080,
            "raw_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "status": "PASS"})
        return label
    finally:
        write(RUN / "execution" / label / "released.json", {"gpu": gpu, "released_unix": time.time()})
        lock.close()


def score_sample(label, sample):
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES="", PYTHONPATH=str(REPO / "src"),
        PATH=str(RUN / "bin") + ":" + env["PATH"], TOKENIZERS_PARALLELISM="false")
    job = RUN / "validation" / label / "jobs" / f"{label}_s{sample}"
    out = RUN / "validation" / label / "scores" / f"{label}_s{sample}"
    command = [PYTHON, str(SCORER / "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"),
        "--job-dir", str(job), "--pack", str(RUN / "validation_pack"), "--name", f"{label}_s{sample}",
        "--gold-dir", str(SCORER / "veribench_dataset/lean_src/veribench"),
        "--lake-dir", str(RUN / "grading"), "--skip-tc", "--out-dir", str(out)]
    return run_stage(label, f"score_{sample}", command, env, 8 * 3600)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpus", default="1,2,6")
    args = parser.parse_args()
    gpus = args.gpus.split(",")
    assert len(gpus) == len(set(gpus)) == 3
    labels = ("1p7_control", "1p7_mixed", "4b_mixed")
    # Read-only descriptors can take the existing Linux flock admission locks.
    # Keep the waiting 14B allocator and other owners serialized through startup
    # without modifying their registries or interpreting planned devices as leases.
    gates = ExitStack()
    for p in (Path("/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.lock"),
              Path("/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/lock")):
        stream = gates.enter_context(p.open("rb"))
        deadline = time.monotonic() + 180
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    gates.close()
                    raise RuntimeError(f"another allocator still owns admission lock {p}")
                time.sleep(1)
    sys.path.insert(0, str(HERE.parent / "expt_v1/scripts"))
    import gpu_lease_e08
    live = gpu_lease_e08.live_leases()
    assert not any(set(map(str, r["gpus"])) & set(gpus) for r in live.values()), "selected device has a live E08 lease"
    registry = json.loads(Path("/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.json").read_text())
    active = [r for r in registry["leases"] if r.get("status") != "RELEASED"
        and r.get("host", "").split(".")[0] == "skampere1" and str(r.get("index")) in gpus]
    assert not active, "selected device has a live E13 lease"
    assert (RUN / "protocol_lock.json").is_file(), "freeze source/protocol first"
    lock = json.loads((RUN / "protocol_lock.json").read_text())
    for relative, expected in lock["source_sha256"].items():
        assert hashlib.sha256((REPO / relative).read_bytes()).hexdigest() == expected, relative
    assert json.loads((RUN / "validation_preflight.json").read_text())["status"] == "PASS"
    assert json.loads((RUN / "scoring_preflight.json").read_text())["status"] == "PASS"
    assert json.loads((RUN / "optimizer_preflight.json").read_text())["status"] == "PASS"
    write(RUN / "launch.json", {"started_unix": time.time(), "gpus": dict(zip(labels, gpus)),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "status": "RUNNING"})
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as gpu_pool, concurrent.futures.ThreadPoolExecutor(max_workers=8) as score_pool:
        pending = {gpu_pool.submit(gpu_pipeline, label, gpu): label for label, gpu in zip(labels, gpus, strict=True)}
        # Release admission locks after production processes hold real device contexts.
        # This keeps startup atomic against the existing shared allocators.
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline and not any(f.done() for f in pending):
            started = []
            for label in labels:
                path = RUN / "execution" / label / "training.json"
                started.append(path.exists() and json.loads(path.read_text()).get("status") == "RUNNING")
            devices, busy = device_inventory()
            if all(started) and all(devices[g]["uuid"] in busy for g in gpus):
                break
            time.sleep(2)
        gates.close()
        scores = []
        for future in concurrent.futures.as_completed(pending):
            label = pending[future]
            try:
                future.result()
                env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(REPO / "src")}
                run_stage(label, "materialize", [PYTHON, "-m", "rl4cv.veribench.jobs", "--gen",
                    str(RUN / "validation" / label / "raw.jsonl"), "--out-root",
                    str(RUN / "validation" / label / "jobs"), "--name", label], env, 300)
                scores.extend(score_pool.submit(score_sample, label, k) for k in range(8))
            except Exception as exc:
                failures.append({"label": label, "error": str(exc)})
                write(RUN / "failures.json", failures)
        for future in concurrent.futures.as_completed(scores):
            try:
                future.result()
            except Exception as exc:
                failures.append({"error": str(exc)})
                write(RUN / "failures.json", failures)
    write(RUN / "terminal.json", {"status": "FAILED" if failures else "SCORED", "failures": failures,
        "ended_unix": time.time(), "analysis": "pending coordinator reconciliation"})
    if failures:
        sys.exit(1)
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(REPO / "src")}
    run_stage("aggregate", "analysis", [PYTHON, str(HERE / "analyze.py")], env, 900)
    write(RUN / "terminal.json", {"status": "COMPLETE", "failures": [],
        "ended_unix": time.time(), "analysis": str(RUN / "analysis/summary.json")})


if __name__ == "__main__":
    main()
