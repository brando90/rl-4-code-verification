#!/usr/bin/env python3
"""Audit existing private controls without treating infrastructure errors as issue outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

DOC = "https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v2/results/official_evaluator_controls.md"
HARNESS = "f7bbbb2ccdf479001d6467c9e34af59e44a840f9"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(report: dict | None, log: str) -> tuple[str, bool | None]:
    """Keep raw grader flags separate; these conservative labels are a post-hoc audit."""
    if not isinstance(report, dict) or type(report.get("resolved")) is not bool:
        return "missing_or_ambiguous_report", None
    if report.get("patch_successfully_applied") is not True:
        return "patch_application_unverified", None
    summary = bool(re.search(r"\b\d+ (?:passed|failed|errors?|skipped|xfailed|xpassed)\b", log))
    if re.search(r"ImportError|ModuleNotFoundError", log) and not summary:
        return "import_failure_before_test_completion", None
    if re.search(r"AttributeError:\s*['\"]Test[^'\"]*['\"] object has no attribute", log):
        return "fixture_failure_requires_environment_validation", None
    if not summary:
        return "test_completion_unverified", None
    return "test_execution_observed", report["resolved"]


def receipts(root: Path) -> list[dict]:
    values = []
    for path in sorted(root.glob("*/receipt.json")):
        value = json.loads(path.read_text())
        value["_path"] = path
        values.append(value)
    return values


def select(values: list[dict], task: str, condition: str) -> dict | None:
    options = [v for v in values if v.get("instance_id") == task
               and (v.get("condition") == condition or v.get("kind") == condition)
               and v.get("status") == "COMPLETE"]
    if len(options) > 1:
        raise ValueError(f"multiple completed receipts require explicit reconciliation: {task}/{condition}")
    return options[0] if options else None


def audit_cell(runtime: Path, task: str, condition: str, value: dict | None,
               retry_exhausted: bool = False) -> dict:
    result = {"condition": condition, "report_present": False, "raw_resolved": None,
              "endpoint_value": None, "matches_expected": None,
              "status": "retry_exhausted" if retry_exhausted else "unmeasured"}
    if value is None:
        return result
    if condition == "exact_empty_patch_adapter" and value.get("patch_sha256") != EMPTY_SHA256:
        raise ValueError("nonempty patch cannot be selected as the unchanged baseline")
    folder = "SWE-bench-f7bbbb2" if condition == "gold" else "SWE-bench-f7bbbb2-empty-baseline-adapter"
    model = "control-gold" if condition == "gold" else "control-empty-adapter"
    report_path = runtime / "evaluator_sources" / folder / "logs/run_evaluation" / value["run_id"] / model / task / "report.json"
    result["receipt_sha256"] = sha256(value["_path"])
    result["patch_sha256"] = value.get("patch_sha256")
    try:
        report = json.loads(report_path.read_text())[task]
    except (OSError, KeyError, json.JSONDecodeError):
        result["status"] = "missing_or_ambiguous_report"
        return result
    report_hash = sha256(report_path)
    if value.get("report_sha256") not in (None, report_hash):
        raise ValueError(f"report hash mismatch: {task}/{condition}")
    log_paths = sorted(report_path.parent.glob("*.txt"))
    status, endpoint = classify(report, "\n".join(p.read_text(errors="replace") for p in log_paths))
    result.update(report_present=True, report_sha256=report_hash,
                  log_sha256=[sha256(p) for p in log_paths],
                  raw_resolved=report.get("resolved"), status=status, endpoint_value=endpoint,
                  matches_expected=None if endpoint is None else endpoint == (condition == "gold"))
    result["test_group_counts"] = {
        group: {key: len(items) for key, items in counts.items() if isinstance(items, list)}
        for group, counts in report.get("tests_status", {}).items() if isinstance(counts, dict)
    }
    return result


def label(cell: dict) -> str:
    if cell["endpoint_value"] is None:
        raw = cell["raw_resolved"]
        return f"NULL — {cell['status']}" + (f" (raw resolved={str(raw).lower()})" if raw is not None else "")
    return "resolved" if cell["endpoint_value"] else "unresolved"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    panel_path = runtime / "evaluator_inputs/panel_evaluator_manifest.json"
    manifest_path = runtime / "evaluator_controls/eligible_control_manifest_v3.json"
    panel = json.loads(panel_path.read_text())
    blocked = set(json.loads(manifest_path.read_text())["null_cells"])
    values = receipts(runtime / "evaluator_controls")
    rows = []
    for task in panel["tasks"]:
        task_id = task["instance_id"]
        gold = audit_cell(runtime, task_id, "gold", select(values, task_id, "gold"))
        empty = audit_cell(runtime, task_id, "exact_empty_patch_adapter",
                           select(values, task_id, "exact_empty_patch_adapter"), task_id in blocked)
        rows.append({"instance_id": task_id, "gold": gold, "empty": empty,
                     "valid_control_pair": gold["matches_expected"] is True and empty["matches_expected"] is True})
    if len(rows) != 8 or len({r["instance_id"] for r in rows}) != 8:
        raise ValueError("expected the complete eight-task panel")
    cells = [r[k] for r in rows for k in ("gold", "empty")]
    counts = {"declared_cells": 16, "report_backed_cells": sum(c["report_present"] for c in cells),
              "endpoint_values_measured": sum(c["endpoint_value"] is not None for c in cells),
              "endpoint_values_null": sum(c["endpoint_value"] is None for c in cells),
              "valid_control_pairs": sum(r["valid_control_pair"] for r in rows),
              "declared_tasks": 8, "required_control_pairs": 6}
    elapsed = sum(float(v.get("elapsed_seconds") or 0) for v in values)
    audit = {"schema": "e06_parent_control_audit_v1", "harness_commit": HARNESS,
             "panel_sha256": sha256(panel_path), "reconciliation_manifest_sha256": sha256(manifest_path),
             "audit_script_sha256": sha256(Path(__file__)),
             "chronology": "Post-hoc interpretation of existing receipts and logs; no new evaluation or model call.",
             "counts": counts, "recorded_wrapper_elapsed_seconds": round(elapsed, 3),
             "resource_limitations": ["outer build timeout was not enforced", "120-GiB new-storage ceiling was not enforced",
                                      "wrapper elapsed time is not measured processor use", "pre-receipt failures have incomplete duration accounting"],
             "rows": rows}
    json_path = args.output.with_suffix(".json")
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    lines = ["# Official evaluator control reconciliation", "", f"**Doc link:** <{DOC}>", "",
             f"**TLDR:** There are {counts['report_backed_cells']}/16 official reports, but only {counts['endpoint_values_measured']}/16 controls have interpretable endpoint values after checking execution logs. The other {counts['endpoint_values_null']}/16 remain null. Only {counts['valid_control_pairs']}/8 tasks have the required resolved gold and unresolved unchanged-base controls, below the frozen 6/8 engineering gate. No repair comparison ran.", "",
             "This corrects the earlier report-only summary: import and test-fixture errors appear in execution logs even when the grader emits `resolved=false` and test-status maps. Raw grader flags are retained separately from endpoint values. Fixture failures remain conservatively null pending environment validation. This audit is post hoc; it is not a new prospective experiment or a change to grading, reference patches, tests, or task selection.", "",
             f"The [machine-readable audit]({json_path.name}) contains all 16 cells, evidence hashes and safe test-group counts. Raw patches, tests, test identifiers and logs remain in private evaluator storage. Harness: `{HARNESS}`; panel: `{audit['panel_sha256']}`; audit script: `{audit['audit_script_sha256']}`.", "",
             "The empty adapter leaves the base tree unchanged and alters only empty-patch selection and absent patch application in a separately hashed harness copy. Official test/grading bytes remain unchanged. Two marker-file variants are excluded and consume their existing retry allowances; original filtered empty wrappers remain unmeasured. Earlier wrapper invocations that failed before creating receipts also count against retries; attempt labels alone do not establish remaining allowance.", "",
             f"Recorded wrapper duration across retained receipts is {elapsed:.3f} seconds, including excluded attempts. Four processors/eight gibibytes per evaluation container and the 1,800-second test-execution timeout were observed. There was no enforced outer build timeout or 120-gibibyte new-storage ceiling. Elapsed time multiplied by four is an allocation estimate, not measured processor use; setup/build and pre-receipt failure accounting is incomplete. No claim of complete resource-gate enforcement is made.", "",
             "These are fixed engineering controls, not sampled model-performance estimates; confidence intervals and hypothesis tests are not applicable. Missing and infrastructure-invalid cells stay in the declared denominators.", "",
             "| Task | Gold endpoint | Exact empty endpoint | Valid control pair |", "|---|---|---|---|"]
    for row in rows:
        lines.append(f"| `{row['instance_id']}` | {label(row['gold'])} | {label(row['empty'])} | {'yes' if row['valid_control_pair'] else 'no'} |")
    lines += ["", "**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] The evaluator-control gate fails; raw unresolved flags caused by infrastructure are not evidence of model failure. A separately frozen environment/check protocol and new explicit call budget are required for continuation.", ""]
    args.output.write_text("\n".join(lines))
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
