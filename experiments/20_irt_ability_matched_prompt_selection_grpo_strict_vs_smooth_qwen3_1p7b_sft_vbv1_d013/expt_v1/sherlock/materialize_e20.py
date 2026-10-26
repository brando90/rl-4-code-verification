"""TLDR: Turn experiment 20's Phase 0a generation rows (4 chunk raw.jsonl files) into VeriBench scorer job directories, one per (chunk, sample index) = 32 jobs named e20_p0_c<chunk>_s<k> (rl4cv.veribench.jobs layout, write-once), and record the per-cell generation receipts (no completions) in phase0_gen_receipts.csv for the committed per-cell table."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

E20 = Path(os.environ.get("E20_ROOT", "/scratch/users/brando9/rl4cv_sherlock/e20"))
sys.path.insert(0, os.environ.get("RL4CV_SRC", "/scratch/users/brando9/rl4cv_sherlock/grading/rl4cv/src"))
from rl4cv.veribench.jobs import materialize_jobs  # noqa: E402

FIELDS = ("chunk", "task_id", "sample_idx", "label", "prompt_tokens", "generated_tokens", "finish_reason", "measured",
          "truncated", "admitted", "extraction", "lean_sha256", "lean_bytes", "prompt_sha256", "seed")


def main() -> int:
    out_root = E20 / "phase0/jobs"
    out_root.mkdir(parents=True, exist_ok=True)
    receipts = []
    for c in range(4):
        raw = E20 / f"phase0/gen/chunk_{c}/raw.jsonl"
        rows = [json.loads(line) for line in raw.open() if line.strip()]
        ids = [line.strip() for line in (E20 / f"phase0/ids/chunk_{c}.txt").open() if line.strip()]
        cells = {(r["task_id"], int(r["sample_idx"])) for r in rows}
        missing = [(t, k) for t in ids for k in range(8) if (t, k) not in cells]
        if missing or len(cells) != len(rows):
            raise RuntimeError(f"chunk {c}: {len(missing)} missing cells, {len(rows) - len(cells)} duplicates")
        jobs = materialize_jobs(rows, out_root, f"e20_p0_c{c}")
        for r in rows:
            lean = r.get("lean") or ""
            receipts.append({"chunk": c, "task_id": r["task_id"], "sample_idx": int(r["sample_idx"]), "label": r.get("label"),
                             "prompt_tokens": r.get("prompt_tokens"), "generated_tokens": r.get("generated_tokens"),
                             "finish_reason": r.get("finish_reason"), "measured": r.get("measured"), "truncated": r.get("truncated"),
                             "admitted": r.get("admitted"), "extraction": r.get("extraction"),
                             "lean_sha256": hashlib.sha256(lean.encode()).hexdigest() if lean else "",
                             "lean_bytes": len(lean.encode()), "prompt_sha256": r.get("prompt_sha256"),
                             "seed": (r.get("sampling") or {}).get("seed")})
        print(f"chunk {c}: {len(rows)} rows -> {len(jobs)} jobs: {sorted(p.name for p in jobs.values())}")
    receipts.sort(key=lambda r: (r["task_id"], r["sample_idx"]))
    with (E20 / "phase0/phase0_gen_receipts.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(receipts)
    print(f"receipts: {len(receipts)} cells (expected 4312)")
    return 0 if len(receipts) == 4312 else 3


if __name__ == "__main__":
    raise SystemExit(main())
