"""TLDR: Experiment 07 phase A analysis: SCS4C-T versus pass@1 across SWE-bench Verified submissions (H1 construct check, H1b partial-credit signal, H2 held-out prediction, H3 signal density)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from rl4cv.scs4c import TEST_FACTORS, Cell, cell_from_report, cell_score, kendall_tau_b, pearson, spearman, system_summary

EMPTY_KEYS = ("no_generation", "empty_patch", "empty_generation")


def load_gold(path: Path) -> dict[str, tuple[list[str], list[str]]]:
    gold = {}
    for line in path.read_text().splitlines():
        r = json.loads(line)
        gold[r["instance_id"]] = (r["FAIL_TO_PASS"], r["PASS_TO_PASS"])
    return gold


def load_cells(sub: Path, gold: dict) -> list[Cell]:
    """One cell per gold task. A report decides the gate; without one, a known-empty patch is 0, otherwise unmeasured."""
    preds = None
    if (sub / "all_preds.jsonl").is_file():
        preds = {}
        for line in (sub / "all_preds.jsonl").read_text().splitlines():
            if line.strip():
                p = json.loads(line)
                preds[p["instance_id"]] = bool((p.get("model_patch") or "").strip())
    empty: set[str] = set()
    if (sub / "results.json").is_file():
        res = json.loads((sub / "results.json").read_text())
        empty = {i for k in EMPTY_KEYS for i in res.get(k, [])}
    cells = []
    for iid, (f2p, p2p) in gold.items():
        rp = sub / "logs" / iid / "report.json"
        report = json.loads(rp.read_text()).get(iid) if rp.is_file() else None
        has_patch = report is not None or (preds.get(iid, False) if preds is not None else iid not in empty)
        cells.append(cell_from_report(iid, report, has_patch=has_patch))
    return cells


def gold_mismatches(sub: Path, gold: dict) -> int:
    """Reports whose FAIL_TO_PASS or PASS_TO_PASS test sets differ from the pinned gold lists (validity check)."""
    bad = 0
    for iid, (f2p, p2p) in gold.items():
        rp = sub / "logs" / iid / "report.json"
        if not rp.is_file():
            continue
        status = (json.loads(rp.read_text()).get(iid) or {}).get("tests_status") or {}
        for group, ref in (("FAIL_TO_PASS", f2p), ("PASS_TO_PASS", p2p)):
            entry = status.get(group) or {}
            if set(entry.get("success", [])) | set(entry.get("failure", [])) != set(ref):
                bad += 1
                break
    return bad


def factor_matrices(systems: dict[str, list[Cell]], cohort: list[str]) -> dict[str, np.ndarray]:
    """Systems × cohort-task matrices of gated factors, per-cell score and resolution."""
    out = {f: [] for f in (*TEST_FACTORS, "score", "resolved")}
    for cells in systems.values():
        by_id = {c.instance_id: c for c in cells}
        row = [by_id[i] for i in cohort]
        for f in TEST_FACTORS:
            out[f].append([c.gated(f) for c in row])
        out["score"].append([cell_score(c) for c in row])
        out["resolved"].append([float(bool(c.resolved)) for c in row])
    return {k: np.asarray(v, float) for k, v in out.items()}


def system_scores(m: dict[str, np.ndarray], idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """SCS4C-T (geometric mean of gated factor means) and pass@1 per system over task columns ``idx``."""
    means = np.stack([m[f][:, idx].mean(1) for f in TEST_FACTORS])
    with np.errstate(divide="ignore"):
        scs = np.where((means > 0).all(0), np.exp(np.log(np.where(means > 0, means, 1)).mean(0)), 0.0)
    return scs, m["resolved"][:, idx].mean(1)


def three_corr(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = ~(np.isnan(x) | np.isnan(y))
    x, y = x[keep], y[keep]
    return {"pearson": pearson(x, y), "spearman": spearman(x, y), "kendall_tau_b": kendall_tau_b(x, y)}


def percentile_ci(vals: list[float]) -> list[float] | None:
    vals = [v for v in vals if v is not None]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def bootstrap_corr(x_fn, n_tasks: int, n_sys: int, rng, b: int) -> dict:
    """Percentile intervals for Spearman/Pearson/Kendall, resampling tasks and, separately, systems."""
    out = {}
    for unit in ("tasks", "systems"):
        draws = {k: [] for k in ("pearson", "spearman", "kendall_tau_b")}
        for _ in range(b):
            if unit == "tasks":
                x, y = x_fn(rng.integers(0, n_tasks, n_tasks))
            else:
                x, y = x_fn(np.arange(n_tasks))
                s = rng.integers(0, n_sys, n_sys)
                x, y = x[s], y[s]
            for k, v in three_corr(x, y).items():
                draws[k].append(v)
        out[unit] = {k: percentile_ci(v) for k, v in draws.items()}
    return out


def partial_credit(m: dict[str, np.ndarray], idx: np.ndarray) -> np.ndarray:
    """Mean per-cell SCS4C-T over each system's unresolved cohort cells (the credit pass@1 discards)."""
    unresolved = m["resolved"][:, idx] == 0
    score = m["score"][:, idx]
    return np.array([score[i][unresolved[i]].mean() if unresolved[i].any() else np.nan for i in range(len(score))])


def held_out_prediction(m: dict[str, np.ndarray], sizes: list[int], r: int, rng) -> dict:
    """For random task splits A/B: Spearman(SCS4C-T on A, pass@1 on B) minus Spearman(pass@1 on A, pass@1 on B)."""
    n = m["resolved"].shape[1]
    out = {}
    for size in sizes:
        deltas, scs_rho, p1_rho, undefined = [], [], [], 0
        for _ in range(r):
            perm = rng.permutation(n)
            a, b = perm[:size], perm[size:]
            scs_a, p1_a = system_scores(m, a)
            _, p1_b = system_scores(m, b)
            ra, rb = spearman(scs_a, p1_b), spearman(p1_a, p1_b)
            if ra is None or rb is None:
                undefined += 1
                continue
            deltas.append(ra - rb)
            scs_rho.append(ra)
            p1_rho.append(rb)
        out[str(size)] = {
            "splits": r, "undefined": undefined,
            "delta_median": float(np.median(deltas)), "delta_p05_p95": [float(np.percentile(deltas, 5)), float(np.percentile(deltas, 95))],
            "share_delta_positive": float(np.mean(np.array(deltas) > 0)),
            "spearman_scs4c_A_vs_pass1_B_median": float(np.median(scs_rho)), "spearman_pass1_A_vs_pass1_B_median": float(np.median(p1_rho)),
        }
    return out


def signal_density(systems: dict[str, list[Cell]]) -> dict:
    measured = [c for cells in systems.values() for c in cells if cell_score(c) is not None]
    partial = sum(1 for c in measured if not c.resolved and cell_score(c) > 0)
    return {
        "measured_cells": len(measured),
        "unresolved_cells": sum(1 for c in measured if not c.resolved),
        "unresolved_with_partial_credit": partial,
        "resolved_but_score_below_1": sum(1 for c in measured if c.resolved and cell_score(c) < 1),
        "unresolved_but_score_1": sum(1 for c in measured if not c.resolved and cell_score(c) == 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True, help="fetch_e07.py output root")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--min-measured", type=float, default=0.95)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--splits", type=int, default=2000)
    ap.add_argument("--sizes", type=int, nargs="+", default=[25, 50, 100, 250])
    ap.add_argument("--seed", type=int, default=20261007)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    gold = load_gold(args.data / "gold_tests.jsonl")
    all_systems = {s.name: load_cells(s, gold) for s in sorted((args.data / "submissions").iterdir()) if s.is_dir()}
    summaries = {k: system_summary(v) for k, v in all_systems.items()}
    included = {k: v for k, v in all_systems.items() if summaries[k]["measured"] >= args.min_measured * len(gold)}
    excluded = {k: summaries[k]["measured"] for k in all_systems if k not in included}
    measured_ids = [{c.instance_id for c in cells if cell_score(c) is not None} for cells in included.values()]
    cohort = [i for i in gold if all(i in ids for ids in measured_ids)]
    m = factor_matrices(included, cohort)
    full = np.arange(len(cohort))
    scs, p1 = system_scores(m, full)
    pc = partial_credit(m, full)

    analysis = {
        "declared_tasks": len(gold), "systems_total": len(all_systems), "systems_included": len(included),
        "systems_excluded_measured_counts": excluded, "common_cohort_tasks": len(cohort),
        "H1_scs4c_vs_pass1": three_corr(scs, p1)
        | {"bootstrap_95": bootstrap_corr(lambda i: system_scores(m, i), len(cohort), len(included), rng, args.boot),
           "mean_bias_scs4c_minus_pass1": float(np.mean(scs - p1)), "mae": float(np.mean(np.abs(scs - p1)))},
        "H1b_partial_credit_vs_pass1": three_corr(pc, p1)
        | {"bootstrap_95": bootstrap_corr(lambda i: (partial_credit(m, i), system_scores(m, i)[1]), len(cohort), len(included), rng, args.boot)},
        "H2_held_out_prediction": held_out_prediction(m, args.sizes, args.splits, rng),
        "H3_signal_density": signal_density(included),
        "validity_reports_differing_from_pinned_gold_lists": {k: gold_mismatches(args.data / "submissions" / k, gold) for k in included},
        "settings": vars(args) | {"data": str(args.data), "out_dir": str(args.out_dir)},
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "analysis_e07.json").write_text(json.dumps(analysis, indent=1, default=str) + "\n")
    with (args.out_dir / "per_system_e07.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["submission", "included", "measured", "unmeasured", "scs4c_t_own_cohort", "per_task_mean", "pass1_own_cohort",
                    "pass1_declared", "t_fix_mean", "t_keep_mean"])
        for k, s in summaries.items():
            fm = s["factor_means"]
            w.writerow([k, k in included, s["measured"], s["unmeasured"], s["scs4c"], s["per_task_mean"], s["pass1"], s["pass1_declared"],
                        fm.get("t_fix"), fm.get("t_keep")])
    print(json.dumps({k: analysis[k] for k in ("systems_included", "common_cohort_tasks", "H1_scs4c_vs_pass1")}, indent=1, default=str))


if __name__ == "__main__":
    main()
