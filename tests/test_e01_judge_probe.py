# TLDR: Offline checks for experiment 01's G = 8 probe judging: proving-cell selection from scored rows,
# the probe suite's names, and the FSC export that feeds rl4cv.veribench.collect; zero model calls.
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = (REPO / "experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1"
          / "judge_rl4cv_e01.py")
E103_SCRIPTS = (REPO / "external/veribench/experiments"
                / "103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/scripts")
X100_SCRIPTS = (REPO / "external/veribench/experiments"
                / "100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts")


@pytest.fixture(scope="module")
def judge():
    if not (E103_SCRIPTS.is_dir() and X100_SCRIPTS.is_dir()):
        pytest.skip("pinned external/veribench experiments 100/103 not fetched (make external)")
    spec = importlib.util.spec_from_file_location("judge_rl4cv_e01", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(task, k, ic_t, ic_p, status="scored"):
    return {"task_id": task, "sample_idx": k, "status": status, "IC_tests": ic_t, "IC_proofs": ic_p,
            "split": task.split("__", 1)[0], "measured": True, "admitted": True, "truncated": False,
            "generated_tokens": 10, "rewards": {"kernel_binary": 1.0 if ic_t * ic_p == 1 else 0.0}}


def test_probe_cells_are_the_proving_samples_only(judge):
    rows = [_row("a_set__x", 0, 1.0, 1.0), _row("a_set__x", 1, 1.0, 0.0), _row("a_set__x", 2, 0.0, 0.0),
            _row("b_set__y", 5, 1.0, 0.5), _row("c_set__z", 3, 1.0, 1.0, status="unscored"),
            {"task_id": "d_set__w", "sample_idx": 1, "status": "scored", "IC_tests": None, "IC_proofs": None}]
    cells = judge.probe_cells_from_scored("m", rows)
    assert [(c["task_id"], c["sample_idx"]) for c in cells] == [("a_set__x", 0), ("b_set__y", 5)]
    assert cells[0]["item"] == "a_set__x__s0" and cells[1]["item"] == "b_set__y__s5"
    assert cells[1]["IC_proofs"] == 0.5 and cells[0]["model"] == "m"


def test_probe_suite_spec_and_expectations(judge):
    spec = judge.suite_spec("rl4cv-e01-probe:qwen3.5-9b")
    assert spec["benchmark"] == "veribench-rl4cv-e01-probe-qwen3-5-9b"
    assert spec["pack_receipt"].name == "judge_pack_probe_qwen3.5-9b.json"
    assert spec["key_prefix"] == "probe-qwen3.5-9b/" and spec["model"] == "qwen3.5-9b"
    with pytest.raises(AssertionError):
        judge.suite_spec("rl4cv-e01-probe:qwen3-14b", "r23")
    assert judge.PROBE_EXPECTED == {"qwen3.5-9b": 4, "qwen3-14b": 7}
    assert judge.REPEATS_PROBE == (1, 2, 3)
    # the gate and r23 specs are unchanged
    assert judge.suite_spec("rl4cv-e01:qwen3-14b")["benchmark"] == "veribench-rl4cv-e01-qwen3-14b"
    assert judge.suite_spec("rl4cv-e01:qwen3-14b", "r23")["benchmark"] == "veribench-rl4cv-e01-qwen3-14b-r23"


def test_probe_fsc_export_keeps_incomplete_items_unmeasured(judge):
    per_task = {"t__s0": {"task_id": "t", "sample_idx": 0, "FSC": 0.7, "complete": True},
                "t__s3": {"task_id": "t", "sample_idx": 3, "FSC": 0.9, "complete": True},
                "u__s3": {"task_id": "u", "sample_idx": 3, "FSC": 0.4, "complete": False}}
    export = judge.probe_fsc_export(per_task)
    assert export == {0: {"t": 0.7}, 3: {"t": 0.9}}       # u__s3 is absent, so collect leaves it null
