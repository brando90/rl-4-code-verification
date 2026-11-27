"""CPU checks for the 11-27-2026 02B v2 config and forecast gate. No outcome is read."""
import importlib.util
import json
from pathlib import Path

import pytest

PREP = Path("experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026")


def load(name):
    path = PREP / name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_config_matches_the_readiness_manifest_and_stays_unadmitted():
    validator = load("validate_production_config_11-27-2026.py")
    manifest = json.loads(validator.MANIFEST.read_text())
    report = validator.validate(validator.load(), manifest)
    assert report["admitted"] is False
    assert report["status"] == "PREPARED_NOT_ADMITTED"
    assert report["model"] == {
        "id": "Qwen/Qwen3-1.7B-Base",
        "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
    }
    assert any("sorryAx" in blocker for blocker in report["blockers"])
    assert any("paper_frozen_14b_model" in blocker for blocker in report["blockers"])


def test_validator_rejects_an_invented_learning_rate():
    validator = load("validate_production_config_11-27-2026.py")
    config = validator.load()
    config["unset_because_the_locked_protocol_does_not_name_them"]["learning_rate"] = 1e-6
    manifest = json.loads(validator.MANIFEST.read_text())
    report = validator.validate(config, manifest)
    assert any("learning_rate" in blocker for blocker in report["blockers"])


def test_forecast_script_writes_nothing_and_refuses_a_paper_coefficient_stand_in(tmp_path, capsys):
    freezer = load("forecast_freeze_11-27-2026.py")
    assert freezer.main([]) == 2
    assert "NOT FROZEN" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []
    forecast = freezer.skeleton()
    forecast["prediction"] = {
        "winning_environment": "full_file",
        "expected_external_test_delta": 0.01,
        "rho_full_file": 1.0,
        "H_full_file": 0.5,
        "rho_theorem_completion": 1.0,
        "H_theorem_completion": 0.4,
        "standardizer_source": "paper_frozen_14b_model",
    }
    path = tmp_path / "prediction.json"
    path.write_text(json.dumps(forecast))
    assert freezer.main(["--forecast", str(path), "--commit-freeze", "--out-dir", str(tmp_path / "out")]) == 2
    assert not (tmp_path / "out").exists()


def test_forecast_freeze_of_a_non_synthetic_prediction_is_append_only(tmp_path):
    freezer = load("forecast_freeze_11-27-2026.py")
    forecast = freezer.skeleton()
    forecast["prediction"] = {
        "winning_environment": "theorem_completion",
        "expected_external_test_delta": 0.0,
        "rho_full_file": 2.0,
        "H_full_file": 0.2,
        "rho_theorem_completion": 3.0,
        "H_theorem_completion": 0.8,
        "standardizer_source": "unit-test probes, not a scientific 02B forecast",
    }
    path = tmp_path / "prediction.json"
    path.write_text(json.dumps(forecast))
    out = tmp_path / "forecasts"
    assert freezer.main(["--forecast", str(path), "--out-dir", str(out), "--commit-freeze"]) == 0
    frozen = json.loads((out / "02b_v2_environment_choice.json").read_text())
    assert frozen["prediction"]["winning_environment"] == "theorem_completion"
    assert freezer.main(["--forecast", str(path), "--out-dir", str(out), "--commit-freeze"]) == 2
    with pytest.raises(ValueError, match="outcomes"):
        freezer.assert_ready(forecast, outcomes_observed=True, outcome_paths=[])
    outcome = tmp_path / "scored_cells.json"
    outcome.write_text("{}")
    with pytest.raises(ValueError, match="outcome"):
        freezer.assert_ready(forecast, outcomes_observed=False, outcome_paths=[str(outcome)])
