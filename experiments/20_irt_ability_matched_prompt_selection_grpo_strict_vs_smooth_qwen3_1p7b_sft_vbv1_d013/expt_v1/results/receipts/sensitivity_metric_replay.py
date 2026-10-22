#!/usr/bin/env python3
"""Read-only point-metric reconciliation for Experiment 20's E05 sensitivity G0."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


E20 = "20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--validator", type=Path, default=Path("/tmp/e20_verify_final_phase0.py"))
    ap.add_argument("--out", type=Path, default=Path("/tmp/e20_sensitivity_metric_verification.json"))
    args = ap.parse_args()
    repo, validator_path = args.repo.resolve(), args.validator.resolve()
    spec = importlib.util.spec_from_file_location("e20_final_validator", validator_path)
    validator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(validator)
    base = repo / "experiments" / E20 / "expt_v1/results/phase0b"
    scores_path = repo / "experiments" / E20 / "expt_v1/results/phase0_cells_e20.csv"
    paths = {
        "scores": scores_path,
        "primary_g0": base / "primary_g0.json",
        "primary_predictions": base / "primary_g0_predictions.csv",
        "with_e05_g0": base / "with_e05_g0.json",
        "with_e05_predictions": base / "with_e05_g0_predictions.csv",
        "validator": validator_path,
    }
    primary_g0 = json.loads(paths["primary_g0"].read_text())
    sensitivity_g0 = json.loads(paths["with_e05_g0"].read_text())
    primary_rows, sensitivity_rows = rows(paths["primary_predictions"]), rows(paths["with_e05_predictions"])
    audit = validator.Audit()
    labels, _ = validator.verify_strict_labels(audit, scores_path, sensitivity_rows)
    validator.verify_folds(audit, sensitivity_rows)
    audit.check("with_e05_g0_shape", (sensitivity_g0.get("tasks"), sensitivity_g0.get("groups")) == (539, 400),
                [sensitivity_g0.get("tasks"), sensitivity_g0.get("groups")], [539, 400])
    validator.verify_metrics(audit, sensitivity_g0, sensitivity_rows, labels)
    selected = validator.verify_g0_selection(audit, sensitivity_g0)
    primary_map = {r["task_id"]: (r["group_id"], r["fold"], r["observed_active"]) for r in primary_rows}
    sensitivity_map = {r["task_id"]: (r["group_id"], r["fold"], r["observed_active"]) for r in sensitivity_rows}
    audit.check("primary_sensitivity_task_order", [r["task_id"] for r in sensitivity_rows] == [r["task_id"] for r in primary_rows],
                len(sensitivity_rows), len(primary_rows))
    audit.check("primary_sensitivity_task_group_fold_label_identity", sensitivity_map == primary_map,
                {"sensitivity_unique": len(sensitivity_map), "primary_unique": len(primary_map),
                 "mismatches": sum(primary_map.get(t) != value for t, value in sensitivity_map.items())},
                {"sensitivity_unique": 539, "primary_unique": 539, "mismatches": 0})
    audit.check("primary_and_sensitivity_select_explanatory",
                primary_g0.get("selected_model") == sensitivity_g0.get("selected_model") == selected == "explanatory",
                [primary_g0.get("selected_model"), sensitivity_g0.get("selected_model"), selected],
                ["explanatory", "explanatory", "explanatory"])
    audit.check("primary_and_sensitivity_g0_pass",
                primary_g0.get("gate", {}).get("passed") is True and sensitivity_g0.get("gate", {}).get("passed") is True,
                [primary_g0.get("gate", {}).get("passed"), sensitivity_g0.get("gate", {}).get("passed")], [True, True])
    audit.check("sensitivity_selected_auc_expected", validator.close(sensitivity_g0["gate"]["auc"], 0.9331589654170299),
                sensitivity_g0["gate"]["auc"], 0.9331589654170299)
    audit.check("sensitivity_selected_log_loss_expected", validator.close(sensitivity_g0["gate"]["log_loss"], 0.311872477109588),
                sensitivity_g0["gate"]["log_loss"], 0.311872477109588)
    counts = Counter(row["result"] for row in audit.checks.values())
    failures = sorted(name for name, row in audit.checks.items() if row["result"] == "fail")
    receipt = {
        "status": "PASS" if not failures else "FAIL",
        "experiment": E20,
        "scope": "with-E05 G0 saved-prediction point metrics and primary identity; no fit or bootstrap replay",
        "read_only": True,
        "fits_gpu_or_model_calls": 0,
        "selected_model": selected,
        "tasks": len(sensitivity_rows),
        "groups": len({r["group_id"] for r in sensitivity_rows}),
        "active_tasks": int(sum(labels)),
        "check_counts": dict(counts),
        "failed_checks": failures,
        "checks": audit.checks,
        "actual_metrics": audit.metrics,
        "input_hashes": {name: {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size}
                         for name, path in paths.items()},
        "conditioning_limit": "Point metrics condition on completed saved held-out predictions; no model refit, bootstrap, or selection uncertainty is added.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "checks": dict(counts), "failures": failures,
                      "out": str(args.out), "bytes": args.out.stat().st_size}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
