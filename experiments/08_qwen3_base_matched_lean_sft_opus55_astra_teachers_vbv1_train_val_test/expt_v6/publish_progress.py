"""Collect finished compact evidence and publish only owned progress files when main has not advanced."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess


def publish(here, socket, host, remote, state):
    repo = here.parents[2]
    result = here / "results"
    owned = [here / "results.md", result / "runtime_snapshot.json"]
    def copy(source, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["scp", "-q", "-o", "ControlPath=" + socket,
            f"{host}:{remote}/{source}", str(destination)], check=True, timeout=30)
        owned.append(destination)
    for label, item in state["systems"].items():
        if not item.get("training_result"):
            continue
        size, condition = ("four" if label == "4b_mixed" else "onep7"), ("control" if label.endswith("control") else "mixed")
        for source in ("steps.csv", "identity.json", "result.json", "weights_manifest.json"):
            destination = result / "training" / f"{label}_{source}"
            if not destination.exists():
                copy(f"{size}/runs/{condition}/{source}", destination)
            else:
                owned.append(destination)
    summary = state.get("summary") or state.get("primary_summary")
    if summary:
        phase = "full" if state.get("summary") else "primary"
        source = "summary.json" if phase == "full" else "summary_primary.json"
        copy("analysis/" + source, result / "analysis" / source)
        for label in summary["systems"]:
            for suffix, expected in (("cells", 1080), ("tasks", 135)):
                destination = result / "analysis" / f"{label}_{suffix}.csv"
                copy(f"analysis/{label}_{suffix}.csv", destination)
                with destination.open() as stream:
                    assert len(list(csv.DictReader(stream))) == expected, "partial evidence copy; retry after source settles"
    relative = [str(p.relative_to(repo)) for p in owned]
    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=repo, check=check, text=True, capture_output=True, timeout=45)
    staged = set(git("diff", "--cached", "--name-only").stdout.splitlines())
    if staged - set(relative):
        return {"status": "PENDING_OTHER_STAGED_FILES", "paths": sorted(staged - set(relative))}
    git("fetch", "origin", "+refs/heads/main:refs/remotes/origin/main")
    if git("merge-base", "--is-ancestor", "origin/main", "HEAD", check=False).returncode:
        return {"status": "PENDING_MAIN_ADVANCED", "local_results_current": True,
            "reason": "Preserve other owners' new commits; coordinator must reconcile before publishing."}
    git("add", "--", *relative)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return {"status": "UNCHANGED"}
    git("diff", "--cached", "--check")
    git("commit", "-qm", "Update concise Lean training progress and completed evidence")
    pushed = git("push", "origin", "HEAD:main", check=False)
    if pushed.returncode:
        return {"status": "PENDING_PUSH", "error": pushed.stderr[-1500:], "local_results_current": True}
    return {"status": "PUBLISHED", "commit": git("rev-parse", "HEAD").stdout.strip()}
