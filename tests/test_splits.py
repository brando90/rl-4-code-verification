"""Tests for the D-013 VeriBench V1 split: ids, security pairing, grouping, deterministic stratified assignment, leakage."""

import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from rl4cv.splits import (
    SPLITS,
    VBTask,
    assign_splits,
    build_split,
    group_tasks,
    largest_remainder,
    load_vbv1_tasks,
    pair_key,
    similar_pairs,
    task_id_for,
)

REPO = Path(__file__).resolve().parents[1]
COMMITTED = REPO / "experiments" / "08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test" / "expt_v1" / "results" / "split"


def test_task_id_matches_veribench_convention():
    assert task_id_for("easy_set/4_MyRemainder.py") == "easy_set__4_myremainder"
    assert task_id_for("security_set/security_6858/vulnerabilities/107_unsafeProfileSandbox.py") == "security_set__security_6858__vulnerabilities__107_unsafeprofilesandbox"


def test_security_pair_keys():
    assert pair_key("security_set/security_6858/vulnerabilities/0_unsafeCopy.py") == pair_key("security_set/security_6858/safe/0_unsafeCopy_safe.py")
    assert pair_key("security_set/security_python/vulnerabilities/0_shell_injection.py") == pair_key("security_set/security_python/safe/0_no_shell_injection_safe.py")
    assert pair_key("security_set/security_6858/vulnerabilities/100_unsafeDefaultCreds.py") != pair_key("security_set/security_6858/vulnerabilities/100_unsafeLengthLeakage.py")
    assert pair_key("easy_set/1_MyAdd.py") is None


def test_largest_remainder_sums_and_rounds():
    assert largest_remainder(10, (0.6, 0.15, 0.25)) == [6, 2, 2]
    assert largest_remainder(1, (0.6, 0.15, 0.25)) == [1, 0, 0]
    for n in range(0, 50):
        assert sum(largest_remainder(n, (0.6, 0.15, 0.25))) == n


def _program(i: int, words: str) -> str:
    return f'"""Task {i}: {words}."""\n\ndef f_{i}(x):\n    return x + {i}\n\n\ndef check(candidate):\n    assert candidate(1) == {1 + i}\n'


def _lean(i: int, words: str) -> str:
    return f"/-! {words} -/\nnamespace T{i}\ndef f (x : Nat) : Nat := x + {i}\ntheorem f_spec (x : Nat) : f x = x + {i} := rfl\nend T{i}\n"


def _make_tree(root: Path, n_per_family: int = 12) -> None:
    py = root / "veribench_dataset" / "py_src"
    lean = root / "veribench_dataset" / "lean_src" / "veribench"
    k = 0
    for fam in ("easy_set", "cs_set", "finance_set_synthetic"):
        for i in range(n_per_family):
            k += 1
            words = " ".join(f"w{k}_{j}" for j in range(30))
            (py / fam).mkdir(parents=True, exist_ok=True)
            (lean / fam).mkdir(parents=True, exist_ok=True)
            (py / fam / f"{i}_my_task_{k}.py").write_text(_program(k, words))
            (lean / fam / f"{i}_MyTask{k}.lean").write_text(_lean(k, words))
    # an exact copy, which must share a split with its original
    (py / "easy_set" / "99_my_copy.py").write_text((py / "easy_set" / "0_my_task_1.py").read_text())
    (lean / "easy_set" / "99_MyCopy.lean").write_text((lean / "easy_set" / "0_MyTask1.lean").read_text())
    # a security vulnerable/safe pair with unrelated texts
    for sub, name, i in (("vulnerabilities", "5_unsafeThing", 500), ("safe", "5_unsafeThing_safe", 501)):
        words = " ".join(f"s{i}_{j}" for j in range(30))
        (py / "security_set" / "security_6858" / sub).mkdir(parents=True, exist_ok=True)
        (lean / "security_set" / "security_6858" / sub).mkdir(parents=True, exist_ok=True)
        (py / "security_set" / "security_6858" / sub / f"{name}.py").write_text(_program(i, words))
        (lean / "security_set" / "security_6858" / sub / f"{name}.lean").write_text(_lean(i, words))


def test_synthetic_split_invariants(tmp_path):
    _make_tree(tmp_path)
    res = build_split(tmp_path)
    rows = res["rows"]
    assert len(rows) == 3 * 12 + 1 + 2
    assert {r["split"] for r in rows} <= set(SPLITS)
    by_id = {r["task_id"]: r for r in rows}
    # every group sits in exactly one split
    groups = {}
    for r in rows:
        groups.setdefault(r["group_id"], set()).add(r["split"])
    assert all(len(s) == 1 for s in groups.values())
    assert by_id["easy_set__99_my_copy"]["split"] == by_id["easy_set__0_my_task_1"]["split"]
    pair = [r for r in rows if r["family"] == "security_set"]
    assert len({r["split"] for r in pair}) == 1 and pair[0]["group_size"] == 2
    # per-family counts follow the largest-remainder targets within one group of slack
    for fam in ("cs_set", "finance_set_synthetic"):
        got = [sum(1 for r in rows if r["family"] == fam and r["split"] == s) for s in SPLITS]
        assert got == largest_remainder(12, (0.6, 0.15, 0.25))
    assert res["leakage"]["py"]["max_cross_split_jaccard"] < 0.70
    assert res["summary"]["gold_mapping"]["gold_matched"] == len(rows)


def test_split_is_deterministic_and_salted(tmp_path):
    _make_tree(tmp_path)
    a = build_split(tmp_path, with_leakage=False)
    b = build_split(tmp_path, with_leakage=False)
    assert a["manifest_csv"] == b["manifest_csv"]
    c = build_split(tmp_path, salt="another-salt", with_leakage=False)
    assert c["manifest_csv"] != a["manifest_csv"]


def test_assign_rejects_bad_fractions(tmp_path):
    _make_tree(tmp_path, n_per_family=3)
    tasks, _ = load_vbv1_tasks(tmp_path)
    group_of, _ = group_tasks(tasks)
    with pytest.raises(ValueError):
        assign_splits(tasks, group_of, fractions=(0.5, 0.5, 0.0))


def test_cross_family_transitive_groups_are_order_independent():
    tasks = [
        VBTask("a", "easy_set", True, "easy_set/a.py", "same python", "a.lean", "gold a"),
        VBTask("b", "cs_set", True, "cs_set/b.py", "same python", "b.lean", "shared gold"),
        VBTask("c", "finance_set_real", False, "finance_set_real/c.py", "different python", "c.lean", "shared gold"),
    ]
    groups, _ = group_tasks(tasks)
    assert groups == {"a": "a", "b": "a", "c": "a"}
    reversed_groups, _ = group_tasks(list(reversed(tasks)))
    assert reversed_groups == groups
    assigned = assign_splits(tasks, groups)
    assert len(set(assigned.values())) == 1
    assert assign_splits(list(reversed(tasks)), reversed_groups) == assigned


def test_near_duplicate_threshold_is_inclusive():
    # Seven shared unigrams among ten in the union: exactly the declared boundary.
    texts = {"a": "a b c d e f g h i", "b": "a b c d e f g j"}
    assert similar_pairs(texts, n=1, threshold=0.70) == [("a", "b", "near", 0.7)]
    assert similar_pairs(texts, n=1, threshold=0.7001) == []


def _experiment_script(name):
    spec = importlib.util.spec_from_file_location(name, COMMITTED.parents[1] / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_base_table_reproduces_committed_results():
    module = _experiment_script("base_tables_from_e05")
    expected = json.loads((COMMITTED.parent / "base_qwen3_e05_on_d013_splits.json").read_text())
    assert module.table(COMMITTED / "vbv1_split_manifest.csv") == expected["results"]


@pytest.mark.parametrize("corruption", ["duplicate", "incomplete"])
def test_base_table_rejects_corrupt_receipts(tmp_path, corruption):
    module = _experiment_script("base_tables_from_e05")
    model = module.MODELS[0]
    with (module.E05 / f"per_task_{model}_g8.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields, rows = reader.fieldnames, list(reader)
    if corruption == "duplicate":
        rows.append(rows[0])
    else:
        rows[0]["samples_present"] = "7"
    with (tmp_path / f"per_task_{model}_g8.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    module.E05 = tmp_path
    with pytest.raises(ValueError):
        module.table(COMMITTED / "vbv1_split_manifest.csv")


def test_teacher_budget_requires_every_passing_file(tmp_path, monkeypatch):
    module = _experiment_script("estimate_token_budget")
    monkeypatch.setattr(module, "_tokenizer", lambda: lambda text, **kw: {"input_ids": text.split()})
    monkeypatch.setattr(module, "_manifest", lambda: [{"task_id": "a", "split": "train"}])
    model = module.E103_MODELS[0]
    scores = tmp_path / "scsc_vbv1" / model
    scores.mkdir(parents=True)
    (scores / f"scsc_expt103-single-call-vbv1-{model}_{model}_per_task.csv").write_text(
        "task,submission_status,IC_ap,IC_pp,kernel_n_theorems,agent_n_ex\n"
        "a,submitted,1.0,1.0,1,1\n"
    )
    with pytest.raises(FileNotFoundError):
        module.e103(tmp_path)


def _veribench_root():
    for cand in (os.environ.get("VERIBENCH_ROOT"), str(REPO / "external" / "veribench")):
        if cand and (Path(cand) / "veribench_dataset" / "py_src").is_dir():
            return Path(cand)
    return None


@pytest.mark.skipif(_veribench_root() is None, reason="needs VeriBench (VERIBENCH_ROOT or external/veribench)")
def test_committed_manifest_reproduces_from_pinned_dataset():
    """Require the pinned dataset and reproduce every committed split artifact byte for byte."""
    manifest = COMMITTED / "vbv1_split_manifest.csv"
    with open(manifest, encoding="utf-8", newline="") as fh:
        committed = list(csv.DictReader(fh))
    tasks, _ = load_vbv1_tasks(_veribench_root())
    have = {t.task_id: (hashlib.sha256(t.py_text.encode()).hexdigest(), hashlib.sha256((t.gold_text or "").encode()).hexdigest() if t.gold_text else "") for t in tasks}
    want = {r["task_id"]: (r["py_sha256"], r["gold_sha256"]) for r in committed}
    assert have == want, "VeriBench files differ from the pinned dataset; reproduction did not pass"
    res = build_split(_veribench_root())
    assert res["manifest_csv"] == manifest.read_text(encoding="utf-8")
    assert len(committed) == 896
    summary = dict(res["summary"], veribench_commit="c11b99badfa386fd26810b208eef1eb8dc9f6806")
    for name, value, indent in (("summary", summary, 2), ("links", res["edges"], 1), ("leakage", res["leakage"], 2)):
        assert (COMMITTED / f"vbv1_split_{name}.json").read_text() == json.dumps(value, indent=indent) + "\n"
    for split in SPLITS:
        ids = "".join(r["task_id"] + "\n" for r in res["rows"] if r["split"] == split)
        assert (COMMITTED / f"vbv1_{split}_task_ids.txt").read_text() == ids
