"""Check that the continuation audit cannot hide incomplete or malformed validation groups."""
import importlib.util
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/prepare_continuation.py"
spec = importlib.util.spec_from_file_location("sft_continuation_audit", PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def row(task="a", **changes):
    return dict(task_id=task, samples_known="8", k_kernel_binary="2", mixed="1",
                k_ic_tests="2", k_extracted="8", k_capped="0", **changes)


def test_task_identity_and_order():
    assert [r["task_id"] for r in audit.validate_rows([row("b"), row("a")], {"a", "b"})] == ["a", "b"]
    for rows in ([row(), row()], [row("b")], []):
        with pytest.raises(ValueError, match="manifest"):
            audit.validate_rows(rows, {"a"})


@pytest.mark.parametrize("key,value", [("samples_known", "7"), ("k_kernel_binary", "9"), ("mixed", "0")])
def test_incomplete_or_inconsistent_groups_fail(key, value):
    sample = row()
    sample[key] = value
    with pytest.raises(ValueError):
        audit.validate_rows([sample], {"a"})


def test_paired_estimate_retains_task_pairing():
    indices = audit.np.array([[0, 1], [1, 0]])
    result = audit.estimate([0.125, -0.125], indices)
    assert result == {"mean": 0.0, "ci95": [0.0, 0.0], "p_value": None}
