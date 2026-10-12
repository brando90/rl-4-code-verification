"""Verify compile gating, missing evidence and manifest identity in the final test-factor export."""
import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts"
spec = importlib.util.spec_from_file_location("test_receipts_e08", SCRIPTS / "summarize_test_receipts_e08.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def kernel(tests, proofs):
    return {"known": "True", "IC_tests": str(tests), "IC_proofs": str(proofs), "kernel_binary": "0"}


def test_zero_proof_file_retains_coverage_factor():
    r = module.factor_cell(kernel(1, 0), {"FSC": 0.8})
    assert r["fsc_compiled"] == 0.8
    assert r["SCSC_per_cell_diagnostic"] == 0
    assert r["factors_known"]


def test_audit_does_not_bypass_compile_gate():
    r = module.factor_cell(kernel(0, 0), {"FSC": 0.8})
    assert r["FSC_judged"] == 0.8
    assert r["fsc_compiled"] == 0
    assert r["factors_known"]


def test_missing_required_judge_remains_unknown():
    r = module.factor_cell(kernel(1, 1), None)
    assert r["fsc_compiled"] is None
    assert r["SCSC_per_cell_diagnostic"] is None
    assert not r["factors_known"]
    assert module.factor_cell(kernel(0, 0), None)["factors_known"]
    assert not module.factor_cell(None, {"FSC": 0.8})["factors_known"]


def test_duplicate_manifest_identity_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        module.unique([{"task_id": "a"}, {"task_id": "a"}], lambda r: r["task_id"])


def test_rating_sample_and_transport_must_match():
    declaration = {"system": "s", "task_id_vb": "t", "sample_idx": 2, "repeat": 1, "prompt_sha256": "digest"}
    row = {**declaration, "task_id": "rating", "status": "measured", "transport_matches": True,
           "prompt_hash_matches": True, "prompt_sha256_served": "digest", "score_raw": 4, "requests_sent": 1}
    assert module.check_ratings([row], {"rating": declaration})
    with pytest.raises(ValueError, match="identity mismatch"):
        module.check_ratings([{**row, "sample_idx": 3}], {"rating": declaration})
    with pytest.raises(ValueError, match="unverified"):
        module.check_ratings([{**row, "transport_matches": False}], {"rating": declaration})
    with pytest.raises(ValueError, match="extra rating"):
        module.check_ratings([row], {})


def test_teacher_summary_does_not_count_served_errors_as_responses(tmp_path, monkeypatch):
    import json
    import sys
    import types

    teacher_spec = importlib.util.spec_from_file_location("teacher_analysis_e08", SCRIPTS / "analyze_teachers.py")
    teacher = importlib.util.module_from_spec(teacher_spec)
    teacher_spec.loader.exec_module(teacher)
    monkeypatch.setattr(teacher, "EXP", tmp_path)
    template = types.ModuleType("template_check")
    template.load_tokenizers = lambda sizes: {"8B": {"tokenizer": None}}
    monkeypatch.setitem(sys.modules, "template_check", template)
    split = tmp_path / "results/split"
    split.mkdir(parents=True)
    (split / "vbv1_split_manifest.csv").write_text("task_id,family,split\na,easy_set,train\nb,easy_set,train\nc,easy_set,train\n")
    rows = [{"teacher": "astra", "r": "s1", "task_id": task, "served": True,
             "measured": available, "status": status, "kernel_binary": 0,
             "generated_tokens": 10 if available else None,
             "failure_class": "no_typecheck" if available else "no_lean"}
            for task, available, status in [("a", True, "measured"), ("b", True, "incomplete"), ("c", False, "model_error")]]
    scored = tmp_path / "scored.jsonl"
    scored.write_text("".join(json.dumps(row) + "\n" for row in rows))
    out = tmp_path / "summary.json"
    assert teacher.main(["--scored", str(scored), "--job-root", str(tmp_path),
                         "--out", str(out), "--md-out", str(tmp_path / "summary.md")]) == 0
    result = json.loads(out.read_text())["per_run"]["astra/s1"]
    assert result["measured"] == 2
    assert result["unmeasured"] == 537
    assert result["harvested"] == 3
