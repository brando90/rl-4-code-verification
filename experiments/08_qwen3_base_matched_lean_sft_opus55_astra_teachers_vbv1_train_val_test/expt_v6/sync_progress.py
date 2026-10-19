"""Mirror cluster receipts and live progress through the existing SSH connection into the owned local experiment."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import time
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
SOCKET = "/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control"
HOST = "eth127@skampere1.stanford.edu"
REMOTE = "/lfs/skampere1/0/eth127/rl4cv_tiny_training"
REL = "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6"
CANONICAL = Path("/Users/lethan3/Documents/veribench-projects/rl-4-code-verification") / REL


def once():
    subprocess.run(["ssh", "-S", SOCKET, "-O", "check", HOST], capture_output=True, check=True, timeout=5)
    command = f"/usr/bin/python3 {REMOTE}/repo/{REL}/snapshot.py"
    result = subprocess.run(["ssh", "-S", SOCKET, "-o", "BatchMode=yes", HOST, command],
        text=True, capture_output=True, timeout=30, check=True)
    state = json.loads(result.stdout)
    target = HERE / "results/runtime_snapshot.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(state, indent=2) + "\n")
    stamp = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%m-%d-%Y %H:%M:%S %Z")
    terminal = state.get("terminal") or {}
    status = terminal.get("status") or ("RUNNING" if state.get("launch") else "PREPARING")
    lines = ["# Concise Lean curriculum: 1.7B / 4B training comparison", "",
        "**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/" + REL + "/results.md", "",
        f"**Status:** {status}. **Last updated:** {stamp}.", "",
        "| Condition | Training progress | Assistant tokens consumed | Validation generated | Scoring jobs complete |",
        "|---|---:|---:|---:|---:|"]
    for label, item in state["systems"].items():
        progress = item.get("progress") or {}
        stages = item.get("stages") or {}
        preparation = item.get("preparation") or {}
        condition = "control" if label.endswith("control") else "mixed"
        plan = preparation.get("schedules", {}).get(condition, {})
        step = progress.get("step", 0)
        total = plan.get("steps", "pending")
        progress_text = f"{step}/{total} updates"
        failed = [name for name, value in stages.items() if value and (value.get("status") == "FAILED" or value.get("alive") is False)]
        if failed:
            progress_text += "; failed/dead: " + ", ".join(failed)
        scored = sum(1 for name, value in stages.items() if name.startswith("score_") and value and value.get("status") == "DONE")
        lines.append(f"| {label} | {progress_text} | {progress.get('loss_tokens', 0):,} | {item.get('generated_cells', 0)}/1,080 | {scored}/8 |")
    admission = state.get("curriculum_admission") or state.get("curriculum_progress") or {}
    lines += ["", "## Verified preparation", "",
        f"- Corrected tiny examples: {admission.get('compiled', admission.get('accepted', 0))}/500. Each includes an anonymous executable `example`; original version 5 remains pristine.",
        "- All 135 validation prompts match the prior frozen instruction/system/addendum/prompt hashes.",
        "- Frozen-scorer positive, compile-error and sorry-proof controls passed. The 4B float32 CPU optimizer matched native AdamW in its numerical control.",
        "- Both augmented conditions expose all 500 tiny examples once and 1,308 existing responses; control exposes 1,328 existing responses. Source pool contains 2,585 admitted existing responses.",
        "- Target budget is 5,752,936 assistant loss tokens. Actual crossing totals: control 5,759,732; augmented 5,753,602. Planned updates: control 664; each augmented condition 904.",
        "- 4B uses full-parameter training with float32 CPU master weights/Adam moments and bfloat16 GPU parameters. It has no new replay control.",
        "- Test evaluation is not performed. Formal specification coverage is unmeasured; no judge-dependent aggregate is claimed.", ""]
    if state.get("summary") or state.get("primary_summary"):
        summary = state.get("summary") or state["primary_summary"]
        heading = "## Validation results" if state.get("summary") else "## Primary validation results (2,160/3,240 cells; 4B pending)"
        lines += [heading, "", "| System | Binary successes / 1,080 | Success rate | Tasks with 2–6 successes / 135 |", "|---|---:|---:|---:|"]
        for label, row in summary["systems"].items():
            ci = row.get("success_rate_ci95", [None, None])
            interval = f" [{ci[0]:.4f}, {ci[1]:.4f}]" if ci[0] is not None else ""
            lines.append(f"| {label} | {row['successes']}/1,080 | {row['success_rate']:.4f}{interval} | {row['target_tasks_2_to_6']}/135 |")
        lines += ["", "Intervals resample tasks with their eight attempts together, 10,000 draws, seed 0; p-val=n/a. Historical starting-checkpoint comparisons are descriptive.", ""]
        primary = summary["comparisons"]["1p7_mixed_minus_1p7_control"]
        lines.append(f"Primary augmented-minus-control difference: {primary['difference']:.4f}, 95% interval {primary['ci95']}; **{primary['interpretation']}**. One training seed; training-seed variability is unmeasured.")
    else:
        lines.append("Held-out validation improvement is not yet measured. Training loss is not a correctness result.")
    lines += ["", "[Protocol](PROTOCOL.md) · [Checkpoint](CKPT_tiny_training.md) · [Runtime snapshot](results/runtime_snapshot.json)", "",
        f"**TLDR-end:** [rl4cv: concise Lean training] {status}; the full declared evaluation has 3,240 cells.", ""]
    (HERE / "results.md").write_text("\n".join(lines))
    CANONICAL.mkdir(parents=True, exist_ok=True)
    (CANONICAL / "results").mkdir(exist_ok=True)
    if CANONICAL != HERE:
        shutil.copy2(HERE / "results.md", CANONICAL / "results.md")
        shutil.copy2(target, CANONICAL / "results/runtime_snapshot.json")
    print(json.dumps({"observed": stamp, "status": status,
        "training_steps": {k: (v.get("progress") or {}).get("step", 0) for k, v in state["systems"].items()}}), flush=True)
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    while True:
        try:
            status = once()
        except Exception as exc:
            print(json.dumps({"status": "SYNC_FAILED", "error": str(exc)}), flush=True)
            if not args.watch:
                raise
            time.sleep(60)
            continue
        if not args.watch or status in ("COMPLETE", "FAILED"):
            break
        time.sleep(60)
