#!/usr/bin/env python3
"""Recover only Experiment 20 Phase 0b terminal metadata after the known final stamp TypeError.

The numerical analysis and forecast must already be complete.  This helper verifies them,
archives the exact terminal failure bytes, records recovery, writes a safe complete progress
receipt, then removes only the stale active failure marker.  It never runs a fit or changes
the original driver, run receipt, numerical outputs, input pins, or frozen forecast.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


E20 = "20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013"
EXPECTED_DRIVER_SHA = "24c2a19ee63d1c25a6610834cdd7976f8b0b267e66bdc5c1f5bf6ed8c83b59cd"
EXPECTED_FAILURE = {
    "error": "dict() got multiple values for keyword argument 'trainer_status'",
    "error_type": "TypeError",
    "status": "BLOCKED",
    "trainer_status": "FAILED; unchanged",
}
EXPECTED_GATE = {
    "auc": 0.9312699796570765,
    "auc_threshold": 0.7,
    "baseline_log_loss": 0.4811850677871736,
    "log_loss": 0.3044314614670819,
    "passed": True,
    "selected_model": "explanatory",
    "status": "evaluated",
    "threshold_source": "E20 PROTOCOL section 3; E13 F2",
}
GRAD_TOL = 1e-4
VERSION = 1


class RecoveryError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"cannot read valid JSON {path}: {exc}") from exc


def require(condition: bool, message: str):
    if not condition:
        raise RecoveryError(message)


def atomic_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text)
    with tmp.open("rb") as fh:
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def archive_exact(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, f"existing failure archive differs: {path}")
        return
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(data)
    with tmp.open("rb") as fh:
        os.fsync(fh.fileno())
    try:
        os.link(tmp, path)
    except FileExistsError:
        require(path.read_bytes() == data, f"concurrent failure archive differs: {path}")
    finally:
        tmp.unlink(missing_ok=True)
    require(path.read_bytes() == data, "failure archive did not preserve exact bytes")


def finite_gradient(fit: dict) -> bool:
    return fit.get("converged") is True and all(
        isinstance(fit.get(k), (int, float)) and math.isfinite(fit[k]) and fit[k] <= GRAD_TOL
        for k in ("max_abs_grad", "check_grid_max_abs_grad")
    )


@dataclass(frozen=True)
class Config:
    repo: Path
    out: Path
    forecast: Path
    run_receipt: Path
    driver: Path
    archive: Path
    recovery_receipt: Path
    expected_driver_sha: str = EXPECTED_DRIVER_SHA

    @classmethod
    def from_repo(cls, repo: Path):
        repo = repo.resolve()
        expt = repo / "experiments" / E20 / "expt_v1"
        out = expt / "results/phase0b"
        return cls(
            repo=repo,
            out=out,
            forecast=expt / "forecasts/phase0_item_parameters_e20.json",
            run_receipt=expt / "results/receipts/phase0b_run_receipt.json",
            driver=expt / "analyze_phase0_e20.py",
            archive=expt / "results/receipts/phase0b_terminal_failure_original.json",
            recovery_receipt=out / "phase0b_completion_recovery_receipt.json",
        )


def protected_paths(cfg: Config) -> dict[str, Path]:
    return {
        "analysis": cfg.out / "analysis_e20.json",
        "primary_g0": cfg.out / "primary_g0.json",
        "dimensionality": cfg.out / "dimensionality.json",
        "smooth_analysis": cfg.out / "smooth_analysis.json",
        "input_pins": cfg.out / "input_pins_e20.json",
        "freeze_receipt": cfg.out / "freeze_receipt.json",
        "forecast": cfg.forecast,
        "forecast_sidecar": cfg.forecast.with_suffix(".sha256"),
    }


def verify_completed_outputs(cfg: Config, forecast_verifier) -> dict:
    files = protected_paths(cfg)
    for name, path in {**files, "driver": cfg.driver, "run_receipt": cfg.run_receipt}.items():
        require(path.is_file(), f"missing required {name}: {path}")
    driver_sha = digest(cfg.driver)
    require(driver_sha == cfg.expected_driver_sha, f"driver hash differs: {driver_sha}")
    pins = load_json(files["input_pins"])
    provenance = {k: v for k, v in pins.items() if k != "identity"}
    identity = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    require(identity == pins.get("identity"), "input pin identity does not recompute")
    require(pins.get("software", {}).get(str(cfg.driver)) == driver_sha, "input pins do not preserve the original driver hash")

    analysis = load_json(files["analysis"])
    require(analysis.get("status") == "complete: Phase 0b analysis", "analysis is not terminally complete")
    require(analysis.get("trainer_status") == "FAILED; unchanged", "trainer status changed")
    require(analysis.get("smooth_status") == "available", "smooth analysis is not available")
    require(analysis.get("dimensionality_status") == "available", "dimensionality analysis is not available")
    require(analysis.get("inputs") == identity, "analysis/input identity mismatch")

    g0 = load_json(files["primary_g0"])
    require(g0.get("tasks") == 539 and g0.get("groups") == 400, "primary G0 task/group counts differ")
    require(g0.get("selected_model") == "explanatory", "primary G0 selected model differs")
    require(g0.get("gate") == EXPECTED_GATE == analysis.get("G0"), "primary G0 gate differs from exact completed result")
    chosen = g0.get("models", {}).get("explanatory", {})
    require(chosen.get("status") == "available", "selected G0 model is unavailable")
    require(chosen.get("auc") == EXPECTED_GATE["auc"] and chosen.get("log_loss") == EXPECTED_GATE["log_loss"],
            "selected G0 numerical metrics differ")
    require(len(g0.get("convergence", [])) == 25 and all(finite_gradient(x) for x in g0["convergence"]),
            "primary G0 does not contain 25 accepted gradient-checked fits")

    dim = load_json(files["dimensionality"])
    require(dim.get("status") == "available", "dimensionality status is not available")
    require((dim.get("paired_cells_declared"), dim.get("paired_cells_observed"), dim.get("paired_cells_scored")) == (4312, 4202, 4202),
            "dimensionality paired-cell counts differ")
    full = dim.get("full_fits", {})
    folds = dim.get("fold_fits", [])
    require(set(full) == {"tied", "untied"} and all(finite_gradient(x) for x in full.values()),
            "dimensionality full fits are incomplete or unaccepted")
    require(len(folds) == 10 and {(x.get("fold"), x.get("model")) for x in folds} == {(f, m) for f in range(5) for m in ("tied", "untied")},
            "dimensionality must contain exactly ten fold/model fits")
    require(all(finite_gradient(x) and isinstance(x.get("joint_log_likelihood"), (int, float))
                and math.isfinite(x["joint_log_likelihood"]) for x in folds), "dimensionality held-out fits are not all accepted")
    require(isinstance(dim.get("untied_minus_tied"), (int, float)) and math.isfinite(dim["untied_minus_tied"]),
            "dimensionality comparison is unavailable")

    freeze = load_json(files["freeze_receipt"])
    require(analysis.get("freeze") == freeze, "analysis/freeze receipt mismatch")
    require(Path(freeze.get("file", "")).resolve() == cfg.forecast.resolve(), "freeze receipt points to another forecast")
    require(freeze.get("status") in {"frozen and verified", "already frozen; verified"}, "freeze receipt status is invalid")
    require(forecast_verifier(cfg.forecast) is True, "native forecast verification failed")
    forecast = load_json(cfg.forecast)
    require(forecast.get("input_identity") == identity, "forecast/input identity mismatch")
    require(forecast.get("model") == "explanatory" and forecast.get("G0") == EXPECTED_GATE, "forecast model/G0 mismatch")
    require(len(forecast.get("task_ids", [])) == 539 and len(set(forecast["task_ids"])) == 539, "forecast task identity differs")
    for key in ("a", "d", "p_strict", "p_active", "p_strict_at_theta0", "p_active_at_theta0"):
        values = forecast.get(key, [])
        require(len(values) == 539 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in values),
                f"forecast array {key} is not 539 finite values")
    sidecar_sha = files["forecast_sidecar"].read_text().split()[0]
    require(sidecar_sha == freeze.get("sha256"), "forecast sidecar/freeze hash mismatch")

    run = load_json(cfg.run_receipt)
    require(run.get("status") == "FAILED" and run.get("returncode") == 1, "original run receipt is not FAILED/exit 1")
    require(run.get("driver_sha256") == driver_sha and run.get("trainer_status") == "FAILED; unchanged",
            "original run receipt driver/trainer identity differs")
    require(run.get("ended") and run.get("elapsed_wall_seconds", 0) > 0, "original run receipt lacks terminal timing")
    return {
        "analysis": analysis,
        "input_identity": identity,
        "driver_sha256": driver_sha,
        "run_receipt": run,
        "protected_hashes": {name: digest(path) for name, path in files.items()},
        "run_receipt_sha256": digest(cfg.run_receipt),
    }


def default_forecast_verifier(repo: Path):
    sys.path.insert(0, str(repo / "src"))
    from rl4cv.forecast import verify_forecast
    return verify_forecast


def recover(cfg: Config, *, now: dt.datetime | None = None, pid: int | None = None, forecast_verifier=None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    require(now.tzinfo is not None, "recovery timestamp must be timezone-aware")
    pid = os.getpid() if pid is None else pid
    forecast_verifier = forecast_verifier or default_forecast_verifier(cfg.repo)
    verified = verify_completed_outputs(cfg, forecast_verifier)
    failure = cfg.out / "failure.json"
    progress = cfg.out / "progress.json"
    existing_receipt = load_json(cfg.recovery_receipt) if cfg.recovery_receipt.exists() else None
    if existing_receipt is not None:
        require(existing_receipt.get("recovery_version") == VERSION, "foreign/incompatible recovery receipt exists")
        require(existing_receipt.get("original_run", {}).get("receipt_sha256") == verified["run_receipt_sha256"],
                "recovery receipt/run receipt hash mismatch")
        require(existing_receipt.get("protected_hashes_before") == verified["protected_hashes"],
                "protected numerical artifacts changed since recovery began")
        if existing_receipt.get("state") == "complete":
            require(not failure.exists(), "active failure marker reappeared after completed recovery")
            require(cfg.archive.is_file(), "completed recovery failure archive is missing")
            archived = cfg.archive.read_bytes()
            original = existing_receipt.get("original_failure", {})
            require(digest_bytes(archived) == original.get("sha256") and len(archived) == original.get("bytes")
                    and json.loads(archived) == original.get("exact") == EXPECTED_FAILURE,
                    "completed recovery failure archive differs")
            saved_progress = load_json(progress)
            require(saved_progress.get("phase") == "complete"
                    and saved_progress.get("metadata_recovery_receipt") == str(cfg.recovery_receipt)
                    and saved_progress.get("original_returncode") == 1,
                    "completed recovery progress is inconsistent")
            return {"status": "already complete; verified", "receipt": str(cfg.recovery_receipt),
                    "receipt_sha256": digest(cfg.recovery_receipt), "mutated": False}

    original_failure_bytes = failure.read_bytes() if failure.exists() else (cfg.archive.read_bytes() if cfg.archive.exists() else b"")
    require(bool(original_failure_bytes), "neither active failure marker nor archived failure exists")
    try:
        original_failure = json.loads(original_failure_bytes)
    except json.JSONDecodeError as exc:
        raise RecoveryError(f"terminal failure is not valid JSON: {exc}") from exc
    require(original_failure == EXPECTED_FAILURE, f"refusing recovery for unexpected terminal error: {original_failure!r}")
    failure_sha = digest_bytes(original_failure_bytes)
    if existing_receipt is not None:
        require(existing_receipt.get("original_failure", {}).get("sha256") == failure_sha, "recovery receipt/failure hash mismatch")
        started_utc = existing_receipt["recovery_started_utc"]
        started_local = existing_receipt["recovery_started_local"]
    else:
        started_utc = now.astimezone(dt.timezone.utc).isoformat()
        started_local = now.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%m-%d-%Y %H:%M:%S %Z")

    archive_exact(cfg.archive, original_failure_bytes)
    require(cfg.archive.read_bytes() == original_failure_bytes, "exact failure archive verification failed")
    original_run = verified["run_receipt"]
    receipt = {
        "recovery_version": VERSION,
        "state": "recorded_before_failure_removal",
        "recovery_started_utc": started_utc,
        "recovery_started_local": started_local,
        "recovery_completed_utc": None,
        "recovery_completed_local": None,
        "scope": "terminal metadata only after all Phase 0b computations and native freeze completed",
        "trainer_status": "FAILED; unchanged",
        "fits_gpu_or_model_calls": 0,
        "original_run": {
            "path": str(cfg.run_receipt),
            "receipt_sha256": verified["run_receipt_sha256"],
            "status": original_run["status"],
            "returncode": original_run["returncode"],
            "started": original_run["started"],
            "ended": original_run["ended"],
            "elapsed_wall_seconds": original_run["elapsed_wall_seconds"],
        },
        "original_failure": {"active_path": str(failure), "archive_path": str(cfg.archive),
                             "sha256": failure_sha, "bytes": len(original_failure_bytes), "exact": original_failure},
        "source": {"path": str(cfg.driver), "sha256": verified["driver_sha256"], "unchanged": True},
        "input_identity": verified["input_identity"],
        "analysis_status": verified["analysis"]["status"],
        "primary_G0": verified["analysis"]["G0"],
        "smooth_status": verified["analysis"]["smooth_status"],
        "dimensionality_status": verified["analysis"]["dimensionality_status"],
        "native_forecast_verified": True,
        "protected_hashes_before": verified["protected_hashes"],
        "protected_hashes_after": None,
        "original_run_receipt_unchanged": None,
        "failure_removed": False,
    }
    atomic_json(cfg.recovery_receipt, receipt)
    require(load_json(cfg.recovery_receipt).get("state") == "recorded_before_failure_removal",
            "recovery was not recorded before failure removal")
    progress_value = {
        "phase": "complete",
        "utc": now.astimezone(dt.timezone.utc).isoformat(),
        "pid": pid,
        "trainer_status": "FAILED; unchanged",
        "gpu_or_model_calls": 0,
        "status": verified["analysis"]["status"],
        "inputs": verified["input_identity"],
        "G0": verified["analysis"]["G0"],
        "smooth_status": verified["analysis"]["smooth_status"],
        "dimensionality_status": verified["analysis"]["dimensionality_status"],
        "freeze": verified["analysis"]["freeze"],
        "metadata_recovery_receipt": str(cfg.recovery_receipt),
        "original_run_status": "FAILED",
        "original_returncode": 1,
    }
    atomic_json(progress, progress_value)
    require(load_json(progress) == progress_value, "safe complete progress write did not verify")
    require(cfg.archive.read_bytes() == original_failure_bytes and cfg.recovery_receipt.is_file(),
            "archive/recovery receipt missing before failure removal")
    if failure.exists():
        require(failure.read_bytes() == original_failure_bytes, "active failure changed before removal")
        failure.unlink()
    require(not failure.exists(), "stale failure marker was not removed")
    hashes_after = {name: digest(path) for name, path in protected_paths(cfg).items()}
    require(hashes_after == verified["protected_hashes"], "protected numerical/forecast artifact changed during recovery")
    run_after = digest(cfg.run_receipt)
    require(run_after == verified["run_receipt_sha256"], "original run receipt changed during recovery")
    receipt.update(
        state="complete",
        recovery_completed_utc=now.astimezone(dt.timezone.utc).isoformat(),
        recovery_completed_local=now.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%m-%d-%Y %H:%M:%S %Z"),
        protected_hashes_after=hashes_after,
        original_run_receipt_unchanged=True,
        failure_removed=True,
        progress={"path": str(progress), "sha256": digest(progress)},
    )
    atomic_json(cfg.recovery_receipt, receipt)
    final = load_json(cfg.recovery_receipt)
    require(final.get("state") == "complete" and final.get("failure_removed") is True, "final recovery receipt did not verify")
    return {"status": "recovered", "receipt": str(cfg.recovery_receipt),
            "receipt_sha256": digest(cfg.recovery_receipt), "mutated": True}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    args = ap.parse_args()
    cfg = Config.from_repo(args.repo)
    result = recover(cfg)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RecoveryError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)
