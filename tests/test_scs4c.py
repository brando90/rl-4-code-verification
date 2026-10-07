"""TLDR: Unit tests for SCS4C factors, gating, system aggregation and the numpy-only rank correlations."""

import math
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

import pytest

from rl4cv.scs4c import (
    Cell,
    cell_from_report,
    cell_score,
    fraction_passed,
    geometric_mean,
    kendall_tau_b,
    pearson,
    spearman,
    system_summary,
)

F2P = ["t::fix_a", "t::fix_b"]
P2P = ["t::keep_a", "t::keep_b", "t::keep_c", "t::keep_d"]


def report(applied=True, f2p_ok=(), p2p_ok=(), resolved=False):
    return {
        "patch_exists": True,
        "patch_is_None": False,
        "patch_successfully_applied": applied,
        "resolved": resolved,
        "tests_status": {
            "FAIL_TO_PASS": {"success": list(f2p_ok), "failure": [t for t in F2P if t not in f2p_ok]},
            "PASS_TO_PASS": {"success": list(p2p_ok), "failure": [t for t in P2P if t not in p2p_ok]},
        },
    }


def test_fraction_passed_uses_gold_denominator_and_vacuous_empty():
    assert fraction_passed(["t::fix_a", "unrelated"], F2P) == 0.5
    assert fraction_passed([], []) == 1.0


def test_report_lists_are_the_default_denominator():
    c = cell_from_report("i", report(f2p_ok=["t::fix_a"], p2p_ok=P2P), has_patch=True)
    assert (c.t_fix, c.t_keep) == (0.5, 1.0)


def test_resolved_patch_scores_one():
    c = cell_from_report("i", report(f2p_ok=F2P, p2p_ok=P2P, resolved=True), F2P, P2P, has_patch=True)
    assert (c.gate, c.t_fix, c.t_keep, c.resolved) == (1, 1.0, 1.0, True)
    assert cell_score(c) == 1.0


def test_partial_credit_is_geometric_mean_of_test_factors():
    c = cell_from_report("i", report(f2p_ok=["t::fix_a"], p2p_ok=P2P), F2P, P2P, has_patch=True)
    assert cell_score(c) == pytest.approx(math.sqrt(0.5 * 1.0))


def test_any_zero_factor_collapses_the_score():
    c = cell_from_report("i", report(f2p_ok=[], p2p_ok=P2P), F2P, P2P, has_patch=True)
    assert cell_score(c) == 0.0


def test_gate_failure_scores_zero_and_leaves_factors_not_run():
    c = cell_from_report("i", report(applied=False), F2P, P2P, has_patch=True)
    assert c.gate == 0 and c.t_fix is None and c.t_keep is None
    assert cell_score(c) == 0.0 and c.gated("t_fix") == 0.0


def test_missing_patch_is_zero_but_missing_report_is_unmeasured():
    assert cell_score(cell_from_report("i", None, F2P, P2P, has_patch=False)) == 0.0
    unmeasured = cell_from_report("i", None, F2P, P2P, has_patch=True)
    assert unmeasured.gate is None and cell_score(unmeasured) is None


def test_system_summary_is_geometric_mean_of_factor_means_on_measured_cohort():
    cells = [
        Cell("a", 1, 1.0, 1.0, True),
        Cell("b", 1, 0.5, 1.0, False),
        Cell("c", 0, None, None, False),
        Cell("d", None, None, None, None),
    ]
    s = system_summary(cells)
    assert (s["declared"], s["measured"], s["unmeasured"]) == (4, 3, 1)
    assert s["factor_means"]["t_fix"] == pytest.approx(0.5)
    assert s["factor_means"]["t_keep"] == pytest.approx(2 / 3)
    assert s["scs4c"] == pytest.approx(math.sqrt(0.5 * 2 / 3))
    assert s["pass1"] == pytest.approx(1 / 3)
    assert s["pass1_declared"] == pytest.approx(1 / 4)


def test_geometric_mean_does_not_clamp_zero():
    assert geometric_mean([0.0, 1.0]) == 0.0
    assert geometric_mean([0.25, 1.0]) == pytest.approx(0.5)


def test_correlations_match_scipy_with_ties():
    stats = pytest.importorskip("scipy.stats")
    x = [0.1, 0.4, 0.4, 0.9, 0.3, 0.7, 0.7, 0.2]
    y = [0.2, 0.5, 0.1, 0.8, 0.3, 0.9, 0.6, 0.2]
    assert pearson(x, y) == pytest.approx(stats.pearsonr(x, y)[0])
    assert spearman(x, y) == pytest.approx(stats.spearmanr(x, y)[0])
    assert kendall_tau_b(x, y) == pytest.approx(stats.kendalltau(x, y, variant="b")[0])


def test_constant_input_has_no_correlation():
    assert pearson([1, 1, 1], [1, 2, 3]) is None


@pytest.mark.parametrize("missing", ["tests_status", "resolved", "patch_successfully_applied", "patch_exists", "patch_is_None"])
def test_incomplete_report_is_unmeasured(missing):
    r = report(f2p_ok=F2P, p2p_ok=P2P, resolved=True)
    del r[missing]
    assert cell_score(cell_from_report("i", r, has_patch=True)) is None


def test_missing_group_is_not_a_vacuously_passing_group():
    r = report(f2p_ok=F2P, p2p_ok=P2P, resolved=True)
    del r["tests_status"]["PASS_TO_PASS"]
    assert not cell_from_report("i", r, has_patch=True).measured
    r["tests_status"]["PASS_TO_PASS"] = {"success": [], "failure": []}
    assert cell_score(cell_from_report("i", r, has_patch=True)) == 1


def test_conflicting_test_lists_are_unmeasured():
    r = report(f2p_ok=F2P, p2p_ok=P2P)
    r["tests_status"]["FAIL_TO_PASS"]["failure"] = [F2P[0]]
    assert not cell_from_report("i", r, has_patch=True).measured


def test_all_unmeasured_has_only_leaderboard_convention_zero():
    s = system_summary([Cell("i", None, None, None, None)])
    assert s["scs4c"] is None and s["pass1"] is None
    assert s["pass1_declared"] == 0
    assert system_summary([])["pass1_declared"] is None


@pytest.mark.parametrize("corr", [pearson, spearman, kendall_tau_b])
def test_correlations_filter_nonfinite_pairs_before_ranking(corr):
    assert corr([1, 2, float("nan"), 3, float("inf")], [1, 2, 99, 3, 99]) == pytest.approx(1)
    assert corr([1, float("nan"), 3], [1, 2, 3]) is None
    with pytest.raises(ValueError):
        corr([1, 2, 3], [1, 2])


def test_missing_factor_is_not_hidden_by_another_zero():
    assert cell_score(Cell("i", 1, 0, float("nan"), False)) is None
    with pytest.raises(ValueError):
        geometric_mean([0, float("nan")])


@pytest.fixture
def e07():
    path = Path(__file__).parents[1] / "experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/analyze_e07.py"
    spec = importlib.util.spec_from_file_location("analyze_e07", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_loader_keeps_no_logs_unmeasured_and_empty_predictions_zero(e07, tmp_path):
    (tmp_path / "results.json").write_text(json.dumps({"no_generation": ["empty"], "no_logs": ["lost"], "resolved": []}))
    (tmp_path / "all_preds.jsonl").write_text("\n".join(json.dumps({"instance_id": i, "model_patch": "diff"}) for i in ("empty", "lost")))
    cells = e07.load_cells(tmp_path, {i: ([], []) for i in ("empty", "lost", "absent")})
    assert [cell_score(c) for c in cells] == [0, None, 0]
    # An authoritative report wins over stale aggregate no_generation evidence.
    rp = tmp_path / "logs/empty/report.json"
    rp.parent.mkdir(parents=True)
    rp.write_text(json.dumps({"empty": report(f2p_ok=F2P, p2p_ok=P2P, resolved=True)}))
    assert cell_score(e07.load_cells(tmp_path, {"empty": ([], [])})[0]) == 1


def test_bad_report_without_patch_evidence_stays_unmeasured(e07, tmp_path):
    rp = tmp_path / "logs/i/report.json"
    rp.parent.mkdir(parents=True)
    rp.write_text('{"i":')
    assert not e07.load_cells(tmp_path, {"i": ([], [])})[0].measured
    rp.write_text(json.dumps({"i": {"patch_successfully_applied": True}}))
    assert not e07.load_cells(tmp_path, {"i": ([], [])})[0].measured


def test_empty_or_nonfinite_cohort_does_not_become_zero(e07):
    m = {key: np.ones((3, 2)) for key in ("t_fix", "t_keep", "score", "resolved")}
    assert all(np.isnan(a).all() for a in e07.system_scores(m, np.array([], int)))
    m["t_fix"][0, 0] = np.nan
    assert np.isnan(e07.system_scores(m, np.arange(2))[0][0])


def test_undefined_splits_and_percentiles_are_json_null(e07):
    m = {key: np.ones((3, 10)) for key in ("t_fix", "t_keep", "score", "resolved")}
    out = e07.held_out_prediction(m, [5, 10, 25], 4, np.random.default_rng(1))
    for result in out.values():
        assert result["defined"] == 0 and result["undefined"] == 4
        assert result["delta_median"] is None and result["share_delta_positive"] is None
    assert e07.percentile_ci([None, float("nan"), float("inf")]) is None
    json.dumps(out, allow_nan=False)


def test_bootstrap_reports_agreement_and_defined_draws(e07):
    x, y = np.ones(4), np.arange(4) / 4
    out = e07.bootstrap_corr(lambda _: (x, y), 3, 4, np.random.default_rng(1), 8, include_agreement=True)
    assert out["tasks"]["defined_draws"]["spearman"] == 0
    assert out["tasks"]["defined_draws"]["mae"] == 8
    assert out["tasks"]["mean_bias_scs4c_minus_pass1"] == pytest.approx([0.625, 0.625])
    json.dumps(out, allow_nan=False)


@pytest.mark.parametrize("mode", ["none", "underpowered", "inconsistent", "no_common", "valid"])
def test_analysis_stop_rules_manifest_and_receipts(e07, tmp_path, monkeypatch, mode):
    count = 0 if mode == "none" else 1 if mode == "underpowered" else 20
    names = [f"system_{i:02d}" for i in range(count)]
    (tmp_path / "inventory.json").write_text(json.dumps([{"submission": n, "error": None} for n in names]))
    (tmp_path / "submissions/stale_not_in_manifest").mkdir(parents=True)
    gold = {f"task_{i}": (F2P, P2P) for i in range(500)}
    gold_path = tmp_path / "gold_tests.jsonl"
    gold_path.write_text("\n".join(json.dumps({"instance_id": iid, "FAIL_TO_PASS": f2p, "PASS_TO_PASS": p2p}) for iid, (f2p, p2p) in gold.items()))
    inputs = {"experiments_commit": "40f164d5b8f1d249bf95a6df8b74b577fd8e519d", "split": "verified",
              "gold_dataset": "princeton-nlp/SWE-bench_Verified", "gold_revision": "c104f840cc67f8b6eec6f759ebc8b2693d585d4a",
              "submissions": names, "gold_sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest()}
    (tmp_path / "inputs_manifest.json").write_text(json.dumps(inputs))
    monkeypatch.setattr(e07, "gold_mismatches", lambda *_: 0)
    def cells(path, _):
        k = names.index(path.name)
        result = []
        for i, iid in enumerate(gold):
            if mode == "no_common" and i // 25 == k or mode == "valid" and i == 499:
                result.append(Cell(iid, None, None, None, None))
            elif mode == "inconsistent":
                result.append(Cell(iid, 1, 1, 1, False))
            else:
                resolved = i % 25 <= k
                result.append(Cell(iid, 1, 1 if resolved else 0.5, 1, resolved))
        return result
    monkeypatch.setattr(e07, "load_cells", cells)
    out = tmp_path / "out"
    monkeypatch.setattr("sys.argv", ["analyze", "--data", str(tmp_path), "--out-dir", str(out), "--boot", "3", "--splits", "4"])
    e07.main()
    data = json.loads((out / "analysis_e07.json").read_text(), parse_constant=lambda x: pytest.fail(f"nonfinite JSON {x}"))
    assert data["systems_total"] == count
    with gzip.open(out / "per_cell_e07.jsonl.gz", "rt") as fh:
        assert sum(1 for _ in fh) == count * 500
    if mode == "valid":
        assert data["common_cohort_tasks"] == 499
        assert data["H3_signal_density"]["measured_cells"] == 20 * 499
        assert data["validity_all_declared_systems"]["unmeasured_cells"] == 20
        rows = list(csv.DictReader((out / "per_system_e07.csv").open()))
        assert all(row["common_cohort_tasks"] == "499" for row in rows)
        assert data["H1_scs4c_vs_pass1"]["bootstrap_95"]["tasks"]["defined_draws"]["mae"] == 3
    else:
        assert "H1_scs4c_vs_pass1" not in data
        expected = "STOP" if mode == "inconsistent" else "UNMEASURED" if mode == "no_common" else "UNDERPOWERED"
        assert data["status"].startswith(expected)


@pytest.fixture
def e07_fetch():
    path = Path(__file__).parents[1] / "experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/fetch_e07.py"
    spec = importlib.util.spec_from_file_location("fetch_e07", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failed_prediction_download_does_not_create_false_zeros(e07_fetch, tmp_path, monkeypatch):
    from types import SimpleNamespace
    def run(args, **kwargs):
        if "cp" in args:
            Path(args[-1]).write_text('{"instance_id": "first"}')
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(e07_fetch.subprocess, "run", run)
    assert e07_fetch.sync_s3("verified", "example", tmp_path) == 0
    assert not (tmp_path / "all_preds.jsonl").exists()
    assert not (tmp_path / "all_preds.jsonl.partial").exists()


def test_fetch_rejects_wrong_commit_before_download(e07_fetch, tmp_path, monkeypatch):
    monkeypatch.setattr(e07_fetch.subprocess, "check_output", lambda *a, **k: "wrong-pin")
    monkeypatch.setattr("sys.argv", ["fetch", "--experiments-repo", str(tmp_path), "--out", str(tmp_path / "out"),
                                     "--gold-revision", e07_fetch.GOLD_REVISION])
    with pytest.raises(ValueError, match="locked phase A pins"):
        e07_fetch.main()


def test_fetch_rejects_unverified_cached_gold(e07_fetch, tmp_path, monkeypatch):
    def git(args, **kwargs):
        return e07_fetch.EXPERIMENTS_COMMIT if "rev-parse" in args else "one-system" if "ls-tree" in args else ""
    monkeypatch.setattr(e07_fetch.subprocess, "check_output", git)
    (tmp_path / "gold_tests.jsonl").write_text("{}")
    monkeypatch.setattr("sys.argv", ["fetch", "--experiments-repo", str(tmp_path), "--out", str(tmp_path),
                                     "--gold-revision", e07_fetch.GOLD_REVISION])
    with pytest.raises(ValueError, match="cached gold lacks provenance"):
        e07_fetch.main()



def test_known_official_resolution_survives_missing_test_report(e07, tmp_path):
    (tmp_path / "results.json").write_text(json.dumps({"no_generation": [], "no_logs": ["unknown"], "resolved": ["solved"]}))
    cells = e07.load_cells(tmp_path, {i: (F2P, P2P) for i in ("solved", "unknown")})
    summary = system_summary(cells)
    assert summary["measured"] == 0 and summary["pass1"] is None and summary["scs4c"] is None
    assert summary["pass1_declared"] == 0.5
    r = report(resolved=True)
    del r["tests_status"]
    incomplete = cell_from_report("solved", r, has_patch=True)
    assert not incomplete.measured and incomplete.resolved is True



def test_decimal_constant_is_undefined_despite_roundoff_in_standard_deviation():
    assert pearson([0.1, 0.1, 0.1], [1, 2, 3]) is None
