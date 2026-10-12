#!/usr/bin/env python3
"""Join frozen test factors, verify judge receipts, and export audit/repeat diagnostics without model calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1] / "results"
MEMBERS = ("H2_sol_high", "H2_opus55_max")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(rows, key):
    out = {}
    for row in rows:
        identity = key(row)
        if identity in out:
            raise ValueError(f"duplicate cell: {identity}")
        out[identity] = row
    return out


def factor_cell(kernel, judged):
    """Apply the frozen compile gate; proof failure never gates coverage a second time."""
    known = kernel is not None and kernel["known"] == "True"
    values = {k: float(kernel[k]) if known and kernel[k] not in ("", "None") else None
              for k in ("IC_tests", "IC_proofs", "kernel_binary")}
    raw = judged.get("FSC") if judged else None
    t = values["IC_tests"]
    fc = None if t is None else (0.0 if t == 0.0 else raw)
    values.update(FSC_judged=raw, fsc_compiled=fc)
    complete = all(values[k] is not None for k in ("IC_tests", "IC_proofs", "fsc_compiled"))
    values["factors_known"] = complete
    values["SCSC_per_cell_diagnostic"] = (
        (values["IC_tests"] * values["IC_proofs"] * fc) ** (1 / 3) if complete else None)
    return values


def check_ratings(rows, declared):
    ratings = unique(rows, lambda r: r["task_id"])
    if set(ratings) - set(declared):
        raise ValueError("extra rating outside frozen manifest")
    for task, row in ratings.items():
        meta = declared[task]
        for key in ("system", "task_id_vb", "sample_idx", "repeat"):
            if row[key] != meta[key]:
                raise ValueError(f"rating identity mismatch: {task} {key}")
        if row["status"] == "measured":
            if not row.get("transport_matches") or not row.get("prompt_hash_matches"):
                raise ValueError(f"unverified measured rating: {task}")
            if row["prompt_sha256_served"] != meta["prompt_sha256"]:
                raise ValueError(f"prompt digest mismatch: {task}")
            if not 0 <= row["score_raw"] <= 5 or not 1 <= row["requests_sent"] <= 2:
                raise ValueError(f"rating range/request bound: {task}")
    return ratings


def summarize(root):
    inputs = {}
    def read(name):
        p = root / name
        inputs[name] = digest(p)
        return json.loads(p.read_text())
    def csv_read(name):
        p = root / name
        inputs[name] = digest(p)
        with p.open(newline="") as f:
            return list(csv.DictReader(f))
    selection = read("selection.json")
    manifest = read("test_manifest.json")
    evaluation = read("test_eval.json")
    pack = read("judge/judge_pack_test.json")
    if manifest["selection_sha256"] != inputs["selection.json"] or evaluation["selection_sha256"] != inputs["selection.json"]:
        raise ValueError("selection digest mismatch")
    if pack["systems_manifest_sha256"] != inputs["test_manifest.json"]:
        raise ValueError("judge manifest binding mismatch")
    splits = csv_read("split/vbv1_split_manifest.csv")
    tasks = {r["task_id"]: r for r in splits if r["split"] == "test"}
    ids_path = root / "split/vbv1_test_task_ids.txt"
    inputs["split/vbv1_test_task_ids.txt"] = digest(ids_path)
    ids = ids_path.read_text().splitlines()
    if len(ids) != 222 or set(ids) != set(tasks):
        raise ValueError("test task identity mismatch")
    expected = {(t, k) for t in ids for k in range(8)}
    audit = set()
    families = sorted({r["family"] for r in tasks.values() if r["core"] == "1"})
    for family in families:
        pool = [(t, k) for t in ids if tasks[t]["family"] == family for k in range(8)]
        pool.sort(key=lambda x: hashlib.sha256(f"rl4cv-e08-audit-v1:{x[0]}|{x[1]}".encode()).hexdigest())
        audit.update(pool[:12])
    if len(audit) != 60 or len(families) != 5:
        raise ValueError("fixed audit identity mismatch")
    joined, systems = [], {}
    requests = []
    for system in manifest["systems"]:
        label = system["label"]
        kernel = unique(csv_read(f"ladder/{label}_test_cells.csv"), lambda r: (r["task_id"], int(r["sample_idx"])))
        if set(kernel) != expected:
            raise ValueError(f"kernel manifest mismatch: {label}")
        fsc = read(f"judge/fsc_{label}.json")
        declarations = unique([r for r in pack["cells"] if r["system"] == label], lambda r: r["task_id"])
        per_member, charges, variability = {}, 0.0, {}
        by_file = {}
        for cfg in MEMBERS:
            harvest = read(f"judge/harvests/cells_{label}__{cfg}.json")
            ratings = check_ratings(harvest["cells"], declarations)
            per_member[cfg] = ratings
            charges += harvest["charges_usd"]
            for row in ratings.values():
                key = (row["task_id_vb"], row["sample_idx"])
                if row["status"] == "measured":
                    by_file.setdefault(key, {}).setdefault(cfg, {})[row["repeat"]] = row["score_raw"]
                    requests.append(row["requests_sent"])
            stdevs = [statistics.stdev(list(v[cfg].values())) / 5 for v in by_file.values()
                      if set(v.get(cfg, {})) == {1, 2, 3}]
            variability[cfg] = {"n_files_with_three_ratings": len(stdevs),
                                "mean_within_file_sample_sd_normalized_0_1": statistics.mean(stdevs) if stdevs else None,
                                "max_within_file_sample_sd_normalized_0_1": max(stdevs) if stdevs else None}
        if not math.isclose(charges, fsc["charges_usd"], abs_tol=0.00011):
            raise ValueError(f"charge mismatch: {label}")
        declared_files = {(r["task_id_vb"], r["sample_idx"]) for r in declarations.values()}
        main = {k for k, r in kernel.items() if r["known"] == "True" and float(r["IC_tests"]) == 1}
        missing_files = sorted((main | audit) - declared_files)
        if declared_files - (main | audit):
            raise ValueError(f"unexpected judged file: {label}")
        rows = []
        for t, k in sorted(expected):
            key = (t, k)
            j = fsc["cells"].get(f"{t}#{k}")
            measured = by_file.get(key, {})
            complete = all(set(measured.get(cfg, {})) == {1, 2, 3} for cfg in MEMBERS)
            recomputed = statistics.mean(statistics.median(measured[cfg].values()) for cfg in MEMBERS) / 5 if complete else None
            if (j.get("FSC") if j else None) != recomputed:
                raise ValueError(f"FSC aggregation mismatch: {label} {t}#{k}")
            row = {"system": label, "task_id": t, "sample_idx": k,
                   "family": tasks[t]["family"], "core": int(tasks[t]["core"]),
                   "lean_sha256": kernel[key]["lean_sha256"],
                   **factor_cell(kernel[key], j), "is_fixed_audit": key in audit,
                   "judge_ratings_measured": sum(len(v) for v in measured.values())}
            rows.append(row)
        scopes = {}
        for scope in ("all", "core", "industryset"):
            sr = [r for r in rows if scope == "all" or r["core"] == (1 if scope == "core" else 0)]
            kr = [r for r in sr if r["factors_known"]]
            original = evaluation["systems"][label]["scopes"][scope]
            if len(kr) != original["n_known_cells"] or len(sr) != original["n_declared_cells"]:
                raise ValueError(f"aggregate denominator mismatch: {label} {scope}")
            if kr:
                means = {f: statistics.mean(r[f] for r in kr) for f in ("IC_tests", "IC_proofs", "fsc_compiled")}
                means["SCSC"] = math.prod(means.values()) ** (1 / 3)
                for f, v in means.items():
                    if not math.isclose(v, original["point_common_cohort"][f], rel_tol=1e-12, abs_tol=1e-14):
                        raise ValueError(f"aggregate mismatch: {label} {scope} {f}")
            scopes[scope] = {"n_known": len(kr), "n_declared": len(sr)}
        ar = [r for r in rows if r["is_fixed_audit"]]
        missing_ratings = [{"config": cfg, "task_id": t} for cfg in MEMBERS for t in declarations
                           if t not in per_member[cfg] or per_member[cfg][t]["status"] != "measured"]
        systems[label] = {"scopes": scopes, "n_declared_judge_files": len(declared_files),
                          "n_declared_ratings": len(declarations) * 2,
                          "n_measured_ratings": sum(r["judge_ratings_measured"] for r in rows),
                          "missing_ratings": missing_ratings, "missing_judge_files": missing_files,
                          "fixed_audit": {"n_declared": 60, "n_measured": sum(r["FSC_judged"] is not None for r in ar),
                                          "n_compile_gate_overlap": sum(r["IC_tests"] == 1 for r in ar),
                                          "diagnostic_mean_ungated_FSC": statistics.mean(r["FSC_judged"] for r in ar if r["FSC_judged"] is not None)},
                          "raw_repeat_variability": variability, "reported_judge_charge_usd": charges}
        joined.extend(rows)
    declared = sum(v["n_declared_ratings"] for v in systems.values())
    if len(joined) != manifest["n_declared_cells"] or declared != pack["n_declared_ratings"]:
        raise ValueError("full manifest count mismatch")
    summary = {"schema": 1, "verdict": selection["verdict"], "n_test_cells": len(joined),
               "n_known_factor_cells": sum(r["factors_known"] for r in joined),
               "n_declared_ratings": declared, "n_measured_ratings": len(requests),
               "reported_requests_sent": sum(requests), "rating_request_counts": {str(k): requests.count(k) for k in sorted(set(requests))},
               "systems": systems, "input_sha256": inputs,
               "audit_identity": [{"task_id": t, "sample_idx": k} for t, k in sorted(audit)],
               "aggregate_crosscheck": "All system/scope factor means and D-009 aggregates match published test_eval.json.",
               "notes": ["SCSC_per_cell_diagnostic is not the official geometric mean of factor means.",
                         "Audit ungated FSC is diagnostic and never bypasses the compile gate.",
                         "Repeat SD uses three raw ratings per file/member, normalized from 0-5 to 0-1, sample denominator 2.",
                         "Independent repeated six-rating ensemble aggregates and training-seed variation were not measured.",
                         "No new model calls; failed/missing source receipts remain unchanged."]}
    return joined, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    rows, summary = summarize(args.results)
    out = args.out_dir or args.results
    out.mkdir(parents=True, exist_ok=True)
    cells = out / "test_factor_cells.csv"
    with cells.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary["factor_cells_sha256"] = digest(cells)
    (out / "test_receipts_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: summary[k] for k in ("n_test_cells", "n_known_factor_cells", "n_declared_ratings", "n_measured_ratings")}))


if __name__ == "__main__":
    main()
