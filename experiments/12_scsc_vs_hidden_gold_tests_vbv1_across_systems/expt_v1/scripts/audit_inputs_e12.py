"""Audit phase A's frozen factor inputs and candidate hashes without executing hidden tests."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

from rl4cv.forecast import verify_forecast

LABELS = {
    "claude_code": "Claude Code (Opus 5, spec v2)",
    "codex": "Codex (GPT-5.6 Sol, spec v2)",
    "leanstral": "Leanstral (labs-leanstral-1-5-1, spec v2)",
    "baseline": "Single-call baseline (Opus 5, spec v2)",
}
FACTORS = ("IC_tests", "IC_proofs", "FSC")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(rows: list[dict], published: float) -> dict:
    """Keep missing factors missing and compare both aggregations on a common cohort."""
    measured = [r for r in rows if all(r.get(k) is not None for k in FACTORS)]
    means = {k: statistics.mean(r[k] for r in measured) for k in FACTORS} if measured else {}
    geometric = math.prod(means.values()) ** (1 / 3) if measured else None
    per_cell = statistics.mean(math.prod(r[k] for k in FACTORS) ** (1 / 3) for r in measured) if measured else None
    return {
        "n_declared": len(rows), "n_common_measured": len(measured),
        "n_missing_factors": len(rows) - len(measured), "factor_means_common_measured": means,
        "geometric_mean_of_factor_means_measured": geometric,
        "geometric_mean_of_factor_means_all896": geometric if len(measured) == len(rows) == 896 else None,
        "mean_per_cell_scsc_measured": per_cell, "published_scsc": published,
        "matches_published_three_decimals": geometric is not None and f"{geometric:.3f}" == f"{published:.3f}",
        "mean_per_cell_matches_published_three_decimals": per_cell is not None and f"{per_cell:.3f}" == f"{published:.3f}",
        "difference_geometric_minus_published": geometric - published if geometric is not None else None,
    }


def resolve_candidate(paths: list[Path], expected: str | None) -> dict:
    """Select only matching recorded bytes when a full or truncated hash is available."""
    existing = []
    for p in paths:
        if p.is_file():
            digest = sha(p)
            existing.append({"path": str(p), "sha256": digest, "bytes": p.stat().st_size})
    matching = [r for r in existing if not expected or r["sha256"].startswith(expected)]
    if matching:
        # Multiple copies of identical bytes are provenance aliases, not new cells.
        hashes = {r["sha256"] for r in matching}
        if len(hashes) != 1:
            return {"join_status": "ambiguous", "expected_sha256": expected, "copies": existing}
        return {"join_status": "bound" if expected else "located_without_recorded_hash",
                "expected_sha256": expected, **matching[0], "matching_copies": len(matching)}
    return {"join_status": "hash_mismatch" if existing else "file_missing",
            "expected_sha256": expected, "searched_paths": [str(p) for p in paths], "copies": existing}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vb103-root", type=Path, default=Path("/lfs/skampere1/0/brando9/veribench_vb103"))
    ap.add_argument("--vb102-root", type=Path, default=Path("/lfs/skampere1/0/brando9/vb100"))
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = ap.parse_args()
    phase = Path(__file__).resolve().parents[1]
    forecast = phase / "forecasts/e12_phase_a_forecast.json"
    if not verify_forecast(forecast):
        raise RuntimeError("Frozen forecast hash mismatch; refusing to read input results")
    sources = []

    def record(path):
        sources.append({"path": str(path), "sha256": sha(path)})
        return path

    e103 = next((args.vb103_root / "experiments").glob("103_single_call_baselines*"))
    e102 = next((args.vb103_root / "experiments").glob("102_rescore_vbv1*"))
    e102_private = next((args.vb102_root / "experiments").glob("102_rescore_vbv1*"))
    original = json.loads(record(e103 / "results/summary.json").read_text())
    rows103 = [r for r in original["rows"] if r["benchmark"] == "vbv1_896"]
    forecast_data = json.loads(forecast.read_text())
    models = forecast_data["primary_panel"]["veribench_103_vbv1_896"]
    assert len(rows103) == 7 * 896
    assert {r["model"] for r in rows103} == set(models)
    published = {}
    for line in record(e103 / "results.md").read_text().splitlines():
        if not line.startswith("|"):
            continue
        fields = [x.strip().replace("**", "").replace("`", "") for x in line.split("|")[1:-1]]
        if len(fields) == 7 and fields[0] in models and fields[0] not in published:
            published[fields[0]] = float(fields[4])
    assert set(published) == set(models)
    rows102 = list(csv.DictReader(record(e102 / "results/tables/validated_per_candidate.csv").open()))
    published102 = json.loads(record(e102 / "results/tables/VALIDATED_TABLES.json").read_text())["all896_fixed_validated"]["estimates"]
    source_path = record(args.vb102_root / "paper_support/iclr2027/results/01_arm_convergence/per_task_factors_rerun.csv")
    raw102 = {(r["system"], r["task_id"]): r for r in csv.DictReader(source_path.open())}
    items = {}
    for tier in ("tier1", "tier2"):
        inventory = json.loads(record(e102 / f"results/input_inventory_{tier}.json").read_text())
        assert sha(source_path) == inventory["source_sha256"]
        item_path = Path(inventory["items_file"])
        if not item_path.is_file():
            item_path = e102_private / f"private/{tier}_inputs/items.jsonl"
        assert sha(item_path) == inventory["items_sha256"]
        record(item_path)
        for line in item_path.read_text().splitlines():
            r = json.loads(line)
            assert (r["system"], r["task"]) not in items
            items[r["system"], r["task"]] = r
    units = {}
    for system in LABELS:
        f = record(args.vb102_root / f"experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/results/rerun_scored/{system}_units.json")
        units[system] = json.loads(f.read_text())

    cells, summaries = [], []
    for model in models:
        rr = [r for r in rows103 if r["model"] == model]
        assert len(rr) == len({r["task"] for r in rr}) == 896
        audit = aggregate(rr, published[model])
        summaries.append({"source_experiment": 103, "system": model, **audit})
        for r in rr:
            paths = [e103 / f"private/{job}/{model}/{r['task']}/verifier/solution.lean" for job in ("jobs", "jobs_recovery_1")]
            cells.append({"source_experiment": 103, "system": model, "task_id": r["task"],
                          "source_status": r["cell_status"], **{k: r.get(k) for k in FACTORS},
                          **resolve_candidate(paths, r.get("solution_sha256"))})
    for system, label in LABELS.items():
        rr = [r for r in rows102 if r["system"] == system]
        assert len(rr) == len({r["task_id"] for r in rr}) == 896
        converted = [{a: float(r[b]) if r[b] else None for a, b in zip(FACTORS, ("ic_ap", "ic_pp", "validated_tc"))} for r in rr]
        summaries.append({"source_experiment": 102, "system": system,
                          **aggregate(converted, published102[label]["scsc"]["estimate"])})
        for r, factors in zip(rr, converted):
            item = items.get((system, r["task_id"]))
            raw = raw102[label, r["task_id"]]
            raw_path = args.vb102_root / raw["artifact_path"].replace("experiments/71_vals_ai_eval_code", "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code") if raw["artifact_path"] else None
            paths = [Path(item["candidate_path"])] if item else ([raw_path] if raw_path else [])
            trial = paths[0].parent.parent.name if paths else None
            unit = units[system].get(trial, {})
            expected = item["cand_sha256"] if item else unit.get("sha")
            cells.append({"source_experiment": 102, "system": system, "task_id": r["task_id"],
                          "source_status": r["status"], "recorded_compiles": unit.get("compiles"),
                          **factors, **resolve_candidate(paths, expected)})
    assert len(cells) == 9856
    for summary in summaries:
        group = [r for r in cells if r["system"] == summary["system"]]
        summary["candidate_joins"] = {s: sum(r["join_status"] == s for r in group) for s in sorted({r["join_status"] for r in group})}
        summary["empty_candidate_files"] = sum(r.get("bytes") == 0 for r in group)
    missing = [{"system": r["system"], "task_id": r["task_id"]} for r in cells if r["join_status"] == "file_missing"]
    failures = [r["system"] for r in summaries if not r["matches_published_three_decimals"]]
    report = {
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "forecast_verified": True, "forecast_canonical_sha256": forecast.with_suffix(".sha256").read_text().split()[0],
        "audit_script_sha256": sha(Path(__file__)), "status": "BLOCKED" if failures else "PREFLIGHT_PARTIAL",
        "stop_rule": "PROTOCOL.md section 6: recomputed system SCSC must match the published value to 3 decimals",
        "aggregation_mismatch_systems": failures, "n_declared": len(cells),
        "file_missing_count": len(missing), "file_missing_fraction": len(missing) / len(cells),
        "file_missing_gate_passes": len(missing) / len(cells) <= 0.05,
        "systems": summaries, "sources": sources,
        "not_run": ["100-candidate compilation reproduction (short-circuited by aggregation stop)",
                    "gold extraction", "adapter controls", "protocol lock", "hidden evaluation", "P1/P2/P3/G-A analyses", "secondary panel evaluation"],
        "uncertainty": "Deterministic census of supplied factor records, not a statistical estimate; confidence intervals and p-values not applicable.",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "input_manifest.json").write_text(json.dumps({"status": report["status"], "scope": "primary factor and candidate joins; later preflight stages not run after mandatory aggregation stop", "n_declared": len(cells), "sources": sources, "systems": summaries, "file_missing": missing, "cells": cells}, indent=2) + "\n")
    (args.out / "aggregation_preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "n_declared", "aggregation_mismatch_systems", "file_missing_count", "file_missing_gate_passes")}))
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
