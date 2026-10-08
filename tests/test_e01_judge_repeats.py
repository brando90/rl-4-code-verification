# TLDR: Offline checks for experiment 01's FSC repeat fix: repeats 2-3 derive byte-identical prompts from
# repeat 1, and median-of-3 aggregation follows experiment 103's missing-repeat rule; zero model calls.
from __future__ import annotations

import hashlib
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


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_repeat_rows_are_byte_identical_and_doubled(judge):
    rendered = {"a__r1": {"system": "SYS", "user": "U-a"}, "b__r1": {"system": "SYS", "user": "U-b"}}
    r1 = [{"cell": f"{it}__r1", "item": it, "task": it, "repeat": 1, "kind": "main",
           "candidate_sha256": _sha(it), "prompt_sha256": _sha("SYS\n\n" + rendered[f"{it}__r1"]["user"])}
          for it in ("a", "b")]
    rows, out = judge.repeat_rows(r1, lambda c: rendered[c], (2, 3))
    assert [r["cell"] for r in rows] == ["a__r2", "a__r3", "b__r2", "b__r3"]
    assert len(rows) == 2 * len(r1)
    for row in rows:
        assert row["repeat"] in (2, 3) and row["kind"] == "main"
        assert out[row["cell"]] == rendered[f"{row['item']}__r1"]          # same bytes
        assert row["prompt_sha256"] == _sha(out[row["cell"]]["system"] + "\n\n" + out[row["cell"]]["user"])


def test_repeat_rows_refuse_a_prompt_hash_mismatch(judge):
    r1 = [{"cell": "a__r1", "item": "a", "task": "a", "repeat": 1, "kind": "main",
           "candidate_sha256": _sha("a"), "prompt_sha256": "0" * 64}]
    with pytest.raises(SystemExit):
        judge.repeat_rows(r1, lambda c: {"system": "SYS", "user": "U"}, (2, 3))


def test_parts_and_suite_spec_for_r23(judge):
    assert judge.PARTS["r23"] == ("cells", "@r23")
    spec = judge.suite_spec("rl4cv-e01:qwen3.5-4b", "r23")
    assert spec["benchmark"] == "veribench-rl4cv-e01-qwen3-5-4b-r23"
    assert spec["pack_receipt"].name == "judge_pack_qwen3.5-4b_r23.json"
    assert spec["key_prefix"] == "qwen3.5-4b/"
    # the repeat-1 spec is unchanged
    assert judge.suite_spec("rl4cv-e01:qwen3.5-4b")["benchmark"] == "veribench-rl4cv-e01-qwen3-5-4b"


def test_aggregate_median3_follows_experiment_103_rule(judge):
    sol, opus = judge.CONFIGS
    members = {sol: {"x": [2, 4, 3], "y": [5, 5, 5], "z": [1, 2, 3], "w": [4]},
               opus: {"x": [1, 1, 5], "y": [4, 4], "z": [], "w": [2, 2, 2]}}
    per_task, incomplete = judge.aggregate_median3(members)
    assert per_task["x"]["FSC"] == pytest.approx((3 + 1) / 2 / 5)       # medians 3 and 1
    assert per_task["x"]["complete"] and per_task["x"]["repeats"] == {sol: 3, opus: 3}
    assert per_task["y"]["FSC"] == pytest.approx((5 + 4) / 2 / 5)       # opus median of 2 repeats
    assert per_task["y"]["complete"]
    assert per_task["z"]["complete"] is False and per_task["z"]["FSC"] == pytest.approx(2 / 5)
    assert per_task["w"]["complete"] and per_task["w"]["FSC"] == pytest.approx((4 + 2) / 2 / 5)
    listed = {row["item"] for row in incomplete}
    assert listed == {"z", "w"}                                          # a member with < 2 repeats; y has 2
    assert "x" not in listed
