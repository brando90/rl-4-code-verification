"""Resume V20 validation from the finished checkpoint, without another training pass."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

RUN = Path("/lfs/skampere1/0/eth127/rl4cv_tiny_training")
REPO = RUN / "repo"
ROOT = RUN / "corpus_training_v20"
MODEL = ROOT / "base" / "run" / "hf"
PACK = RUN / "validation_pack"
IDS = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_validation_task_ids.txt"
PREFLIGHT = RUN / "validation_preflight.json"
GEN_SITE = Path("/lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/lib/python3.12/site-packages")
PYTHON = "/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python"
SCORER = REPO / "external/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
GOLD = REPO / "external/veribench_scorer/veribench_dataset/lean_src/veribench"
HOME = Path("/lfs/skampere1/0/brando9/rl4cv_v20_validation_recovery")
LABEL = "v20_base"
RAW = HOME / "validation" / LABEL / "raw.jsonl"
CANDIDATES = ("1", "0", "5")


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def inventory():
    rows = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,uuid,memory.total,memory.used", "--format=csv,noheader,nounits"],
        text=True,
    )
    devices = {}
    for line in rows.splitlines():
        index, uuid, total, used = [part.strip() for part in line.split(",")]
        devices[index] = {"uuid": uuid, "total_mib": int(total), "used_mib": int(used)}
    busy = set(subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid", "--format=csv,noheader"], text=True).split())
    return devices, busy


def empty_gpu():
    devices, busy = inventory()
    for gpu in CANDIDATES:
        info = devices.get(gpu)
        if info and info["uuid"] not in busy and info["used_mib"] < 64 and info["total_mib"] >= 79000:
            return gpu, info
    return None, devices


def env_for(gpu: str) -> dict:
    env = os.environ.copy()
    env.update(
        CUDA_VISIBLE_DEVICES=gpu,
        PYTHONPATH=f"{REPO / 'src'}:{GEN_SITE}",
        VERIBENCH_ROOT=str(REPO / "external/veribench"),
        VLLM_WORKER_MULTIPROC_METHOD="spawn",
        FLASHINFER_WORKSPACE_BASE=str(HOME / "flashinfer"),
        HF_HUB_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false",
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
    )
    for key in list(env):
        if any(word in key for word in ("API_KEY", "AUTH_TOKEN", "ACCESS_TOKEN", "BEARER_TOKEN")):
            env.pop(key)
    return env


def verify() -> dict:
    rows = [json.loads(line) for line in RAW.read_text().splitlines() if line.strip()]
    ids = IDS.read_text().splitlines()
    expected = {(task, sample) for task in ids for sample in range(8)}
    found = {(row["task_id"], row["sample_idx"]) for row in rows}
    preflight = json.loads(PREFLIGHT.read_text())
    assert len(rows) == len(found) == len(expected) == 1080
    assert found == expected
    for row in rows:
        assert all(row[key] == value for key, value in preflight["prompts"][row["task_id"]].items())
    return {"status": "PASS", "cells": 1080, "test_split_opened": False, "observed_unix": time.time()}


def generate(gpu: str) -> int:
    command = [
        "/usr/bin/python3", "-m", "rl4cv.veribench.generate",
        "--pack", str(PACK), "--task-ids", str(IDS), "--model", str(MODEL),
        "--label", LABEL, "--samples", "8", "--thinking", "on", "--seed", "91",
        "--stop-token", "<|im_end|>", "--max-tokens", "12288", "--temperature", "0.6",
        "--top-p", "0.95", "--top-k", "20", "--batch", "128", "--tensor-parallel-size", "1",
        "--gpu-memory-utilization", "0.85", "--out", str(RAW),
    ]
    log = HOME / "generation.log"
    with log.open("a") as stream:
        process = subprocess.Popen(command, env=env_for(gpu), cwd=REPO, stdin=subprocess.DEVNULL,
                                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        write(HOME / "generation.json", {
            "status": "RUNNING", "pid": process.pid, "gpu": gpu, "command": command,
            "started_unix": time.time(), "cuda_visible_devices": gpu, "training_rerun": False,
        })
        try:
            return process.wait(timeout=8 * 3600)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, 15)
            process.wait(timeout=30)
            return 124


def main() -> None:
    assert MODEL.joinpath("model.safetensors.index.json").is_file()
    assert json.loads((ROOT / "base/run/result.json").read_text())["status"] == "COMPLETE"
    HOME.mkdir(parents=True, exist_ok=True)
    failures = 0
    while True:
        gpu, info = empty_gpu()
        if gpu is None:
            write(HOME / "status.json", {"state": "WAITING_FOR_EMPTY_A100", "failures": failures, "devices": info, "observed_unix": time.time()})
            time.sleep(30)
            continue
        again, _ = empty_gpu()
        if again != gpu:
            continue
        write(HOME / "status.json", {"state": "GENERATING", "gpu": gpu, "device": info, "failures": failures, "observed_unix": time.time()})
        code = generate(gpu)
        if code != 0:
            failures += 1
            write(HOME / "status.json", {"state": "GENERATION_FAILED_RETRY", "exit_code": code, "gpu": gpu, "failures": failures, "observed_unix": time.time()})
            if failures >= 3:
                raise SystemExit(code)
            time.sleep(20)
            continue
        receipt = verify()
        write(HOME / "validation" / LABEL / "generation_verified.json", receipt)
        write(HOME / "status.json", {"state": "GENERATION_VERIFIED", **receipt})
        return


if __name__ == "__main__":
    main()
