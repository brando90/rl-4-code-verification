#!/usr/bin/env python3
"""TLDR: Freeze experiment 08's validation-ladder manifest (PROTOCOL § 9) before any trained-checkpoint generation: the 135 validation tasks × 8 samples for every system (the 5 token-fraction checkpoints × 4 sizes with their exported-weights SHA-256 manifests, actual steps and cumulative assistant tokens from `sft_schedule.json`; Base 14B as generated earlier; Base 1.7B / 4B / 8B from experiment 05's receipts), and record which systems are exported so far; zero model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
SIZES = ("1.7B", "4B", "8B", "14B")
FRACTIONS = ("0.125", "0.25", "0.5", "0.75", "1.0")
BASE_E05 = {"1.7B": "qwen3-1.7b-base", "4B": "qwen3-4b-base", "8B": "qwen3-8b-base"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=EXP / "results" / "ladder_manifest.json")
    a = ap.parse_args()
    sched = json.loads((EXP / "results" / "sft_schedule.json").read_text())
    base14 = json.loads((EXP / "results" / "ladder_manifest_base14b.json").read_text())
    mw = json.load(open(EXP / "results" / "model_weights_e08.json"))
    ids = [l.strip() for l in (EXP / "results" / "split" / "vbv1_validation_task_ids.txt").read_text().splitlines() if l.strip()]
    systems = []
    for size in SIZES:
        for f in FRACTIONS:
            ck = sched["checkpoints"][f]
            hf = WORK / "ckpt" / size / "hf" / f"step_{ck['step']}"
            sums = hf / "SHA256SUMS"
            systems.append({"label": f"sft_{size.replace('.', 'p')}_f{f.replace('.', 'p')}", "size": size, "fraction": f, "role": "trained", "source": "e08",
                            "step": ck["step"], "cumulative_assistant_tokens": ck["cumulative_assistant_tokens"], "hf_path": str(hf),
                            "weights_sha256_manifest": sha(sums.read_bytes()) if sums.exists() else None, "exported": sums.exists(), "in_test": True})
    systems.append(dict(base14["systems"][0], role="base", in_test=True))
    for size, lab in BASE_E05.items():
        systems.append({"label": f"base_{size.replace('.', 'p')}_e05", "size": size, "role": "base", "source": "e05", "e05_label": lab, "model": mw[size]["model"], "revision": mw[size]["revision"],
                        "note": "experiment 05 receipts restricted to the split; kernel factors preserved, non-vacuity screen recomputed into experiment 08 receipts", "in_test": True})
    old = json.loads(a.out.read_text()) if a.out.exists() else None
    m = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "split": "validation", "n_tasks": len(ids), "samples_per_task": 8,
         "task_ids_sha256": sha("".join(t + "\n" for t in ids).encode()), "sampling": base14["sampling"], "schedule_sha256": sha((EXP / "results" / "sft_schedule.json").read_bytes()),
         "systems": systems, "n_systems": len(systems), "n_declared_cells": len(ids) * 8 * len(systems),
         "frozen_first_utc": (old or {}).get("frozen_first_utc") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "note": "systems, cells and sampling are frozen at frozen_first_utc; later runs of this script only fill in exported-weights hashes as checkpoints land (labels, steps and tokens never change)"}
    if old:
        for k in ("task_ids_sha256", "schedule_sha256", "n_systems"):
            assert old[k] == m[k], f"frozen field {k} changed"
        for o, n in zip(old["systems"], systems):
            assert (o["label"], o.get("step"), o.get("cumulative_assistant_tokens")) == (n["label"], n.get("step"), n.get("cumulative_assistant_tokens"))
            if o.get("weights_sha256_manifest") and n.get("weights_sha256_manifest"):
                assert o["weights_sha256_manifest"] == n["weights_sha256_manifest"], f"{o['label']}: exported weights changed"
    a.out.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"n_systems": len(systems), "exported": [s["label"] for s in systems if s.get("exported")], "n_declared_cells": m["n_declared_cells"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
