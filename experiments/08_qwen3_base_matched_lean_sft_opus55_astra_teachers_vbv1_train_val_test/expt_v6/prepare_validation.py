"""Reconstruct only validation instructions with the pinned adapter and require all historical prompt hashes."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path(os.environ["TINY_RUN_ROOT"])
sys.path.insert(0, str(REPO / "src"))


def main():
    from rl4cv.veribench.exp103 import build_prompt

    vb = REPO / "external/veribench"
    adapter_path = HERE / "validation_adapter_v6.py"
    os.environ["VERIBENCH_ROOT"] = str(vb)
    spec = importlib.util.spec_from_file_location("pinned_task_adapter", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    expected = json.loads((HERE.parent / "expt_v3/results/generation_prompt_hashes_v3.json").read_text())
    ids = (HERE.parent / "expt_v1/results/split/vbv1_validation_task_ids.txt").read_text().splitlines()
    manifest = {r["task_id"]: r for r in csv.DictReader((HERE.parent / "expt_v1/results/split/vbv1_split_manifest.csv").open())}
    assert len(ids) == len(set(ids)) == len(expected) == 135
    pack = RUN / "validation_pack"
    pack.mkdir(exist_ok=True)
    failures, hashes = [], {}
    template = (vb / "vb_harbor/adapter/template/task.toml").read_bytes()
    for tid in ids:
        row = manifest[tid]
        assert row["split"] == "validation"
        source = (vb / "veribench_dataset/py_src" / row["py_relpath"]).read_text()
        stem = Path(row["gold_relpath"]).stem
        instruction = adapter.generate_instruction(source, stem)
        prompt = build_prompt(instruction, root=vb)
        actual = {k: getattr(prompt, k) for k in expected[tid]}
        if actual != expected[tid]:
            failures.append({"task_id": tid, "expected": expected[tid], "actual": actual})
            continue
        target = pack / tid
        target.mkdir(exist_ok=True)
        (target / "instruction.md").write_text(instruction)
        (target / "task.toml").write_bytes(template)
        hashes[tid] = actual
    result = {"status": "PASS" if not failures else "BLOCKED", "tasks": len(hashes),
        "failures": failures, "pack": str(pack),
        "adapter_sha256": hashlib.sha256(adapter_path.read_bytes()).hexdigest(),
        "prompts": hashes, "test_split_opened_for_evaluation": False}
    (RUN / "validation_preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    cells = [{"system": system, "task_id": tid, "sample_idx": k, "status": "PENDING"}
        for system in ("1p7_control", "1p7_mixed", "4b_mixed") for tid in ids for k in range(8)]
    (RUN / "validation_manifest.json").write_text(json.dumps(cells, indent=2) + "\n")
    assert not failures, f"{len(failures)} frozen prompt mismatches; no validation generation admitted"
    print(json.dumps({k: v for k, v in result.items() if k != "prompts"}), flush=True)


if __name__ == "__main__":
    main()
