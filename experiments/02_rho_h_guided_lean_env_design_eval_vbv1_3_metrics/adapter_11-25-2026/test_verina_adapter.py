"""11-25-2026: Check the pinned real VERINA panel and candidate failures with actual Lean."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

import pytest


HERE = Path(__file__).resolve().parent
MANIFEST = (
    HERE.parent
    / "phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/results"
    / "verina_external24_candidate_manifest_2026-10-06.json"
)
MANIFEST_SHA256 = "026fd9ed3058f28505a00ac2329e6ca36c872ea770e95a7e6f343cdcfea8ddef"
spec = importlib.util.spec_from_file_location("at3598_verina_adapter", HERE / "verina_adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
ADAPTER_SHA256 = adapter.sha((HERE / "verina_adapter.py").read_bytes())


def test_axiom_whitelist_rejects_unknown_unicode_names():
    assert not adapter.axioms_allowed("'f' depends on axioms: [Ω]", 1)
    assert not adapter.axioms_allowed("'f' depends on axioms: [«bad axiom»]", 1)
    assert adapter.axioms_allowed("'f' depends on axioms: [propext, Classical.choice, Quot.sound]", 1)


@pytest.fixture(scope="module")
def manifest():
    assert adapter.sha(MANIFEST.read_bytes()) == MANIFEST_SHA256
    value = json.loads(MANIFEST.read_text())
    assert len(value["tasks"]) == len({r["task_id"] for r in value["tasks"]}) == 24
    assert value["source"]["commit"] == "66b3ce5014edafb20cb26b87c681e7f31847249f"
    return value


@pytest.fixture(scope="module")
def real_root():
    path = os.environ.get("VERINA_ROOT")
    if not path:
        pytest.skip("Set VERINA_ROOT to the pinned real VERINA checkout; no mock support count.")
    root = Path(path)
    assert (root / "datasets/verina").is_dir()
    return root


@pytest.fixture(scope="module")
def lean_env():
    executable = os.environ.get("VERINA_LEAN")
    library_path = os.environ.get("VERINA_LEAN_PATH")
    if not executable or library_path is None:
        pytest.skip("Set VERINA_LEAN and VERINA_LEAN_PATH for actual Lean 4.22.0 checks.")
    lean = Path(executable)
    version = subprocess.check_output([str(lean), "--version"], text=True)
    assert "version 4.22.0," in version
    return lean, library_path


@pytest.fixture
def first_duplicate(real_root, manifest):
    row = next(r for r in manifest["tasks"] if r["task_id"] == "verina_advanced_12")
    task = adapter.load_task(real_root, row)
    assert task["signature"]["name"] == "firstDuplicate"
    assert task["signature"]["return_type"] == "Option Int"
    return task


def test_wrong_implementation_is_measured_against_identical_requirements(first_duplicate, lean_env, tmp_path):
    """Always returning none is type-correct but fails the six duplicate-containing inputs."""
    lean, lean_path = lean_env
    good = adapter.evaluate(
        first_duplicate, first_duplicate["candidate"], lean, lean_path, tmp_path / "good", timeout=120
    )
    wrong = dict(first_duplicate["candidate"], code="  none\n")
    bad = adapter.evaluate(first_duplicate, wrong, lean, lean_path, tmp_path / "wrong", timeout=120)
    assert good["endpoint_supported"] and bad["endpoint_supported"]
    assert good["n_tests"] == bad["n_tests"] == 8
    assert good["n_passed"] == 8
    assert bad["n_passed"] == 2
    assert [r["passed"] for r in bad["behavioral_tests"]] == [False, False, True, False, True, False, False, False]
    assert good["candidate_sha256"] != bad["candidate_sha256"]
    for field in ("source_sha256", "interface_sha256", "requirements_sha256", "endpoint_sha256"):
        assert good[field] == bad[field]
    assert (tmp_path / "good/Endpoint.lean").read_bytes() == (tmp_path / "wrong/Endpoint.lean").read_bytes()
    assert "firstDuplicate_postcond" not in (tmp_path / "wrong/Candidate.lean").read_text()


def test_wrong_return_type_cannot_satisfy_frozen_interface(first_duplicate, lean_env, tmp_path):
    lean, lean_path = lean_env
    wrong = dict(first_duplicate["candidate"], code="  true\n")
    result = adapter.evaluate(first_duplicate, wrong, lean, lean_path, tmp_path / "wrong_type", timeout=120)
    assert result["candidate_compile_rc"] != 0
    assert not result["endpoint_supported"]
    assert not (tmp_path / "wrong_type/Endpoint.lean").exists()


def test_transitive_sorry_axiom_rejected_after_actual_lean_compile(first_duplicate, lean_env, tmp_path):
    """A helper can hide an axiom from token checks; Lean's transitive axiom report must reject it."""
    lean, lean_path = lean_env
    untrusted = dict(
        first_duplicate["candidate"],
        solution_aux="def hiddenWitness : Option Int := sorryAx (Option Int) true\n",
        code="  hiddenWitness\n",
    )
    result = adapter.evaluate(first_duplicate, untrusted, lean, lean_path, tmp_path / "transitive_axiom", timeout=120)
    assert result["candidate_compile_rc"] == 0
    assert not result["candidate_axioms_allowed"]
    assert not result["endpoint_supported"]
    assert "sorryAx" in (tmp_path / "transitive_axiom/candidate.stdout.txt").read_text()
    assert not (tmp_path / "transitive_axiom/Endpoint.lean").exists()


@pytest.mark.parametrize("fragment", [
    "instance : BEq (Option Int) where beq := fun _ _ => true\n",
    'def marker := "--" instance : BEq (Option Int) where beq := fun _ _ => true\n',
    "attribute [instance] fakeEquality\n",
    "notation:50 a \" == \" b => true\n",
    "def _root_.AdapterEvaluator.firstDuplicate := fun (_ : List Int) (_ : True) => none\n",
    "@[implemented_by fake] def hidden : Option Int := none\n",
    "@[extern \"fake\"] def hidden : Option Int := none\n",
])
def test_candidate_cannot_replace_evaluator_primitives(first_duplicate, fragment):
    changed = dict(first_duplicate["candidate"], solution_aux=fragment)
    with pytest.raises(ValueError, match="unsupported candidate command|forbidden trust"):
        adapter.candidate_source(first_duplicate, changed)


def test_real_frozen_24_task_panel_support(manifest, real_root, lean_env, tmp_path):
    """Compile and measure all 24 real tasks, retaining each source and compiler log."""
    lean, lean_path = lean_env
    started_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for source_row in manifest["tasks"]:
        task = adapter.load_task(real_root, source_row)
        rows.append(adapter.evaluate(task, task["candidate"], lean, lean_path, tmp_path / source_row["task_id"], timeout=120))
        (tmp_path / "real24_receipt.json").write_text(json.dumps({"rows": rows}, indent=2) + "\n")
    supported = sum(row["endpoint_supported"] for row in rows)
    receipt = {
        "date": "11-25-2026",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "harness": "Codex CLI, GPT-6 Astra ultra (Vals account); pytest invokes Lean 4.22.0",
        "manifest_sha256": MANIFEST_SHA256,
        "source_commit": manifest["source"]["commit"],
        "adapter_sha256": ADAPTER_SHA256,
        "lean_version": subprocess.check_output([str(lean), "--version"], text=True).strip(),
        "n_declared": 24,
        "n_supported": supported,
        "scope": "fixed behavioral tests plus kernel precondition witnesses; no reference proof acceptance, no DT",
        "rows": rows,
    }
    (tmp_path / "real24_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    assert adapter.sha((HERE / "verina_adapter.py").read_bytes()) == ADAPTER_SHA256, "Adapter changed during measured test"
    assert supported == 24, [(row["task_id"], row["endpoint_status"]) for row in rows if not row["endpoint_supported"]]
    assert all(row["candidate_axioms_allowed"] and row["nonvacuity_witnesses_allowed"] for row in rows)
    assert all(len(row["behavioral_tests"]) == row["n_tests"] > 0 for row in rows)
