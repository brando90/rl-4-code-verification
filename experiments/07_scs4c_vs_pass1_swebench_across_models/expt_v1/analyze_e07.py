"""TLDR: Experiment 07 phase A analysis: SCS4C-T versus pass@1 across SWE-bench Verified submissions (H1 construct check, H1b partial-credit signal, H2 held-out prediction, H3 signal density)."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from rl4cv.scs4c import TEST_FACTORS, Cell, cell_from_report, cell_score, kendall_tau_b, pearson, spearman, system_summary

EMPTY_KEYS = ("no_generation", "empty_patch", "empty_generation")
CORRELATIONS = ("pearson", "spearman", "kendall_tau_b")
UNNAMED_MODELS = {"undisclosed", "unknown", "n/a", "none", ""}


def load_gold(path: Path) -> dict[str, tuple[list[str], list[str]]]:
    gold = {}
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if r["instance_id"] in gold:
            raise ValueError(f"duplicate gold task: {r['instance_id']}")
        for key in ("FAIL_TO_PASS", "PASS_TO_PASS"):
            if not isinstance(r[key], list) or not all(isinstance(t, str) for t in r[key]):
                raise ValueError(f"invalid gold test list: {r['instance_id']} {key}")
        gold[r["instance_id"]] = (r["FAIL_TO_PASS"], r["PASS_TO_PASS"])
    return gold



REPORT_KEYS = ("patch_exists", "patch_successfully_applied", "tests_status")


def read_report(path: Path, iid: str) -> dict | None:
    """One instance's report in either official shape; missing, truncated or malformed files provide no evidence.

    The 2024 harness writes ``{"<instance_id>": {...report...}}``; sb-cli and the mini-SWE-agent runs from 2025 on
    write the report dict itself at the top level. A file keyed by a different instance id is not evidence for ``iid``.
    """
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if iid in data:
        report = data[iid]
    elif any(key in data for key in REPORT_KEYS):
        report = data
    else:
        return None
    return report if isinstance(report, dict) else None

def official_resolution(sub: Path) -> tuple[set[str], set[str] | None]:
    """Known-empty patches and the official resolved set: ``results.json`` first, else ``per_instance_details.json``.

    The mini-SWE-agent entries publish per-instance ``resolved`` flags in ``per_instance_details.json`` instead of
    a ``results.json``; either file is committed in SWE-bench/experiments and copied by the fetch.
    """
    empty: set[str] = set()
    official = None
    if (sub / "results.json").is_file():
        res = json.loads((sub / "results.json").read_text())
        empty = {i for k in EMPTY_KEYS for i in res.get(k, [])}
        if isinstance(res.get("resolved"), list):
            official = set(res["resolved"])
    elif (sub / "per_instance_details.json").is_file():
        details = json.loads((sub / "per_instance_details.json").read_text())
        if isinstance(details, dict):
            official = {i for i, d in details.items() if isinstance(d, dict) and d.get("resolved") is True}
    return empty, official


def load_cells(sub: Path, gold: dict) -> list[Cell]:
    """One cell per gold task. A report decides the gate; without one, a known-empty patch is 0, otherwise unmeasured."""
    preds = None
    if (sub / "all_preds.jsonl").is_file():
        preds = {}
        for line in (sub / "all_preds.jsonl").read_text().splitlines():
            if line.strip():
                p = json.loads(line)
                preds[p["instance_id"]] = bool((p.get("model_patch") or "").strip())
    empty, official_resolved = official_resolution(sub)
    cells = []
    for iid in gold:
        rp = sub / "logs" / iid / "report.json"
        report = read_report(rp, iid)
        has_patch = report is not None or (iid not in empty and (preds.get(iid, False) if preds is not None else True))
        cell = cell_from_report(iid, report, has_patch=has_patch)
        if official_resolved is not None and (report is None or cell.resolved is None):
            cell = replace(cell, resolved=iid in official_resolved)
        if not cell.measured:
            reason = ("no report file" if not rp.is_file() else "report file empty, malformed or for another instance" if report is None
                      else "report lacks gate flags or per-test status")
            cell = replace(cell, unmeasured_reason=reason)
        cells.append(cell)
    return cells


def official_disagreements(sub: Path, gold: dict) -> dict | None:
    """Validity: reports whose ``resolved`` flag differs from the submission's official resolved list; ``None`` without a list."""
    _, official = official_resolution(sub)
    if official is None:
        return None
    compared, bad = 0, []
    for iid in gold:
        report = read_report(sub / "logs" / iid / "report.json", iid)
        if report is not None and isinstance(report.get("resolved"), bool):
            compared += 1
            if report["resolved"] != (iid in official):
                bad.append(iid)
    return {"compared": compared, "disagreements": len(bad), "examples": bad[:5]}


def exclusion_reason(cells: list[Cell], row: dict, threshold: float) -> str:
    """Human-readable reason a system failed inclusion, from its cells and the fetch inventory row."""
    measured = sum(c.measured for c in cells)
    reasons = Counter(c.unmeasured_reason for c in cells if not c.measured)
    parts = [f"{measured}/{len(cells)} measured cells, below the {threshold:g} inclusion threshold",
             f"logs source {row.get('source')} ({row.get('reports', 0)} report files)"]
    if row.get("error"):
        parts.append(f"fetch error: {row['error']}")
    parts.extend(f"{n} cells: {reason}" for reason, n in reasons.most_common())
    return "; ".join(parts)


def gold_mismatches(sub: Path, gold: dict) -> int:
    """Reports whose FAIL_TO_PASS or PASS_TO_PASS test sets differ from the pinned gold lists (validity check)."""
    bad = 0
    for iid, (f2p, p2p) in gold.items():
        rp = sub / "logs" / iid / "report.json"
        if not rp.is_file():
            continue
        report = read_report(rp, iid)
        status = (report or {}).get("tests_status")
        if not isinstance(status, dict):
            continue
        for group, ref in (("FAIL_TO_PASS", f2p), ("PASS_TO_PASS", p2p)):
            entry = status.get(group)
            if not isinstance(entry, dict) or not all(isinstance(entry.get(k), list) for k in ("success", "failure")):
                continue
            if set(entry["success"]) | set(entry["failure"]) != set(ref):
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
    if len(idx) == 0:
        missing = np.full(m["resolved"].shape[0], np.nan)
        return missing, missing.copy()
    means = np.stack([m[f][:, idx].mean(1) for f in TEST_FACTORS])
    with np.errstate(divide="ignore"):
        scs = np.where((means > 0).all(0), np.exp(np.log(np.where(means > 0, means, 1)).mean(0)), 0.0)
    scs[~np.isfinite(means).all(0)] = np.nan
    return scs, m["resolved"][:, idx].mean(1)


def three_corr(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    return {"pearson": pearson(x, y), "spearman": spearman(x, y), "kendall_tau_b": kendall_tau_b(x, y),
            "n_systems": len(x), "excluded_systems": int((~keep).sum())}


def percentile_ci(vals: list[float]) -> list[float] | None:
    vals = [v for v in vals if v is not None and np.isfinite(v)]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def agreement(x, y) -> dict:
    """Absolute score agreement on finite pairs; positive bias means SCS4C-T exceeds pass@1."""
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    return {"mean_bias_scs4c_minus_pass1": float(np.mean(x - y)) if len(x) else None,
            "mae": float(np.mean(np.abs(x - y))) if len(x) else None,
            "mean_scs4c": float(np.mean(x)) if len(x) else None,
            "mean_pass1": float(np.mean(y)) if len(x) else None}


def bootstrap_corr(x_fn, n_tasks: int, n_sys: int, rng, b: int, *, include_agreement: bool = False) -> dict:
    """Paired task and separate system bootstraps, including defined-draw denominators."""
    out = {}
    base_x, base_y = x_fn(np.arange(n_tasks))
    keys = (*CORRELATIONS, *agreement(base_x, base_y)) if include_agreement else CORRELATIONS
    for unit in ("tasks", "systems"):
        draws = {k: [] for k in keys}
        pair_counts = []
        for _ in range(b):
            if unit == "tasks":
                x, y = x_fn(rng.integers(0, n_tasks, n_tasks))
            else:
                s = rng.integers(0, n_sys, n_sys)
                x, y = base_x[s], base_y[s]
            stats = three_corr(x, y)
            pair_counts.append(stats["n_systems"])
            if include_agreement:
                stats.update(agreement(x, y))
            for k in keys:
                draws[k].append(stats[k])
        out[unit] = {k: percentile_ci(v) for k, v in draws.items()} | {
            "requested_draws": b,
            "defined_draws": {k: sum(1 for v in values if v is not None and np.isfinite(v)) for k, values in draws.items()},
            "n_systems_range": [min(pair_counts), max(pair_counts)] if pair_counts else None,
        }
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
        result = {"splits": r, "defined": 0, "undefined": r, "n_A": size, "n_B": n - size,
                  "delta_median": None, "delta_p05_p95": None, "share_delta_positive": None,
                  "spearman_scs4c_A_vs_pass1_B_median": None, "spearman_pass1_A_vs_pass1_B_median": None,
                  "positive_splits": 0, "share_denominator": r}
        if not 0 < size < n:
            out[str(size)] = result | {"status": "unavailable: split needs nonempty A and B"}
            continue
        deltas, scs_rho, p1_rho = [], [], []
        for _ in range(r):
            perm = rng.permutation(n)
            a, b = perm[:size], perm[size:]
            scs_a, p1_a = system_scores(m, a)
            _, p1_b = system_scores(m, b)
            ra, rb = spearman(scs_a, p1_b), spearman(p1_a, p1_b)
            if ra is None or rb is None:
                continue
            deltas.append(ra - rb)
            scs_rho.append(ra)
            p1_rho.append(rb)
        result.update(defined=len(deltas), undefined=r - len(deltas),
                      status="complete" if len(deltas) == r else "undefined correlations; verdict unavailable")
        if deltas:
            positive = int((np.asarray(deltas) > 0).sum())
            result.update(delta_median=float(np.median(deltas)),
                          delta_p05_p95=[float(v) for v in np.percentile(deltas, [5, 95])],
                          positive_splits=positive, share_delta_positive=positive / r,
                          spearman_scs4c_A_vs_pass1_B_median=float(np.median(scs_rho)),
                          spearman_pass1_A_vs_pass1_B_median=float(np.median(p1_rho)))
        out[str(size)] = result
    return out


def model_key(display: str) -> str:
    """Order-insensitive token key so 'Claude Opus 4.5' and 'Claude 4.5 Opus' name one base model."""
    return " ".join(sorted(re.findall(r"[a-z0-9.]+", display.lower())))


def base_model_sensitivity(included: dict[str, list[Cell]], cohort: list[str], data: Path, rng, boot: int, splits: int,
                           size: int = 50) -> dict:
    """Protocol sensitivity, not primary: one system per base model (the latest submission, by the folder-name date) keyed by
    metadata ``tags.model_display``; H1, H1b and H2 at n_A = 50 on the primary common cohort."""
    import yaml

    chosen: dict[str, str] = {}
    display: dict[str, str] = {}
    skipped: dict[str, str] = {}
    for name in included:
        meta = {}
        for fname in ("metadata.yaml", "metadata.yml"):
            if (data / "submissions" / name / fname).is_file():
                meta = yaml.safe_load((data / "submissions" / name / fname).read_text()) or {}
                break
        model = (meta.get("tags") or {}).get("model_display") or (meta.get("info") or {}).get("model_display")
        if not isinstance(model, str) or model.strip().lower() in UNNAMED_MODELS:
            skipped[name] = "metadata does not name the model"
            continue
        key = model_key(model)
        if key not in chosen or name > chosen[key]:
            chosen[key], display[key] = name, model.strip()
    systems = {chosen[k]: included[chosen[k]] for k in sorted(chosen)}
    out = {"selection": "one system per base model: the latest submission (folder-name date) per metadata tags.model_display, "
                        "matched on an order-insensitive token key; same common cohort as the primary analysis",
           "systems": {display[k]: chosen[k] for k in sorted(chosen)}, "skipped_systems": skipped,
           "n_systems": len(systems), "common_cohort_tasks": len(cohort)}
    if len(systems) < 3 or not cohort:
        return out | {"status": "unavailable: fewer than 3 named-model systems or an empty cohort"}
    m = factor_matrices(systems, cohort)
    full = np.arange(len(cohort))
    scs, p1 = system_scores(m, full)
    pc = partial_credit(m, full)
    return out | {
        "status": "computed" if len(systems) >= 20 else "computed (fewer than 20 systems; descriptive only)",
        "H1_scs4c_vs_pass1": three_corr(scs, p1) | agreement(scs, p1)
        | {"bootstrap_95": bootstrap_corr(lambda i: system_scores(m, i), len(cohort), len(systems), rng, boot, include_agreement=True)},
        "H1b_partial_credit_vs_pass1": three_corr(pc, p1)
        | {"bootstrap_95": bootstrap_corr(lambda i: (partial_credit(m, i), system_scores(m, i)[1]), len(cohort), len(systems), rng, boot),
           "systems_without_unresolved_cells": [name for name, value in zip(systems, pc) if not np.isfinite(value)]},
        "H2_held_out_prediction": held_out_prediction(m, [size], splits, rng),
    }


def signal_density(systems: dict[str, list[Cell]]) -> dict:
    measured = [c for cells in systems.values() for c in cells if cell_score(c) is not None]
    partial = sum(1 for c in measured if not c.resolved and cell_score(c) > 0)
    unresolved = sum(1 for c in measured if not c.resolved)
    declared = sum(len(cells) for cells in systems.values())
    return {
        "declared_cells": declared, "unmeasured_cells": declared - len(measured),
        "share_unresolved_with_partial_credit": partial / unresolved if unresolved else None,
        "measured_cells": len(measured),
        "unresolved_cells": sum(1 for c in measured if not c.resolved),
        "unresolved_with_partial_credit": partial,
        "resolved_but_score_below_1": sum(1 for c in measured if c.resolved and cell_score(c) < 1),
        "unresolved_but_score_1": sum(1 for c in measured if not c.resolved and cell_score(c) == 1),
    }


def write_outputs(out_dir: Path, analysis: dict, all_systems: dict, included: dict, cohort: list[str]) -> None:
    """Write strict JSON, paired own/common system scores, and one receipt per declared cell."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "analysis_e07.json").write_text(json.dumps(analysis, indent=1, allow_nan=False) + "\n")
    cohort_ids = set(cohort)
    with (out_dir / "per_system_e07.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["submission", "included", "declared", "measured", "unmeasured", "scs4c_t_own_cohort",
                    "per_task_mean", "pass1_own_cohort", "pass1_declared", "t_fix_mean", "t_keep_mean",
                    "common_cohort_tasks", "scs4c_t_common_cohort", "pass1_common_cohort",
                    "t_fix_common_mean", "t_keep_common_mean"])
        for k, cells in all_systems.items():
            own = system_summary(cells)
            common = system_summary([c for c in cells if c.instance_id in cohort_ids]) if k in included else system_summary([])
            fm, cm = own["factor_means"], common["factor_means"]
            w.writerow([k, k in included, own["declared"], own["measured"], own["unmeasured"], own["scs4c"],
                        own["per_task_mean"], own["pass1"], own["pass1_declared"], fm.get("t_fix"), fm.get("t_keep"),
                        common["measured"], common["scs4c"], common["pass1"], cm.get("t_fix"), cm.get("t_keep")])
    with gzip.open(out_dir / "per_cell_e07.jsonl.gz", "wt") as fh:
        for name, cells in all_systems.items():
            for cell in cells:
                state = f"unmeasured: {cell.unmeasured_reason or 'missing or incomplete report or patch evidence'}" if not cell.measured else (
                    "no_patch_or_patch_not_applied" if cell.gate == 0 else "measured_test_report")
                receipt = asdict(cell) | {"submission": name, "status": state, "score": cell_score(cell),
                                         "included": name in included, "common_cohort": name in included and cell.instance_id in cohort_ids}
                fh.write(json.dumps(receipt, allow_nan=False) + "\n")


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
    if not 0 < args.min_measured <= 1 or min(args.boot, args.splits, *args.sizes) < 1:
        ap.error("inclusion must be in (0, 1]; draws and split sizes must be positive")
    rng = np.random.default_rng(args.seed)
    gold = load_gold(args.data / "gold_tests.jsonl")
    if len(gold) != 500:
        raise ValueError(f"locked task universe requires 500 unique tasks; found {len(gold)}")
    inventory = json.loads((args.data / "inventory.json").read_text())
    names = [s["submission"] for s in inventory]
    inputs = json.loads((args.data / "inputs_manifest.json").read_text())
    expected = {"experiments_commit": "40f164d5b8f1d249bf95a6df8b74b577fd8e519d", "split": "verified",
                "gold_dataset": "princeton-nlp/SWE-bench_Verified", "gold_revision": "c104f840cc67f8b6eec6f759ebc8b2693d585d4a",
                "submissions": sorted(names), "gold_sha256": hashlib.sha256((args.data / "gold_tests.jsonl").read_bytes()).hexdigest()}
    if inputs != expected:
        raise ValueError("data/inventory differ from pinned input provenance; rerun the fetch into a fresh directory")
    if len(names) != len(set(names)) or any(Path(n).name != n or n in (".", "..") for n in names):
        raise ValueError("inventory requires unique submission directory names")
    # Inventory is the manifest; stale directories are never extra systems, and absent directories stay declared.
    all_systems = {name: load_cells(args.data / "submissions" / name, gold) for name in sorted(names)}
    summaries = {k: system_summary(v) for k, v in all_systems.items()}
    threshold = args.min_measured * len(gold)
    included = {k: v for k, v in all_systems.items() if summaries[k]["measured"] >= threshold}
    excluded = {k: summaries[k]["measured"] for k in all_systems if k not in included}
    rows = {row["submission"]: row for row in inventory}
    measured_ids = [{c.instance_id for c in cells if cell_score(c) is not None} for cells in included.values()]
    cohort = [i for i in gold if measured_ids and all(i in ids for ids in measured_ids)]
    validity = signal_density(all_systems)
    inconsistent = validity["resolved_but_score_below_1"] + validity["unresolved_but_score_1"]
    consistency_rate = inconsistent / validity["measured_cells"] if validity["measured_cells"] else None
    analysis = {
        "declared_tasks": len(gold), "systems_total": len(all_systems), "systems_included": len(included),
        "systems_excluded_measured_counts": excluded,
        "systems_excluded_reasons": {k: exclusion_reason(all_systems[k], rows.get(k, {}), threshold) for k in excluded},
        "unmeasured_reasons_per_system": {k: dict(Counter(c.unmeasured_reason for c in cells if not c.measured)) for k, cells in all_systems.items()},
        "inventory": inventory, "common_cohort_tasks": len(cohort), "common_cohort_ids": cohort,
        "unmeasured_task_ids": {k: [c.instance_id for c in cells if not c.measured] for k, cells in all_systems.items()},
        "validity_all_declared_systems": validity | {"inconsistent_cells": inconsistent, "inconsistent_fraction": consistency_rate},
        "validity_reports_differing_from_pinned_gold_lists": {k: gold_mismatches(args.data / "submissions" / k, gold) for k in all_systems},
        "validity_report_vs_official_resolved": {k: official_disagreements(args.data / "submissions" / k, gold) for k in all_systems},
        "settings": vars(args) | {"data": str(args.data), "out_dir": str(args.out_dir)}, "input_provenance": inputs,
        "locked_settings": (args.min_measured, args.boot, args.splits, args.sizes, args.seed) == (0.95, 2000, 2000, [25, 50, 100, 250], 20261007),
        "p_value": None, "p_value_note": "p-val=n/a; no hypothesis test run; protocol uses intervals and split summaries",
        "uncertainty_note": "Separate task/system percentile bootstraps conditional on the observed cohort; split percentiles are not population intervals.",
        "sensitivity_status": "not computed: primary analysis not valid",
    }
    if consistency_rate is not None and consistency_rate > 0.005:
        analysis["status"] = "STOP: consistency violations exceed 0.5% of measured cells"
    elif len(included) < 20:
        analysis["status"] = "UNDERPOWERED: fewer than 20 included systems; no hypotheses reported"
    elif not cohort:
        analysis["status"] = "UNMEASURED: empty common cohort; no hypotheses reported"
    else:
        m = factor_matrices(included, cohort)
        full = np.arange(len(cohort))
        scs, p1 = system_scores(m, full)
        pc = partial_credit(m, full)
        cohort_ids = set(cohort)
        common_systems = {k: [c for c in cells if c.instance_id in cohort_ids] for k, cells in included.items()}
        analysis.update({
            "status": "PRIMARY ANALYSES COMPUTED",
            "H1_scs4c_vs_pass1": three_corr(scs, p1) | agreement(scs, p1)
            | {"bootstrap_95": bootstrap_corr(lambda i: system_scores(m, i), len(cohort), len(included), rng, args.boot, include_agreement=True)},
            "H1b_partial_credit_vs_pass1": three_corr(pc, p1)
            | {"bootstrap_95": bootstrap_corr(lambda i: (partial_credit(m, i), system_scores(m, i)[1]), len(cohort), len(included), rng, args.boot),
               "systems_without_unresolved_cells": [name for name, value in zip(included, pc) if not np.isfinite(value)],
               "unresolved_cells_per_system": dict(zip(included, (m["resolved"] == 0).sum(1).tolist()))},
            "H2_held_out_prediction": held_out_prediction(m, args.sizes, args.splits, rng),
            "H3_signal_density": signal_density(common_systems),
            "own_cohort_signal_density": signal_density(included),
            "sensitivity_status": "computed on a separate random stream (seed [seed, 1]); see sensitivity_one_system_per_base_model",
            "sensitivity_one_system_per_base_model": base_model_sensitivity(
                included, cohort, args.data, np.random.default_rng([args.seed, 1]), args.boot, args.splits),
        })
    write_outputs(args.out_dir, analysis, all_systems, included, cohort)
    print(json.dumps({k: analysis[k] for k in ("status", "systems_included", "common_cohort_tasks")}, indent=1, allow_nan=False))


if __name__ == "__main__":
    main()
