"""Hand off the owned 4B job at a complete checkpoint and finish its original validation manifest."""
from __future__ import annotations

import concurrent.futures
from contextlib import ExitStack
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

import run_jobs as jobs
from extend_4b_wait import identity, matching, read

RUN, HERE = jobs.RUN, jobs.HERE
HANDOFF = RUN / "fused_handoff"
STATE = HANDOFF / "status.json"


def record(status, **values):
    current = read(STATE)
    jobs.write(STATE, {**current, **values, "status": status, "observed_unix": time.time()})


def wait_for_checkpoint(child, deadline):
    root = RUN / "four/runs/mixed"
    target = 100
    while time.time() < deadline:
        process = matching(child)
        assert process and process["state"] != "Z", "original trainer ended before handoff"
        state = root / "training_state.pt"
        rows = list(csv.DictReader((root / "steps.csv").open()))
        step = int(rows[-1]["step"])
        if state.exists() and step >= target and not (root / "training_state.tmp.pt").exists():
            os.kill(child["pid"], signal.SIGSTOP)
            try:
                # Re-read after fencing the writer; never discard a completed CSV update.
                rows = list(csv.DictReader((root / "steps.csv").open()))
                step = int(rows[-1]["step"])
                if step != target or (root / "training_state.tmp.pt").exists():
                    if step != target:
                        target = (step // 100 + 1) * 100
                    record("WAITING_FOR_CHECKPOINT", target_step=target)
                    os.kill(child["pid"], signal.SIGCONT)
                    time.sleep(0.25)
                    continue
                saved = HANDOFF / f"training_state_step_{target}.pt"
                os.link(state, saved)  # Atomic checkpoint inode retained even after later saves.
                shutil.copy2(root / "steps.csv", HANDOFF / "steps_unfused.csv")
                shutil.copy2(root / "identity.json", HANDOFF / "identity_unfused.json")
                record("VERIFYING_CHECKPOINT", checkpoint=str(saved), target_step=target,
                    original_trainer_paused=True)
                env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "TINY_TRAIN_ROOT": str(RUN / "four")}
                command = [jobs.PYTHON, str(HERE / "resume_4b_fused.py"), "inspect",
                    "--checkpoint", str(saved), "--step", str(target)]
                with (HANDOFF / "checkpoint_inspection.json").open("x") as output, (HANDOFF / "checkpoint_inspection.log").open("x") as log:
                    result = subprocess.run(command, env=env, stdout=output, stderr=log, timeout=600)
                assert result.returncode == 0 and read(HANDOFF / "checkpoint_inspection.json").get("status") == "PASS"
                assert int(list(csv.DictReader((root / "steps.csv").open()))[-1]["step"]) == target
                return saved, target
            except BaseException:
                if matching(child):
                    os.kill(child["pid"], signal.SIGCONT)
                raise
        time.sleep(0.25)
    raise TimeoutError("checkpoint handoff exceeded original training deadline")


def retire_old_guard(parent):
    receipt = read(RUN / "four_wallclock_extension.json")
    guards = []
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            if item.stat().st_uid != os.getuid():
                continue
            command = (item / "cmdline").read_bytes().split(b"\0")
            if str(HERE / "extend_4b_wait.py").encode() in command:
                guards.append(identity(int(item.name)))
        except (OSError, ProcessLookupError):
            continue
    assert len(guards) <= 1
    for guard in guards:
        os.kill(guard["pid"], signal.SIGSTOP)
        os.kill(guard["pid"], signal.SIGTERM)
        os.kill(guard["pid"], signal.SIGCONT)
    current = matching(parent)
    if current and current["state"] in ("T", "t"):
        os.kill(parent["pid"], signal.SIGCONT)
    jobs.write(HANDOFF / "superseded_wallclock_guard.json", receipt)
    jobs.write(RUN / "four_wallclock_extension.json", {**receipt, "status": "SUPERSEDED_BY_FUSED_CONTINUATION",
        "coordinator_paused": False, "successor": str(STATE), "ended_unix": time.time()})


def main():
    HANDOFF.mkdir(parents=True, exist_ok=True)
    with (HANDOFF / "controller.lock").open("a") as own_lock:
        fcntl.flock(own_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not STATE.exists(), "existing handoff; preserve and reconcile"
        stage = read(RUN / "execution/4b_mixed/training.json")
        assert stage["status"] == "RUNNING" and matching(stage)
        child = identity(stage["pid"])
        fields = Path(f"/proc/{child['pid']}/stat").read_text().rsplit(") ", 1)[1].split()
        parent = identity(int(fields[1]))
        assert str(HERE / "run_jobs.py").encode() in Path(f"/proc/{parent['pid']}/cmdline").read_bytes().split(b"\0")
        deadline = stage["started_unix"] + 12 * 3600
        source_lock = read(RUN / "fused_source_lock.json")
        assert source_lock["status"] == "LOCKED_BEFORE_HANDOFF"
        for name, digest in source_lock["source_sha256"].items():
            assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
        assert read(RUN / "fused_restore_control.json")["status"] == "PASS"
        assert read(RUN / "fused_handoff_control.json")["status"] == "PASS"
        record("WAITING_FOR_CHECKPOINT", original_trainer=child, original_coordinator=parent,
            deadline_unix=deadline, target_step=100, controller=identity(os.getpid()),
            user_authorization="10-19-2026: ok can you deploy that one then")
        terminated = False
        gates = ExitStack()
        try:
            checkpoint, step = wait_for_checkpoint(child, deadline)
            # Serialize the brief device-6 gap with the cluster's existing allocators.
            for path in ("/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.lock",
                         "/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/lock"):
                stream = gates.enter_context(open(path, "rb"))
                acquired = time.monotonic()
                while True:
                    try:
                        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() - acquired > 180:
                            raise TimeoutError("allocator admission lock unavailable")
                        time.sleep(0.5)
            retire_old_guard(parent)
            assert matching(child) and os.getpgid(child["pid"]) == child["pid"]
            record("REPLACING_TRAINER", original_completed_updates=step, original_trainer_paused=True)
            os.killpg(child["pid"], signal.SIGTERM)
            os.kill(child["pid"], signal.SIGCONT)
            terminated = True
            end = time.monotonic() + 120
            while time.monotonic() < end:
                old = read(RUN / "execution/4b_mixed/training.json")
                if old.get("status") == "FAILED" and not matching(child):
                    break
                time.sleep(0.25)
            assert old.get("exit_code") == -signal.SIGTERM and not matching(child)
            jobs.write(HANDOFF / "original_training_receipt.json", old)
            for filename in ("allocation.json", "released.json"):
                path = RUN / "execution/4b_mixed" / filename
                if path.exists():
                    shutil.copy2(path, HANDOFF / ("original_" + filename))
            # Wait for the old pipeline's finally block to release the owned device lock.
            with (RUN / "device_6.lock").open("a") as lock:
                while True:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() > end:
                            raise TimeoutError("old device lock did not release")
                        time.sleep(0.25)
            while True:
                devices, busy = jobs.device_inventory()
                if devices["6"]["uuid"] not in busy and devices["6"]["used_mib"] < 64:
                    break
                if time.monotonic() > end:
                    raise TimeoutError("old CUDA context did not release")
                time.sleep(0.25)
            normal_stage = jobs.run_stage
            def continuation_stage(label, name, command, env, timeout):
                if name == "smoke":
                    return read(RUN / "execution/4b_mixed/smoke.json")
                if name == "training":
                    command = [jobs.PYTHON, str(HERE / "resume_4b_fused.py"), "train",
                        "--checkpoint", str(checkpoint), "--step", str(step)]
                    return normal_stage(label, "training_fused", command, env, max(1, deadline - time.time()))
                return normal_stage(label, name, command, env, timeout)
            jobs.run_stage = continuation_stage
            record("RESUMING", original_trainer_paused=False, completed_updates_preserved=step)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pipeline = pool.submit(jobs.gpu_pipeline, "4b_mixed", "6")
                startup_deadline = time.monotonic() + 600
                while not pipeline.done():
                    new = read(RUN / "execution/4b_mixed/training_fused.json")
                    devices, busy = jobs.device_inventory()
                    apps = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid",
                        "--format=csv,noheader,nounits"], text=True)
                    contexts = {tuple(v.strip() for v in line.split(",")) for line in apps.splitlines()}
                    if new.get("pid") and (devices["6"]["uuid"], str(new["pid"])) in contexts:
                        record("FUSED_TRAINING", resumed_trainer=new, cuda_context_verified=True)
                        break
                    if time.monotonic() > startup_deadline:
                        gates.close()
                        if new.get("pid") and matching(new):
                            assert os.getpgid(new["pid"]) == new["pid"]
                            os.killpg(new["pid"], signal.SIGTERM)
                        raise TimeoutError("continuation did not establish a device context")
                    time.sleep(1)
                gates.close()
                pipeline.result()
            jobs.run_stage = normal_stage
            record("GENERATION_COMPLETE_WAITING_FOR_PRIMARY", generated_cells=1080)
            # The first supervisor owns all primary scoring. Serialize the two CPU pools.
            while matching(parent):
                if time.time() > deadline + 16 * 3600:
                    raise TimeoutError("primary supervisor did not finish")
                time.sleep(10)
            terminal = read(RUN / "terminal.json")
            jobs.write(HANDOFF / "original_supervisor_terminal.json", terminal)
            failures = terminal.get("failures", [])
            planned = [failure for failure in failures if failure.get("label") == "4b_mixed"
                and "training exited -15;" in failure.get("error", "")]
            unexpected = [failure for failure in failures if failure not in planned]
            assert len(planned) == 1, "original planned handoff termination not accounted for"
            jobs.write(RUN / "terminal.json", {"status": "RUNNING", "phase": "4B scoring",
                "planned_supervisor_handoff": str(STATE), "unexpected_primary_failures": unexpected})
            env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(jobs.REPO / "src")}
            jobs.run_stage("4b_mixed", "materialize", [jobs.PYTHON, "-m", "rl4cv.veribench.jobs", "--gen",
                str(RUN / "validation/4b_mixed/raw.jsonl"), "--out-root", str(RUN / "validation/4b_mixed/jobs"),
                "--name", "4b_mixed"], env, 300)
            record("SCORING")
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as scores:
                futures = [scores.submit(jobs.score_sample, "4b_mixed", k) for k in range(8)]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
            assert not unexpected, f"primary failures retained: {unexpected}"
            assert all(read(RUN / "execution" / label / f"score_{k}.json").get("status") == "DONE"
                for label in ("1p7_control", "1p7_mixed", "4b_mixed") for k in range(8))
            jobs.run_stage("aggregate", "analysis", [jobs.PYTHON, str(HERE / "analyze.py")], env, 900)
            record("COMPLETE", completed_cells=3240, completed_unix=time.time())
            jobs.write(RUN / "terminal.json", {"status": "COMPLETE", "failures": [],
                "ended_unix": time.time(), "analysis": str(RUN / "analysis/summary.json"),
                "planned_supervisor_handoff": str(STATE)})
        except BaseException as exc:
            gates.close()
            if not terminated and matching(child):
                os.kill(child["pid"], signal.SIGCONT)
            record("FAILED", error=repr(exc), original_trainer_terminated=terminated)
            raise
        finally:
            gates.close()


if __name__ == "__main__":
    main()
