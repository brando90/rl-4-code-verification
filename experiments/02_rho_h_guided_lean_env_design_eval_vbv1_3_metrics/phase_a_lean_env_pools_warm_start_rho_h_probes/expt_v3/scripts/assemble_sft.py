#!/usr/bin/env python3
"""TLDR: Assemble the host-only Lean warm-start SFT set from kept, screen-clean (task, teacher) pairs: one JSONL row per pair holding the exact teacher prompt (system + user message) and the kept Lean file, plus a committed manifest of task ids, teachers and SHA-256s with no file contents (experiment 02A v3 cc.md § 6.4)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", type=Path, required=True)
    ap.add_argument("--screen", type=Path, required=True)
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--pack-manifest", type=Path, required=True)
    ap.add_argument("--job-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="host-only JSONL (never committed)")
    ap.add_argument("--manifest-out", type=Path, required=True, help="committed manifest without contents")
    a = ap.parse_args()
    from rl4cv.veribench.exp103 import build_prompt

    rows = [json.loads(l) for l in a.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    excluded = set(json.loads(a.screen.read_text()).get("excluded_cells", []))
    pack_manifest = json.loads(a.pack_manifest.read_text())
    expected_prompt = {r["task_id"]: r["prompt_sha256"] for r in pack_manifest["tasks"]}
    kept = sorted((r for r in rows if r.get("kernel_binary") == 1.0 and f"{r['teacher']}/{r['task_id']}" not in excluded and r["task_id"] in expected_prompt),
                  key=lambda r: (r["task_id"], r["teacher"]))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    with a.out.open("w", encoding="utf-8") as fh:
        for r in kept:
            instruction = (a.pack / r["task_id"] / "instruction.md").read_text(encoding="utf-8")
            prompt = build_prompt(instruction, root=REPO_ROOT / "external" / "veribench")
            if prompt.prompt_sha256 != expected_prompt[r["task_id"]]:
                raise RuntimeError(f"{r['task_id']}: prompt hash drift")
            lean = (a.job_root / f"{r['teacher']}_s0" / r["task_id"] / "verifier" / "solution.lean").read_text(encoding="utf-8")
            if sha(lean) != r["lean_sha256"]:
                raise RuntimeError(f"{r['teacher']}/{r['task_id']}: Lean hash drift")
            fh.write(json.dumps({"task_id": r["task_id"], "teacher": r["teacher"], "model": r["model"], "system": prompt.system, "user": prompt.user,
                                 "lean": lean, "prompt_sha256": prompt.prompt_sha256, "lean_sha256": r["lean_sha256"]}, sort_keys=True) + "\n")
            entries.append({"task_id": r["task_id"], "teacher": r["teacher"], "model": r["model"], "prompt_sha256": prompt.prompt_sha256,
                            "lean_sha256": r["lean_sha256"], "lean_bytes": len(lean.encode("utf-8")), "n_theorems": r.get("n_theorems_stated")})
    manifest = {"manifest_kind": "lean_warmstart_v3_sft_manifest", "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sft_path_host_only": str(a.out.resolve()), "sft_sha256": hashlib.sha256(a.out.read_bytes()).hexdigest(), "n_pairs": len(entries),
                "n_distinct_tasks": len({e["task_id"] for e in entries}), "per_teacher": {t: sum(1 for e in entries if e["teacher"] == t) for t in sorted({e["teacher"] for e in entries})},
                "system_prompt_sha256": pack_manifest["prompt"]["system_prompt_sha256"], "addendum_sha256": pack_manifest["prompt"]["addendum_sha256"],
                "keep_rule": "kernel_binary = 1 under the frozen scorer and not excluded by the generated-Lean screen", "pairs": entries}
    a.manifest_out.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("n_pairs", "n_distinct_tasks", "per_teacher", "sft_sha256")}))


if __name__ == "__main__":
    main()
