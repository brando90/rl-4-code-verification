"""Check scientific follow-up identities, strict receipt completeness, and held-out outcome isolation."""

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("e07_followups", Path(__file__).with_name("analyze_followups.py"))
followups = importlib.util.module_from_spec(spec)
spec.loader.exec_module(followups)
control_spec = importlib.util.spec_from_file_location("e07_d_gold_controls", Path(__file__).with_name("d_gold_controls.py"))
controls = importlib.util.module_from_spec(control_spec)
control_spec.loader.exec_module(controls)
prep_spec = importlib.util.spec_from_file_location("e07_prepare", Path(__file__).with_name("prepare_phase_b.py"))
prep = importlib.util.module_from_spec(prep_spec)
prep_spec.loader.exec_module(prep)


def test_decomposition_separates_aggregation_from_actual_partial_credit():
    m = {"fix": np.array([[1, 0.25, 0]]), "keep": np.array([[1, 1, 0]])}
    m.update(score=np.sqrt(m["fix"] * m["keep"]), resolved=np.array([[1, 0, 0]]))
    result = followups.decomposition(m)
    assert result["per_artifact_credit_gap"] == pytest.approx(1 / 6)
    assert result["mean_bias"] == pytest.approx(result["aggregation_gap"] + 1 / 6)
    assert result["task_variance_mean_per_system"]["identity_max_abs_error"] < 1e-14


@pytest.mark.parametrize("mode", ["missing", "duplicate", "bad_score", "unmeasured"])
def test_receipts_cannot_silently_shrink_or_change(mode, tmp_path):
    original, systems, receipts = (tmp_path / p for p in ("original.json", "systems.csv", "receipts.gz"))
    original.write_text(json.dumps({"common_cohort_ids": ["task"]}))
    systems.write_text("submission,included\nsystem,True\n")
    row = {"submission": "system", "instance_id": "task", "gate": 1, "t_fix": 1,
           "t_keep": 1, "score": 1, "resolved": True}
    rows = [row]
    if mode == "missing": rows = []
    if mode == "duplicate": rows = [row, row]
    if mode == "bad_score": row["score"] = 0.5
    if mode == "unmeasured": row["gate"] = None
    with gzip.open(receipts, "wt") as stream:
        stream.write("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError):
        followups.load_matrices(receipts, original, systems)


def test_binary_factors_reduce_every_diagnostic_to_pass1():
    y = np.array([[0, 0, 0, 1], [0, 1, 1, 1], [1, 1, 1, 1]], float)
    result = followups.split_diagnostics({k: y.copy() for k in ("fix", "keep", "score", "resolved")}, splits=8, size=2)
    for method in result["methods"].values():
        assert method["rank_delta_vs_pass1"]["median"] == pytest.approx(0)
    assert result["methods"]["system_smooth"]["mae"] == result["methods"]["pass1"]["mae"]


def test_split_requires_nonempty_heldout_tasks():
    m = {k: np.ones((3, 4)) for k in ("fix", "keep", "score", "resolved")}
    with pytest.raises(ValueError):
        followups.split_diagnostics(m, size=4)


def observation(value):
    return {"kind": "value", "value": value}


def test_d_gold_detects_bug_and_measures_candidate_agreement():
    runs = {"gold": {"a": observation(1), "b": observation(2)},
            "gold_repeat": {"a": observation(1), "b": observation(2)},
            "base": {"a": observation(0), "b": observation(2)},
            "candidate": {"a": observation(1), "b": observation(0)}}
    result = controls.check_task(["a", "b"], runs)
    assert result["controls_pass"] is True
    assert result["d_gold"] == .5


def test_d_gold_cannot_admit_an_input_set_that_does_not_see_bug():
    result = controls.check_task(["a"], {name: {"a": observation(1)} for name in ("gold", "gold_repeat", "base", "candidate")})
    assert result["controls_pass"] is False
    assert result["d_gold"] is None


def test_d_gold_timeout_is_unmeasured_even_when_both_runs_timeout():
    timed_out = {"kind": "timeout"}
    assert controls.same_behavior(timed_out, timed_out) is None
    result = controls.check_task(["a"], {name: {"a": timed_out} for name in ("gold", "gold_repeat", "base", "candidate")})
    assert result["controls_pass"] is None


def test_d_gold_exception_type_not_message_decides_equality():
    assert controls.same_behavior({"kind": "exception", "type": "builtins.ValueError", "message": "a"},
                                  {"kind": "exception", "type": "builtins.ValueError", "message": "b"}) is True
    assert controls.same_behavior({"kind": "exception", "type": "builtins.ValueError"},
                                  {"kind": "exception", "type": "builtins.TypeError"}) is False


def test_d_gold_rejects_missing_inputs_and_nonfinite_values():
    with pytest.raises(ValueError):
        controls.check_task(["a"], {name: {} for name in ("gold", "gold_repeat", "base", "candidate")})
    with pytest.raises(ValueError):
        controls.same_behavior(observation(float("nan")), observation(float("nan")))


def test_d_gold_coverage_keeps_unmeasured_tasks_in_denominator():
    result = controls.admission([str(i) for i in range(731)], {"0": {"controls_pass": True}})
    assert (result["passed"], result["unmeasured"], result["required"]) == (1, 730, 658)
    assert result["admitted"] is False
    assert result["coverage_bounds"] == [1 / 731, 1]


def test_d_gold_controls_do_not_require_candidate_generation():
    runs = {"gold": {"a": observation(1)}, "gold_repeat": {"a": observation(1)},
            "base": {"a": observation(0)}}
    result = controls.check_task(["a"], runs)
    assert result["controls_pass"] is True and result["d_gold"] is None
    runs["candidate"] = {"a": {"kind": "timeout"}}
    result = controls.check_task(["a"], runs)
    assert result["controls_pass"] is True and result["d_gold"] is None


def test_phase_b_manifest_rejects_content_drift_and_duplicate_task_ids():
    with pytest.raises(ValueError, match="content"):
        prep.prepare(b"{}")
    raw = b'{"instance_id":"task"}\n{"instance_id":"task"}\n'
    with pytest.raises(ValueError, match="uniqueness"):
        prep.prepare(raw, expected_sha256=hashlib.sha256(raw).hexdigest(), expected_count=2)
