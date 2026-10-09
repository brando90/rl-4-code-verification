"""TLDR: Negative controls for experiment09's two-turn reward, feedback, masking and exact-cache contract."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest
from rl4cv.rewards import ScoredResponse

ROOT = Path(__file__).resolve().parents[1] / "experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1"
sys.path.insert(0, str(ROOT))

def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py"); assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod); return mod

env = load("two_turn_env")
queue = load("fsc_queue")

def good(fsc=0.5):
    return ScoredResponse(True, True, 1, 2, 2, fsc=fsc)

def measured(answer):
    return env.MeasuredAnswer(answer, "compile note", "measured")

def test_first_turn_zero_second_turn_only_and_final_file_only(monkeypatch):
    # The pure environment unit test is intentionally independent of whether the
    # optional real NeMo runtime is installed. Separate runtime tests use it.
    monkeypatch.setattr(env, "EnvironmentReturn", None)
    seen = []
    def scorer(meta, text): seen.append(text); return measured(good(0.5))
    subject = env.TwoTurnLeanEnvironment("B", scorer)
    a = subject.step([[{"role":"user","content":"p"},{"role":"assistant","content":"first"}]], [{"rollout_id":"r"}])
    a_meta = a["metadata"][0] if isinstance(a, dict) else a.metadata[0]
    b = subject.step([[{"role":"user","content":"p"},{"role":"assistant","content":"first"},{"role":"user","content":"fb"},{"role":"assistant","content":"final"}]], [a_meta])
    a_rewards = a["rewards"] if isinstance(a, dict) else a.rewards.tolist()
    b_rewards = b["rewards"] if isinstance(b, dict) else b.rewards.tolist()
    b_answers = b["answers"] if isinstance(b, dict) else b.answers
    assert a_rewards == [0.0] and b_rewards == [pytest.approx((0.5)**(1/3))]
    assert seen == ["first", "final"] and b_answers == ["final"]

def test_factor_feedback_is_c_only_and_reward_is_matched():
    m = measured(good(0.5))
    assert env.render_feedback("B", m) == env.render_feedback("A", m)
    assert "IC_tests=" not in env.render_feedback("B", m)
    assert "IC_tests=" in env.render_feedback("C", m)

def test_missing_required_fsc_blocks_instead_of_zero_and_bad_mask_fails():
    missing = measured(ScoredResponse(True, True, 1, 1, 1, fsc=None))
    with pytest.raises(env.RequiredFSCMissing): env.render_feedback("B", missing)
    with pytest.raises(ValueError): env.assert_action_mask(["user", "assistant"], [1, 1])

def test_cache_identity_includes_candidate_and_judge_fingerprint(tmp_path):
    calls = []
    q = queue.FSCQueue(tmp_path, lambda p: calls.append(p) or {"fsc": 0.5}, workers=1)
    base = {"candidate":"a", "reference":"r", "source":"s", "judge_fingerprint":"j1"}
    assert q.request(base).result()["fsc"] == 0.5
    assert q.request(base).result()["fsc"] == 0.5
    assert q.request({**base, "candidate":"b"}).result()["fsc"] == 0.5
    assert q.request({**base, "judge_fingerprint":"j2"}).result()["fsc"] == 0.5
    assert len(calls) == 3
