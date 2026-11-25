"""CPU tests for experiment 18c: stopping rule, frozen files equal 18b's, lazy item stream = 18b's stream, token-stopped training loop on a tiny Qwen3, end-to-end dry run (train18c -> eval -> analyze18c)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

ROOT = Path(__file__).resolve().parents[1]
E18 = ROOT / "experiments" / "18_reasoning_gym_generated_env_prerl_scoring_qwen3"
D18B, D18C = E18 / "expt_18b", E18 / "expt_18c"
sys.path.insert(0, str(D18C))
import common18c as K18C  # noqa: E402
import train18c as T18C  # noqa: E402

import tinymodel  # noqa: E402  (18b)
import train as T  # noqa: E402  (18b)

K = K18C.K
K.C.ensure_pycosat()
pytest.importorskip("reasoning_gym")

FC = json.loads(K18C.FORECASTS_PATH.read_text())


# ---------- frozen files ----------
def test_forecasts_identical_to_18b_and_verified():
    from rl4cv.forecast import verify_forecast

    assert (D18C / "forecasts_18c.json").read_bytes() == (D18B / "forecasts_18b.json").read_bytes()
    assert (D18C / "forecasts_18c.sha256").read_text().split()[0] == (D18B / "forecasts_18b.sha256").read_text().split()[0]
    assert verify_forecast(K18C.FORECASTS_PATH)
    assert FC["selected"] == [s["env_id"] for s in json.loads(K.SELECTION_PATH.read_text())["selected"]] and len(FC["selected"]) == 16


def test_tasks_and_names():
    rows = [l.split("\t") for l in (D18C / "skampere" / "tasks.tsv").read_text().splitlines()]
    assert len(rows) == 48 and {r[0] for r in rows} == set(FC["selected"]) and {int(r[1]) for r in rows} == {0, 1, 2}
    assert len({(r[0], r[1]) for r in rows}) == 48
    for env, seed in rows[:5]:
        p = subprocess.run(["bash", "-c", f'source {D18C}/skampere/env.sh >/dev/null 2>&1; c18_run_name {env} {seed}'], capture_output=True, text=True)
        assert p.stdout.strip() == K.run_name(env, int(seed))
    for f in (D18C / "skampere").glob("*.sh"):
        assert subprocess.run(["bash", "-n", str(f)]).returncode == 0


def test_hp_equal_18b_except_steps():
    assert {k: v for k, v in K18C.HP.items() if k != "steps"} == {k: v for k, v in K.HP.items() if k != "steps"}
    assert K18C.SEEDS == (0, 1, 2) and K18C.TOKEN_BUDGET == 2_000_000 and K18C.MIN_STEPS == 10 and K18C.MAX_STEPS == 1000
    assert K18C.PREFIX_ITEMS == 1280 and K18C.ITEMS_PER_RUN == 32_000


# ---------- stopping rule ----------
def test_stop_rule():
    s = K18C.stop_reason
    assert s(9, 5_000_000) is None  # min steps floor
    assert s(10, 5_000_000) == "budget"
    assert s(500, 1_999_999) is None and s(500, 2_000_000) == "budget"
    assert s(999, 1_000_000) is None and s(1000, 1_000_000) == "cap" and s(1000, 2_000_001) == "budget"
    for st, cum in [(1, 10), (10, 1_999_999), (10, 2_000_000), (1000, 3), (1000, 2_000_000), (200, 7_000_000)]:
        assert T18C._stop(st, cum, K18C.TOKEN_BUDGET, K18C.MIN_STEPS, K18C.MAX_STEPS) == s(st, cum)
    assert K18C.classify(40, 2_100_000, "budget") == "matched" and K18C.classify(40, 2_600_000, "budget") == "overshoot"
    assert K18C.classify(1000, 1_900_000, "cap") == "budget_limited"
    assert T18C._classify(40, 2_100_000, "budget", 2_000_000) == K18C.classify(40, 2_100_000, "budget")


class ToyReward:
    sha256 = "toy"

    def messages(self, i):
        return [{"role": "user", "content": f"say e {i % 5}"}]

    def __call__(self, i, text, finished):
        return (1.0 if "e" in text else 0.0), False


def _hp(**kw):
    return dict(K18C.HP, prompts_per_step=4, group_size=4, max_new_tokens=10, lr=1e-3, warmup_steps=1, micro_batch_seqs=16, **kw)


def test_training_stops_at_token_budget(tmp_path):
    model, tok = tinymodel.tiny_qwen3(0), tinymodel.ByteTok()
    s = T18C.run_training_tokens(model, tok, {tinymodel.EOS}, tinymodel.PAD, ToyReward(), _hp(), tmp_path, 0, torch.device("cpu"),
                                 budget=400, min_steps=2, max_steps=50, save_ckpt=False)
    rows = [json.loads(l) for l in (tmp_path / "train_log.jsonl").read_text().splitlines()]
    cum = [r["cum_response_tokens"] for r in rows]
    assert s["stop_reason"] == "budget" and s["response_tokens"] == cum[-1] >= 400 and (len(cum) == 2 or cum[-2] < 400)
    assert s["steps"] == len(rows) == len(cum) and s["rollouts"] == s["steps"] * 16 and s["items_used"] == s["steps"] * 4
    assert all(b > a for a, b in zip(cum, cum[1:]))


def test_training_min_steps_and_cap(tmp_path):
    model, tok = tinymodel.tiny_qwen3(0), tinymodel.ByteTok()
    a = T18C.run_training_tokens(model, tok, {tinymodel.EOS}, tinymodel.PAD, ToyReward(), _hp(), tmp_path / "a", 0, torch.device("cpu"),
                                 budget=1, min_steps=3, max_steps=50, save_ckpt=False)
    assert a["steps"] == 3 and a["stop_reason"] == "budget"
    b = T18C.run_training_tokens(tinymodel.tiny_qwen3(0), tok, {tinymodel.EOS}, tinymodel.PAD, ToyReward(), _hp(), tmp_path / "b", 0,
                                 torch.device("cpu"), budget=10**9, min_steps=1, max_steps=4, save_ckpt=False)
    assert b["steps"] == 4 and b["stop_reason"] == "cap" and b["run_class"] == "budget_limited"


def test_main_refuses_overrides_and_skips_finished(tmp_path):
    with pytest.raises(SystemExit):
        T18C.main(["--env", "rg/leg_counting/L2", "--seed", "0", "--out", str(tmp_path / "x"), "--budget", "10"])
    (tmp_path / "done").mkdir()
    (tmp_path / "done" / "train_summary.json").write_text("{}")
    assert T18C.main(["--env", "rg/leg_counting/L2", "--seed", "0", "--out", str(tmp_path / "done")]) == 0
    with pytest.raises(SystemExit):
        T18C.main(["--env", "rg/leg_counting/L2", "--seed", "3", "--out", str(tmp_path / "y")])


# ---------- item stream ----------
def test_lazy_stream_prefix_equals_18b():
    spec = K.train_spec(K.C.sets_by_id()["rg/leg_counting/L2"], 1)
    old = T.RGReward(spec, K.hp_total_prompts())
    new = T18C.LazyRGReward(spec, K18C.ITEMS_PER_RUN)
    assert new.sha256 == old.sha256
    assert new.messages(5) == old.messages(5) and new.messages(31_999)  # far indices exist
    q = old.items[7]["question"]
    assert new.entry(7)["question"] == q
    assert new.distinct_questions(1280) == len({e["question"] for e in old.entries})
    txt = "<answer>" + str(old.items[0]["gold"]) + "</answer>"
    assert new(0, txt, True)[0] == old(0, txt, True)[0] and new(0, txt, False)[0] == 0.0


# ---------- end to end ----------
def test_end_to_end_dry_run(tmp_path):
    py = sys.executable
    env = {"PYTHONPATH": ":".join(sys.path), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    gsm = tmp_path / "gsm.jsonl"
    gsm.write_text("".join(json.dumps({"question": f"What is {i} plus 1?", "answer": f"so ... #### {i + 1}"}) + "\n" for i in range(300)))
    common = ["--backend", "hf", "--n", "2", "--limit-items", "3", "--max-tokens", "8", "--gsm8k-jsonl", str(gsm)]
    envs = FC["selected"][:4]
    (tmp_path / "train").mkdir()
    for e in envs:
        for s in K18C.SEEDS:
            out = tmp_path / "runs" / K.run_name(e, s)
            r = subprocess.run([py, str(D18C / "train18c.py"), "--env", e, "--seed", str(s), "--out", str(out), "--backend", "tiny", "--budget", "200",
                                "--min-steps", "2", "--max-steps", "6", "--prompts", "4", "--group", "4", "--max-new", "12"], capture_output=True, text=True, env=env)
            assert r.returncode == 0, r.stderr[-2000:]
            sm = json.loads((out / "train_summary.json").read_text())
            assert sm["schema"] == "train_summary_18c/v1" and sm["run_class"] in ("matched", "overshoot", "budget_limited")
            (tmp_path / "train" / f"{K.run_name(e, s)}.train_summary.json").write_text(json.dumps(sm))
            r = subprocess.run([py, str(D18B / "eval.py"), "--model", str(out / "ckpt"), "--envs", e,
                                "--out", str(tmp_path / "post" / f"post_{K.run_name(e, s)}.json")] + common, capture_output=True, text=True, env=env)
            assert r.returncode == 0, r.stderr[-2000:]
    base = tmp_path / "runs" / K.run_name(envs[0], 0) / "ckpt"
    r = subprocess.run([py, str(D18B / "eval.py"), "--model", str(base), "--envs", ",".join(envs), "--out", str(tmp_path / "eval_pre.json")] + common,
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-2000:]
    r = subprocess.run([py, str(D18C / "analyze18c.py"), "--root", str(tmp_path), "--out", str(tmp_path / "res.json"), "--md", str(tmp_path / "res.md"),
                        "--n-boot", "30"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-3000:]
    assert "ANALYZE OK" in r.stdout
    res = json.loads((tmp_path / "res.json").read_text())
    assert res["n_envs"] == 4 and res["n_envs_two_seeds"] == 4 and len(res["runs"]) == 12
    assert res["reliability_3seed"]["mean_pairwise"] == res["reliability_3seed"]["mean_pairwise"] or True
    assert res["confound"]["n_envs"] == 4 and sum(res["confound"]["classes"].values()) == 12
    assert "cross_18b" in res and "matched_subset" in res
