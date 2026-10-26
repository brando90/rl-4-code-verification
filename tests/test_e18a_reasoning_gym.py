"""CPU tests for experiment 18a: Reasoning Gym generators and verifiers, GSM8K matcher, metric code and a fake-model end-to-end run."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

E = Path(__file__).resolve().parents[1] / "experiments" / "18_reasoning_gym_generated_env_prerl_scoring_qwen3" / "expt_v1"
sys.path.insert(0, str(E))
import e18a_common as C  # noqa: E402

C.ensure_pycosat()
pytest.importorskip("reasoning_gym")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"e18a_{name}", E / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = _load("build")
generate = _load("generate")
score = _load("score")
embed = _load("embed")
analyze = _load("analyze")
# the scripts put their folder on sys.path; drop it so other experiments' same-named modules (analyze, score) win
sys.path[:] = [p for p in sys.path if Path(p).resolve() != E.resolve()]

from rl4cv.experience import Response, measure_environment  # noqa: E402


# ---------- frozen sets ----------

def test_sets_match_protocol():
    sets = C.all_sets()
    assert len(sets) == 38
    assert [s.set_index for s in sets] == list(range(38))
    assert len({s.set_id for s in sets}) == 38
    envs = [s for s in sets if s.kind == "env"]
    assert len(envs) == 32 and {s.level for s in envs} == {0, 1, 2, 3}
    sets_by = C.sets_by_id()
    assert sets_by["rg/coin_flip/L2"].seed == 20261020 + 10 * 3 + 2
    assert sets_by["rg/syllogism"].seed == 20261123 and sets_by["rg/syllogism"].kind == "target"
    assert sets[-1].set_id == C.GSM8K_ID and sets[-1].sampling_seed == 1037
    train_fams = {f for _, f, _ in C.TRAIN_FAMILIES}
    assert not train_fams & {f for f, _ in C.TARGET_RG}


def test_shards_partition_sets():
    sets = C.all_sets()
    shards = [C.shard_sets(sets, i, 4) for i in range(4)]
    assert sorted(s.set_index for sh in shards for s in sh) == list(range(38))


# ---------- generators and verifiers ----------

@pytest.mark.parametrize("spec", [s for s in C.all_sets() if s.source == "rg"], ids=lambda s: s.set_id)
def test_rg_generator_deterministic_and_gold_passes(spec):
    ds1 = C.rg_dataset(spec, 8)
    ds2 = C.rg_dataset(spec, 8)
    for i in range(8):
        e1, e2 = ds1[i], ds2[i]
        assert e1["question"] == e2["question"]
        assert C.is_pass(ds1.score_answer(C.extract_answer(f"work\n<answer>{e1['answer']}</answer>"), e1))
        assert ds1.score_answer(None, e1) == 0.0


def test_levels_are_distinct_configs():
    for _, fam, _ in C.TRAIN_FAMILIES:
        cfgs = []
        for L in C.LEVELS:
            d = C.rg_config_dict(C.rg_dataset(C.sets_by_id()[f"rg/{fam}/L{L}"], 4))
            d.pop("seed")
            cfgs.append(json.dumps(d, sort_keys=True))
        assert len(set(cfgs)) == 4, fam


def test_wrong_answer_fails_rg():
    spec = C.sets_by_id()["rg/basic_arithmetic/L3"]
    ds = C.rg_dataset(spec, 4)
    e = ds[0]
    assert not C.is_pass(ds.score_answer(str(int(float(e["answer"])) + 1), e))


@pytest.mark.parametrize("text,gold,want", [
    ("so <answer>18</answer>", "18", 1.0),
    ("<answer>$1,234.</answer>", "1234", 1.0),
    ("<answer>The total is 18 dollars</answer>", "18", 1.0),
    ("<answer>18.0</answer>", "18", 1.0),
    ("<answer>-5</answer>", "-5", 1.0),
    ("<answer>17</answer>", "18", 0.0),
    ("the answer is 18", "18", 0.0),
    ("<answer>eighteen</answer>", "18", 0.0),
    ("<answer>3</answer> then <answer>18</answer>", "18", 1.0),
])
def test_gsm8k_exact_numeric_match(text, gold, want):
    assert C.gsm8k_score(C.extract_answer(text), gold) == want


def test_gsm8k_gold_parsing_and_selection():
    assert C.gsm8k_gold("blah\n#### 1,234") == "1234"
    picks = C.gsm8k_select(1319, 256)
    assert len(picks) == 256 and picks == sorted(set(picks)) and picks == C.gsm8k_select(1319, 256)


# ---------- metric code ----------

def test_cell_metrics_equal_measure_environment():
    rows, groups = [], []
    rng = np.random.default_rng(1)
    for i in range(5):
        g = []
        for k in range(4):
            p = float(rng.random() < 0.5)
            tok = int(rng.integers(10, 100))
            capped = k == 3 and i == 0
            rows.append({"item_id": f"x#{i}", "pass": p, "score": p, "generated_tokens": tok, "capped": capped,
                         "has_answer_tag": True})
            g.append(Response(reward=p, generated_tokens=tok, admitted=not capped))
        groups.append(g)
    m = analyze.cell_metrics(rows, 5, 4)
    ref = measure_environment(groups)
    assert m["complete"]
    assert m["rho"] == pytest.approx(ref.rho) and m["H"] == pytest.approx(ref.H)
    assert m["pass_rate"] == pytest.approx(np.mean([r["pass"] for r in rows]))
    lo, hi = m["pass_rate_ci95"]
    assert lo <= m["pass_rate"] <= hi
    assert m["capped_rate"] == pytest.approx(1 / 20)


def test_incomplete_cell_flagged():
    rows = [{"item_id": "a#0", "pass": 1.0, "score": 1.0, "generated_tokens": 5, "capped": False, "has_answer_tag": True},
            {"item_id": "a#0", "pass": 0.0, "score": 0.0, "generated_tokens": 5, "capped": False, "has_answer_tag": True}]
    assert not analyze.cell_metrics(rows, 2, 2)["complete"]


def test_rank_statistics():
    assert analyze.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert analyze.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert list(analyze.rankdata([3, 1, 3, 2])) == [3.5, 1.0, 3.5, 2.0]
    assert analyze.kendalls_w(np.array([[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]])) == pytest.approx(1.0)
    lo, hi = analyze.spearman_ci(list(range(10)), list(range(10)), n_boot=200)
    assert lo == pytest.approx(1.0) and hi == pytest.approx(1.0)


def test_alignment_geometry():
    # two envs, two targets in 2-D: env "a" sits on the target side, env "b" opposite
    ids = ["a", "b", "t1", "t2"]
    cents = np.array([[1.0, 0.0], [-1.0, 0.0], [1.0, 0.2], [1.0, -0.2]])
    out = analyze.alignment_scores(ids, cents, ["a", "b"], ["t1", "t2"])
    assert out["a"]["alignment"] > 0.9 and out["b"]["alignment"] < -0.9
    assert set(out["a"]["alignment_by_target"]) == {"t1", "t2"}


# ---------- fake-model dry run, end to end ----------

def test_fake_end_to_end(tmp_path):
    run = tmp_path / "run"
    gsm = tmp_path / "gsm8k.jsonl"
    with open(gsm, "w") as fh:
        for i in range(12):
            fh.write(json.dumps({"question": f"Ann has {i} apples and buys 3. How many?", "answer": f"...\n#### {i + 3}"}) + "\n")
    assert build.main(["--out", str(run), "--n-items", "6", "--gsm8k-jsonl", str(gsm)]) == 0
    manifest = json.loads((run / "items" / "manifest.json").read_text())
    assert len(manifest["sets"]) == 38 and manifest["rg_version"] == C.RG_VERSION
    for tag in C.MODELS:
        for shard in range(2):
            assert generate.main(["--run", str(run), "--model-tag", tag, "--backend", "fake", "--n", "4",
                                  "--shard", str(shard), "--nshards", "2"]) == 0
        assert score.main(["--run", str(run), "--model-tag", tag]) == 0
        assert embed.main(["--run", str(run), "--model-tag", tag, "--backend", "fake"]) == 0
    # resume: a rerun skips every finished set
    raw = run / "raw" / "qwen3_4b" / "rg__mini_sudoku__L3.jsonl"
    before = raw.stat().st_mtime_ns
    generate.main(["--run", str(run), "--model-tag", "qwen3_4b", "--backend", "fake", "--n", "4"])
    assert raw.stat().st_mtime_ns == before

    # build manifest says group_size 16; the dry run used 4, so patch it for completeness checks
    manifest["group_size"] = 4
    (run / "items" / "manifest.json").write_text(json.dumps(manifest))
    assert analyze.main(["--run", str(run)]) == 0
    res = run / "results"
    envs = [json.loads(line) for line in open(res / "envs_18a.jsonl")]
    tgts = [json.loads(line) for line in open(res / "targets_18a.jsonl")]
    summary = json.loads((res / "summary_18a.json").read_text())
    assert len(envs) == 96 and len(tgts) == 18
    required = {"schema", "env_id", "family", "category", "level", "rg_version", "rg_config", "probe_seed", "n_items",
                "group_size", "model", "model_revision", "model_size_b", "complete", "pass_rate", "pass_rate_ci95",
                "mean_score", "answer_tag_rate", "capped_rate", "frac_items_all_fail", "frac_items_all_pass", "rho",
                "rho_raw", "H", "q_mixed_empirical", "admission_rate", "mean_generated_tokens",
                "total_generated_tokens", "advantage_survival", "token_weighted_coverage", "top_decile_mass_share",
                "n_groups", "n_responses", "mean_reward", "rho_score", "H_score", "alignment", "alignment_by_target",
                "alignment_mid", "in_learnable_band", "format_dominated"}
    for r in envs:
        assert required <= set(r), required - set(r)
        assert r["schema"] == "envs_18a/v1" and r["complete"]
        assert -1.0 <= r["alignment"] <= 1.0 and len(r["alignment_by_target"]) == 6
        assert 0.0 <= r["pass_rate"] <= 1.0
    a1 = summary["analysis1_difficulty_transfer"]
    assert a1["n_envs_all_models"] == 32 and a1["verdict"] in {"transfers", "partial", "fails"}
    assert len(a1["pairwise"]) == 3
    assert summary["incomplete_cells"] == []
    assert all(v["n_families"] == 8 for v in summary["analysis2_within_family"].values())
    # the fake model gets worse with level: mean pass rate over families falls from L0 to L3
    by_level = {L: np.mean([r["pass_rate"] for r in envs if r["level"] == L]) for L in C.LEVELS}
    assert by_level[0] > by_level[3]


def test_fake_smoke_path(tmp_path):
    """The smoke job's exact chain: a few sets, few items, separate *_smoke folders, analyze in smoke mode."""
    run = tmp_path / "run"
    gsm = tmp_path / "gsm8k.jsonl"
    with open(gsm, "w") as fh:
        for i in range(5):
            fh.write(json.dumps({"question": f"What is {i} + 1?", "answer": f"#### {i + 1}"}) + "\n")
    sets = "rg/word_sorting/L3,rg/mini_sudoku/L3,rg/gsm_symbolic,gsm8k/test256"
    assert build.main(["--out", str(run), "--n-items", "4", "--sets", sets, "--gsm8k-jsonl", str(gsm)]) == 0
    tag = "qwen3_4b"
    assert generate.main(["--run", str(run), "--model-tag", tag, "--backend", "fake", "--n", "2", "--limit-items", "3",
                          "--sets", sets, "--out-subdir", "smoke"]) == 0
    assert score.main(["--run", str(run), "--model-tag", tag, "--raw-subdir", "smoke"]) == 0
    assert embed.main(["--run", str(run), "--model-tag", tag, "--backend", "fake", "--limit-items", "3",
                       "--out-subdir", "smoke"]) == 0
    assert analyze.main(["--run", str(run), "--subdir", "smoke", "--smoke-group-size", "2"]) == 0
    envs = [json.loads(line) for line in open(run / "results_smoke" / "envs_18a.jsonl")]
    assert {r["env_id"] for r in envs} == {"rg/word_sorting/L3", "rg/mini_sudoku/L3"}
    assert all(r["complete"] and r["n_responses"] == 6 for r in envs)
    assert not (run / "raw").exists()
