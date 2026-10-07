"""Tests for experiment 02A v3's MBPP rewrite: a known task round-trips through the gate; a task with no callable function is dropped."""

import importlib.util
import sys
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics"
          / "phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/scripts/build_mbpp_tasks.py")


def _mod():
    spec = importlib.util.spec_from_file_location("build_mbpp_tasks", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# MBPP task 511 as stored in the `full` configuration (CRLF line endings in `code`).
ROW_511 = {
    "task_id": 511,
    "text": "Write a python function to find minimum sum of factors of a given number.",
    "code": "def find_Min_Sum(num): \r\n    sum = 0\r\n    i = 2\r\n    while(i * i <= num): \r\n        while(num % i == 0): \r\n            sum += i \r\n            num /= i \r\n        i += 1\r\n    sum += num \r\n    return sum",
    "test_list": ["assert find_Min_Sum(12) == 7", "assert find_Min_Sum(105) == 15", "assert find_Min_Sum(2) == 2"],
    "test_setup_code": "",
    "challenge_test_list": [],
}


def test_known_task_round_trips_through_the_python_gate():
    m = _mod()
    src, info = m.rewrite_task(ROW_511)
    assert info["task_id"] == "mbpp__task_511" and info["lean_stem"] == "task_511" and info["function"] == "find_Min_Sum"
    assert "\r" not in src and src.startswith('"""Write a python function')
    assert "def find_Min_Sum(num):" in src  # MBPP code kept, only line endings normalized
    assert "assert candidate(12) == 7" in src and "assert check(find_Min_Sum)" in src
    gate = m.python_gate(src, sys.executable)
    assert gate["exit_code"] == 0, gate


def test_failing_reference_is_dropped_by_the_gate():
    m = _mod()
    row = dict(ROW_511, test_list=["assert find_Min_Sum(12) == 8"])
    src, _info = m.rewrite_task(row)
    assert m.python_gate(src, sys.executable)["exit_code"] != 0


def test_task_without_callable_function_is_dropped():
    m = _mod()
    row = dict(ROW_511, code="x = 1\r\ny = x + 1\r\n", test_list=["assert y == 2"])
    src, info = m.rewrite_task(row)
    assert src is None and info["dropped"] == "no_top_level_function"
    row2 = dict(ROW_511, code="def f(a):\r\n    return a\r\ndef g(a):\r\n    return a\r\n", test_list=["assert f(1) == 1", "assert g(2) == 2"])
    src2, info2 = m.rewrite_task(row2)
    assert src2 is None and info2["dropped"].startswith("asserts_call_several_top_level_functions")


def test_assert_rename_only_touches_the_reference_function():
    m = _mod()
    assert m.rewrite_assert("assert find_Min_Sum(find_Min_Sum(2)) == 2", "find_Min_Sum") == "assert candidate(candidate(2)) == 2"
    assert m.rewrite_assert("assert my_find_Min_Sum(2) == 2", "find_Min_Sum") == "assert my_find_Min_Sum(2) == 2"


def test_reference_named_check_is_dropped_as_a_harness_collision():
    m = _mod()
    row = dict(ROW_511, code="def check(n):\r\n    return n > 1\r\n", test_list=["assert check(70) == True"])
    src, info = m.rewrite_task(row)
    assert src is None and info["dropped"] == "harness_name_collision:check"
