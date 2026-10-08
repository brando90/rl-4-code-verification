#!/usr/bin/env python3
"""TLDR: Experiment 08 test evaluation (PROTOCOL § 10, D-009): per system, factor means (IC_tests, IC_proofs, compile-gated FSC) on the one common cohort of cells with all three factors known, SCSC = (mean IC_tests · mean IC_proofs · mean fsc_compiled)^(1/3), measured / declared cell and task counts with every unknown cell listed, full-manifest bounds (unknown factors set to 0 or 1), all 222 tasks / core 152 / IndustrySet 70 separately, 10,000 task-bootstrap resamples with seed 0 carrying all eight samples, and paired π₀(N) − Base differences (kernel_binary mean pass rate and SCSC) on the shared known cohort with shared resampled task indices; p-val=n/a (interval estimation only). Never the legacy mean per-file SCSC. Zero model calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

EXP = Path(__file__).resolve().parents[1]
G = 8
N_BOOT, SEED = 10000, 0
SCOPES = ("all", "core", "industryset")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_ids(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]


def load_system(label: str, cells_dir: Path, judge_dir: Path, test_ids: list[str]) -> dict:
    """Per cell: IC_tests, IC_proofs, kernel_binary (None = unknown), fsc_compiled (None = unknown: IC_tests = 1 without a judged FSC)."""
    cells = {}
    with (cells_dir / f"{label}_test_cells.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            cells[(r["task_id"], int(r["sample_idx"]))] = r
    fsc_path = judge_dir / f"fsc_{label}.json"
    fsc = json.loads(fsc_path.read_text())["cells"] if fsc_path.exists() else {}
    out = {}
    for t in test_ids:
        for k in range(G):
            r = cells.get((t, k))
            known = bool(r) and r["known"] == "True"
            ic_t = float(r["IC_tests"]) if known and r["IC_tests"] not in ("", "None") else None
            ic_p = float(r["IC_proofs"]) if known and r["IC_proofs"] not in ("", "None") else None
            kb = float(r["kernel_binary"]) if known and r["kernel_binary"] not in ("", "None") else None
            if ic_t is None:
                fc = None
            elif ic_t == 0.0:
                fc = 0.0
            else:
                j = fsc.get(f"{t}#{k}")
                fc = j["FSC"] if j and j.get("FSC") is not None else None
            out[(t, k)] = {"IC_tests": ic_t, "IC_proofs": ic_p, "kernel_binary": kb, "fsc_compiled": fc}
    return out


def scsc_of(m_t: float, m_p: float, m_f: float) -> float:
    prod = m_t * m_p * m_f
    return prod ** (1.0 / 3.0) if prod > 0 else 0.0


def factor_arrays(cells: dict, tasks: list[str], keys=("IC_tests", "IC_proofs", "fsc_compiled")) -> tuple[np.ndarray, np.ndarray]:
    """(T x G x 3 array of factors with NaN for unknown, T x G known-mask for the common cohort)."""
    arr = np.full((len(tasks), G, len(keys)), np.nan)
    for i, t in enumerate(tasks):
        for k in range(G):
            c = cells[(t, k)]
            for j, key in enumerate(keys):
                if c[key] is not None:
                    arr[i, k, j] = c[key]
    known = ~np.isnan(arr).any(axis=2)
    return arr, known


def summarize(arr: np.ndarray, known: np.ndarray, rng: np.random.Generator | None, idx_sets: np.ndarray | None) -> dict:
    T = arr.shape[0]
    flat_known = known.reshape(-1)
    n_known = int(flat_known.sum())
    means = np.nanmean(arr.reshape(-1, 3)[flat_known], axis=0) if n_known else np.array([np.nan] * 3)
    point = {"IC_tests": float(means[0]), "IC_proofs": float(means[1]), "fsc_compiled": float(means[2]), "SCSC": scsc_of(*means) if n_known else None}
    # Full-manifest bounds: unknown factors set to 0 (lower) or 1 (upper) for every declared cell.
    lo_arr, hi_arr = np.nan_to_num(arr, nan=0.0), np.nan_to_num(arr, nan=1.0)
    lo_m, hi_m = lo_arr.reshape(-1, 3).mean(axis=0), hi_arr.reshape(-1, 3).mean(axis=0)
    bounds = {"IC_tests": [float(lo_m[0]), float(hi_m[0])], "IC_proofs": [float(lo_m[1]), float(hi_m[1])], "fsc_compiled": [float(lo_m[2]), float(hi_m[2])],
              "SCSC": [scsc_of(*lo_m), scsc_of(*hi_m)]}
    boot = None
    if idx_sets is not None and n_known:
        vals = []
        for idx in idx_sets:
            a, kn = arr[idx].reshape(-1, 3), known[idx].reshape(-1)
            if not kn.any():
                continue
            m = a[kn].mean(axis=0)
            vals.append([m[0], m[1], m[2], scsc_of(*m)])
        v = np.array(vals)
        q = np.percentile(v, [2.5, 97.5], axis=0)
        boot = {"IC_tests": [float(q[0, 0]), float(q[1, 0])], "IC_proofs": [float(q[0, 1]), float(q[1, 1])], "fsc_compiled": [float(q[0, 2]), float(q[1, 2])],
                "SCSC": [float(q[0, 3]), float(q[1, 3])], "n_resamples": int(len(v))}
    return {"n_tasks": T, "n_declared_cells": T * G, "n_known_cells": n_known, "n_unknown_cells": T * G - n_known, "tasks_with_all_known": int(known.all(axis=1).sum()),
            "point_common_cohort": point, "bootstrap95_task": boot, "full_manifest_bounds": bounds}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selection", type=Path, default=EXP / "results" / "selection.json")
    ap.add_argument("--cells-dir", type=Path, default=EXP / "results" / "ladder")
    ap.add_argument("--judge-dir", type=Path, default=EXP / "results" / "judge")
    ap.add_argument("--out", type=Path, default=EXP / "results" / "test_eval.json")
    a = ap.parse_args(argv)
    sel = json.loads(a.selection.read_text())
    test_ids = read_ids(EXP / "results" / "split" / "vbv1_test_task_ids.txt")
    with (EXP / "results" / "split" / "vbv1_split_manifest.csv").open(encoding="utf-8", newline="") as fh:
        core = {r["task_id"]: int(r["core"]) for r in csv.DictReader(fh)}
    scopes = {"all": test_ids, "core": [t for t in test_ids if core[t] == 1], "industryset": [t for t in test_ids if core[t] == 0]}
    rng = np.random.default_rng(SEED)
    idx = {s: rng.integers(0, len(ids), size=(N_BOOT, len(ids))) for s, ids in scopes.items()}   # shared resampled task indices per scope
    systems = sel["test_manifest"]["systems"]
    results, cells_by = {}, {}
    for s in systems:
        label = s["label"]
        cells = load_system(label, a.cells_dir, a.judge_dir, test_ids)
        cells_by[label] = cells
        unknown = sorted(f"{t}#{k}" for (t, k), c in cells.items() if any(c[x] is None for x in ("IC_tests", "IC_proofs", "fsc_compiled")))
        per_scope = {}
        for sc, ids in scopes.items():
            arr, known = factor_arrays(cells, ids)
            per_scope[sc] = summarize(arr, known, rng, idx[sc])
            kb = np.array([[cells[(t, k)]["kernel_binary"] if cells[(t, k)]["kernel_binary"] is not None else np.nan for k in range(G)] for t in ids])
            per_scope[sc]["kernel_binary_mean_pass_rate"] = float(np.nanmean(kb)) if not np.isnan(kb).all() else None
            per_scope[sc]["kernel_binary_known_cells"] = int((~np.isnan(kb)).sum())
        results[label] = {"system": s, "scopes": per_scope, "n_unknown_cells": len(unknown), "unknown_cells": unknown[:200]}
    # Paired differences per size: selected π₀(N) minus Base on the shared known cohort with shared resampled task indices.
    paired = {}
    base_of = {s.get("size"): s["label"] for s in systems if s.get("role") == "base"}
    for s in systems:
        if s.get("role") == "base" or not s.get("size") or s["size"] not in base_of:
            continue
        lab, base = s["label"], base_of[s["size"]]
        paired[s["size"]] = {}
        for sc, ids in scopes.items():
            A, kA = factor_arrays(cells_by[lab], ids)
            B, kB = factor_arrays(cells_by[base], ids)
            shared = kA & kB
            kbA = np.array([[cells_by[lab][(t, k)]["kernel_binary"] if cells_by[lab][(t, k)]["kernel_binary"] is not None else np.nan for k in range(G)] for t in ids])
            kbB = np.array([[cells_by[base][(t, k)]["kernel_binary"] if cells_by[base][(t, k)]["kernel_binary"] is not None else np.nan for k in range(G)] for t in ids])
            kshared = ~np.isnan(kbA) & ~np.isnan(kbB)
            def diff(ix):
                a, b = A[ix].reshape(-1, 3), B[ix].reshape(-1, 3)
                sh = shared[ix].reshape(-1)
                ma, mb = (a[sh].mean(axis=0), b[sh].mean(axis=0)) if sh.any() else (np.array([np.nan] * 3), np.array([np.nan] * 3))
                ks = kshared[ix].reshape(-1)
                d_kb = (kbA[ix].reshape(-1)[ks].mean() - kbB[ix].reshape(-1)[ks].mean()) if ks.any() else np.nan
                return d_kb, (scsc_of(*ma) - scsc_of(*mb)) if sh.any() else np.nan
            point = diff(np.arange(len(ids)))
            boots = np.array([diff(ix) for ix in idx[sc]])
            q = np.nanpercentile(boots, [2.5, 97.5], axis=0)
            paired[s["size"]][sc] = {"selected": lab, "base": base, "n_shared_known_cells": int(shared.sum()), "n_missing_pairs": int(len(ids) * G - shared.sum()),
                                     "kernel_binary_mean_pass_rate_diff": {"point": float(point[0]), "bootstrap95": [float(q[0, 0]), float(q[1, 0])]},
                                     "SCSC_diff": {"point": float(point[1]), "bootstrap95": [float(q[0, 1]), float(q[1, 1])]}, "p_val": "n/a (interval estimation only)"}
    out = {"written_utc": stamp(), "selection_sha256": sha(a.selection.read_bytes()), "verdict": sel["verdict"], "f_star": sel.get("f_star"), "n_test_tasks": len(test_ids),
           "scopes": {s: len(ids) for s, ids in scopes.items()}, "bootstrap": {"n_resamples": N_BOOT, "seed": SEED, "unit": "task (all 8 samples carried together)"},
           "aggregate_rule": "D-009: SCSC = (mean IC_tests · mean IC_proofs · mean fsc_compiled)^(1/3) on the common cohort of cells with all three factors known; fsc_compiled = FSC when IC_tests = 1 else 0 (D-003); bounds set unknown factors to 0 / 1",
           "systems": results, "paired_differences": paired, "p_val": "n/a"}
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for lab, r in results.items():
        p = r["scopes"]["all"]
        print(lab, {"known": p["n_known_cells"], "of": p["n_declared_cells"], "SCSC": round(p["point_common_cohort"]["SCSC"], 4) if p["point_common_cohort"]["SCSC"] is not None else None,
                    "boot": p["bootstrap95_task"]["SCSC"] if p["bootstrap95_task"] else None})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
