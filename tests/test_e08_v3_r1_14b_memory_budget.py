"""CPU checks for the 11-27-2026 14B admission budget. No GPU and no outcome files."""
import importlib.util
from pathlib import Path

import pytest

MODULE = Path("experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/r1_14b_memory_budget_11-27-2026.py")
YAML_DIR = MODULE.parent / "configs"


def load():
    spec = importlib.util.spec_from_file_location("r1_budget", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def node(kind_total, free, used=0, util=0, foreign_on=None):
    devices = []
    apps = []
    for i in range(8):
        uuid = f"GPU-{i}"
        devices.append({
            "index": i, "uuid": uuid, "total_mib": kind_total,
            "used_mib": used, "free_mib": free, "utilization": util,
        })
        if foreign_on is not None and i == foreign_on:
            apps.append({"uuid": uuid, "pid": 999, "memory_mib": int(130.69 * 1024)})
            devices[-1]["used_mib"] = int(130.69 * 1024)
            devices[-1]["free_mib"] = kind_total - devices[-1]["used_mib"]
    return {"devices": devices, "apps": apps}


def test_gemma_logits_match_the_smoke_note_and_tp8_does_not():
    budget = load()
    diag = budget.chunked_lm_head_applies()
    assert diag["applies_to_this_oom"] is False
    assert round(diag["gemma3_unsharded_fp32_logits_gib"], 2) == 16.82
    assert diag["qwen3_tp8_fp32_logits_gib_at_16384"] < 2
    assert diag["qwen3_unsharded_fp32_logits_gib_at_16384"] < 10


def test_foreign_130gib_on_skampere3_is_not_admitted_and_a100_is_never_the_fallback():
    budget = load()
    inventories = {
        "skampere3": node(178 * 1024, 178 * 1024, foreign_on=2),
        "skampere2": node(140 * 1024, 100_000),
        "skampere1": node(81920, 80000),
    }
    decision = budget.admit_node(inventories)
    assert decision["admitted"] is False
    assert decision["host"] is None
    assert any("skampere3" in reason and "foreign" in reason for reason in decision["reasons"])
    assert any("skampere1" in reason and "refused" in reason.lower() for reason in decision["reasons"])


def test_clean_b200_node_beats_a_clean_h200_node():
    budget = load()
    inventories = {
        "skampere3": node(180 * 1024, 170 * 1024),
        "skampere2": node(143157, 143157),
    }
    decision = budget.admit_node(inventories)
    assert decision == {
        "admitted": True,
        "host": "skampere3",
        "kind": "B200",
        "gpus": list(range(8)),
        "min_free_mib": 160 * 1024,
        "planning_peak_gib": 73.18,
        "planning_peak_is_upper_bound": False,
        "launch_env": {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"},
        "reasons": [],
    }
    assert budget.planned_command(decision, "E") == [
        "env", "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True",
        "bash", "train_continuation.sh", "E", "14b", "0,1,2,3,4,5,6,7", "production",
    ]


def test_h200_is_second_and_a_busy_b200_does_not_spill_onto_a100():
    budget = load()
    only_h200 = {"skampere2": node(143157, 143157), "skampere1": node(81920, 80000)}
    decision = budget.admit_node(only_h200)
    assert decision["admitted"] is True and decision["host"] == "skampere2"
    busy = {
        "skampere3": node(180 * 1024, 180 * 1024, foreign_on=0),
        "skampere2": node(143157, 143157, foreign_on=4),
        "skampere1": node(81920, 80000),
    }
    refused = budget.admit_node(busy)
    assert refused["admitted"] is False
    with pytest.raises(ValueError, match="admission failed"):
        budget.planned_command(refused, "R")


def test_rungs_and_work_root_match_the_frozen_schedule():
    budget = load()
    assert [row["system"] for row in budget.RUNGS] == [
        "v3_E_14b_f0p5", "v3_E_14b_f1p0", "v3_R_14b_f0p5", "v3_R_14b_f1p0",
    ]
    assert [row["step"] for row in budget.RUNGS] == [335, 667, 334, 658]
    assert budget.MISSING_CELLS == 4320
    assert budget.MEASURED_CELLS_UNTOUCHED == 12960
    assert budget.work_root("skampere3.stanford.edu", "ub9sc") == "/lfs/skampere3/0/ub9sc/rl4cv_e08_v3_r1_14b"
    assert budget.foreign_pids(
        [{"uuid": "GPU-1", "pid": 5}, {"uuid": "GPU-1", "pid": 9}], {5}, {"GPU-1"}) == [9]


def test_locked_14b_yaml_is_unchanged():
    for name in ("e08_v3_E_14B.yaml", "e08_v3_R_14B.yaml"):
        text = (YAML_DIR / name).read_text()
        assert "activation_checkpointing: true" in text
        assert "cpu_offload: false" in text
        assert "train_micro_batch_size: 1" in text
        assert "tensor_parallel_size: 8" in text
        assert "precision: bfloat16" in text
