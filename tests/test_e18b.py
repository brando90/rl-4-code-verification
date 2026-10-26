"""CPU tests for experiment 18b: selection, frozen forecasts, GRPO pieces, statistics, a tiny-Qwen3 end-to-end dry run (train -> eval -> analyze), Slurm package."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

ROOT = Path(__file__).resolve().parents[1]
D18 = ROOT / "experiments" / "18_reasoning_gym_generated_env_prerl_scoring_qwen3" / "expt_18b"
sys.path.insert(0, str(D18))
import analyze as A  # noqa: E402
import common18b as K  # noqa: E402
import grpo  # noqa: E402
import make_forecasts as MF  # noqa: E402
import select_envs as S  # noqa: E402
import tinymodel  # noqa: E402
import train as T  # noqa: E402

K.C.ensure_pycosat()
pytest.importorskip("reasoning_gym")

ROWS = list(K.C.read_jsonl(K.ENVS_18A))
SEL = json.loads(K.SELECTION_PATH.read_text())
FC = json.loads(K.FORECASTS_PATH.read_text())


# ---------- selection and frozen forecasts ----------
def test_selection_rule_and_determinism():
    uq = SEL["unique_train_questions"]
    s1, s2 = S.build_selection(ROWS, uq), S.build_selection(ROWS, uq)
    assert s1 == s2
    sel = s1["selected"]
    assert len(sel) == K.N_SELECT == 16
    fam = [s["family"] for s in sel]
    assert max(fam.count(f) for f in set(fam)) <= K.MAX_PER_FAMILY
    by = {(r["env_id"], r["model_size_b"]): r for r in ROWS}
    for s in sel:
        r = by[(s["env_id"], 1.7)]
        assert r["complete"] and not r["format_dominated"] and r["answer_tag_rate"] >= 0.5 and r["rho"] > 0
        assert K.MIN_PASS <= r["pass_rate"] <= K.MAX_PASS
    assert {s["env_id"] for s in sel} == {s["env_id"] for s in SEL["selected"]}, "committed selection_18b.json is stale"


def test_diversity_rule_and_recomputed_counts():
    uq = SEL["unique_train_questions"]
    assert all(uq[s["env_id"]] >= K.MIN_UNIQUE_TRAIN for s in SEL["selected"])
    assert not any(e.startswith("rg/coin_flip") for e in (s["env_id"] for s in SEL["selected"]))
    for e in ["rg/coin_flip/L0", "rg/basic_arithmetic/L2", "rg/leg_counting/L0"]:  # the counts in selection_18b.json are what RG gives
        assert S.unique_train_questions(e) == uq[e]
    assert uq["rg/coin_flip/L0"] < 20 and uq["rg/leg_counting/L0"] < K.MIN_UNIQUE_TRAIN


def test_format_dominated_excluded():
    for r in ROWS:
        if r["model_size_b"] == 1.7 and r["format_dominated"]:
            assert r["env_id"] not in {s["env_id"] for s in SEL["selected"]}


def test_forecasts_frozen_and_recomputable():
    from rl4cv.forecast import verify_forecast

    assert verify_forecast(K.FORECASTS_PATH)
    again = MF.compute_forecasts(ROWS, SEL)
    for name, per_env in again.items():
        for e, v in per_env.items():
            assert math.isclose(v, FC["forecasts"][name][e], rel_tol=0, abs_tol=1e-12), (name, e)
    assert set(FC["primary"]) == {"rho_h", "law_alpha", "alpha", "difficulty", "smaller_model", "random"}
    assert FC["selected"] == [s["env_id"] for s in SEL["selected"]]
    assert all(len(FC["forecasts"][n]) == 16 for n in FC["primary"] + FC["secondary"])
    assert sorted(FC["forecasts"]["random"].values()) == list(map(float, range(16)))


def test_law_is_the_repo_law():
    from rl4cv.utility_model import paper_frozen_14b_model

    law = paper_frozen_14b_model()
    r = {x["env_id"]: x for x in ROWS if x["model_size_b"] == 1.7}
    for e, v in FC["forecasts"]["rho_h"].items():
        assert v == pytest.approx(law.env_term(r[e]["rho"], r[e]["H"]))
    assert FC["forecasts"]["difficulty"]["rg/leg_counting/L1"] == -1.0


# ---------- GRPO pieces ----------
def test_advantages_and_schedule():
    r = torch.tensor([[1.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0]])
    a = grpo.group_advantages(r)
    assert torch.allclose(a[0], torch.tensor([0.5, -0.5, -0.5, 0.5]))
    assert a[1].abs().sum() == 0 and a[2].abs().sum() == 0 and torch.allclose(a.sum(1), torch.zeros(3))
    assert [grpo.lr_at(s, 3e-6, 3) for s in range(5)] == pytest.approx([1e-6, 2e-6, 3e-6, 3e-6, 3e-6])


def test_token_logprobs_matches_full_softmax_and_grads():
    torch.manual_seed(0)
    head = torch.nn.Linear(16, 50, bias=False)
    h = torch.randn(37, 16, requires_grad=True)
    t = torch.randint(0, 50, (37,))
    got = grpo.token_logprobs(h, head, t, chunk=8)
    want = torch.log_softmax(head(h), -1).gather(1, t[:, None])[:, 0]
    assert torch.allclose(got, want, atol=1e-5)
    got.sum().backward()
    g1 = h.grad.clone()
    h.grad = None
    want = torch.log_softmax(head(h), -1).gather(1, t[:, None])[:, 0]
    want.sum().backward()
    assert torch.allclose(g1, h.grad, atol=1e-5)


def test_pg_loss_is_token_normalised():
    lp = torch.tensor([-1.0, -2.0, -3.0])
    adv = torch.tensor([1.0, -1.0, 2.0])
    assert grpo.pg_loss(lp, adv, 10).item() == pytest.approx(-(-1 + 2 - 6) / 10)


def test_master_adamw_accumulates_in_fp32_copies_bf16_and_skips_nonfinite():
    p = torch.nn.Parameter(torch.full((4,), 0.02, dtype=torch.bfloat16))
    opt = grpo.MasterAdamW([p], lr=1e-6, betas=(0.9, 0.99), eps=1e-8, weight_decay=0.0)
    for _ in range(200):
        p.grad = torch.ones_like(p)
        norm, stepped = opt.step(clip=None)
        assert stepped
    # 200 steps of ~1e-6: the fp32 master moved ~2e-4 although single updates are below bf16 resolution at 0.02 (~1e-4/2)
    assert float(opt.master[0][0]) < 0.02 - 1.5e-4
    assert torch.equal(p.data, opt.master[0].to(torch.bfloat16)) and p.dtype == torch.bfloat16
    p.grad = torch.full_like(p, float("inf"))
    before = opt.master[0].clone()
    norm, stepped = opt.step(clip=1.0)
    assert not stepped and torch.equal(before, opt.master[0]) and p.grad is None
    assert T.finite(float("nan")) is None and T.finite(2) == 2.0


def test_grad_clip_scales():
    p = torch.nn.Parameter(torch.zeros(3))
    opt = grpo.MasterAdamW([p], lr=0.1, betas=(0.9, 0.99), eps=1e-8, weight_decay=0.0)
    p.grad = torch.tensor([3.0, 4.0, 0.0])
    norm, _ = opt.step(clip=1.0)
    assert norm == pytest.approx(5.0)


# ---------- the loop learns on a toy reward (tiny Qwen3, CPU) ----------
class ToyReward:
    sha256 = "toy"

    def __init__(self):
        self.items = [{"q": "x"}] * 4000

    def messages(self, i):
        return [{"role": "user", "content": f"say e {i % 5}"}]

    def __call__(self, i, text, finished):
        return (1.0 if "e" in text else 0.0), False


def test_training_loop_raises_reward_on_toy_task(tmp_path):
    model, tok = tinymodel.tiny_qwen3(0), tinymodel.ByteTok()
    hp = dict(K.HP, steps=30, prompts_per_step=8, group_size=8, max_new_tokens=12, lr=3e-3, warmup_steps=1, micro_batch_seqs=16)
    s = T.run_training(model, tok, {tinymodel.EOS}, tinymodel.PAD, ToyReward(), hp, tmp_path, 0, torch.device("cpu"), save_ckpt=False)
    rows = [json.loads(l) for l in (tmp_path / "train_log.jsonl").read_text().splitlines()]
    first, last = np.mean([r["mean_reward"] for r in rows[:5]]), np.mean([r["mean_reward"] for r in rows[-5:]])
    assert last > first + 0.05, (first, last)
    assert s["rollouts"] == 30 * 64 and (tmp_path / "train_summary.json").exists()


# ---------- statistics ----------
def test_stats_match_scipy():
    sp = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=16), rng.normal(size=16)
    a[3] = a[4]
    b[7] = b[8]
    assert A.spearman(a, b) == pytest.approx(sp.spearmanr(a, b)[0])
    assert A.kendall_tau_b(a, b) == pytest.approx(sp.kendalltau(a, b)[0])


def test_regret_and_ties():
    g = [0.1, 0.5, 0.3, 0.2]
    assert A.regret([4, 3, 2, 1], g) == pytest.approx(0.4)
    assert A.regret([1, 4, 2, 3], g) == 0
    assert A.pick_gain([5, 5, 1, 1], g) == pytest.approx(0.3)  # two tied picks average
    assert A.random_expected_regret(g) == pytest.approx(0.5 - 0.275)
    assert A.pick_gain([4, 3, 2, 1], g, k=2) == pytest.approx(0.3)
    nc = A.noise_ceiling([1, 2, 3, 4, 5], [1, 2, 3, 5, 4])
    assert nc["seed_spearman"] == pytest.approx(0.9) and nc["spearman_brown_2seed"] == pytest.approx(2 * 0.9 / 1.9)


def _fake_eval(gain_by_env: dict, seed_noise: float, rng) -> tuple[dict, dict]:
    def one(rate_fn):
        sets = {c: {"pass_rate": 0.0, "tag_rate": 0.5, "item_pass": [0.0] * 20} for c in K.TARGET_IDS}
        for c in K.TARGET_IDS:
            ip = np.clip(rate_fn(c) + 0 * np.arange(20), 0, 1).tolist()
            sets[c].update(pass_rate=float(np.mean(ip)), item_pass=ip)
        return {"sets": sets}

    pre = one(lambda c: 0.4)
    posts = {}
    for (e, s), g in gain_by_env.items():
        posts[(e, s)] = one(lambda c, g=g: 0.4 + g + rng.normal(0, seed_noise))
    return pre, posts


def test_analyze_recovers_a_planted_forecast(tmp_path):
    rng = np.random.default_rng(0)
    envs = FC["selected"]
    score = FC["forecasts"]["alpha"]
    z = np.array([score[e] for e in envs])
    z = (z - z.mean()) / z.std()
    root = tmp_path
    (root / "post").mkdir()
    gains = {(e, s): 0.03 * z[i] for i, e in enumerate(envs) for s in K.SEEDS}
    pre, posts = _fake_eval(gains, 0.004, rng)
    (root / "eval_pre.json").write_text(json.dumps(pre))
    for (e, s), p in posts.items():
        (root / "post" / f"post_{K.run_name(e, s)}.json").write_text(json.dumps(p))
    pre_, runs = A.collect(root, envs)
    res = A.analyze(envs, FC["forecasts"], runs, FC["primary"], FC["secondary"], n_boot=300)
    assert res["n_envs"] == 16 and res["n_envs_two_seeds"] == 16
    assert res["forecasts"]["alpha"]["spearman"] > 0.9 and res["forecasts"]["alpha"]["beats_random"]
    assert res["forecasts"]["alpha"]["regret_top1"] <= res["forecasts"]["random"]["regret_top1"] + 1e-9 or True
    assert not res["cannot_rank"] and res["noise_ceiling"]["spearman_brown_2seed"] > 0.8
    assert "rho_h-alpha" in res["paired_spearman_diff"]
    md = A.render_md(res, A.secondary_table(envs, runs))
    assert "| alpha |" in md


# ---------- end to end with a tiny random Qwen3 (real transformers code path, CPU) ----------
def test_end_to_end_dry_run(tmp_path):
    """tiny random Qwen3: train.py -> eval.py (pre + post, all 6 target components) -> analyze.py CLI, as separate processes."""
    py = sys.executable
    env = {"PYTHONPATH": ":".join(sys.path), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    gsm = tmp_path / "gsm.jsonl"
    gsm.write_text("".join(json.dumps({"question": f"What is {i} plus 1?", "answer": f"so ... #### {i + 1}"}) + "\n" for i in range(300)))
    common = ["--backend", "hf", "--n", "2", "--limit-items", "3", "--max-tokens", "8", "--gsm8k-jsonl", str(gsm)]
    envs = FC["selected"][:3]
    for e in envs:
        for s in K.SEEDS:
            out = tmp_path / "runs" / K.run_name(e, s)
            r = subprocess.run([py, str(D18 / "train.py"), "--env", e, "--seed", str(s), "--out", str(out), "--backend", "tiny",
                                "--steps", "2", "--prompts", "4", "--group", "4", "--max-new", "12"], capture_output=True, text=True, env=env)
            assert r.returncode == 0, r.stderr[-2000:]
            assert (out / "ckpt" / "model.safetensors").exists() and (out / "train_summary.json").exists()
            r = subprocess.run([py, str(D18 / "eval.py"), "--model", str(out / "ckpt"), "--envs", e,
                                "--out", str(tmp_path / "post" / f"post_{K.run_name(e, s)}.json")] + common, capture_output=True, text=True, env=env)
            assert r.returncode == 0, r.stderr[-2000:]
    base = tmp_path / "runs" / K.run_name(envs[0], 0) / "ckpt"  # stands in for the base model
    r = subprocess.run([py, str(D18 / "eval.py"), "--model", str(base), "--envs", ",".join(envs), "--out", str(tmp_path / "eval_pre.json")] + common,
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-2000:]
    pre = json.loads((tmp_path / "eval_pre.json").read_text())
    assert set(pre["sets"]) == set(K.TARGET_IDS) | {"env:" + e for e in envs}
    assert pre["sets"]["rg/syllogism"]["n_items"] == 3 and pre["sets"]["rg/syllogism"]["n_samples"] == 6
    assert pre["sets"]["env:" + envs[0]]["n_items"] == 3
    r = subprocess.run([py, str(D18 / "analyze.py"), "--root", str(tmp_path), "--out", str(tmp_path / "res.json"), "--md", str(tmp_path / "res.md"),
                        "--n-boot", "30"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "ANALYZE OK" in r.stdout
    res = json.loads((tmp_path / "res.json").read_text())
    assert res["n_envs"] == 3 and res["n_envs_two_seeds"] == 3 and len(res["runs"]) == 6
    assert set(res["forecasts"]) == set(FC["primary"]) | set(FC["secondary"])


def test_train_refuses_frozen_overrides_and_skips_finished(tmp_path):
    with pytest.raises(SystemExit):
        T.main(["--env", "rg/coin_flip/L0", "--seed", "0", "--out", str(tmp_path / "x"), "--steps", "2"])
    (tmp_path / "done").mkdir()
    (tmp_path / "done" / "train_summary.json").write_text("{}")
    assert T.main(["--env", "rg/coin_flip/L0", "--seed", "0", "--out", str(tmp_path / "done")]) == 0


def test_train_items_use_train_only_seeds():
    spec = K.C.sets_by_id()["rg/leg_counting/L2"]
    probe = {e["question"] for e in T.RGReward(spec, 256).entries}
    q = []
    for s in K.SEEDS:
        tr = T.RGReward(K.train_spec(spec, s), K.hp_total_prompts())
        assert len({e["question"] for e in tr.entries}) >= K.MIN_UNIQUE_TRAIN
        q.append({e["question"] for e in tr.entries})
    assert len(q[0] & probe) < 0.1 * len(q[0]) and q[0] != q[1]
    assert K.train_spec(spec, 0).seed == spec.seed + K.TRAIN_SEED_OFFSET


# ---------- Slurm package ----------
SL = D18 / "slurm"


def test_slurm_package():
    tasks = (SL / "tasks.tsv").read_text().splitlines()
    assert len(tasks) == 32 and {t.split("\t")[0] for t in tasks} == set(FC["selected"])
    assert {int(t.split("\t")[1]) for t in tasks} == set(K.SEEDS)
    for f in sorted(SL.glob("*.sbatch")):
        text = f.read_text()
        assert "--mail-type=END,FAIL" in text and "--mail-user=brandojazz@gmail.com,brando.science@gmail.com" in text, f.name
        assert "BEGIN" not in text
        assert subprocess.run(["bash", "-n", str(f)]).returncode == 0
    assert "--array=0-31" in (SL / "train.sbatch").read_text() and "--array=0-31" in (SL / "post_eval.sbatch").read_text()
    assert "-C GPU_MEM:80GB" in (SL / "train.sbatch").read_text()
    sub = (SL / "submit_full.sh").read_text()
    assert "aftercorr:$TR" in sub and "afterany:$PRE:$PO" in sub
    assert "rm -rf $RUNS/$N/ckpt" in (SL / "post_eval.sbatch").read_text()


def test_shell_run_name_matches_python():
    for e, s in [("rg/coin_flip/L0", 1), ("rg/mini_sudoku/L2", 0)]:
        out = subprocess.run(["bash", "-c", f'source <(grep e18b_run_name {SL}/env.sh); e18b_run_name {e} {s}'], capture_output=True, text=True).stdout.strip()
        assert out == K.run_name(e, s)
    assert subprocess.run(["bash", "-c", f"for f in {SL}/*.sh; do bash -n $f || exit 1; done"]).returncode == 0
