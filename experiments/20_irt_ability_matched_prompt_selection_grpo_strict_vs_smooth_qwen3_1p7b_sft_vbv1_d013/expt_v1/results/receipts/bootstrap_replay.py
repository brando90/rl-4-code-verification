#!/usr/bin/env python3
"""Independent read-only replay of Experiment 20's primary G0 group bootstrap."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


E20 = "20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013"
SEED = 20261021
DRAWS = 10_000
TOL = 1e-12


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def auc(scores, labels) -> float:
    """Mann-Whitney AUC using independently constructed average ranks."""
    scores, labels = np.asarray(scores, float), np.asarray(labels, bool)
    n1, n0 = int(labels.sum()), int((~labels).sum())
    if not n1 or not n0:
        return float("nan")
    _, inverse, counts = np.unique(scores, return_inverse=True, return_counts=True)
    starts = np.cumsum(counts) - counts
    average_ranks = starts + (counts + 1) / 2.0
    rank_sum = average_ranks[inverse][labels].sum()
    return float((rank_sum - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def log_loss(prob, labels) -> float:
    p, y = np.clip(np.asarray(prob, float), 1e-12, 1 - 1e-12), np.asarray(labels, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log1p(-p)))


def ece10(prob, labels) -> float:
    p, y = np.asarray(prob, float), np.asarray(labels, float)
    total = 0.0
    for b in range(10):
        lo, hi = b / 10.0, (b + 1) / 10.0
        mask = (p >= lo) & ((p <= hi) if b == 9 else (p < hi))
        if mask.any():
            total += float(mask.mean() * abs(p[mask].mean() - y[mask].mean()))
    return total


def summarize(point: float, samples: list[float], null: float | None = None) -> dict:
    values = np.asarray(samples, float)
    finite = values[np.isfinite(values)]
    if not len(finite):
        return {"point": point, "lo": None, "hi": None, "valid_draws": 0,
                "requested_draws": len(values), "p_two_sided": None, "null": null}
    lo, hi = np.percentile(finite, [2.5, 97.5])
    p = None
    if null is not None:
        p = min(1.0, max(1 / len(values), 2 * min(np.mean(finite <= null), np.mean(finite >= null))))
    return {"point": float(point), "lo": float(lo), "hi": float(hi),
            "valid_draws": int(len(finite)), "requested_draws": int(len(values)),
            "p_two_sided": None if p is None else float(p), "null": null}


def same(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isfinite(float(a)) and math.isfinite(float(b)) and math.isclose(float(a), float(b), rel_tol=TOL, abs_tol=TOL)


def compare_summary(replay: dict, reported: dict) -> dict:
    keys = ("point", "lo", "hi", "valid_draws", "requested_draws", "p_two_sided", "null")
    differences = {}
    ok = True
    for key in keys:
        a, b = replay.get(key), reported.get(key)
        key_ok = (a == b) if key in ("valid_draws", "requested_draws") else same(a, b)
        ok &= key_ok
        if not key_ok:
            differences[key] = {"replay": a, "reported": b}
    return {"pass": bool(ok), "differences": differences, "replay": replay, "reported": reported}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--predictions", type=Path)
    ap.add_argument("--g0", type=Path)
    ap.add_argument("--bootstrap", type=Path)
    ap.add_argument("--out", type=Path, default=Path("/tmp/e20_bootstrap_replay_receipt.json"))
    args = ap.parse_args()
    repo = args.repo.resolve()
    base = repo / "experiments" / E20 / "expt_v1/results/phase0b"
    predictions_path = (args.predictions or base / "primary_g0_predictions.csv").resolve()
    g0_path = (args.g0 or base / "primary_g0.json").resolve()
    bootstrap_path = (args.bootstrap or base / "primary_g0_bootstrap.json").resolve()
    rows = list(csv.DictReader(predictions_path.open(newline="")))
    g0 = json.loads(g0_path.read_text())
    bootstrap = json.loads(bootstrap_path.read_text())
    selected = g0["selected_model"]
    if selected not in ("random_intercept", "explanatory"):
        raise ValueError(f"unexpected selected primary model: {selected!r}")
    if len(rows) != 539 or len({r["task_id"] for r in rows}) != 539:
        raise ValueError("primary prediction table must contain exactly 539 unique tasks")
    y = np.array([float(r["observed_active"]) for r in rows])
    group_ids = np.array([r["group_id"] for r in rows])
    unique_groups, inverse = np.unique(group_ids, return_inverse=True)
    if len(unique_groups) != 400:
        raise ValueError("primary prediction table must contain exactly 400 D-013 groups")
    members = [np.flatnonzero(inverse == g) for g in range(len(unique_groups))]
    ps = np.array([float(r[f"active_{selected}"]) for r in rows])
    pb = np.array([float(r["active_baseline"]) for r in rows])
    pf = np.array([float(r["active_features_only"]) for r in rows])
    panel = np.array([float(r["panel_rate"]) for r in rows])
    if not all(np.isfinite(x).all() for x in (y, ps, pb, pf, panel)):
        raise ValueError("requested replay columns must all be finite")
    if not set(np.unique(y)) <= {0.0, 1.0}:
        raise ValueError("observed_active must be binary")
    selected_loss = log_loss(ps, y)
    baseline_loss = log_loss(pb, y)
    points = {
        "selected_auc": auc(ps, y),
        "selected_log_loss": selected_loss,
        "selected_ece": ece10(ps, y),
        "selected_log_loss_gain_vs_baseline": baseline_loss - selected_loss,
        "selected_auc_minus_panel": auc(ps, y) - auc(panel, y),
        "baseline_log_loss": baseline_loss,
        "features_only_auc": auc(pf, y),
        "panel_strict_rate_auc": auc(panel, y),
    }
    samples = {key: [] for key in points}
    rng = np.random.default_rng(SEED)
    for _ in range(DRAWS):
        idx = np.concatenate([members[g] for g in rng.integers(0, len(members), len(members))])
        yy, s, b, f, pan = y[idx], ps[idx], pb[idx], pf[idx], panel[idx]
        selected_auc, panel_auc = auc(s, yy), auc(pan, yy)
        selected_ll, baseline_ll = log_loss(s, yy), log_loss(b, yy)
        samples["selected_auc"].append(selected_auc)
        samples["selected_log_loss"].append(selected_ll)
        samples["selected_ece"].append(ece10(s, yy))
        samples["selected_log_loss_gain_vs_baseline"].append(baseline_ll - selected_ll)
        samples["selected_auc_minus_panel"].append(selected_auc - panel_auc)
        samples["baseline_log_loss"].append(baseline_ll)
        samples["features_only_auc"].append(auc(f, yy))
        samples["panel_strict_rate_auc"].append(panel_auc)
    nulls = {"selected_auc": 0.70, "selected_log_loss_gain_vs_baseline": 0.0,
             "selected_auc_minus_panel": 0.0, "features_only_auc": 0.70}
    replay = {key: summarize(points[key], samples[key], nulls.get(key)) for key in points}
    reported = g0["intervals"]
    mapping = {
        "selected_auc": reported[selected]["auc"],
        "selected_log_loss": reported[selected]["log_loss"],
        "selected_ece": reported[selected]["ece"],
        "selected_log_loss_gain_vs_baseline": reported[selected]["log_loss_gain_vs_baseline"],
        "selected_auc_minus_panel": reported[selected]["auc_minus_panel"],
        "baseline_log_loss": reported["baseline"]["log_loss"],
        "features_only_auc": reported["features_only"]["auc"],
        "panel_strict_rate_auc": reported["panel_strict_rate"]["auc"],
    }
    comparisons = {key: compare_summary(replay[key], mapping[key]) for key in replay}
    bootstrap_identity_ok = (bootstrap.get("draws") == DRAWS and bootstrap.get("seed") == SEED
                             and bootstrap.get("unit") == "D-013 train task group"
                             and bootstrap.get("intervals") == reported)
    selection_expected = min(("random_intercept", "explanatory"),
                             key=lambda name: (g0["models"][name]["log_loss"], name != "random_intercept"))
    checks = {
        "all_replayed_summaries_match": all(x["pass"] for x in comparisons.values()),
        "bootstrap_file_matches_g0": bootstrap_identity_ok,
        "selected_is_lowest_loss_primary_2pl": selected == selection_expected,
        "task_count": len(rows) == 539,
        "group_count": len(unique_groups) == 400,
        "active_count": int(y.sum()) == 74,
        "draws": DRAWS == 10_000,
        "seed": SEED == 20261021,
    }
    script_path = Path(__file__).resolve()
    receipt = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "experiment": E20,
        "read_only": True,
        "fits_gpu_or_model_calls": 0,
        "selected_model": selected,
        "tasks": len(rows),
        "active_tasks": int(y.sum()),
        "groups": len(unique_groups),
        "draws": DRAWS,
        "seed": SEED,
        "unit": "D-013 train task group",
        "checks": checks,
        "comparisons": comparisons,
        "input_hashes": {str(p): digest(p) for p in (predictions_path, g0_path, bootstrap_path)},
        "script": {"path": str(script_path), "sha256": digest(script_path), "bytes": script_path.stat().st_size},
        "conditioning_and_selection_limits": [
            "Intervals condition on the saved held-out predictions and the selected primary model; models are not refit inside bootstrap draws.",
            "The replay does not include nested model-selection or prior-selection uncertainty.",
            "D-013 task groups are the resampling units, preserving tasks linked within a group.",
            "The panel strict rate is a scalar ranking comparator, so only its AUC is evaluated; no panel probability calibration or log loss is claimed.",
            "Features-only is a prespecified alternative and does not replace the selected primary two-parameter logistic model.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "selected_model": selected,
                      "out": str(args.out), "bytes": args.out.stat().st_size}, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
