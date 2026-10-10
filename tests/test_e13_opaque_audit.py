"""Typed counterexamples for the sealed E13 base-equality manifest builder."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/opaque_base_audit.py"


def load():
    spec = importlib.util.spec_from_file_location("opaque_audit_test", AUDIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(model: str, task: str = "task", sample: int = 0, extraction: str = "by\n") -> dict:
    return {"model": model, "task_id": task, "sample_idx": sample, "extraction": extraction, "compiles": False,
            "n_examples": 0, "n_theorems_stated": 0, "n_theorems_proved": 0, "truncated": False,
            "rewards": {"kernel_binary": 0.0}}


def fixture(tmp_path: Path, *, replacement: bool = False, duplicate: bool = False):
    scored, jobs = tmp_path / "scores", tmp_path / "jobs"
    scored.mkdir()
    split = tmp_path / "split.csv"
    split.write_text("task_id,group_id,split\ntask,g,train\n")
    for model in ("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base"):
        rows = [row(model)]
        if duplicate:
            rows.append(row(model))
        (scored / f"scored_{model}_g8.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        source = jobs / f"{model}_g8_s0/task/verifier/solution.lean"
        source.parent.mkdir(parents=True)
        actual = "changed\n" if replacement else "by\n"
        source.write_text(actual)
        (source.parent.parent / "config.json").write_text(json.dumps({"model": model}))
        (source.parent.parent / "receipt.json").write_text(json.dumps({"task_id": "task", "sample_idx": 0,
                                                                          "solution_sha256": hashlib.sha256(b"by\n").hexdigest()}))
    return scored, jobs, split


def test_manifest_rejects_replaced_source(tmp_path):
    audit = load(); scored, jobs, split = fixture(tmp_path, replacement=True)
    with pytest.raises(audit.AuditError, match="replaced"):
        audit.build_manifest(scored_dir=scored, jobs_root=jobs, split_manifest=split, private_dir=tmp_path / "private", expected_cells=3)


def test_manifest_rejects_duplicate_cell(tmp_path):
    audit = load(); scored, jobs, split = fixture(tmp_path, duplicate=True)
    with pytest.raises(audit.AuditError, match="duplicate"):
        audit.build_manifest(scored_dir=scored, jobs_root=jobs, split_manifest=split, private_dir=tmp_path / "private", expected_cells=3)


def test_manifest_rejects_missing_denominator(tmp_path):
    audit = load(); scored, jobs, split = fixture(tmp_path)
    with pytest.raises(audit.AuditError, match="denominator"):
        audit.build_manifest(scored_dir=scored, jobs_root=jobs, split_manifest=split, private_dir=tmp_path / "private", expected_cells=4)
