"""Tests for experiment 02A v3's analysis helpers: Wilson intervals, the locked decision rule, and the scorer adapter's theorem-type extraction and failure classification."""

import importlib.util
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1] / "experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics"
           / "phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/scripts")


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_wilson_interval_matches_known_values():
    a = _mod("analyze_v3")
    lo, hi = a.wilson(0, 10)
    assert lo == 0.0 and 0.27 < hi < 0.31
    lo, hi = a.wilson(50, 100)
    assert 0.40 < lo < 0.41 and 0.59 < hi < 0.60
    assert a.wilson(0, 0)[0] != a.wilson(0, 0)[0]  # nan when nothing was measured


def test_decision_rule_thresholds():
    a = _mod("analyze_v3")
    assert a.verdict_of(1024, 512) == "SUFFICIENT"
    assert a.verdict_of(1024, 511) == "PARTIAL"
    assert a.verdict_of(1023, 600) == "PARTIAL"
    assert a.verdict_of(300, 300) == "PARTIAL"
    assert a.verdict_of(299, 299) == "INSUFFICIENT"


def test_theorem_type_extraction_and_vacuity():
    s = _mod("score_teacher_files")
    assert s._theorem_type("theorem foo (n : Nat) : n + 0 = n := by simp") == "n + 0 = n"
    assert s._theorem_type("theorem t : True := trivial") == "True"
    assert s._theorem_type("theorem bar {α : Type} (xs : List α) : (xs ++ []).length = xs.length :=\n  by simp") == "(xs ++ []).length = xs.length"
    from rl4cv.rewards import is_vacuous_statement
    assert is_vacuous_statement(s._theorem_type("theorem t : True := trivial"))
    assert is_vacuous_statement(s._theorem_type("theorem r (x : Nat) : x = x := rfl"))
    assert not is_vacuous_statement(s._theorem_type("theorem foo (n : Nat) : n + 0 = n := by simp"))


def test_failure_classification_order():
    s = _mod("score_teacher_files")
    served = {"served": True, "lean": "import Mathlib\n"}
    assert s.classify({"served": False, "lean": None}, None, 0) == "unmeasured"
    assert s.classify({"served": True, "lean": ""}, None, 0) == "no_lean"
    assert s.classify(served, {"agent_compiles": "False"}, 0) == "no_typecheck"
    assert s.classify(served, {"agent_compiles": "True", "agent_n_ex": "0"}, 0) == "no_example"
    assert s.classify(served, {"agent_compiles": "True", "agent_n_ex": "2", "kernel_n_theorems": "0"}, 0) == "no_theorem"
    row = {"agent_compiles": "True", "agent_n_ex": "2", "kernel_n_theorems": "3", "kernel_n_honest": "3", "kernel_n_native_decide": "0", "kernel_n_declared_axiom": "0"}
    assert s.classify(served, row, 0) == "kept"
    assert s.classify(served, dict(row, kernel_n_honest="2"), 0) == "unproved_theorem"
    assert s.classify(served, dict(row, kernel_n_native_decide="1"), 0) == "forbidden_axiom"
    assert s.classify(served, row, 1) == "vacuous_theorem"
