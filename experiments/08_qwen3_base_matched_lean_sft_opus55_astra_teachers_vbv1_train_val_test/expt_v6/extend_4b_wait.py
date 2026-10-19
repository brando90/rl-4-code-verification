"""Apply the prospective 12-hour 4B allowance without restarting any healthy training process."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import time

RUN = Path("/lfs/skampere1/0/eth127/rl4cv_tiny_training")
STATE = RUN / "four_wallclock_extension.json"


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def write(value):
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(STATE)


def identity(pid):
    root = Path(f"/proc/{pid}")
    if root.stat().st_uid != os.getuid():
        raise RuntimeError("foreign process identity")
    fields = (root / "stat").read_text().rsplit(") ", 1)[1].split()
    return {"pid": pid, "start_ticks": fields[19], "state": fields[0],
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def matching(expected):
    try:
        current = identity(expected["pid"])
    except OSError:
        return None
    if any(current[k] != expected[k] for k in ("pid", "start_ticks", "boot_id")):
        return None
    return current


def primary_done():
    return all(read(RUN / "execution" / label / f"score_{k}.json").get("status") == "DONE"
        for label in ("1p7_control", "1p7_mixed") for k in range(8))


def main():
    stage = read(RUN / "execution/4b_mixed/training.json")
    assert stage.get("status") == "RUNNING"
    child = identity(stage["pid"])
    assert child["start_ticks"] == stage["start_ticks"] and child["boot_id"] == stage["boot_id"]
    fields = Path(f"/proc/{child['pid']}/stat").read_text().rsplit(") ", 1)[1].split()
    parent = identity(int(fields[1]))
    assert b"run_jobs.py" in Path(f"/proc/{parent['pid']}/cmdline").read_bytes()
    deadline = stage["started_unix"] + 12 * 3600
    record = {"status": "WAITING_FOR_PRIMARY_SCORING", "training": child, "coordinator": parent,
        "original_hours": 8, "amended_hours": 12, "deadline_unix": deadline,
        "training_process_restarted": False, "optimizer_or_data_changed": False,
        "created_unix": time.time(), "coordinator_paused": False}
    write(record)
    paused = False
    try:
        while time.time() < deadline:
            current = matching(child)
            if current is None or current["state"] == "Z":
                record.update(status="TRAINING_PROCESS_ENDED", ended_unix=time.time())
                return
            if read(RUN / "execution/4b_mixed/training.json").get("status") != "RUNNING":
                record.update(status="ORIGINAL_COORDINATOR_FINISHED_STAGE", ended_unix=time.time())
                return
            if not matching(parent):
                raise RuntimeError("original coordinator disappeared; preserve the healthy child and reconcile")
            if not paused and primary_done():
                try:
                    path = Path(__file__).with_name("analyze_primary.py")
                    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "TINY_RUN_ROOT": str(RUN)}
                    with (RUN / "primary_analysis.log").open("w") as log:
                        analysis = subprocess.run(["/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python", str(path)],
                            env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
                    record["primary_analysis_exit_code"] = analysis.returncode
                except Exception as exc:
                    record["primary_analysis_error"] = str(exc)
                # No primary generation/scoring remains. Its subprocess outputs go to
                # regular files, so pausing only this waiting coordinator cannot block
                # the separately session-owned 4B training process or its logging.
                os.kill(parent["pid"], signal.SIGSTOP)
                paused = True
                record.update(status="EXTENDED_TRAINING_WAIT", coordinator_paused=True,
                    paused_unix=time.time(), primary_scoring_complete=True)
            record["checked_unix"] = time.time()
            write(record)
            time.sleep(30)
        # The amended limit is real and bounded; signal only this exact owned process group.
        current = matching(child)
        if current and current["state"] != "Z":
            assert os.getpgid(child["pid"]) == child["pid"]
            os.killpg(child["pid"], signal.SIGTERM)
            time.sleep(10)
            current = matching(child)
            if current and current["state"] != "Z":
                os.killpg(child["pid"], signal.SIGKILL)
        record.update(status="AMENDED_12_HOUR_BOUNDARY", ended_unix=time.time())
    finally:
        if paused and matching(parent):
            os.kill(parent["pid"], signal.SIGCONT)
            record.update(coordinator_paused=False, resumed_unix=time.time())
        write(record)


if __name__ == "__main__":
    main()
