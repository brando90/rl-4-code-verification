"""Exercise checkpoint fencing and failed-validation recovery on disposable CPU subprocesses."""
import csv
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

import torch
import deploy_4b_fused as deployment
import experiment


def main():
    parent = deployment.RUN
    results = []
    for valid in (True, False):
        with tempfile.TemporaryDirectory(prefix="fused_handoff_control_", dir=parent) as directory:
            root = Path(directory)
            deployment.RUN = root
            deployment.HANDOFF = root / "fused_handoff"
            deployment.HANDOFF.mkdir()
            deployment.STATE = deployment.HANDOFF / "status.json"
            out = root / "four/runs/mixed"
            out.mkdir(parents=True)
            data = root / "four/data"
            data.mkdir()
            receipt = {"code_sha256": experiment.digest(experiment.__file__), "initial_manifest_sha256": "control"}
            (root / "four/prepare_receipt.json").write_text(json.dumps(receipt))
            (data / "schedule_mixed.json").write_text(json.dumps([{"cumulative_loss_tokens": i} for i in range(1, 101)]))
            with (out / "steps.csv").open("w") as stream:
                writer = csv.DictWriter(stream, fieldnames=["step", "loss_tokens"])
                writer.writeheader()
                writer.writerows({"step": i, "loss_tokens": i} for i in range(1, 101))
            identity = {"size": "4B", "condition": "mixed", **receipt}
            (out / "identity.json").write_text(json.dumps(identity))
            state = {"step": 100, "consumed": 100 if valid else 99, "identity": identity,
                "cpu_rng": torch.get_rng_state(), "cuda_rng": [torch.get_rng_state()],
                "optimizer": {"master_weights": [torch.ones(3)], "optimizer": {
                    "param_groups": [{"params": [0]}], "state": {0: {"step": torch.tensor(100.)}}}}}
            torch.save(state, out / "training_state.pt")
            child = subprocess.Popen(["/usr/bin/python3", "-c", "import time;time.sleep(60)"], start_new_session=True)
            try:
                process = deployment.identity(child.pid)
                try:
                    saved, step = deployment.wait_for_checkpoint(process, time.time() + 30)
                    assert valid and step == 100
                    assert saved.stat().st_ino == (out / "training_state.pt").stat().st_ino
                    assert deployment.matching(process)["state"] in ("T", "t")
                    results.append({"case": "valid_checkpoint", "status": "PASS", "paused_at_complete_boundary": True})
                except AssertionError:
                    if valid:
                        raise
                    end = time.monotonic() + 3
                    while deployment.matching(process)["state"] in ("T", "t") and time.monotonic() < end:
                        time.sleep(0.01)
                    assert deployment.matching(process)["state"] not in ("T", "t")
                    results.append({"case": "invalid_checkpoint", "status": "PASS", "original_process_resumed": True})
            finally:
                if child.poll() is None:
                    child.send_signal(signal.SIGCONT)
                    child.terminate()
                child.wait(timeout=5)
    print(json.dumps({"status": "PASS", "controls": results,
        "production_processes_modified": False, "cuda_allocated": False}, indent=2))


if __name__ == "__main__":
    main()
