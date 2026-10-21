"""TLDR: Build experiment 20's Phase 0 train pack on Sherlock (539 D-013 train tasks, instruction.md + task.toml) with experiment 08's pinned task adapter and experiment 103's prompt builder, hash-check every Python source against the D-013 split manifest, and prove the builder is the frozen one by reproducing all 135 validation prompt hashes of experiment 08 v3; writes train_pack_manifest.json next to the pack."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

# Paths on Sherlock (the v4-validation generation tree holds the pinned code and the VeriBench subset).
B = Path(os.environ.get("E20_GEN_TREE", "/scratch/users/brando9/rl4cv_sherlock/v4_validation/rl4cv_gen"))
E20 = Path(os.environ.get("E20_ROOT", "/scratch/users/brando9/rl4cv_sherlock/e20"))
E08 = B / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
VB = B / "external/veribench"
sys.path.insert(0, str(B / "src"))
os.environ["VERIBENCH_ROOT"] = str(VB)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    from rl4cv.veribench.exp103 import build_prompt

    adapter_path = E08 / "expt_v6/validation_adapter_v6.py"
    spec = importlib.util.spec_from_file_location("pinned_task_adapter", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    manifest = {r["task_id"]: r for r in csv.DictReader((E08 / "expt_v1/results/split/vbv1_split_manifest.csv").open())}
    # The split lists are derived from the manifest's split column (verified identical to the committed id files).
    train_ids = sorted(t for t, r in manifest.items() if r["split"] == "train")
    val_ids = sorted(t for t, r in manifest.items() if r["split"] == "validation")
    test_ids = {t for t, r in manifest.items() if r["split"] == "test"}
    assert len(train_ids) == 539 and len(set(train_ids)) == 539 and len(val_ids) == 135 and len(test_ids) == 222
    assert not (set(train_ids) & test_ids) and not (set(val_ids) & test_ids)
    expected_val = json.loads((E08 / "expt_v3/results/generation_prompt_hashes_v3.json").read_text())
    template = (VB / "vb_harbor/adapter/template/task.toml").read_bytes()

    # Control: the same builder must reproduce every frozen validation prompt hash of experiment 08 v3 (no pack written).
    val_mismatch = []
    for tid in val_ids:
        row = manifest[tid]
        src = (VB / "veribench_dataset/py_src" / row["py_relpath"]).read_text()
        prompt = build_prompt(adapter.generate_instruction(src, Path(row["gold_relpath"]).stem), root=VB)
        actual = {k: getattr(prompt, k) for k in expected_val[tid]}
        if actual != expected_val[tid]:
            val_mismatch.append(tid)
    pack = E20 / "phase0/train_pack"
    pack.mkdir(parents=True, exist_ok=True)
    hashes, bad_source = {}, []
    for tid in train_ids:
        row = manifest[tid]
        assert row["split"] == "train", tid
        data = (VB / "veribench_dataset/py_src" / row["py_relpath"]).read_bytes()
        if sha256(data) != row["py_sha256"]:
            bad_source.append(tid)
            continue
        instruction = adapter.generate_instruction(data.decode("utf-8"), Path(row["gold_relpath"]).stem)
        prompt = build_prompt(instruction, root=VB)
        target = pack / tid
        target.mkdir(exist_ok=True)
        (target / "instruction.md").write_text(instruction)
        (target / "task.toml").write_bytes(template)
        hashes[tid] = {"instruction_sha256": prompt.instruction_sha256, "prompt_sha256": prompt.prompt_sha256,
                       "addendum_sha256": prompt.addendum_sha256, "system_prompt_sha256": prompt.system_prompt_sha256,
                       "required_paths": list(prompt.required_paths), "py_sha256": row["py_sha256"], "group_id": row["group_id"]}
    status = "PASS" if not val_mismatch and not bad_source and len(hashes) == 539 else "BLOCKED"
    out = {"status": status, "train_tasks_packed": len(hashes), "validation_control_mismatches": val_mismatch,
           "train_source_hash_mismatches": bad_source, "pack": str(pack),
           "adapter_sha256": sha256(adapter_path.read_bytes()), "template_sha256": sha256(template),
           "test_split_opened": False, "prompts": hashes}
    (E20 / "phase0/train_pack_manifest.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "prompts"}))
    return 0 if status == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
