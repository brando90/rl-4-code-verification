"""Lean-backed counterexamples for the Experiment 13 declaration adapter."""
from pathlib import Path
import importlib.util
import os
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/declaration_adapter.py"
SPEC = importlib.util.spec_from_file_location("e13_declaration_adapter", ADAPTER_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules["e13_declaration_adapter"] = ADAPTER
SPEC.loader.exec_module(ADAPTER)
AdapterError = ADAPTER.AdapterError
inspect_source = ADAPTER.inspect_source
sha256 = ADAPTER.sha256


# Integration prerequisites: the frozen fixture directory, the pinned scorer checkout and the pinned
# Lean v4.22.0 + Mathlib project. Defaults are the skampere1 paths; override them with E13_* variables.
CONTROLS = Path(os.environ.get(
    "E13_CONTROLS_DIR", "/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls"))
SCORER = Path(os.environ.get(
    "E13_SCORER_ROOT", "/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench_scorer"))
LAKE = Path(os.environ.get("E13_LAKE_DIR", "/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src"))

_MISSING = [f"{var}={path}" for var, path in (
    ("E13_CONTROLS_DIR", CONTROLS / "fixtures"), ("E13_SCORER_ROOT", SCORER), ("E13_LAKE_DIR", LAKE))
    if not path.exists()]
if _MISSING and os.environ.get("E13_REQUIRE_LEAN_INTEGRATION") == "1":
    raise RuntimeError("E13_REQUIRE_LEAN_INTEGRATION=1 but Lean integration prerequisites are absent: "
                       + ", ".join(_MISSING))
pytestmark = pytest.mark.skipif(
    bool(_MISSING),
    reason=("Lean integration prerequisites absent (" + ", ".join(_MISSING) + "); set the E13_* paths, "
            "and set E13_REQUIRE_LEAN_INTEGRATION=1 on the pinned host so absence fails instead of skipping"))


def inspect(name: str):
    path = CONTROLS / "fixtures" / f"{name}.lean"
    return inspect_source(path, lake_dir=LAKE, scorer_root=SCORER, expected_sha256=sha256(path))


def test_parser_spans_and_kernel_cones_use_real_pinned_lean():
    result = inspect("valid")
    assert result["strict"] == result["factored_reward"] == 1
    assert result["theorems"] == ["good"]
    assert result["p"] == {"numerator": 1, "denominator": 1}


@pytest.mark.parametrize("name", ["helper_sorry", "native_theorem", "declared_axiom", "failed_then_valid"])
def test_theorem_dependency_controls_reject_nonhonest_cones(name: str):
    result = inspect(name)
    assert result["strict"] == 0
    assert result["p"]["numerator"] == 0


def test_source_hash_and_malformed_source_are_rejected():
    valid = CONTROLS / "fixtures" / "valid.lean"
    with pytest.raises(AdapterError, match="source hash mismatch"):
        inspect_source(valid, lake_dir=LAKE, scorer_root=SCORER, expected_sha256="0" * 64)
    with pytest.raises(AdapterError, match="malformed source"):
        inspect("truncated_syntax")


def test_namespaces_attributes_multiline_and_duplicate_identity_controls(tmp_path):
    source = tmp_path / "namespaced.lean"
    source.write_text("import Mathlib\n/- nested /- comments -/ do not create declarations -/\nnamespace Outer\n@[simp] theorem first\n    : 1 + 1 = 2 := by norm_num\nnamespace Inner\ntheorem second : 2 + 2 = 4 := by norm_num\nend Inner\nend Outer\n", encoding="utf-8")
    result = inspect_source(source, lake_dir=LAKE, scorer_root=SCORER, expected_sha256=sha256(source))
    assert result["theorems"] == ["Outer.first", "Outer.Inner.second"]
    duplicate = tmp_path / "duplicate.lean"
    duplicate.write_text("import Mathlib\ntheorem same : True := by trivial\ntheorem same : True := by trivial\n", encoding="utf-8")
    with pytest.raises(AdapterError, match="duplicate"):
        inspect_source(duplicate, lake_dir=LAKE, scorer_root=SCORER, expected_sha256=sha256(duplicate))
