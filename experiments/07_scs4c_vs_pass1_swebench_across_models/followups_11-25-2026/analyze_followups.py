"""Compute post-hoc level-bias, task-variance and held-out diagnostics from unchanged experiment 07 receipts."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from rl4cv.scs4c import spearman


def load_matrices(receipts: Path, original: Path, systems_csv: Path) -> dict:
    """Require every originally included system/task pair exactly once, without changing its score."""
    old = json.loads(original.read_text())
    with systems_csv.open() as stream:
        names = [r["submission"] for r in csv.DictReader(stream) if r["included"] == "True"]
    tasks = old["common_cohort_ids"]
    si, ti = {s: i for i, s in enumerate(names)}, {t: i for i, t in enumerate(tasks)}
    matrices = {k: np.full((len(names), len(tasks)), np.nan) for k in ("fix", "keep", "score", "resolved")}
    seen = set()
    with gzip.open(receipts, "rt") as stream:
        for line in stream:
            r = json.loads(line)
            if r["submission"] not in si or r["instance_id"] not in ti:
                continue
            key = si[r["submission"]], ti[r["instance_id"]]
            if key in seen:
                raise ValueError(f"duplicate receipt {key}")
            seen.add(key)
            if r["gate"] not in (0, 1) or not isinstance(r["resolved"], bool):
                raise ValueError(f"unmeasured receipt {key}")
            for short, field in (("fix", "t_fix"), ("keep", "t_keep")):
                matrices[short][key] = 0 if r["gate"] == 0 else r[field]
            matrices["score"][key] = r["score"]
            matrices["resolved"][key] = float(r["resolved"])
    if len(seen) != len(names) * len(tasks):
        raise ValueError("incomplete common-cohort receipt grid")
    if not all(np.isfinite(m).all() and ((m >= 0) & (m <= 1)).all() for m in matrices.values()):
        raise ValueError("non-finite or out-of-range measurement")
    if not np.allclose(matrices["score"], np.sqrt(matrices["fix"] * matrices["keep"]), atol=1e-12):
        raise ValueError("saved score differs from gated test-factor product")
    return matrices


def decomposition(m: dict) -> dict:
    """Separate aggregation bias from per-artifact credit and decompose within-system task variance exactly."""
    s, y = m["score"], m["resolved"]
    system_smooth = np.sqrt(m["fix"].mean(1) * m["keep"].mean(1))
    credit = s - y
    yc, dc = y - y.mean(1, keepdims=True), credit - credit.mean(1, keepdims=True)
    variance_y = (yc ** 2).mean(1)
    variance_d = (dc ** 2).mean(1)
    covariance_twice = 2 * (yc * dc).mean(1)
    variance_s = s.var(1)
    return {
        "mean_pass1": float(y.mean()),
        "mean_system_smooth": float(system_smooth.mean()),
        "mean_per_artifact_smooth": float(s.mean()),
        "mean_bias": float((system_smooth - y.mean(1)).mean()),
        "aggregation_gap": float((system_smooth - s.mean(1)).mean()),
        "per_artifact_credit_gap": float(credit.mean()),
        "unresolved_positive_credit": float(np.where(y == 0, s, 0).mean()),
        "resolved_inconsistency_contribution": float(np.where(y == 1, s - y, 0).mean()),
        "mean_gated_t_fix": float(m["fix"].mean()),
        "mean_gated_t_keep": float(m["keep"].mean()),
        "task_variance_mean_per_system": {
            "resolved": float(variance_y.mean()),
            "per_artifact_smooth": float(variance_s.mean()),
            "score_minus_resolved": float(variance_d.mean()),
            "twice_covariance": float(covariance_twice.mean()),
            "identity_max_abs_error": float(np.max(abs(variance_s - variance_y - variance_d - covariance_twice))),
        },
    }


def summarize(values: list[float | None], requested: int) -> dict:
    values = np.asarray([v for v in values if v is not None and np.isfinite(v)], float)
    return {"defined": len(values), "requested": requested,
            "median": float(np.median(values)) if len(values) else None,
            "p05_p95": np.quantile(values, [.05, .95]).tolist() if len(values) else None}


def split_diagnostics(m: dict, *, splits: int = 2000, size: int = 50, seed: int = 20261125) -> dict:
    """Use independent post-hoc task splits; affine level calibration sees only A outcomes, never B."""
    n = m["resolved"].shape[1]
    if not 0 < size < n or splits < 1:
        raise ValueError("positive splits and nonempty A/B required")
    rng = np.random.default_rng(seed)
    methods = ("pass1", "system_smooth", "per_artifact_mean", "t_fix_mean", "calibrated_system_smooth")
    ranks, errors, deltas = ({k: [] for k in methods} for _ in range(3))
    slopes = []
    for _ in range(splits):
        order = rng.permutation(n)
        a, b = order[:size], order[size:]
        ya, yb = m["resolved"][:, a].mean(1), m["resolved"][:, b].mean(1)
        sa = np.sqrt(m["fix"][:, a].mean(1) * m["keep"][:, a].mean(1))
        design = np.column_stack([np.ones(len(sa)), sa])
        coefficients = np.linalg.lstsq(design, ya, rcond=None)[0]
        slopes.append(float(coefficients[1]))
        predictions = {"pass1": ya, "system_smooth": sa,
                       "per_artifact_mean": m["score"][:, a].mean(1),
                       "t_fix_mean": m["fix"][:, a].mean(1),
                       "calibrated_system_smooth": design @ coefficients}
        reference = spearman(ya, yb)
        for name, prediction in predictions.items():
            rank = spearman(prediction, yb)
            ranks[name].append(rank)
            errors[name].append(float(np.mean(abs(prediction - yb))))
            deltas[name].append(rank - reference if rank is not None and reference is not None else None)
    return {"seed": seed, "n_A": size, "n_B": n - size, "splits": splits,
            "interval_note": "5th–95th split-distribution percentiles, not population confidence intervals",
            "calibration_note": "OLS pass1_A ~ intercept + system_smooth_A across the same systems; unbounded predictions; post-hoc task generalization only",
            "calibration_slope": summarize(slopes, splits),
            "methods": {k: {"spearman": summarize(ranks[k], splits), "mae": summarize(errors[k], splits),
                             "rank_delta_vs_pass1": summarize(deltas[k], splits),
                             "rank_delta_positive": sum(v is not None and v > 0 for v in deltas[k])}
                        for k in methods}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--systems", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    m = load_matrices(args.receipts, args.original, args.systems)
    old = json.loads(args.original.read_text())
    result = {
        "date": "11-25-2026", "status": "POST-HOC FOLLOW-UP; original locked outcomes unchanged",
        "host": "skampere1", "harness": "Codex CLI, GPT-6 Astra ultra (Vals account)",
        "execution": "CPU only; zero model generation or judge calls; no DT; not a Lean check",
        "input_files": {k: {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                        for k, p in (("receipts", args.receipts), ("original", args.original), ("systems", args.systems))},
        "systems": m["resolved"].shape[0], "tasks": m["resolved"].shape[1],
        "original_H1": old["H1_scs4c_vs_pass1"],
        "original_H2_n50": old["H2_held_out_prediction"]["50"],
        "decomposition": decomposition(m), "posthoc_splits": split_diagnostics(m),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"out": str(args.out), "systems": result["systems"], "tasks": result["tasks"],
                      "decomposition": result["decomposition"], "posthoc_splits": result["posthoc_splits"]}, indent=2))


if __name__ == "__main__":
    main()
