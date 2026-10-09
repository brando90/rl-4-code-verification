"""TLDR: No silently discarded train-task tail in the fixed cyclic schedule."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/train_schedule_e09.py'
spec = importlib.util.spec_from_file_location('e09_schedule', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_cyclic_schedule_preserves_all_539_and_pairing():
    ids = [f'train_{i}' for i in range(539)]
    rows = mod.schedule(ids, 20261008, 540)
    assert {r['task_id'] for r in rows[:539]} == set(ids)
    assert rows[539]['task_id'] == rows[0]['task_id']
    assert rows == mod.schedule(ids, 20261008, 540)
    assert rows != mod.schedule(ids, 20261009, 540)
    assert len(mod.schedule(ids, 20261008, 32)) == 32
