"""Read persistent experiment receipts without importing a model or allocating a GPU."""
import json
import os
from pathlib import Path
import time

RUN = Path(os.environ.get("TINY_RUN_ROOT", "/lfs/skampere1/0/eth127/rl4cv_tiny_training"))


def load(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def main():
    result = {"observed_unix": time.time(), "root": str(RUN), "systems": {}}
    for name in ("launch", "terminal", "preparation_exit", "optimizer_preflight", "make_test_exit"):
        result[name] = load(RUN / (name + ".json"))
    for name in ("validation_preflight", "scoring_preflight"):
        receipt = load(RUN / (name + ".json"))
        result[name] = None if receipt is None else {k: v for k, v in receipt.items() if k not in ("prompts", "controls", "lean_path")}
    result["curriculum_admission"] = load(RUN / "curriculum/admission.json")
    log = RUN / "curriculum.log"
    if log.exists() and result["curriculum_admission"] is None:
        rows = []
        for line in log.read_text().splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if "accepted" in row:
                rows.append(row)
        result["curriculum_progress"] = {"checked": len(rows), "accepted": sum(r["accepted"] for r in rows),
            "failures": [r for r in rows if not r["accepted"]]}
    for label, size, condition in (("1p7_control", "onep7", "control"), ("1p7_mixed", "onep7", "mixed"), ("4b_mixed", "four", "mixed")):
        root = RUN / size
        execution = RUN / "execution" / label
        stages = {p.stem: load(p) for p in execution.glob("*.json")}
        for stage in stages.values():
            if stage and stage.get("status") == "RUNNING" and stage.get("start_ticks"):
                try:
                    ticks = Path(f"/proc/{stage['pid']}/stat").read_text().rsplit(") ", 1)[1].split()[19]
                    stage["alive"] = ticks == stage["start_ticks"] and Path("/proc/sys/kernel/random/boot_id").read_text().strip() == stage["boot_id"]
                except OSError:
                    stage["alive"] = False
        result["systems"][label] = {"stages": stages,
            "preparation": load(root / "prepare_receipt.json"),
            "progress": load(root / "runs" / condition / "progress.json"),
            "training_result": load(root / "runs" / condition / "result.json"),
            "generation_verified": load(RUN / "validation" / label / "generation_verified.json")}
        raw = RUN / "validation" / label / "raw.jsonl"
        if raw.exists():
            with raw.open("rb") as stream:
                count = sum(block.count(b"\n") for block in iter(lambda: stream.read(1 << 20), b""))
            result["systems"][label]["generated_cells"] = count
    result["summary"] = load(RUN / "analysis/summary.json")
    result["primary_summary"] = load(RUN / "analysis/summary_primary.json")
    result["four_wallclock_extension"] = load(RUN / "four_wallclock_extension.json")
    handoff = load(RUN / "fused_handoff/status.json")
    result["four_fused_handoff"] = handoff
    if handoff:
        result["four_fused_restore"] = load(RUN / "fused_handoff/restore_verified.json")
        item = result["systems"]["4b_mixed"]
        stages = item["stages"]
        old = stages.get("training") or {}
        if handoff.get("status") not in ("WAITING_FOR_CHECKPOINT", "VERIFYING_CHECKPOINT"):
            item["superseded_training"] = old
            stages["training"] = stages.get("training_fused") or {"status": "PLANNED_HANDOFF"}
        terminal = result.get("terminal") or {}
        if handoff.get("status") == "FAILED":
            result["terminal"] = {"status": "FAILED", "fused_handoff_error": handoff.get("error"),
                "original_supervisor_terminal": terminal}
        elif terminal.get("status") == "FAILED":
            # Preserve the raw supervisor's deliberate -15 receipt while the successor runs.
            failures = terminal.get("failures", [])
            planned = [r for r in failures if r.get("label") == "4b_mixed" and "training exited -15;" in r.get("error", "")]
            if len(planned) == len(failures) == 1:
                result["original_supervisor_terminal"] = terminal
                result["terminal"] = {"status": "RUNNING", "phase": handoff["status"], "planned_4b_handoff": True}
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
