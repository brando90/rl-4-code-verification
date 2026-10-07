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
    assert cells[1].unmeasured_reason == "no report file" and cells[0].unmeasured_reason is None
    # An authoritative report wins over stale aggregate no_generation evidence.
    rp = tmp_path / "logs/empty/report.json"
    rp.parent.mkdir(parents=True)
    rp.write_text(json.dumps({"empty": report(f2p_ok=F2P, p2p_ok=P2P, resolved=True)}))
    assert cell_score(e07.load_cells(tmp_path, {"empty": ([], [])})[0]) == 1


def test_bad_report_without_patch_evidence_stays_unmeasured(e07, tmp_path):
    rp = tmp_path / "logs/i/report.json"
    rp.parent.mkdir(parents=True)
    rp.write_text('{"i":')
    cell = e07.load_cells(tmp_path, {"i": ([], [])})[0]
    assert not cell.measured and cell.unmeasured_reason == "report file empty, malformed or for another instance"
    rp.write_text(json.dumps({"i": {"patch_successfully_applied": True}}))
    assert not e07.load_cells(tmp_path, {"i": ([], [])})[0].measured


def test_flat_report_shape_is_read_but_another_instance_is_not(e07, tmp_path):
    rp = tmp_path / "logs/i/report.json"
    rp.parent.mkdir(parents=True)
    rp.write_text(json.dumps(report(f2p_ok=F2P, p2p_ok=P2P, resolved=True)))  # sb-cli / mini-SWE-agent shape: no instance key
    assert cell_score(e07.load_cells(tmp_path, {"i": (F2P, P2P)})[0]) == 1
    rp.write_text(json.dumps({"other": report(f2p_ok=F2P, p2p_ok=P2P, resolved=True)}))
    assert not e07.load_cells(tmp_path, {"i": (F2P, P2P)})[0].measured
    rp.write_text("")
    assert e07.load_cells(tmp_path, {"i": (F2P, P2P)})[0].unmeasured_reason == "report file empty, malformed or for another instance"


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
        assert data["sensitivity_one_system_per_base_model"]["status"].startswith("unavailable")  # no metadata in this fixture
        # The renderer reproduces every published number from these files and never invents one.
        import subprocess, sys
        render = Path(__file__).parents[1] / "experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/render_results_e07.py"
        text = subprocess.run([sys.executable, str(render), "--results", str(out), "--top", "3"], capture_output=True, text=True, check=True).stdout
        assert "| Included systems (≥ 475/500 measured cells) | 20 |" in text and "### H2 — held-out prediction" in text
        assert f"| {data['H1_scs4c_vs_pass1']['spearman']:.3f} |" in text.replace("Spearman ρ | ", "")
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
    seen = []
    def run(args, **kwargs):
        seen.append(args)
        if "cp" in args:
            Path(args[-1]).write_text('{"instance_id": "first"}')
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(e07_fetch.subprocess, "run", run)
    assert e07_fetch.sync_s3("s3://swe-bench-submissions/bash-only/example/logs/", tmp_path) == 0
    assert not (tmp_path / "all_preds.jsonl").exists()
    assert not (tmp_path / "all_preds.jsonl.partial").exists()
    # The sync and the predictions download both derive from the resolved logs URL, not the folder name.
    assert "s3://swe-bench-submissions/bash-only/example/logs/" in seen[0]
    assert "s3://swe-bench-submissions/bash-only/example/all_preds.jsonl" in seen[1]


def test_invalid_predictions_are_discarded_rather_than_read_as_no_generation(e07_fetch, tmp_path):
    pending = tmp_path / "all_preds.jsonl.partial"
    pending.write_text('{"instance_id": "a", "model_patch": "diff"}\n{"instance_id": 7}\n')
    with pytest.raises(ValueError, match="discarded"):
        e07_fetch.install_predictions(pending, tmp_path)
    assert not pending.exists() and not (tmp_path / "all_preds.jsonl").exists()
    pending.write_text('{"instance_id": "a", "model_patch": ""}\n')
    e07_fetch.install_predictions(pending, tmp_path)
    assert (tmp_path / "all_preds.jsonl").is_file() and not pending.exists()


def _metadata_dir(root, name, assets):
    import yaml
    d = root / name
    d.mkdir(parents=True)
    (d / "metadata.yaml").write_text(yaml.safe_dump({"assets": assets, "info": {"name": name}}))
    return d


def test_resolve_source_uses_metadata_before_the_folder_name(e07_fetch, tmp_path):
    live = {"s3://swe-bench-submissions/bash-only/mini_x/logs", "s3://swe-bench-submissions/verified/20250805-openhands/logs",
            "s3://swe-bench-submissions/verified/plain/logs"}
    exists = lambda url: url in live  # noqa: E731
    # A self-hosted repository wins outright, without any S3 listing.
    gh = _metadata_dir(tmp_path, "gh", {"repo": "https://github.com/someone/gh/", "logs": "https://github.com/someone/gh/tree/main/logs"})
    assert e07_fetch.resolve_source(gh, "verified", exists) == {"kind": "github", "repo": "https://github.com/someone/gh", "rule": "assets.repo"}
    # assets.logs is authoritative even when it disagrees with the folder name (hyphen versus underscore, bash-only prefix).
    hyphen = _metadata_dir(tmp_path, "20250805_openhands", {"logs": "s3://swe-bench-submissions/verified/20250805-openhands/logs", "trajs": None})
    assert e07_fetch.resolve_source(hyphen, "verified", exists)["logs"] == "s3://swe-bench-submissions/verified/20250805-openhands/logs"
    # logs: null falls back to the logs/ sibling of the trajectories prefix, and the rule is recorded.
    null_logs = _metadata_dir(tmp_path, "mini_x", {"logs": None, "trajs": "s3://swe-bench-submissions/bash-only/mini_x/trajs"})
    got = e07_fetch.resolve_source(null_logs, "verified", exists)
    assert (got["logs"], got["rule"]) == ("s3://swe-bench-submissions/bash-only/mini_x/logs", "logs sibling of assets.trajs")
    # A relative path falls through to the folder-name convention under the split.
    plain = _metadata_dir(tmp_path, "plain", {"logs": "evaluation/verified/plain/logs", "trajs": None})
    assert e07_fetch.resolve_source(plain, "verified", exists)["rule"] == "folder name under split"
    # A metadata URL that names the submission root gets its logs/ suffix; a letter-case mismatch falls back to the
    # folder name under the same parent prefix as the metadata URL.
    live.add("s3://swe-bench-submissions/bash-only/root_only/logs")
    root_only = _metadata_dir(tmp_path, "root_only", {"logs": "s3://swe-bench-submissions/bash-only/root_only", "trajs": None})
    got = e07_fetch.resolve_source(root_only, "verified", exists)
    assert (got["logs"], got["rule"]) == ("s3://swe-bench-submissions/bash-only/root_only/logs", "assets.logs + /logs")
    live.add("s3://swe-bench-submissions/bash-only/mini_kimi-k2/logs")
    cased = _metadata_dir(tmp_path, "mini_kimi-k2", {"logs": "s3://swe-bench-submissions/bash-only/mini_Kimi-K2/logs", "trajs": None})
    got = e07_fetch.resolve_source(cased, "verified", exists)
    assert (got["logs"], got["rule"]) == ("s3://swe-bench-submissions/bash-only/mini_kimi-k2/logs", "folder name under the assets.logs parent prefix")
    # Nothing public: every candidate is reported, none is invented.
    gone = _metadata_dir(tmp_path, "gone", {"logs": "s3://swe-bench-submissions/verified/elsewhere/logs", "trajs": None})
    got = e07_fetch.resolve_source(gone, "verified", exists)
    assert got["kind"] == "none" and got["tried"] == ["s3://swe-bench-submissions/verified/elsewhere/logs", "s3://swe-bench-submissions/verified/gone/logs"]


def test_json_array_predictions_are_rewritten_as_json_lines(e07_fetch, tmp_path):
    pending = tmp_path / "all_preds.jsonl.partial"
    pending.write_text(json.dumps([{"instance_id": "a", "model_patch": "diff"}, {"instance_id": "b", "model_patch": ""}], indent=2))
    e07_fetch.install_predictions(pending, tmp_path)
    lines = (tmp_path / "all_preds.jsonl").read_text().splitlines()
    assert [json.loads(l)["instance_id"] for l in lines] == ["a", "b"]


def test_logs_layout_counts_legacy_eval_logs(e07_fetch, monkeypatch):
    listing = ["all_preds.jsonl", "astropy__astropy-12907.sub.eval.log", "django__django-11099.sub.eval.log", "x__x-1/"]
    monkeypatch.setattr(e07_fetch, "s3_list", lambda url: listing)
    assert e07_fetch.logs_layout("s3://b/verified/sub/logs") == {"logs_entries": 4, "legacy_eval_logs": 2, "instance_dirs": 1}


def test_sync_github_copies_only_reports_and_predictions(e07_fetch, tmp_path, monkeypatch):
    from types import SimpleNamespace
    def run(args, **kwargs):
        if args[:2] == ["git", "clone"]:
            clone = Path(args[-1])
            for iid, body in (("a__a-1", {"a__a-1": report(resolved=True)}), ("b__b-2", {"b__b-2": report()})):
                (clone / "logs" / iid).mkdir(parents=True)
                (clone / "logs" / iid / "report.json").write_text(json.dumps(body))
                (clone / "logs" / iid / "test_output.txt.gz").write_bytes(b"x")
            (clone / "all_preds.jsonl").write_text(json.dumps({"instance_id": "a__a-1", "model_patch": "diff"}) + "\n")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(e07_fetch.subprocess, "run", run)
    monkeypatch.setattr(e07_fetch.subprocess, "check_output", lambda *a, **k: "abc123\n")
    dest = tmp_path / "dest"
    dest.mkdir()
    assert e07_fetch.sync_github("https://github.com/x/y", dest, tmp_path / "clones") == (2, "abc123")
    assert sorted(p.name for p in (dest / "logs").iterdir()) == ["a__a-1", "b__b-2"]
    assert not list((dest / "logs").glob("*/test_output.txt.gz"))
    assert (dest / "all_preds.jsonl").is_file()
    assert not list((tmp_path / "clones").iterdir())  # the temporary clone is removed


def test_fetch_submission_keeps_downloaded_reports_when_predictions_fail(e07_fetch, tmp_path, monkeypatch):
    from types import SimpleNamespace
    repo = tmp_path / "experiments"
    _metadata_dir(repo / "evaluation" / "verified", "sub", {"logs": "s3://swe-bench-submissions/verified/sub/logs", "trajs": None})
    monkeypatch.setattr(e07_fetch, "s3_prefix_exists", lambda url: True)
    monkeypatch.setattr(e07_fetch, "s3_list", lambda url: ["x__x-1/"])
    def run(args, **kwargs):
        if "sync" in args:
            dest = args[next(i for i, a in enumerate(args) if a.startswith("s3://")) + 1]
            rp = Path(dest) / "x__x-1" / "report.json"
            rp.parent.mkdir(parents=True)
            rp.write_text("{}")
        elif "cp" in args:
            Path(args[-1]).write_text("not json")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(e07_fetch.subprocess, "run", run)
    args = SimpleNamespace(experiments_repo=repo, split="verified", out=tmp_path / "out")
    entry = e07_fetch.fetch_submission(args, "sub")
    assert entry["reports"] == 1 and entry["error"].startswith("ValueError") and entry["source_rule"] == "assets.logs"
    assert (entry["logs_entries"], entry["legacy_eval_logs"], entry["instance_dirs"]) == (1, 0, 1)
    assert not (tmp_path / "out" / "submissions" / "sub" / "all_preds.jsonl").exists()


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


def test_per_instance_details_supply_official_resolution_and_disagreements(e07, tmp_path):
    (tmp_path / "per_instance_details.json").write_text(json.dumps({"a": {"resolved": True, "cost": 1}, "b": {"resolved": False}}))
    gold = {i: (F2P, P2P) for i in ("a", "b", "c")}
    assert e07.official_resolution(tmp_path) == (set(), {"a"})
    cells = e07.load_cells(tmp_path, gold)
    assert [c.resolved for c in cells] == [True, False, False] and all(c.unmeasured_reason == "no report file" for c in cells)
    for iid, resolved in (("a", False), ("b", False)):  # the report for "a" contradicts the official flag
        rp = tmp_path / "logs" / iid / "report.json"
        rp.parent.mkdir(parents=True)
        rp.write_text(json.dumps({iid: report(f2p_ok=F2P, p2p_ok=P2P, resolved=resolved)}))
    assert e07.official_disagreements(tmp_path, gold) == {"compared": 2, "disagreements": 1, "examples": ["a"]}
    assert e07.official_disagreements(tmp_path / "nowhere", gold) is None
    (tmp_path / "logs" / "c").mkdir()
    (tmp_path / "logs" / "c" / "report.json").write_text(json.dumps({"c": {"patch_exists": True, "patch_is_None": False, "patch_successfully_applied": True}}))
    reasons = {c.instance_id: c.unmeasured_reason for c in e07.load_cells(tmp_path, gold) if not c.measured}
    assert reasons == {"c": "report lacks gate flags or per-test status"}


def test_exclusion_reason_names_counts_source_and_fetch_error(e07):
    cells = [Cell("a", 1, 1, 1, True), Cell("b", None, None, None, None, unmeasured_reason="no report file"),
             Cell("c", None, None, None, None, unmeasured_reason="no report file")]
    text = e07.exclusion_reason(cells, {"source": "github:https://github.com/x/y", "reports": 1, "error": "CalledProcessError: clone"}, 2.85)
    assert text == ("1/3 measured cells, below the 2.85 inclusion threshold; logs source github:https://github.com/x/y (1 report files); "
                    "fetch error: CalledProcessError: clone; 2 cells: no report file")


def test_base_model_sensitivity_keeps_latest_named_submission_per_model(e07, tmp_path):
    import yaml
    gold_ids = [f"task_{i}" for i in range(40)]
    included = {}
    meta = {"20250101_a_gpt": "GPT 5", "20250301_b_gpt": "GPT 5", "20250201_c_opus": "Claude Opus 4.5", "20250401_d_opus": "Claude 4.5 Opus",
             "20250501_e_undisclosed": "Undisclosed", "20250601_f_gemini": "Gemini 3 Pro", "20250701_g_nometa": None}
    for k, (name, model) in enumerate(meta.items()):
        included[name] = [Cell(iid, 1, 1 if i % 7 <= k else 0.5, 1, i % 7 <= k) for i, iid in enumerate(gold_ids)]
        d = tmp_path / "submissions" / name
        d.mkdir(parents=True)
        if model is not None:
            (d / "metadata.yaml").write_text(yaml.safe_dump({"tags": {"model_display": model}}))
    out = e07.base_model_sensitivity(included, gold_ids, tmp_path, np.random.default_rng(0), boot=3, splits=4, size=10)
    assert out["systems"] == {"Gemini 3 Pro": "20250601_f_gemini", "GPT 5": "20250301_b_gpt", "Claude 4.5 Opus": "20250401_d_opus"}
    assert set(out["skipped_systems"]) == {"20250501_e_undisclosed", "20250701_g_nometa"}
    assert out["n_systems"] == 3 and out["status"].startswith("computed (fewer than 20")
    assert list(out["H2_held_out_prediction"]) == ["10"] and out["H1_scs4c_vs_pass1"]["n_systems"] == 3
    json.dumps(out, allow_nan=False)
    assert e07.base_model_sensitivity(dict(list(included.items())[:2]), gold_ids, tmp_path, np.random.default_rng(0), 3, 4)["status"].startswith("unavailable")



def test_decimal_constant_is_undefined_despite_roundoff_in_standard_deviation():
    assert pearson([0.1, 0.1, 0.1], [1, 2, 3]) is None
