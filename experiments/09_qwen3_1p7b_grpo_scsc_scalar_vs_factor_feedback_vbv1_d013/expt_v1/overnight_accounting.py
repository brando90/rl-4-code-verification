"""Join published validation factors and every missing cell for the parent overnight report, without model calls or selection."""

import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parents[1]
SOURCE = EXPERIMENTS / "08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test" / "expt_v1"
OUT = HERE / "results" / "overnight_10-09-2026"


def main():
    provenance = {}

    def read(path):
        data = path.read_bytes()
        provenance[str(path.relative_to(EXPERIMENTS))] = hashlib.sha256(data).hexdigest()
        return data.decode()

    manifest = json.loads(read(SOURCE / "results/ladder_manifest.json"))
    summary = json.loads(read(SOURCE / "results/validation_ladder.json"))
    manifest_digest = provenance[str((SOURCE / "results/ladder_manifest.json").relative_to(EXPERIMENTS))]
    assert summary["manifest_sha256"] == manifest_digest
    assert len({s["label"] for s in manifest["systems"]}) == manifest["n_systems"] == 24
    ids = read(SOURCE / "results/split/vbv1_validation_task_ids.txt").splitlines()
    assert provenance[str((SOURCE / "results/split/vbv1_validation_task_ids.txt").relative_to(EXPERIMENTS))] == manifest["task_ids_sha256"]
    assert len(ids) == len(set(ids)) == manifest["n_tasks"] == 135
    expected = {(task, str(sample)) for task in ids for sample in range(manifest["samples_per_task"])}
    assert len(expected) == 1080
    rows, systems = [], []
    for system in manifest["systems"]:
        label = system["label"]
        result = summary["systems"][label]
        source_path = SOURCE / result["cells_csv"]
        source_rows = list(csv.DictReader(read(source_path).splitlines()))
        keyed = {(row["task_id"], row["sample_idx"]): row for row in source_rows}
        assert len(keyed) == len(source_rows), label
        assert set(keyed) <= expected, label
        known = {key for key, row in keyed.items() if row["known"] == "True"}
        assert len(known) == result["gates"]["n_known"], label
        assert result["gates"]["n_declared"] == len(expected), label
        # This dated snapshot admits only the already verified complete systems
        # or the five entirely ungenerated 14B trained checkpoints.
        assert len(known) in (0, 1080), label
        if not known:
            assert system["role"] == "trained" and system["size"] == "14B", label
        for key in sorted(expected):
            item = keyed.get(key, {})
            measured = key in known
            rows.append({
                "system": label, "role": system["role"], "source": system["source"],
                "size": system["size"], "fraction": system.get("fraction", ""),
                "split": "validation", "task_id": key[0], "sample_idx": key[1],
                "status": "kernel_factors_measured" if measured else "not_generated",
                "reason": "" if measured else "14B_training_waiting_for_eight_devices",
                "IC_tests": item["IC_tests"] if measured else "",
                "IC_proofs": item["IC_proofs"] if measured else "",
                "FSC": "", "SCSC": "", "strict_full_score": "",
                "kernel_binary": item["kernel_binary"] if measured else "",
                "n_vacuous": item["n_vacuous"] if measured else "",
                "coverage_status": "unmeasured", "lean_sha256": item.get("lean_sha256", "") if measured else "",
            })
        systems.append({"system": label, "role": system["role"], "source": system["source"],
                        "declared": len(expected), "known": len(known), "missing": len(expected) - len(known)})
    assert len(rows) == manifest["n_declared_cells"] == 25920
    assert len({(r["system"], r["task_id"], r["sample_idx"]) for r in rows}) == len(rows)
    missing = [r for r in rows if r["status"] == "not_generated"]
    assert len(missing) == 5400
    assert all(r[k] == "" for r in missing for k in ("IC_tests", "IC_proofs", "kernel_binary"))
    assert all(r[k] == "" for r in rows for k in ("FSC", "SCSC", "strict_full_score"))
    trained = [s for s in systems if s["role"] == "trained"]
    assert len(trained) == 20
    assert sum(s["known"] for s in trained) == 16200
    OUT.mkdir(exist_ok=True)
    matrix = OUT / "warm_start_validation_item_factors.csv"
    with matrix.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    accounting = {
        "kind": "parent_observation_of_published_artifacts_not_owner_finalization",
        "source_analysis_written_utc": summary["written_utc"],
        "source_manifest_sha256": provenance[str((SOURCE / "results/ladder_manifest.json").relative_to(EXPERIMENTS))],
        "declared": len(rows), "kernel_factors_known": len(rows) - len(missing), "missing": len(missing),
        "trained_declared": 21600, "trained_known": 16200,
        "new_validation_declared": 22680, "new_validation_known": 17280,
        "reused_validation_known": 3240, "coverage_ratings_measured_here": 0,
        "test": {"admitted": False, "selection_manifest_exists": False,
                 "planned_maximum_full_eight_system_cells": 14208,
                 "planned_new_cells": 8880, "planned_reused_cells": 5328,
                 "note": "Conditional protocol plan, not a frozen selected test denominator or completed evaluation."},
        "systems": systems, "input_sha256": provenance,
        "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
        "semantics": "FSC, full SCSC and strict full-score target are unmeasured. Kernel binary is a separate diagnostic, not full SCSC. Blank is unknown, never zero. No test content, selection or model calls.",
    }
    (OUT / "warm_start_accounting.json").write_text(json.dumps(accounting, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: accounting[k] for k in ("declared", "kernel_factors_known", "missing", "matrix_sha256")}))


if __name__ == "__main__":
    main()
