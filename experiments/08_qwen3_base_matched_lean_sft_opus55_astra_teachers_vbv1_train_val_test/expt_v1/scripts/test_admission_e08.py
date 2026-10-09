#!/usr/bin/env python3
"""Fence test generation behind complete validation and the exact published selection and manifest."""
from __future__ import annotations

import argparse
import json
import pipeline_e08 as pipeline


def check(label: str, model: str, revision: str) -> dict:
    p = pipeline
    selection = p.selection_committed()
    if not selection or selection.get("verdict") not in ("RL-READY", "PARTIAL"):
        raise ValueError("No committed, admitted selection")
    for name in ("selection.json", "test_manifest.json"):
        path = p.RES / name
        rel = str(path.relative_to(p.REPO))
        if p.git("diff", "--quiet", "HEAD", "--", rel).returncode:
            raise ValueError(f"{name} differs from HEAD")
        remote = p.git("show", f"origin/main:{rel}")
        if remote.returncode or remote.stdout != path.read_text():
            raise ValueError(f"{name} is not the exact published artifact on origin/main")
    if not all(p.train_log_ok(size) and p.exports_ok(size) for size in p.SIZES):
        raise ValueError("Training artifacts are incomplete")
    labels = [p.label(size, frac) for size in p.SIZES for frac in p.FRACTIONS] + ["base14b"]
    if not all(p.ladder_valid(lab, "validation")["valid"] for lab in labels):
        raise ValueError("Full validation raw/scored artifacts are incomplete")
    manifest = p.read_json(p.RES / "test_manifest.json", {})
    if manifest.get("selection_sha256") != p.sha((p.RES / "selection.json").read_bytes()):
        raise ValueError("Test manifest selection hash mismatch")
    wanted = [dict(s, in_test=True) for s in selection["test_manifest"]["systems"]]
    if manifest.get("systems") != wanted:
        raise ValueError("Test systems differ from frozen selection")
    system = next((s for s in wanted if s["label"] == label and s.get("source") != "e05"), None)
    if not system or p.model_args(system) != (model, revision):
        raise ValueError("Requested test model is outside frozen selection")
    return {"verdict": "PASS", "label": label, "selection_sha256": manifest["selection_sha256"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("label")
    ap.add_argument("model")
    ap.add_argument("revision")
    a = ap.parse_args()
    print(json.dumps(check(a.label, a.model, a.revision)))
