#!/usr/bin/env python3
"""Read-only deterministic audit of Experiment 20's completed Phase 0b artifacts.

This script never fits a model.  It recomputes labels and held-out point metrics
from the saved CSV files, checks selection/convergence/provenance/freeze rules,
and writes a machine-readable receipt.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np


E20 = "20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013"
TOL = 1e-10
GRAD_TOL = 1e-4
SEED = 20261021


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text())


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if str(value).strip().lower() in {"true", "1"}:
        return True
    if str(value).strip().lower() in {"false", "0"}:
        return False
    raise ValueError(f"not a Boolean: {value!r}")


def optional_float(value) -> float:
    """Decode CSV missing-number spellings without treating them as observed predictions."""
    if value is None or str(value).strip().lower() in {"", "nan", "none", "null"}:
        return float("nan")
    return float(value)


def close(a, b, tol: float = TOL) -> bool:
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def auc_pairwise(scores, labels) -> float:
    """Independent Mann-Whitney AUC; ties receive one half."""
    p = np.asarray(scores, float)
    y = np.asarray(labels, int)
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(((pos[:, None] > neg).sum() + 0.5 * (pos[:, None] == neg).sum()) / (len(pos) * len(neg)))


def binary_log_loss(prob, labels) -> float:
    p = np.clip(np.asarray(prob, float), 1e-12, 1 - 1e-12)
    y = np.asarray(labels, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log1p(-p)))


def ece10(prob, labels) -> float:
    p, y = np.asarray(prob, float), np.asarray(labels, float)
    total = 0.0
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10
        mask = (p >= lo) & ((p <= hi) if i == 9 else (p < hi))
        if mask.any():
            total += float(mask.mean() * abs(p[mask].mean() - y[mask].mean()))
    return total


class Audit:
    def __init__(self):
        self.checks: dict[str, dict] = {}
        self.unavailable: dict[str, str] = {}
        self.metrics: dict = {}
        self.artifacts: dict = {}

    def check(self, name: str, ok: bool, actual=None, expected=None, note: str | None = None):
        row = {"result": "pass" if bool(ok) else "fail"}
        if actual is not None:
            row["actual"] = actual
        if expected is not None:
            row["expected"] = expected
        if note:
            row["note"] = note
        self.checks[name] = row
        return bool(ok)

    def mark_unavailable(self, name: str, status: str):
        self.unavailable[name] = status
        self.checks[name] = {"result": "unavailable", "actual": status}

    def hash_artifact(self, path: Path):
        self.artifacts[str(path)] = {"sha256": sha256(path), "bytes": path.stat().st_size}

    def fit(self, name: str, row: dict, required: bool = False):
        converged = row.get("converged") is True
        if required:
            self.check(name + ".converged", converged, row.get("converged"), True)
        if converged:
            gradients = {k: row.get(k) for k in ("max_abs_grad", "check_grid_max_abs_grad")}
            ok = all(isinstance(v, (int, float)) and math.isfinite(v) and v <= GRAD_TOL for v in gradients.values())
            self.check(name + ".accepted_gradients", ok, gradients, {"each_at_most": GRAD_TOL})
            return True
        return False


def verify_pins(audit: Audit, pins_path: Path):
    pins = load_json(pins_path)
    provenance = {k: v for k, v in pins.items() if k != "identity"}
    identity = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    audit.check("input_identity_recomputed", identity == pins.get("identity"), identity, pins.get("identity"))
    pinned = []
    for section in ("inputs",):
        for name, rec in pins[section].items():
            path = Path(rec["path"])
            actual = sha256(path)
            audit.check(f"input_hash.{name}", actual == rec["sha256"] == rec["expected"], actual, rec["sha256"])
            pinned.append(path)
    for name in ("scores", "generation_manifest", "score_summary"):
        if name not in pins:
            continue
        rec, path = pins[name], Path(pins[name]["path"])
        actual = sha256(path)
        audit.check(f"input_hash.{name}", actual == rec["sha256"], actual, rec["sha256"])
        pinned.append(path)
    for i, rec in enumerate(pins.get("e05", [])):
        path, actual = Path(rec["path"]), sha256(Path(rec["path"]))
        audit.check(f"input_hash.e05_{i}", actual == rec["sha256"], actual, rec["sha256"])
        pinned.append(path)
    for name, expected in pins.get("software", {}).items():
        path, actual = Path(name), sha256(Path(name))
        audit.check(f"software_hash.{path.name}", actual == expected, actual, expected, note=str(path))
        pinned.append(path)
    for path in pinned:
        audit.hash_artifact(path)
    return pins


def verify_strict_labels(audit: Audit, scores_path: Path, pred_rows: list[dict[str, str]]):
    rows = load_csv(scores_path)
    by_task: dict[str, list[tuple[int, int]]] = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["task_id"], int(row["sample_idx"]))
        if key in seen:
            raise ValueError(f"duplicate score cell {key}")
        seen.add(key)
        if row["status"] != "measured" or row["strict"] not in {"0", "1"}:
            raise ValueError(f"non-measured/nonbinary strict cell {key}")
        by_task[row["task_id"]].append((int(row["sample_idx"]), int(row["strict"])))
    valid_shape = len(rows) == 4312 and len(by_task) == 539 and all(sorted(s for s, _ in v) == list(range(8)) for v in by_task.values())
    audit.check("strict_manifest_shape", valid_shape, {"cells": len(rows), "tasks": len(by_task)}, {"cells": 4312, "tasks": 539, "samples_per_task": 8})
    successes = {t: sum(v for _, v in cells) for t, cells in by_task.items()}
    total, active = sum(successes.values()), sum(0 < k < 8 for k in successes.values())
    audit.check("strict_success_count", total == 191, total, 191)
    audit.check("active_task_count", active == 74, active, 74)
    pred_by_task = {r["task_id"]: r for r in pred_rows}
    audit.check("prediction_task_identity", len(pred_rows) == len(pred_by_task) == 539 and set(pred_by_task) == set(by_task),
                {"rows": len(pred_rows), "unique": len(pred_by_task), "same_set": set(pred_by_task) == set(by_task)},
                {"rows": 539, "unique": 539, "same_set": True})
    mismatches = []
    for task, k in successes.items():
        observed = float(pred_by_task[task]["observed_active"])
        if observed != float(0 < k < 8):
            mismatches.append(task)
    audit.check("prediction_labels_from_strict_cells", not mismatches, {"mismatches": len(mismatches)}, {"mismatches": 0})
    return np.array([float(r["observed_active"]) for r in pred_rows]), successes


def verify_folds(audit: Audit, rows: list[dict[str, str]]):
    group_folds: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        group_folds[row["group_id"]].add(int(row["fold"]))
    audit.check("group_count", len(group_folds) == 400, len(group_folds), 400)
    audit.check("one_fold_per_group", all(len(v) == 1 for v in group_folds.values()),
                {"violating_groups": sum(len(v) != 1 for v in group_folds.values())}, {"violating_groups": 0})
    groups = np.array([r["group_id"] for r in rows])
    uniq = np.unique(groups)
    perm = np.random.default_rng(SEED).permutation(uniq.size)
    fold_of_group = {uniq[g]: i % 5 for i, g in enumerate(perm)}
    mismatch = sum(int(r["fold"]) != fold_of_group[r["group_id"]] for r in rows)
    audit.check("registered_group_fold_assignment", mismatch == 0, {"mismatches": mismatch, "seed": SEED}, {"mismatches": 0, "seed": SEED})


def verify_metrics(audit: Audit, g0: dict, pred_rows: list[dict[str, str]], labels: np.ndarray):
    actual_metrics = {}
    for name, reported in g0["models"].items():
        if name == "panel_strict_rate":
            score = np.array([float(r["panel_rate"]) for r in pred_rows])
            point = auc_pairwise(score, labels)
            ok = reported.get("status") == "available: ranking only" and close(point, reported.get("auc"))
            forbidden = set(reported) & {"log_loss", "ece", "predicted_active_share", "observed_active_share"}
            audit.check("metric.panel_strict_rate.ranking_only", ok and not forbidden,
                        {"recomputed_auc": point, "reported": reported, "probability_metrics": sorted(forbidden)},
                        {"status": "available: ranking only", "probability_metrics": []})
            actual_metrics[name] = {"auc": point, "scope": "ranking_only"}
            continue
        column = "active_" + name
        if column not in pred_rows[0]:
            audit.check(f"metric.{name}.prediction_column", False, None, column)
            continue
        p = np.array([optional_float(r.get(column)) for r in pred_rows])
        available = reported.get("status") == "available"
        if not available:
            finite = int(np.isfinite(p).sum())
            audit.check(f"metric.{name}.unavailable_count", finite == int(reported.get("predicted_tasks", -1)), finite,
                        reported.get("predicted_tasks"))
            audit.mark_unavailable(f"metric.{name}", str(reported.get("status")))
            continue
        points = {
            "auc": auc_pairwise(p, labels),
            "log_loss": binary_log_loss(p, labels),
            "ece": ece10(p, labels),
            "predicted_active_share": float(p.mean()),
            "observed_active_share": float(labels.mean()),
        }
        valid = np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
        for metric, point in points.items():
            valid &= close(point, reported.get(metric))
            audit.check(f"metric.{name}.{metric}", close(point, reported.get(metric)), point, reported.get(metric))
        audit.check(f"metric.{name}.finite_probabilities", bool(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()),
                    {"finite": int(np.isfinite(p).sum()), "n": len(p), "min": float(np.nanmin(p)), "max": float(np.nanmax(p))},
                    {"finite": len(p), "range": [0, 1]})
        actual_metrics[name] = points
    audit.metrics["primary_g0_recomputed"] = actual_metrics


def verify_priors(audit: Audit, out_dir: Path, tag: str):
    priors = load_json(out_dir / f"{tag}_priors.json")
    grid = load_csv(out_dir / f"{tag}_cv_grid.csv")
    folds = load_csv(out_dir / f"{tag}_cv_folds.csv")
    audit.check(f"{tag}.cv_grid_shape", len(grid) == 50, len(grid), 50)
    audit.check(f"{tag}.cv_fold_shape", len(folds) == 250, len(folds), 250)
    for i, row in enumerate(folds):
        if as_bool(row["converged"]):
            audit.fit(f"{tag}.cv_fold.{i}", {
                "converged": True,
                "max_abs_grad": float(row["max_abs_grad"]),
                "check_grid_max_abs_grad": float(row["check_grid_max_abs_grad"]),
            })
    for family in ("random_intercept", "explanatory"):
        for fixed in (False, True):
            key = family + ("_1pl" if fixed else "")
            candidates = [r for r in grid if r["family"] == family and as_bool(r["fixed_slope"]) == fixed
                          and int(r["converged_folds"]) == int(r["folds"]) == 5]
            chosen = priors.get(key)
            if not candidates:
                audit.check(f"{tag}.prior.{key}.eligible", chosen is None, chosen, None)
                continue
            best = min(candidates, key=lambda r: (float(r["log_loss"]), -float(r["sigma_e"]), -float(r["slope_sd"])))
            ok = isinstance(chosen, dict) and all(close(chosen[k], best[k]) for k in ("log_loss", "sigma_e", "slope_sd"))
            ok &= chosen.get("family") == family and bool(chosen.get("fixed_slope")) == fixed
            ok &= int(chosen.get("converged_folds", -1)) == int(chosen.get("folds", -2)) == 5
            audit.check(f"{tag}.prior.{key}.lowest_converged_cv_loss", ok,
                        {k: chosen.get(k) for k in ("log_loss", "sigma_e", "slope_sd", "converged_folds")} if isinstance(chosen, dict) else chosen,
                        {k: (float(best[k]) if k != "converged_folds" else int(best[k])) for k in ("log_loss", "sigma_e", "slope_sd", "converged_folds")})
            if isinstance(chosen, dict):
                chosen_folds = [r for r in folds if r["family"] == family and as_bool(r["fixed_slope"]) == fixed
                                and close(r["sigma_e"], chosen["sigma_e"]) and close(r["slope_sd"], chosen["slope_sd"])]
                direct_ok = len(chosen_folds) == 5 and all(as_bool(r["converged"]) for r in chosen_folds)
                audit.check(f"{tag}.prior.{key}.five_directly_converged_folds", direct_ok,
                            {"matching_folds": len(chosen_folds), "converged": sum(as_bool(r["converged"]) for r in chosen_folds)},
                            {"matching_folds": 5, "converged": 5})
    return priors


def verify_g0_selection(audit: Audit, g0: dict):
    models = g0["models"]
    eligible = [n for n in ("random_intercept", "explanatory") if models[n].get("status") == "available"]
    expected = min(eligible, key=lambda n: (models[n]["log_loss"], n != "random_intercept")) if len(eligible) == 2 else None
    selected = g0.get("selected_model")
    audit.check("selected_lowest_loss_eligible_2pl", selected == expected and selected is not None, selected, expected)
    gate = g0["gate"]
    audit.check("g0_selected_identity", gate.get("selected_model") == selected, gate.get("selected_model"), selected)
    audit.check("g0_literal_threshold", close(gate.get("auc_threshold"), 0.70), gate.get("auc_threshold"), 0.70)
    if selected:
        expected_pass = models[selected]["auc"] >= 0.70 and models[selected]["log_loss"] < models["baseline"]["log_loss"]
        consistent = (gate.get("passed") is expected_pass and close(gate.get("auc"), models[selected]["auc"])
                      and close(gate.get("log_loss"), models[selected]["log_loss"])
                      and close(gate.get("baseline_log_loss"), models["baseline"]["log_loss"]))
        audit.check("g0_literal_point_gate", consistent, gate,
                    {"passed": expected_pass, "rule": "auc >= 0.70 and log_loss < baseline_log_loss"})
    return selected


def verify_gradients(audit: Audit, out_dir: Path, tag: str, g0: dict):
    by_model = defaultdict(list)
    for i, row in enumerate(g0["convergence"]):
        by_model[row.get("model")].append(row)
        audit.fit(f"{tag}.g0_fit.{i}.{row.get('model')}.fold{row.get('fold')}", row)
    for model in ("random_intercept", "explanatory", "random_intercept_1pl", "explanatory_1pl", "features_only"):
        if g0["models"][model].get("status") == "available":
            records = by_model[model]
            ok = len(records) == 5 and {int(r["fold"]) for r in records} == set(range(5)) and all(r.get("converged") is True for r in records)
            audit.check(f"{tag}.g0_available_model_convergence.{model}", ok,
                        {"records": len(records), "folds": sorted(int(r["fold"]) for r in records),
                         "converged": sum(r.get("converged") is True for r in records)},
                        {"records": 5, "folds": list(range(5)), "converged": 5})
    summaries = load_json(out_dir / f"{tag}_final_fit_summary.json")
    for name, row in summaries.items():
        audit.fit(f"{tag}.final_fit.{name}", row)
    return summaries


def verify_descriptive(audit: Audit, out_dir: Path, analysis: dict):
    smooth = load_json(out_dir / "smooth_analysis.json")
    status = str(smooth.get("status"))
    audit.check("smooth_status_identity", analysis.get("smooth_status") == status, analysis.get("smooth_status"), status)
    audit.check("smooth_counts", (smooth.get("smooth_declared_cells"), smooth.get("smooth_measured_cells"), smooth.get("smooth_missing_cells")) == (4312, 4202, 110),
                [smooth.get("smooth_declared_cells"), smooth.get("smooth_measured_cells"), smooth.get("smooth_missing_cells")], [4312, 4202, 110])
    if status == "available":
        audit.fit("smooth.graded_fit", smooth["fit"], required=True)
    elif status.startswith("unavailable:"):
        audit.mark_unavailable("smooth_fit", status)
        audit.check("smooth_unavailability_consistent", smooth.get("fit", {}).get("converged") is False,
                    smooth.get("fit", {}).get("converged"), False)
    else:
        audit.check("smooth_terminal_status", False, status, "available or unavailable: ...")

    dim = load_json(out_dir / "dimensionality.json")
    dstatus = str(dim.get("status"))
    audit.check("dimensionality_status_identity", analysis.get("dimensionality_status") == dstatus,
                analysis.get("dimensionality_status"), dstatus)
    audit.check("dimensionality_pair_counts", (dim.get("paired_cells_declared"), dim.get("paired_cells_observed")) == (4312, 4202),
                [dim.get("paired_cells_declared"), dim.get("paired_cells_observed")], [4312, 4202])
    full_ok = [audit.fit(f"dimensionality.full.{name}", row) for name, row in dim.get("full_fits", {}).items()]
    fold_ok = [audit.fit(f"dimensionality.fold.{i}.{row.get('model')}", row) for i, row in enumerate(dim.get("fold_fits", []))]
    if dstatus == "available":
        audit.check("dimensionality_available_fits", len(full_ok) == 2 and all(full_ok) and len(fold_ok) == 10 and all(fold_ok),
                    {"full": [len(full_ok), sum(full_ok)], "fold": [len(fold_ok), sum(fold_ok)]},
                    {"full": [2, 2], "fold": [10, 10]})
        audit.check("dimensionality_scored_pairs", dim.get("paired_cells_scored") == 4202, dim.get("paired_cells_scored"), 4202)
    elif dstatus.startswith("unavailable:"):
        audit.mark_unavailable("dimensionality_fit", dstatus)
        if "full-fit" in dstatus:
            audit.check("dimensionality_unavailability_consistent", bool(full_ok) and not all(full_ok), full_ok, "at least one failed full fit")
        elif "held-out" in dstatus:
            audit.check("dimensionality_unavailability_consistent", len(full_ok) == 2 and all(full_ok) and bool(fold_ok) and not all(fold_ok),
                        {"full": full_ok, "fold": fold_ok}, "full fits pass; at least one held-out fit fails")
        else:
            audit.check("dimensionality_unavailability_reason", False, dstatus, "documented convergence gate failure")
        audit.check("dimensionality_no_unavailable_claim", dim.get("joint_log_likelihood") is None and dim.get("untied_minus_tied") is None,
                    {"joint_log_likelihood": dim.get("joint_log_likelihood"), "untied_minus_tied": dim.get("untied_minus_tied")},
                    {"joint_log_likelihood": None, "untied_minus_tied": None})
    else:
        audit.check("dimensionality_terminal_status", False, dstatus, "available or unavailable: ...")


def verify_freeze(audit: Audit, repo: Path, out_dir: Path, freeze_dir: Path, pins: dict, g0: dict,
                  final_summaries: dict, pred_rows: list[dict[str, str]], selected: str, analysis: dict):
    sys.path.insert(0, str(repo / "src"))
    from rl4cv.forecast import verify_forecast  # native project verifier

    forecast_path = freeze_dir / "phase0_item_parameters_e20.json"
    native_ok = verify_forecast(forecast_path)
    audit.check("native_verify_forecast", native_ok, native_ok, True)
    payload = load_json(forecast_path)
    audit.check("forecast_input_identity", payload.get("input_identity") == pins["identity"] == analysis.get("inputs"),
                {"forecast": payload.get("input_identity"), "pins": pins["identity"], "analysis": analysis.get("inputs")}, "all identical")
    audit.check("forecast_selected_model", payload.get("model") == selected, payload.get("model"), selected)
    audit.check("forecast_g0_identity", payload.get("G0") == g0.get("gate") == analysis.get("G0"),
                payload.get("G0"), g0.get("gate"))
    task_ids = payload.get("task_ids", [])
    arrays = {k: payload.get(k) for k in ("a", "d", "p_strict", "p_active", "p_strict_at_theta0", "p_active_at_theta0")}
    arrays_ok = len(task_ids) == len(set(task_ids)) == 539
    array_summary = {}
    for name, values in arrays.items():
        arr = np.asarray(values, float) if isinstance(values, list) else np.array([])
        array_summary[name] = {"n": int(arr.size), "finite": int(np.isfinite(arr).sum())}
        arrays_ok &= arr.size == 539 and np.isfinite(arr).all()
        if name == "a":
            arrays_ok &= (arr > 0).all()
        if name.startswith("p_"):
            arrays_ok &= ((arr >= 0) & (arr <= 1)).all()
    audit.check("forecast_539_finite_parameter_arrays", bool(arrays_ok), {"task_ids": len(task_ids), "arrays": array_summary},
                {"task_ids": 539, "each_array": {k: {"n": 539, "finite": 539} for k in arrays}})
    metadata_ok = (payload.get("experiment") == E20 and payload.get("gradient_tolerance") == GRAD_TOL
                   and payload.get("grid") == {"lo": -12, "hi": 12, "count": 1201}
                   and payload.get("check_grid") == {"lo": -18, "hi": 18, "count": 4801})
    audit.check("forecast_registered_metadata", metadata_ok,
                {k: payload.get(k) for k in ("experiment", "gradient_tolerance", "grid", "check_grid")},
                {"experiment": E20, "gradient_tolerance": GRAD_TOL,
                 "grid": {"lo": -12, "hi": 12, "count": 1201}, "check_grid": {"lo": -18, "hi": 18, "count": 4801}})
    item_path = out_dir / f"primary_items_{selected}.csv"
    items = load_csv(item_path)
    item_by_task = {r["task_id"]: r for r in items}
    match = len(items) == len(item_by_task) == 539 and task_ids == [r["task_id"] for r in pred_rows]
    for j, task in enumerate(task_ids):
        if task not in item_by_task:
            match = False
            continue
        row = item_by_task[task]
        match &= all(close(payload[k][j], row[k]) for k in ("a", "d", "p_strict", "p_active"))
    audit.check("forecast_matches_selected_final_items", bool(match), {"items": len(items), "model": selected}, {"items": 539, "model": selected})
    selected_summary = final_summaries.get(selected)
    audit.check("selected_final_fit_present", isinstance(selected_summary, dict), selected, sorted(final_summaries))
    if isinstance(selected_summary, dict):
        audit.fit("selected_final_fit", selected_summary, required=True)
        audit.check("forecast_theta_matches_selected_fit", close(payload.get("theta0"), selected_summary.get("theta0"))
                    and close(payload.get("theta0_sd"), selected_summary.get("theta0_sd")),
                    [payload.get("theta0"), payload.get("theta0_sd")], [selected_summary.get("theta0"), selected_summary.get("theta0_sd")])
    freeze_receipt = load_json(out_dir / "freeze_receipt.json")
    audit.check("analysis_freeze_receipt_identity", analysis.get("freeze") == freeze_receipt, analysis.get("freeze"), freeze_receipt)
    audit.check("freeze_receipt_status", freeze_receipt.get("status") in {"frozen and verified", "already frozen; verified"},
                freeze_receipt.get("status"), ["frozen and verified", "already frozen; verified"])
    audit.check("freeze_receipt_path", Path(freeze_receipt.get("file", "")).resolve() == forecast_path.resolve(),
                freeze_receipt.get("file"), str(forecast_path))
    for path in (forecast_path, forecast_path.with_suffix(".sha256"), item_path, out_dir / "freeze_receipt.json"):
        audit.hash_artifact(path)


def run(args) -> tuple[Audit, str | None]:
    audit = Audit()
    error = None
    repo = args.repo.resolve()
    expt = repo / "experiments" / E20 / "expt_v1"
    out_dir = (args.phase0b_out or expt / "results/phase0b").resolve()
    scores_path = (args.scores or expt / "results/phase0_cells_e20.csv").resolve()
    freeze_dir = (args.freeze_dir or expt / "forecasts").resolve()
    required = [out_dir / name for name in (
        "analysis_e20.json", "input_pins_e20.json", "input_audit.json", "phase0_tasks.csv",
        "primary_priors.json", "primary_cv_grid.csv", "primary_cv_folds.csv", "primary_g0.json",
        "primary_g0_predictions.csv", "primary_final_fit_summary.json", "with_e05_priors.json",
        "with_e05_cv_grid.csv", "with_e05_cv_folds.csv", "with_e05_g0.json",
        "with_e05_final_fit_summary.json", "e05_sensitivity.json", "smooth_analysis.json", "dimensionality.json", "freeze_receipt.json",
    )] + [scores_path, freeze_dir / "phase0_item_parameters_e20.json", freeze_dir / "phase0_item_parameters_e20.sha256"]
    try:
        missing = [str(p) for p in required if not p.is_file()]
        audit.check("required_final_artifacts", not missing, {"missing": missing, "required": len(required)}, {"missing": []})
        if missing:
            raise FileNotFoundError("final Phase 0b artifacts are incomplete")
        analysis = load_json(out_dir / "analysis_e20.json")
        audit.check("analysis_terminal_status", analysis.get("status") == "complete: Phase 0b analysis",
                    analysis.get("status"), "complete: Phase 0b analysis")
        audit.check("trainer_status_unchanged", analysis.get("trainer_status") == "FAILED; unchanged",
                    analysis.get("trainer_status"), "FAILED; unchanged")
        pins = verify_pins(audit, out_dir / "input_pins_e20.json")
        pred_rows = load_csv(out_dir / "primary_g0_predictions.csv")
        labels, _ = verify_strict_labels(audit, scores_path, pred_rows)
        verify_folds(audit, pred_rows)
        g0 = load_json(out_dir / "primary_g0.json")
        audit.check("primary_g0_shape", (g0.get("tasks"), g0.get("groups")) == (539, 400),
                    [g0.get("tasks"), g0.get("groups")], [539, 400])
        verify_metrics(audit, g0, pred_rows, labels)
        verify_priors(audit, out_dir, "primary")
        selected = verify_g0_selection(audit, g0)
        primary_final = verify_gradients(audit, out_dir, "primary", g0)
        # Sensitivity artifacts are audited for their own registered prior/convergence choices, not used to replace primary.
        verify_priors(audit, out_dir, "with_e05")
        with_e05_g0 = load_json(out_dir / "with_e05_g0.json")
        verify_g0_selection_sensitivity = verify_g0_selection
        # Keep sensitivity check names separate from the primary gate checks.
        original = audit.checks
        temp = Audit()
        verify_g0_selection_sensitivity(temp, with_e05_g0)
        for key, value in temp.checks.items():
            original["with_e05." + key] = value
        verify_gradients(audit, out_dir, "with_e05", with_e05_g0)
        audit.check("analysis_primary_g0_identity", analysis.get("G0") == g0.get("gate"), analysis.get("G0"), g0.get("gate"))
        verify_descriptive(audit, out_dir, analysis)
        if selected is not None:
            verify_freeze(audit, repo, out_dir, freeze_dir, pins, g0, primary_final, pred_rows, selected, analysis)
        else:
            audit.check("freeze_requires_selected_model", False, selected, "a selected converged primary 2PL")
        for path in required + [out_dir / f"primary_items_{selected}.csv" if selected else out_dir / "missing-selected-items"]:
            if path.is_file():
                audit.hash_artifact(path)
    except Exception as exc:  # Always leave a receipt explaining a deterministic failure.
        error = f"{type(exc).__name__}: {exc}"
        audit.check("validator_exception", False, error, "no exception", note="".join(traceback.format_exception_only(type(exc), exc)).strip())
    return audit, error


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--phase0b-out", type=Path)
    ap.add_argument("--scores", type=Path)
    ap.add_argument("--freeze-dir", type=Path)
    ap.add_argument("--receipt", type=Path, default=Path("/tmp/e20_final_phase0_verification.json"))
    args = ap.parse_args()
    audit, error = run(args)
    failed = sorted(k for k, v in audit.checks.items() if v["result"] == "fail")
    status = "FAIL" if failed else ("PASS_WITH_UNAVAILABLE_DESCRIPTIVE" if audit.unavailable else "PASS")
    repo = args.repo.resolve()
    expt = repo / "experiments" / E20 / "expt_v1"
    validator_path = Path(__file__).resolve()
    receipt = {
        "status": status,
        "read_only_validator": True,
        "fits_or_model_calls": 0,
        "experiment": E20,
        "paths": {
            "repo": str(repo),
            "phase0b_out": str((args.phase0b_out or expt / "results/phase0b").resolve()),
            "scores": str((args.scores or expt / "results/phase0_cells_e20.csv").resolve()),
            "freeze_dir": str((args.freeze_dir or expt / "forecasts").resolve()),
            "receipt": str(args.receipt.resolve()),
        },
        "validator": {"path": str(validator_path), "sha256": sha256(validator_path), "bytes": validator_path.stat().st_size},
        "gradient_tolerance": GRAD_TOL,
        "metric_tolerance": TOL,
        "checks": audit.checks,
        "failed_checks": failed,
        "unavailable": audit.unavailable,
        "actual_metrics": audit.metrics,
        "artifacts": audit.artifacts,
        "error": error,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": status, "failed_checks": failed, "unavailable": audit.unavailable,
                      "receipt": str(args.receipt), "receipt_bytes": args.receipt.stat().st_size}, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
