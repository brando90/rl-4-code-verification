#!/usr/bin/env python3
"""Deterministic fixture: metadata recovery is idempotent and rejects any other error."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("finalize_terminal_metadata.py")
spec = importlib.util.spec_from_file_location("e20_finalize_terminal_metadata", HELPER)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def make_fixture(root: Path):
    out, receipts, forecasts = root / "out", root / "receipts", root / "forecasts"
    for path in (out, receipts, forecasts):
        path.mkdir(parents=True)
    driver = root / "analyze_phase0_e20.py"
    driver.write_text("# frozen fixture driver\n")
    driver_sha = hashlib.sha256(driver.read_bytes()).hexdigest()
    forecast_path = forecasts / "phase0_item_parameters_e20.json"
    forecast = {
        "input_identity": "pending",
        "model": "explanatory",
        "G0": module.EXPECTED_GATE,
        "task_ids": [f"t{i}" for i in range(539)],
        **{k: [0.5] * 539 for k in ("a", "d", "p_strict", "p_active", "p_strict_at_theta0", "p_active_at_theta0")},
    }
    provenance = {"software": {str(driver): driver_sha}}
    identity = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    forecast["input_identity"] = identity
    canonical = json.dumps(forecast, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    forecast_path.write_text(canonical + "\n")
    forecast_sha = hashlib.sha256(canonical.encode()).hexdigest()
    forecast_path.with_suffix(".sha256").write_text(f"{forecast_sha}  {forecast_path.name}\n")
    freeze = {"file": str(forecast_path), "name": "phase0_item_parameters_e20", "sha256": forecast_sha,
              "status": "frozen and verified"}
    analysis = {"status": "complete: Phase 0b analysis", "trainer_status": "FAILED; unchanged",
                "smooth_status": "available", "dimensionality_status": "available", "inputs": identity,
                "G0": module.EXPECTED_GATE, "freeze": freeze}
    fit = {"converged": True, "max_abs_grad": 1e-6, "check_grid_max_abs_grad": 1e-6}
    convergence = [{**fit, "fold": fold, "model": model} for fold in range(5)
                   for model in ("random_intercept", "explanatory", "random_intercept_1pl", "explanatory_1pl", "features_only")]
    g0 = {"tasks": 539, "groups": 400, "selected_model": "explanatory", "gate": module.EXPECTED_GATE,
          "models": {"explanatory": {"status": "available", "auc": module.EXPECTED_GATE["auc"],
                                      "log_loss": module.EXPECTED_GATE["log_loss"]}}, "convergence": convergence}
    dim = {"status": "available", "paired_cells_declared": 4312, "paired_cells_observed": 4202,
           "paired_cells_scored": 4202, "full_fits": {"tied": fit, "untied": fit},
           "fold_fits": [{**fit, "fold": fold, "model": model, "joint_log_likelihood": -1.0}
                         for fold in range(5) for model in ("tied", "untied")], "untied_minus_tied": -1.0}
    write_json(out / "analysis_e20.json", analysis)
    write_json(out / "primary_g0.json", g0)
    write_json(out / "dimensionality.json", dim)
    write_json(out / "smooth_analysis.json", {"status": "available"})
    write_json(out / "input_pins_e20.json", {"identity": identity, **provenance})
    write_json(out / "freeze_receipt.json", freeze)
    write_json(out / "progress.json", {"phase": "dimensionality_fold4_untied"})
    write_json(out / "failure.json", module.EXPECTED_FAILURE)
    run_receipt = receipts / "phase0b_run_receipt.json"
    write_json(run_receipt, {"status": "FAILED", "returncode": 1, "driver_sha256": driver_sha,
                             "trainer_status": "FAILED; unchanged", "started": "10-21-2026 19:39:27 PDT",
                             "ended": "10-21-2026 20:27:21 PDT", "elapsed_wall_seconds": 2873.0})
    cfg = module.Config(root, out, forecast_path, run_receipt, driver,
                        receipts / "phase0b_terminal_failure_original.json",
                        out / "phase0b_completion_recovery_receipt.json", driver_sha)

    def native_verify(path):
        text = path.read_text().rstrip("\n")
        return hashlib.sha256(text.encode()).hexdigest() == path.with_suffix(".sha256").read_text().split()[0]

    return cfg, native_verify


def main():
    fixed = dt.datetime(2026, 10, 22, 3, 30, 0, tzinfo=dt.timezone.utc)
    with tempfile.TemporaryDirectory() as td:
        cfg, native = make_fixture(Path(td))
        original_failure = (cfg.out / "failure.json").read_bytes()
        first = module.recover(cfg, now=fixed, pid=123, forecast_verifier=native)
        receipt_bytes = cfg.recovery_receipt.read_bytes()
        second = module.recover(cfg, now=fixed, pid=123, forecast_verifier=native)
        assert first["status"] == "recovered" and first["mutated"] is True
        assert second["status"] == "already complete; verified" and second["mutated"] is False
        assert cfg.recovery_receipt.read_bytes() == receipt_bytes
        assert cfg.archive.read_bytes() == original_failure and not (cfg.out / "failure.json").exists()
        assert json.loads((cfg.out / "progress.json").read_text())["phase"] == "complete"
    with tempfile.TemporaryDirectory() as td:
        cfg, native = make_fixture(Path(td))
        wrong = dict(module.EXPECTED_FAILURE, error="some other failure")
        write_json(cfg.out / "failure.json", wrong)
        try:
            module.recover(cfg, now=fixed, pid=123, forecast_verifier=native)
        except module.RecoveryError as exc:
            assert "unexpected terminal error" in str(exc)
        else:
            raise AssertionError("wrong terminal error was accepted")
        assert (cfg.out / "failure.json").exists()
        assert not cfg.archive.exists() and not cfg.recovery_receipt.exists()
    print("IDEMPOTENCE_AND_WRONG_ERROR_REJECTION_OK")


if __name__ == "__main__":
    main()
