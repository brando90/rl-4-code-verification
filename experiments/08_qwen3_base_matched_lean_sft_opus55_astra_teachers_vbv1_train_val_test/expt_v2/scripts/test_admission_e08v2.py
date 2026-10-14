#!/usr/bin/env python3
"""Admit only new matched-step test systems in the exact published version 2 protocol and manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]


def check(label: str, model: str, revision: str, *, repo: Path = REPO, exp: Path = EXP) -> dict:
    """Fail closed on publication, identity, split, or export-manifest mismatch."""
    for path in (exp / "PROTOCOL_v2.md", exp / "results/test_manifest_v2.json"):
        rel = path.relative_to(repo).as_posix()
        remote = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=repo, capture_output=True, check=False)
        if remote.returncode or remote.stdout != path.read_bytes():
            raise ValueError(f"{path.name} is not the exact published artifact on origin/main")
    manifest = json.loads((exp / "results/test_manifest_v2.json").read_text())
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if digest(exp / "PROTOCOL_v2.md") != manifest["protocol_sha256"]:
        raise ValueError("Protocol hash mismatch")
    ids = repo / manifest["task_ids_file"]
    if digest(ids) != manifest["task_ids_sha256"]:
        raise ValueError("Task list hash mismatch")
    if manifest["split"] != "test" or manifest["n_tasks"] != 222 or manifest["samples_per_task"] != 8:
        raise ValueError("Invalid declared test cells")
    system = next((s for s in manifest["systems"] if s["label"] == label and s.get("generation") == "new"), None)
    if system is None or system["hf_path"] != model or revision != "local":
        raise ValueError("Requested test model is outside the manifest")
    if system["step"] != 658 or system["cumulative_assistant_tokens"] != 5752936:
        raise ValueError("Checkpoint is outside the matched token budget")
    if digest(Path(model) / "SHA256SUMS") != system["weights_sha256_manifest"]:
        raise ValueError("Weight hash mismatch")
    return {"verdict": "PASS", "label": label, "weights_sha256_manifest": system["weights_sha256_manifest"], "protocol_sha256": manifest["protocol_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("model")
    parser.add_argument("revision")
    args = parser.parse_args()
    print(json.dumps(check(args.label, args.model, args.revision)))
