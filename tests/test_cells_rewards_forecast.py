"""Tests for 2x2 cell construction, reward channels and prospective forecast freezing."""

import json

import numpy as np
import pytest

from rl4cv.cells import (
    CELLS,
    ProbeStage,
    load_stages,
    pooled_stats,
    select_balanced_cells,
    stage_a_bands,
    stage_d_confirmation,
    standardized_difference,
)
from rl4cv.forecast import canonical_json, freeze_forecast, verify_forecast
from rl4cv.rewards import (
    REWARD_CHANNELS,
    ScoredResponse,
    is_vacuous_statement,
    needs_judge,
    reward_fsc,
    reward_kernel_binary,
    reward_scsc,
)


def _stage(k, capped, G=8):
    return ProbeStage(tuple(1.0 if i < k else 0.0 for i in range(G)), tuple(i < capped for i in range(G)))


def _synthetic_pool(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    stages = {s: {} for s in "ABCD"}
    for i in range(n):
        p = float(rng.beta(1.0, 2.5))
        cap_rate = float(rng.choice([0.1, 0.7]))
        for s in "ABCD":
            k = int(rng.binomial(8, p))
            capped = int(rng.binomial(8, cap_rate))
            stages[s][f"t{i}"] = ProbeStage(
                tuple(1.0 if j < k else 0.0 for j in range(8)),
                tuple(j < capped for j in range(8)),
            )
    return stages


def test_stage_a_bands_follow_paper_rules():
    st = {"mixed_hi": _stage(3, 0), "mixed_lo": _stage(3, 6), "flat_hi": _stage(0, 1), "both": _stage(8, 4)}
    pools = stage_a_bands(st)
    assert "mixed_hi" in pools["HH"] and "mixed_lo" in pools["HL"] and "flat_hi" in pools["LH"]
    # 4 non-capped responses satisfy both admission bands (at least 3, at most 4).
    assert "both" in pools["LH"] and "both" in pools["LL"]


def test_select_balanced_cells_disjoint_and_balanced():
    stages = _synthetic_pool()
    pools = stage_a_bands(stages["A"])
    stats = {p: pooled_stats([stages[s][p] for s in "ABC"]) for p in stages["A"]}
    sel = select_balanced_cells(pools, stats, n_per_cell=64)
    members = [p for c in CELLS for p in sel.cells[c]]
    assert len(members) == len(set(members)) == 4 * 64
    assert sel.success_spread <= 0.02
    assert sel.admission_contrast > 0.2
    assert min(sel.mean_mixedness["HH"], sel.mean_mixedness["HL"]) > max(sel.mean_mixedness["LH"], sel.mean_mixedness["LL"])
    report = stage_d_confirmation(sel.cells, stages["D"], max_success_spread=0.05, max_std_diff=0.2)
    assert report.admission_contrast > 0.2


def test_load_stages_and_standardized_difference():
    rows = [{"task_id": "a", "stage": "A", "reward": 1, "truncated": False}, {"task_id": "a", "stage": "A", "reward": 0, "truncated": True}]
    st = load_stages(rows)
    assert st["A"]["a"].rewards == (1.0, 0.0) and st["A"]["a"].capped == (False, True)
    assert standardized_difference(0.3, 0.3) == 0.0


def _scored(**kw):
    base = dict(extracted=True, compiles=True, n_examples=2, n_theorems_stated=4, n_theorems_proved=4, fsc=0.8)
    base.update(kw)
    return ScoredResponse(**base)


def test_kernel_binary_requires_everything():
    assert reward_kernel_binary(_scored()) == 1.0
    assert reward_kernel_binary(_scored(n_theorems_proved=3)) == 0.0
    assert reward_kernel_binary(_scored(n_examples=0)) == 0.0
    assert reward_kernel_binary(_scored(compiles=False)) == 0.0
    assert reward_kernel_binary(_scored(vacuous_theorems=1)) == 0.0
    assert reward_kernel_binary(_scored(n_theorems_stated=0, n_theorems_proved=0)) == 0.0


def test_scsc_reward_is_zero_without_ic_and_needs_no_judge_then():
    bad = _scored(compiles=False, fsc=None)
    assert reward_scsc(bad) == 0.0 and not needs_judge(bad, "scsc")
    good = _scored(n_theorems_proved=2, fsc=0.5)
    assert reward_scsc(good) == pytest.approx((1.0 * 0.5 * 0.5) ** (1 / 3))
    assert needs_judge(good, "scsc")


def test_ungated_fsc_pays_noncompiling_text_but_gated_channel_does_not():
    junk = _scored(compiles=False, fsc=0.9)
    assert reward_fsc(junk) == 0.9
    assert REWARD_CHANNELS["fsc_compiled"](junk) == 0.0


def test_vacuity_heuristic():
    assert is_vacuous_statement("True")
    assert is_vacuous_statement("∀ x : Nat, x = x")
    assert is_vacuous_statement("P x → True")
    assert not is_vacuous_statement("∀ x : Nat, f x = x + 1")


def test_freeze_forecast_is_append_only_and_verifiable(tmp_path):
    entry = freeze_forecast({"b": 1, "a": [1.5, 2]}, tmp_path, "fc_8b")
    assert verify_forecast(tmp_path / "fc_8b.json")
    assert json.loads((tmp_path / "fc_8b.json").read_text()) == {"a": [1.5, 2], "b": 1}
    assert entry["sha256"] in (tmp_path / "fc_8b.sha256").read_text()
    with pytest.raises(FileExistsError):
        freeze_forecast({"b": 2}, tmp_path, "fc_8b")
    with pytest.raises(ValueError):
        freeze_forecast({"b": 2}, tmp_path, "late", outcomes_observed=True)
    (tmp_path / "fc_8b.json").write_text(canonical_json({"a": [1.5, 2], "b": 2}) + "\n")
    assert not verify_forecast(tmp_path / "fc_8b.json")


def test_contamination_screen_exact_and_near():
    from rl4cv.screens import screen

    protected = {"vb/easy_set/1_MyAdd.py": "def my_add(a, b):\n    # add two numbers\n    return a + b\n",
                 "vb/cs_set/bs.py": "def binary_search(xs, t):\n    lo, hi = 0, len(xs) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if xs[mid] == t: return mid\n        if xs[mid] < t: lo = mid + 1\n        else: hi = mid - 1\n    return -1\n"}
    pool = {
        "copy": "def my_add(a, b):\n  return a + b   # reformatted copy\n",
        "variant": protected["vb/cs_set/bs.py"].replace("return -1", "return None"),
        "other": "def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n",
    }
    rep = screen(pool, protected)
    assert rep["n_exact"] == 1 and rep["exact"][0]["item_id"] == "copy"
    assert rep["n_near"] == 1 and rep["near"][0]["item_id"] == "variant"
    assert rep["clean_ids"] == ["other"]
