"""Tests for the D-013 VeriBench V1 split: ids, security pairing, grouping, deterministic stratified assignment, leakage."""

import csv
import hashlib
import os
from pathlib import Path

import pytest

from rl4cv.splits import (
    SPLITS,
    assign_splits,
    build_split,
    group_tasks,
    largest_remainder,
    load_vbv1_tasks,
    pair_key,
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


def _veribench_root():
    for cand in (os.environ.get("VERIBENCH_ROOT"), str(REPO / "external" / "veribench")):
        if cand and (Path(cand) / "veribench_dataset" / "py_src").is_dir():
            return Path(cand)
    return None


@pytest.mark.skipif(_veribench_root() is None, reason="needs VeriBench (VERIBENCH_ROOT or external/veribench)")
def test_committed_manifest_reproduces_from_pinned_dataset():
    """If the VeriBench files match the committed hashes, rebuilding gives the committed manifest byte for byte."""
    manifest = COMMITTED / "vbv1_split_manifest.csv"
    if not manifest.is_file():
        pytest.skip("split manifest not committed yet")
    with open(manifest, encoding="utf-8", newline="") as fh:
        committed = list(csv.DictReader(fh))
    tasks, _ = load_vbv1_tasks(_veribench_root())
    have = {t.task_id: (hashlib.sha256(t.py_text.encode()).hexdigest(), hashlib.sha256((t.gold_text or "").encode()).hexdigest() if t.gold_text else "") for t in tasks}
    want = {r["task_id"]: (r["py_sha256"], r["gold_sha256"]) for r in committed}
    if have != want:
        pytest.skip("VeriBench files differ from the pinned dataset the manifest was built from")
    res = build_split(_veribench_root(), with_leakage=False)
    assert res["manifest_csv"] == manifest.read_text(encoding="utf-8")
    assert len(committed) == 896
