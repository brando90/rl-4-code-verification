"""Retry the control's zero-output import failure once with identical cells and sampling settings."""
from contextlib import ExitStack
import concurrent.futures
import fcntl
import os
from pathlib import Path
import shutil
import time

import run_jobs as jobs
from extend_4b_wait import matching, read


def main():
    run = jobs.RUN
    status = run / "primary_recovery/status.json"
    label = "1p7_control"
    jobs.write(status, {"status": "STARTING", "label": label, "started_unix": time.time(),
        "reason": "system SciPy incompatible with generation NumPy; zero generated cells"})
    gates = ExitStack()
    try:
        prior = read(run / "execution" / label / "generation.json")
        assert prior["status"] == "FAILED" and prior["exit_code"] == 1
        raw = run / "validation" / label / "raw.jsonl"
        assert not raw.exists() or raw.stat().st_size == 0
        for name in ("allocation.json", "released.json"):
            shutil.copy2(run / "execution" / label / name, run / "primary_recovery" / ("original_" + name))
        for path in ("/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.lock",
                     "/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/lock"):
            stream = gates.enter_context(open(path, "rb"))
            fcntl.flock(stream, fcntl.LOCK_EX)
        normal = jobs.run_stage
        def retry(label, stage, command, env, timeout):
            if stage in ("smoke", "training"):
                receipt = read(run / "execution" / label / f"{stage}.json")
                assert receipt["status"] == "DONE"
                return receipt
            if stage == "generation":
                assert command == prior["command"], "identical generation command required"
                return normal(label, "generation_retry", command, env, timeout)
            return normal(label, stage, command, env, timeout)
        jobs.run_stage = retry
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(jobs.gpu_pipeline, label, "1")
            while not future.done():
                receipt = read(run / "execution" / label / "generation_retry.json")
                devices, busy = jobs.device_inventory()
                if receipt.get("pid") and devices["1"]["uuid"] in busy:
                    gates.close()
                    jobs.write(status, {"status": "GENERATION", "label": label, "receipt": receipt,
                        "sampling_and_prompts_unchanged": True, "original_output_cells": 0})
                    break
                time.sleep(0.25)
            gates.close()
            future.result()
        jobs.run_stage = normal
        jobs.write(status, {"status": "WAITING_FOR_ORIGINAL_SCORING", "generated_cells": 1080})
        parent = read(run / "fused_handoff/status.json")["original_coordinator"]
        deadline = time.time() + 16 * 3600
        while matching(parent):
            if time.time() > deadline:
                raise TimeoutError("original supervisor did not exit")
            time.sleep(10)
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(jobs.REPO / "src")}
        normal(label, "materialize", [jobs.PYTHON, "-m", "rl4cv.veribench.jobs", "--gen", str(raw),
            "--out-root", str(run / "validation" / label / "jobs"), "--name", label], env, 300)
        jobs.write(status, {"status": "SCORING", "generated_cells": 1080})
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for future in concurrent.futures.as_completed([pool.submit(jobs.score_sample, label, i) for i in range(8)]):
                future.result()
        jobs.write(status, {"status": "DONE", "label": label, "generated_cells": 1080,
            "scoring_jobs_complete": 8, "identical_infrastructure_retry": True, "ended_unix": time.time()})
    except BaseException as exc:
        jobs.write(status, {"status": "FAILED", "label": label, "error": repr(exc), "ended_unix": time.time()})
        raise
    finally:
        gates.close()


if __name__ == "__main__":
    main()
