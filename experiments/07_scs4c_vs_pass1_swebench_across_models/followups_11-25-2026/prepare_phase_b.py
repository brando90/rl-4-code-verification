"""Prepare a pinned 731-task Phase B manifest without copying gold patches into the committed manifest."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

DATASET = "opencompass/SWEBench-Pro-Verified"
REVISION = "ae466f824cdee69d2c010b6c954b7418c411b6e4"
SHA256 = "9eeac2c01fcbf25fd8db4254a23b9e0d306eb659e9c14dd1308b9fda10faf6d8"


def prepare(raw: bytes, *, expected_sha256: str = SHA256, expected_count: int = 731) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("dataset file differs from the recorded revision's content")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    ids = [r["instance_id"] for r in rows]
    if len(rows) != expected_count or len(set(ids)) != len(ids):
        raise ValueError("task count or uniqueness mismatch")
    tasks = []
    for row in rows:
        for key in ("repo", "base_commit", "patch", "dockerhub_tag", "repo_language"):
            if not isinstance(row[key], str) or not row[key]:
                raise ValueError(f"missing {key}: {row['instance_id']}")
        for key in ("fail_to_pass", "pass_to_pass"):
            if not isinstance(row[key], list) or len(row[key]) != row[key + "_count"]:
                raise ValueError(f"test denominator mismatch: {row['instance_id']}")
        tasks.append({k: row[k] for k in ("instance_id", "repo", "base_commit", "repo_language", "dockerhub_tag",
                                         "fail_to_pass_count", "pass_to_pass_count")} |
                     {"gold_patch_sha256": hashlib.sha256(row["patch"].encode()).hexdigest(),
                      "test_patch_sha256": hashlib.sha256(row["test_patch"].encode()).hexdigest(),
                      "d_gold_controls": "unmeasured: frozen task-specific property/fuzz inputs and executable adapters required"})
    return {"date": "11-25-2026", "status": "PREPARATION ONLY; no solver or D_gold control run",
            "dataset": DATASET, "revision": REVISION, "file_sha256": digest, "declared_tasks": len(rows),
            "languages": dict(Counter(r["repo_language"] for r in rows)),
            "repositories": dict(Counter(r["repo"] for r in rows)),
            "controls_required": 658, "controls_measured": 0, "controls_unmeasured": len(rows), "tasks": tasks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.input.read_bytes())
    with args.out.open("x") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "tasks"}, indent=2))


if __name__ == "__main__":
    main()
