"""Check experiment 08's pre-test publication gate and conservative judge recovery on synthetic receipts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

REPO = Path(__file__).parents[1]
SCRIPTS = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def judge(tmp_path, monkeypatch):
    if not (REPO / "external/veribench/experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts").is_dir():
        pytest.skip("pinned judge dependencies unavailable")
    module = load("judge_rl4cv_e08")
    monkeypatch.setattr(module, "RESULTS", tmp_path)
    monkeypatch.setattr(module, "STATE", tmp_path / "state.json")
    return module


def transport(judge, name, prompt="prompt"):
    cfg = judge.judge_config(name)
    config = {k: cfg[k] for k in ("max_tokens", "reasoning_effort", "compute_effort") if cfg.get(k)}
    return {"selector": cfg["selector"], "judge_config": name,
            "benchmark": judge.request_benchmark(judge.suite_spec("rl4cv-e08-controls"), name),
            "config": config, "wire_provider_config": {"fallback_models": []}, "fallback": None,
            "system_sha256": "system", "user_sha256": "user", "prompt_sha256": prompt,
            "expected": {"system": "system", "user": "user", "prompt": prompt},
            "status": "measured", "requests_sent": 1}


def test_ambiguous_admission_is_never_replayed(judge, monkeypatch):
    judge.write_json(judge.RESULTS / "judge_pack_controls.json",
                     {"verdict": "PASS", "control_cells": [{"task_id": "synthetic"}]})
    calls = []
    def cli(args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1, "", "network disappeared after send")
    monkeypatch.setattr(judge, "cli", cli)
    assert judge.admit("rl4cv-e08-controls", [judge.CONFIGS[0]], 1) == 1
    first = judge.STATE.read_bytes()
    assert judge.admit("rl4cv-e08-controls", [judge.CONFIGS[0]], 1) == 1
    assert len(calls) == 1
    assert judge.STATE.read_bytes() == first


def test_admitting_after_abrupt_exit_is_fenced(judge, monkeypatch):
    judge.write_json(judge.RESULTS / "judge_pack_controls.json",
                     {"verdict": "PASS", "control_cells": [{"task_id": "synthetic"}]})
    judge.save_state({"runs": {"controls/" + judge.CONFIGS[0]: {"phase": "admitting"}}})
    monkeypatch.setattr(judge, "cli", lambda args: pytest.fail("ambiguous admission replay"))
    assert judge.admit("rl4cv-e08-controls", [judge.CONFIGS[0]], 1) == 1


@pytest.mark.parametrize("mutation", [
    {"selector": "wrong"}, {"fallback": "another-model"}, {"config": {"max_tokens": 32000}},
    {"requests_sent": 3}, {"expected": {}}, {"status": "model_error"},
])
def test_transport_rejects_wrong_or_missing_evidence(judge, mutation):
    name = judge.CONFIGS[0]
    r = transport(judge, name)
    cfg = judge.judge_config(name)
    assert judge.transport_matches(r, {"prompt_sha256": "prompt"}, cfg, name, r["benchmark"])
    r.update(mutation)
    assert not judge.transport_matches(r, {"prompt_sha256": "prompt"}, cfg, name, transport(judge, name)["benchmark"])


def make_controls(judge):
    scores = {"control_oracle": 5, "control_vacuous": 0, "control_blank": 0,
              "control_shuffled": 0, "control_halfdel": 3}
    declared = [{"task_id": k, "kind": k, "prompt_sha256": k} for k in scores]
    judge.write_json(judge.RESULTS / "judge_pack_controls.json",
                     {"verdict": "PASS", "rubric": judge.RUBRIC,
                      "rubric_fingerprint": judge.prompts.rubric_fingerprint(judge.RUBRIC),
                      "control_cells": declared})
    for name in judge.CONFIGS:
        cells = [{"task_id": k, "kind": k, "status": "measured", "score_raw": score,
                  "transport_receipt": transport(judge, name, k)} for k, score in scores.items()]
        judge.write_json(judge.RESULTS / "harvests" / f"cells_controls__{name}.json",
                         {"run_id": "synthetic", "charges_usd": 0, "status_counts": {"measured": 5},
                          "cells": cells, "receipt_inventory": {"missing": [], "extra": [], "duplicates": []}})


def test_controls_require_every_declared_rating_and_actual_transport(judge):
    make_controls(judge)
    assert judge.controls_check() == 0
    p = judge.RESULTS / "harvests" / f"cells_controls__{judge.CONFIGS[0]}.json"
    h = json.loads(p.read_text())
    h["cells"].pop()
    judge.write_json(p, h)
    assert judge.controls_check() == 1
    make_controls(judge)
    h = json.loads(p.read_text())
    del h["cells"][0]["transport_receipt"]["fallback"]
    judge.write_json(p, h)
    assert judge.controls_check() == 1


def test_missing_member_repeat_keeps_fsc_unknown(judge):
    for n, name in enumerate(judge.CONFIGS):
        cells = [{"task_id_vb": "synthetic", "sample_idx": 0, "is_audit_only": False,
                  "item": "synthetic#0", "status": "measured", "score_raw": 5}
                 for _ in range(2 if n == 0 else 3)]
        judge.write_json(judge.RESULTS / "harvests" / f"cells_synthetic__{name}.json",
                         {"charges_usd": 0, "cells": cells})
    assert judge.fsc("synthetic") == 0
    r = json.loads((judge.RESULTS / "fsc_synthetic.json").read_text())
    assert r["cells"]["synthetic#0"]["FSC"] is None
    assert r["n_ratings_measured"] == 5 and r["n_files_complete_3x2"] == 0


@pytest.fixture
def gate(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    module = load("test_admission_e08")
    p = module.pipeline
    res = tmp_path / "results"
    res.mkdir()
    monkeypatch.setattr(p, "REPO", tmp_path)
    monkeypatch.setattr(p, "RES", res)
    return module


def test_test_gate_blocks_before_reading_test_content(gate, monkeypatch):
    monkeypatch.setattr(gate.pipeline, "selection_committed", lambda: None)
    monkeypatch.setattr(gate.pipeline, "ladder_valid", lambda *a: pytest.fail("read beyond selection gate"))
    with pytest.raises(ValueError, match="No committed"):
        gate.check("synthetic", "model", "local")


def test_test_gate_requires_published_bytes_and_all_validation(gate, monkeypatch):
    p = gate.pipeline
    sel = {"verdict": "PARTIAL", "test_manifest": {"systems": [
        {"label": "synthetic", "hf_path": "model", "source": "e08"}]}}
    (p.RES / "selection.json").write_text(json.dumps(sel))
    manifest = {"systems": [dict(sel["test_manifest"]["systems"][0], in_test=True)],
                "selection_sha256": p.sha((p.RES / "selection.json").read_bytes())}
    (p.RES / "test_manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(p, "selection_committed", lambda: sel)
    monkeypatch.setattr(p, "git", lambda *args: subprocess.CompletedProcess(args, 0,
        (p.RES / args[-1].split("/")[-1]).read_text() if args[0] == "show" else "", ""))
    monkeypatch.setattr(p, "train_log_ok", lambda size: True)
    monkeypatch.setattr(p, "exports_ok", lambda size: True)
    monkeypatch.setattr(p, "ladder_valid", lambda *args: {"valid": True})
    assert gate.check("synthetic", "model", "local")["verdict"] == "PASS"
    monkeypatch.setattr(p, "ladder_valid", lambda *args: {"valid": False})
    with pytest.raises(ValueError, match="Full validation"):
        gate.check("synthetic", "model", "local")
    monkeypatch.setattr(p, "git", lambda *args: subprocess.CompletedProcess(args, 0, "unpublished", ""))
    with pytest.raises(ValueError, match="exact published"):
        gate.check("synthetic", "model", "local")


def test_cron_judge_cli_uses_its_interpreter_bin(judge, monkeypatch, tmp_path):
    executable = tmp_path / "bin" / "python"
    monkeypatch.setattr(judge.sys, "executable", str(executable))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-must-be-removed")
    actual = judge.env()
    assert actual["PATH"].split(":")[0] == str(executable.parent)
    assert "OPENAI_API_KEY" not in actual
    assert actual["VALKYRIE_CONFIG_PATH"] == str(judge.WORK / "private" / "valkyrie.yaml")


@pytest.mark.parametrize("error,started", [
    (FileNotFoundError(2, "missing client"), False),
    (subprocess.TimeoutExpired(["valk", "run", "start"], 1800), True),
])
def test_client_launch_failure_is_recorded_and_never_replayed(judge, monkeypatch, error, started):
    judge.write_json(judge.RESULTS / "judge_pack_controls.json",
                     {"verdict": "PASS", "control_cells": [{"task_id": "synthetic"}]})
    calls = []
    def cli(args):
        calls.append(args)
        raise error
    monkeypatch.setattr(judge, "cli", cli)
    assert judge.admit("rl4cv-e08-controls", [judge.CONFIGS[0]], 1) == 1
    entry = judge.load_state()["runs"]["controls/" + judge.CONFIGS[0]]
    assert entry["phase"] == "admission_failed"
    assert entry["subprocess_started"] is started
    assert entry["retry_blocked"]
    assert judge.admit("rl4cv-e08-controls", [judge.CONFIGS[0]], 1) == 1
    assert len(calls) == 1
