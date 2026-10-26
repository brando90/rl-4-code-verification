"""CPU tests for experiment 18a v2 (wide): frozen family list and probe rules, generators and verifiers of every included
environment, metric and analysis code (size transfer, the 8-family comparison) and a fake-model end-to-end run."""

import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest

E = Path(__file__).resolve().parents[1] / "experiments" / "18_reasoning_gym_generated_env_prerl_scoring_qwen3" / "expt_v2_wide"
sys.path.insert(0, str(E))
import e18v2_common as C  # noqa: E402

C.ensure_pycosat()
pytest.importorskip("reasoning_gym")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"e18v2_{name}", E / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = _load("build")
generate = _load("generate")
score = _load("score")
embed = _load("embed")
analyze = _load("analyze")
probe = _load("probe_families")
# the scripts put their folder on sys.path; drop it so other experiments' same-named modules (analyze, score) win
sys.path[:] = [p for p in sys.path if Path(p).resolve() != E.resolve()]

from rl4cv.experience import Response, measure_environment  # noqa: E402

FAMS = C.load_families()
SETS = C.all_sets()
ENVS = [s for s in SETS if s.kind == "env"]
PROBE = {r["env_id"]: r for r in C.read_jsonl(E / "probe_v2.jsonl")}


# ---------- frozen family list and sets ----------

def test_family_file_matches_probe_and_rules():
    meta = json.loads((E / "families_v2.json").read_text())
    assert meta["rg_version"] == C.RG_VERSION and meta["n_families"] == len(FAMS) >= 40
    assert meta["n_envs"] == sum(len(f["levels"]) for f in FAMS) == len(ENVS)
    curricula = C.all_curricula()
    assert meta["n_curricula"] == len(curricula) and len(PROBE) == 4 * len(curricula)
    targets = {f for f, _ in C.TARGET_RG}
    for f in FAMS:
        assert f["family"] not in targets
        assert curricula.index(f["family"]) == f["k"]
        assert f["levels"] == sorted(set(f["levels"])) and set(f["levels"]) <= set(C.LEVELS)
        assert len(f["levels"]) >= probe.MIN_LEVELS_PER_FAMILY
        for L in f["levels"]:
            r = PROBE[f"rg/{f['family']}/L{L}"]
            assert r["included"] and not r["reasons"] and r["total_s"] <= probe.TIME_LIMIT_S
    # every probe row is either included in the family file or carries a reason
    included = {s.set_id for s in ENVS}
    for env_id, r in PROBE.items():
        assert (env_id in included) == bool(r["included"]) == (not r["reasons"]), env_id


def test_sets_order_seeds_and_targets():
    assert [s.set_index for s in SETS] == list(range(len(SETS)))
    assert len({s.set_id for s in SETS}) == len(SETS)
    assert [s.set_id for s in SETS[-6:]] == [f"rg/{f}" for f, _ in C.TARGET_RG] + [C.GSM8K_ID]
    # target items and seeds are v1's; sampling seeds are v2's own
    assert {s.set_id: s.seed for s in SETS[-6:-1]} == {f"rg/{f}": sd for f, sd in C.TARGET_RG}
    assert SETS[0].sampling_seed == 2000 and SETS[-1].sampling_seed == 2000 + len(SETS) - 1
    for s in ENVS:
        k = C.all_curricula().index(s.family)
        assert s.seed == 20262000 + 10 * k + s.level
    assert len({s.seed for s in SETS if s.source == "rg"}) == len([s for s in SETS if s.source == "rg"])


def test_v1_families_and_models():
    assert set(C.MODELS) == {"qwen3_0p6b", "qwen3_1p7b"}
    assert len(C.V1_FAMILIES) == 8
    present = {f["family"] for f in FAMS} & set(C.V1_FAMILIES)
    assert len(present) >= 6, present  # the comparison needs most of v1's families inside v2


def test_shards_partition_sets():
    shards = [C.shard_sets(SETS, i, 6) for i in range(6)]
    assert sorted(s.set_index for sh in shards for s in sh) == list(range(len(SETS)))


def test_task_table_matches_models():
    rows = (E / "slurm" / "farmshare" / "tasks.tsv").read_text().split("\n")[1:]
    rows = [r.split("\t") for r in rows if r.strip()]
    assert len(rows) == 10
    for tag in C.MODELS:
        shards = sorted(int(r[1]) for r in rows if r[0] == tag)
        n = {int(r[2]) for r in rows if r[0] == tag}
        assert len(n) == 1 and shards == list(range(n.pop()))


# ---------- probe rules ----------

def _row(**kw):
    base = {"family": "fam_a", "k": 0, "level": 0, "category": "x", "error": None, "total_s": 1.0, "gold_pass_frac": 1.0,
            "none_score_max": 0.0, "unique_questions": 256, "top_answer": "1", "top_answer_share": 0.1,
            "prompt_tokens_max": 300, "determinism_ok": True, "config_sha256": "c0"}
    base.update(kw)
    return base


def test_probe_rules():
    rows = [_row(level=0, config_sha256="a"), _row(level=1, config_sha256="b"), _row(level=2, config_sha256="b"),
            _row(level=3, total_s=99.0, config_sha256="d"),
            _row(family="fam_b", level=0), _row(family="fam_b", level=1, gold_pass_frac=0.9, config_sha256="x"),
            _row(family="gsm_symbolic", level=0), _row(family="gsm_symbolic", level=1, config_sha256="y"),
            _row(family="fam_c", level=0, top_answer_share=0.9), _row(family="fam_c", level=1, config_sha256="z", prompt_tokens_max=5000),
            _row(family="fam_d", level=0, error="RuntimeError: boom"), _row(family="fam_d", level=1, determinism_ok=False)]
    rows, fams = probe.judge(rows, 4096)
    assert fams == [{"family": "fam_a", "k": 0, "category": "x", "levels": [0, 1]}]
    why = {(r["family"], r["level"]): " | ".join(r["reasons"]) for r in rows}
    assert "same config" in why[("fam_a", 2)] and "too slow" in why[("fam_a", 3)]
    assert "fewer than 2 usable levels" in why[("fam_b", 0)] and "gold answer fails" in why[("fam_b", 1)]
    assert "held-out target" in why[("gsm_symbolic", 0)]
    assert "on 90% of items" in why[("fam_c", 0)] and "prompt up to 5000" in why[("fam_c", 1)]
    assert "boom" in why[("fam_d", 0)] and "second process" in why[("fam_d", 1)]


# ---------- generators and verifiers (every included environment) ----------

@pytest.mark.parametrize("spec", ENVS + [s for s in SETS[-6:] if s.source == "rg"], ids=lambda s: s.set_id)
def test_rg_generator_deterministic_and_gold_passes(spec):
    ds1 = C.rg_dataset(spec, 8)
    ds2 = C.rg_dataset(spec, 8)
    for i in range(4):
        e1, e2 = ds1[i], ds2[i]
        assert e1["question"] == e2["question"]
        assert C.is_pass(ds1.score_answer(C.extract_answer(f"work\n<answer>{e1['answer']}</answer>"), e1))
        assert not C.is_pass(ds1.score_answer(None, e1))  # some families give 0.01 partial credit, never a pass


def test_full_item_hashes_match_probe_sample():
    """A full 256-item build of 8 random environments reproduces the probe's item hashes (build.py checks all of them)."""
    for spec in random.Random(0).sample(ENVS, 8):
        rows, meta = build.build_set(spec, C.N_ITEMS, C.system_prompt(), None)
        assert meta["items_sha256"] == PROBE[spec.set_id]["items_sha256"], spec.set_id
        assert meta["unique_questions"] == PROBE[spec.set_id]["unique_questions"]


@pytest.mark.parametrize("text,gold,want", [
    ("so <answer>18</answer>", "18", 1.0),
    ("<answer>$1,234.</answer>", "1234", 1.0),
    ("<answer>17</answer>", "18", 0.0),
    ("the answer is 18", "18", 0.0),
])
def test_gsm8k_exact_numeric_match(text, gold, want):
    assert C.gsm8k_score(C.extract_answer(text), gold) == want


# ---------- metric and analysis code ----------

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
    assert m["complete"] and m["rho"] == pytest.approx(ref.rho) and m["H"] == pytest.approx(ref.H)


def test_transfer_verdict_cluster_ci_and_eta2():
    assert analyze.transfer_verdict(0.8, [0.6, 0.9]) == "transfers"
    assert analyze.transfer_verdict(0.8, [0.4, 0.9]) == "partial"
    assert analyze.transfer_verdict(0.3, [0.1, 0.5]) == "fails"
    x = list(range(20))
    lo, hi = analyze.spearman_cluster_ci(x, x, [i // 4 for i in x], n_boot=200)
    assert lo == pytest.approx(1.0) and hi == pytest.approx(1.0)
    assert analyze.eta_squared([0, 0, 1, 1], ["a", "a", "b", "b"]) == pytest.approx(1.0)
    assert analyze.eta_squared([0, 1, 0, 1], ["a", "a", "b", "b"]) == pytest.approx(0.0)


def _synthetic_cells(shift_other: float):
    """Cells for every environment and both models; levels lower pass rate; non-v1 families get an optional twist."""
    by = C.sets_by_id()
    rows = []
    rng = np.random.default_rng(3)
    for s in ENVS:
        base = 0.9 - 0.2 * s.level - (sum(map(ord, s.family)) % 5) / 20
        for t, size in (("qwen3_0p6b", 0.0), ("qwen3_1p7b", 0.1)):
            p = base + size + rng.normal(0, 0.02)
            if shift_other and s.family not in C.V1_FAMILIES and t == "qwen3_1p7b":
                p = rng.random()  # destroys the size transfer outside v1's families
            p = float(np.clip(p, 0, 1))
            rows.append({"env_id": s.set_id, "model_tag": t, "complete": True, "pass_rate": p, "rho": p * (1 - p),
                         "H": 1 - p, "alignment": rng.normal(), "in_learnable_band": 0.1 <= p <= 0.9,
                         "format_dominated": False, "unique_questions": 256, "level": by[s.set_id].level})
    return rows


def test_eight_family_picture_verdicts():
    s = analyze.summarize(_synthetic_cells(0.0), [], list(C.MODELS), [])
    a6 = s["analysis6_eight_family_picture"]
    assert s["analysis1_size_transfer"]["verdict"] == "transfers"
    assert a6["checks"]["a_same_transfer_verdict"] and a6["verdict"] in {"holds", "partially_holds"}
    assert a6["v1_subset_typicality"]["n_subsets"] > 0
    s2 = analyze.summarize(_synthetic_cells(1.0), [], list(C.MODELS), [])
    assert s2["analysis6_eight_family_picture"]["verdict"] == "does_not_hold"
    assert s2["analysis7_robustness"]["eta2_family_pass_rate"]["qwen3_0p6b"] is not None


# ---------- fake-model dry run, end to end ----------

def _gsm(tmp_path, n=12):
    gsm = tmp_path / "gsm8k.jsonl"
    with open(gsm, "w") as fh:
        for i in range(n):
            fh.write(json.dumps({"question": f"Ann has {i} apples and buys 3. How many?", "answer": f"...\n#### {i + 3}"}) + "\n")
    return gsm


def test_fake_end_to_end(tmp_path):
    """Every v1 family present plus 10 other families and the 6 targets, 6 items each, both models, fake backends."""
    run = tmp_path / "run"
    others = [f["family"] for f in FAMS if f["family"] not in C.V1_FAMILIES][::4][:10]
    pick = [s for s in ENVS if s.family in C.V1_FAMILIES or s.family in others] + SETS[-6:]
    ids = ",".join(s.set_id for s in pick)
    assert build.main(["--out", str(run), "--n-items", "6", "--sets", ids, "--gsm8k-jsonl", str(_gsm(tmp_path))]) == 0
    manifest = json.loads((run / "items" / "manifest.json").read_text())
    assert len(manifest["sets"]) == len(pick) and manifest["rg_version"] == C.RG_VERSION
    for tag in C.MODELS:
        for shard in range(2):
            assert generate.main(["--run", str(run), "--model-tag", tag, "--backend", "fake", "--n", "4",
                                  "--shard", str(shard), "--nshards", "2"]) == 0
        for shard in range(2):
            assert score.main(["--run", str(run), "--model-tag", tag, "--shard", str(shard), "--nshards", "2"]) == 0
        assert embed.main(["--run", str(run), "--model-tag", tag, "--backend", "fake"]) == 0
    raw = run / "raw" / "qwen3_1p7b" / f"{pick[0].file_stem}.jsonl"
    before = raw.stat().st_mtime_ns
    generate.main(["--run", str(run), "--model-tag", "qwen3_1p7b", "--backend", "fake", "--n", "4"])
    assert raw.stat().st_mtime_ns == before  # resume skips finished sets

    manifest["group_size"] = 4
    (run / "items" / "manifest.json").write_text(json.dumps(manifest))
    assert analyze.main(["--run", str(run)]) == 0
    res = run / "results"
    envs = [json.loads(line) for line in open(res / "envs_18a_v2.jsonl")]
    tgts = [json.loads(line) for line in open(res / "targets_18a_v2.jsonl")]
    summary = json.loads((res / "summary_18a_v2.json").read_text())
    n_env = len(pick) - 6
    assert len(envs) == 2 * n_env and len(tgts) == 12
    for r in envs:
        assert r["schema"] == "envs_18a_v2/v1" and r["complete"]
        assert -1.0 <= r["alignment"] <= 1.0 and len(r["alignment_by_target"]) == 6
        assert r["unique_questions"] >= 1 and 0 < r["top_answer_share"] <= 1
    a1 = summary["analysis1_size_transfer"]
    assert a1["n_envs"] == n_env and a1["verdict"] in {"transfers", "partial", "fails"}
    assert summary["analysis6_eight_family_picture"]["verdict"] in {"holds", "partially_holds", "does_not_hold"}
    assert summary["incomplete_cells"] == []
    # v1 replication check reads v1-shaped rows
    v1 = tmp_path / "v1.jsonl"
    v1.write_text("".join(json.dumps({"env_id": r["env_id"], "model_tag": r["model_tag"], "complete": True,
                                      "pass_rate": r["pass_rate"]}) + "\n" for r in envs if r["family"] in C.V1_FAMILIES))
    assert analyze.main(["--run", str(run), "--v1-envs", str(v1)]) == 0
    rep = json.loads((res / "summary_18a_v2.json").read_text())["analysis7_robustness"]["v1_replication_new_seeds"]
    assert all(v["spearman"] == pytest.approx(1.0) for v in rep.values())


def test_fake_smoke_path(tmp_path):
    """The smoke job's chain: a few sets, few items, separate *_smoke folders, analyze in smoke mode."""
    run = tmp_path / "run"
    sets = ",".join([ENVS[0].set_id, ENVS[-1].set_id, "rg/gsm_symbolic", "gsm8k/test256"])
    assert build.main(["--out", str(run), "--n-items", "4", "--sets", sets, "--gsm8k-jsonl", str(_gsm(tmp_path, 5))]) == 0
    tag = "qwen3_1p7b"
    assert generate.main(["--run", str(run), "--model-tag", tag, "--backend", "fake", "--n", "2", "--limit-items", "3",
                          "--sets", sets, "--out-subdir", "smoke"]) == 0
    assert score.main(["--run", str(run), "--model-tag", tag, "--raw-subdir", "smoke", "--sets", sets]) == 0
    assert embed.main(["--run", str(run), "--model-tag", tag, "--backend", "fake", "--limit-items", "3",
                       "--out-subdir", "smoke"]) == 0
    assert analyze.main(["--run", str(run), "--subdir", "smoke", "--smoke-group-size", "2"]) == 0
    envs = [json.loads(line) for line in open(run / "results_smoke" / "envs_18a_v2.jsonl")]
    assert {r["env_id"] for r in envs} == {ENVS[0].set_id, ENVS[-1].set_id}
    assert all(r["complete"] and r["n_responses"] == 6 for r in envs)
    assert not (run / "raw").exists()
