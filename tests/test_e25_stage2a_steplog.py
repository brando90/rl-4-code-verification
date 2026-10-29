"""Stage 2a of the checkpoint-reuse plan: constant/cosine learning rate, per-step rollout records for rolling rho/H, checkpoint keep-all checks."""
import importlib.util
import json
import math
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "experiments/25_checkpoint_reuse_for_rho_h_law/stage2a/steplog.py"
spec = importlib.util.spec_from_file_location("steplog", SOURCE)
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)


def test_ckpt_steps_are_the_02b_ladder():
    assert sl.CKPT_STEPS == (16, 32, 48, 64, 96, 128)


def test_lr_constant_and_cosine():
    assert sl.lr_at(1, 1e-6, "constant", 128) == 1e-6
    assert sl.lr_at(128, 1e-6, "constant", 128) == 1e-6
    assert sl.lr_at(1, 1e-6, "cosine", 400) == pytest.approx(1e-6)  # first update uses the full rate
    assert sl.lr_at(201, 1e-6, "cosine", 400) == pytest.approx(0.5e-6)  # t = 200 = T/2
    assert sl.lr_fraction_after(400, "cosine", 400) == pytest.approx(0.0, abs=1e-12)
    assert sl.lr_fraction_after(16, "constant", 128) == 1.0
    with pytest.raises(ValueError):
        sl.lr_at(1, 1e-6, "linear", 128)


def rec(update, successes, G=8):
    rewards = [[1.0] * s + [0.0] * (G - s) for s in successes]
    smooth = [[min(1.0, 0.1 + 0.9 * x) for x in row] for row in rewards]
    tokens = [[100 + i for i in range(G)] for _ in successes]
    return sl.build_step_record(update, [f"t{update}_{i}" for i in range(len(successes))], rewards, smooth, tokens, lr=1e-6, lr_fraction=1.0)


def test_step_record_admitted_and_advantage():
    r = rec(3, [0, 3, 8, 5])
    assert [g["admitted"] for g in r["groups"]] == [False, True, False, True]
    assert [g["strict_successes"] for g in r["groups"]] == [0, 3, 8, 5]
    assert all(a == 0.0 for a in r["groups"][0]["advantages"]) and all(a == 0.0 for a in r["groups"][2]["advantages"])
    adv = r["groups"][1]["advantages"]
    assert sum(adv) == pytest.approx(0.0, abs=1e-9) and adv[0] > 0 > adv[-1]
    assert r["n_groups"] == 4 and r["n_admitted"] == 2 and r["tokens"] == 4 * sum(100 + i for i in range(8))
    json.dumps(r)


def test_step_record_rejects_ragged_input():
    with pytest.raises(ValueError):
        sl.build_step_record(1, ["a"], [[1.0] * 8], [[1.0] * 8], [[5] * 7], lr=1e-6, lr_fraction=1.0)


def write_steps(path, n, skip=()):
    with path.open("w") as fh:
        for u in range(1, n + 1):
            if u not in skip:
                fh.write(json.dumps(rec(u, [2, 4])) + "\n")


def test_window_groups_takes_the_25_steps_before_a_checkpoint(tmp_path):
    p = tmp_path / "steplog.jsonl"
    write_steps(p, 48)
    g = sl.window_groups(p, upto=48, window=25)
    assert len(g) == 25 * 2 and g[0]["update"] == 24 and g[-1]["update"] == 48
    g16 = sl.window_groups(p, upto=16, window=25)  # fewer than 25 steps exist before step 16
    assert len(g16) == 16 * 2 and g16[0]["update"] == 1


def test_window_groups_refuses_a_gap(tmp_path):
    p = tmp_path / "steplog.jsonl"
    write_steps(p, 30, skip={20})
    with pytest.raises(ValueError, match="missing step"):
        sl.window_groups(p, upto=30, window=25)


def make_run(tmp_path, steps, done=True, weights=True):
    run = tmp_path / "A_s0"
    for s in steps:
        d = run / f"ckpt_u{s:03d}"
        (d / "model").mkdir(parents=True)
        if weights:
            (d / "model" / "model.safetensors").write_bytes(b"x")
        if done:
            (d / "DONE").write_text("t\n")
    return run


def test_check_checkpoints_keep_all(tmp_path):
    run = make_run(tmp_path, sl.CKPT_STEPS)
    assert sl.check_checkpoints(run, sl.CKPT_STEPS) == {"present": list(sl.CKPT_STEPS), "missing": [], "incomplete": []}
    run2 = make_run(tmp_path / "b", [16, 32, 48], done=True)
    r = sl.check_checkpoints(run2, sl.CKPT_STEPS)
    assert r["missing"] == [64, 96, 128]
    run3 = make_run(tmp_path / "c", [16], weights=False)
    assert sl.check_checkpoints(run3, [16])["incomplete"] == [16]
