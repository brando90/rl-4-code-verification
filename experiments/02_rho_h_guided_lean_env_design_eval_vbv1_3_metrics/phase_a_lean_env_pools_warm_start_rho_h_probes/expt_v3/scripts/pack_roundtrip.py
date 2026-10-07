#!/usr/bin/env python3
"""TLDR: Round-trip every pack task through the collect-only service's own `load_task_pack` and experiment 103's `required_paths`, checking that each task's solution path, instruction hash and agent-spec stamp match the pack manifest (experiment 02A v3 cc.md § 2.3; zero model calls). Run with the service venv (benchmark_service installed)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
E103 = REPO_ROOT / "external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--pack-manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    sys.path[:0] = [str(E103 / "scripts/vb_service_single_call"), str(E103 / "scripts/valkyrie_single_call_agent")]
    import single_call  # noqa: E402  experiment 103's agent, imported not edited
    import veribench_valkyrie_service as service  # noqa: E402  the base service, imported not edited

    manifest = json.loads(args.pack_manifest.read_text())
    expected = {r["task_id"]: r for r in manifest["tasks"]}
    expected[manifest["preflight"]["task_id"]] = manifest["preflight"]
    tasks = service.load_task_pack(args.pack)
    failures = []
    for tid, row in expected.items():
        t = tasks.get(tid)
        if t is None:
            failures.append({"task_id": tid, "problem": "not loaded by load_task_pack"})
            continue
        paths = single_call.required_paths(t.instruction, "vbv1")
        checks = {
            "solution_path": t.solution_path == row["required_path"],
            "required_paths": paths == [row["required_path"]],
            "instruction_sha256": t.instruction_sha256 == row["instruction_sha256"],
            "agent_spec": t.agent_spec.startswith("<!-- VeriBench agent-spec v6"),
            "split": t.split == "mbpp",
            "lean_stem": t.lean_stem == row["lean_stem"],
        }
        if not all(checks.values()):
            failures.append({"task_id": tid, "checks": checks})
    extra = sorted(set(tasks) - set(expected))
    out = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pack": str(args.pack.resolve()),
           "n_loaded": len(tasks), "n_expected": len(expected), "extra_tasks": extra, "n_failures": len(failures), "failures": failures[:20],
           "service_file_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((E103 / "scripts/vb_service_single_call").glob("*.py"))},
           "agent_file_sha256": hashlib.sha256((E103 / "scripts/valkyrie_single_call_agent/single_call.py").read_bytes()).hexdigest(),
           "verdict": "PASS" if not failures and not extra and len(tasks) == len(expected) else "FAIL"}
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_loaded", "n_expected", "n_failures", "extra_tasks", "verdict")}))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
