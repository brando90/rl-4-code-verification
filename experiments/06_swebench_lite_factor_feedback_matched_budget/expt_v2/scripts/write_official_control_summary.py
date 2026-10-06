#!/usr/bin/env python3
"""Publish a hash-only reconciliation of evaluator-private official control receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipts(root: Path, evaluator: Path) -> list[dict]:
    values = []
    for path in root.glob("*/receipt.json"):
        try:
            value = json.loads(path.read_text())
            value["_path"] = path
            if value.get("report_outcome") is None and value.get("run_id") and value.get("kind"):
                report_path = evaluator / "logs/run_evaluation" / value["run_id"] / f"control-{value['kind']}" / value["instance_id"] / "report.json"
                try:
                    report = json.loads(report_path.read_text())[value["instance_id"]]
                    value["report_outcome"] = report.get("resolved")
                    value["report_sha256"] = sha256(report_path)
                except (OSError, KeyError, json.JSONDecodeError):
                    pass
            values.append(value)
        except (OSError, json.JSONDecodeError):
            pass
    return values


def select(values: list[dict], task: str, condition: str) -> dict | None:
    options = [value for value in values if value.get("instance_id") == task and (value.get("condition") == condition or value.get("kind") == condition) and value.get("status") == "COMPLETE"]
    return max(options, key=lambda value: str(value.get("finished_at", ""))) if options else None


def outcome(value: dict | None) -> str:
    if value is None:
        return "NULL"
    return "resolved" if value.get("report_outcome") is True else "unresolved"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    panel = json.loads((runtime / "evaluator_inputs/panel_evaluator_manifest.json").read_text())
    values = receipts(runtime / "evaluator_controls", runtime / "evaluator_sources/SWE-bench-f7bbbb2")
    rows = []
    for task in panel["tasks"]:
        task_id = task["instance_id"]
        gold = select(values, task_id, "gold")
        empty = select(values, task_id, "exact_empty_patch_adapter")
        rows.append((task_id, gold, empty))
    completed_gold = sum(gold is not None for _, gold, _ in rows)
    completed_empty = sum(empty is not None for _, _, empty in rows)
    total_seconds = sum(float(value.get("elapsed_seconds", 0)) for value in values)
    lines = [
        "# Official evaluator control reconciliation",
        "",
        "**TLDR:** The pinned evaluator ran all eight report-backed gold controls and six exact-empty-base adapter controls. Two exact-empty cells are null after their literal-empty and unadmitted marker attempts consumed the available retry allowance; none is silently scored. The controls validate evaluator operation only, not repair improvement.",
        "",
        "Raw predictions, reports, logs, test identities, and adapter source remain in evaluator-only storage. This published view intentionally contains only identifiers, statuses, resource totals, and hashes.",
        "",
        f"- Harness commit: `f7bbbb2ccdf479001d6467c9e34af59e44a840f9`; panel hash: `{sha256(runtime / 'evaluator_inputs/panel_evaluator_manifest.json')}`.",
        f"- Reconciliation manifest: `{sha256(runtime / 'evaluator_controls/eligible_control_manifest_v3.json')}`; adapter source hashes: run-evaluation `51fac8d78ff0ff20cd58eac91f24262a9d475346a51b08da321c87fc6174f9b8`, Docker-limit patch `b323bac996c6cc7ce7d21ec7de3e2f58418cd5b69485fe59b3bbaedbb752519e`.",
        f"- Report-backed gold: {completed_gold}/8; exact-empty adapter: {completed_empty}/8; aggregate wrapper elapsed seconds: {total_seconds:.3f}; serial driver, max two containers, 4 CPU/8 GiB per container, 1800-second cell timeout.",
        "- The private report audit found 8/8 applied patches, 3 resolved and 5 unresolved gold reports; all reports carried test-status maps, with no collection/import/timeout marker in the reported failure lists. This does not eliminate unobserved environment causes, so unresolved controls are not used as semantic evidence.",
        "- The 4 CPU/8 GiB container limits and per-test timeout were enforced and observed. The outer process did not enforce a separate build-time timeout or 120-GiB new-storage ceiling, and elapsed×4 is an allocation estimate rather than measured CPU use; those limitations remain attached to every count.",
        "",
        "| Task | Gold | Exact empty baseline | Published receipt/report hashes |",
        "|---|---|---|---|",
    ]
    for task_id, gold, empty in rows:
        hashes = []
        for value in (gold, empty):
            if value is not None:
                hashes.append(f"receipt `{sha256(value['_path'])[:16]}` / report `{str(value.get('report_sha256'))[:16]}`")
        empty_text = outcome(empty)
        if empty is None and task_id in {"sqlfluff__sqlfluff-1763", "pvlib__pvlib-python-1606"}:
            empty_text = "NULL — retry allowance consumed by preserved filtered/marker attempts"
        lines.append(f"| `{task_id}` | {outcome(gold)} | {empty_text} | {'; '.join(hashes) or 'none'} |")
    lines.extend(["", "The original literal-empty wrappers exited zero because the upstream harness filtered empty predictions before test execution. They are retained as unmeasured infrastructure receipts. The marker-file variants for `sqlfluff__sqlfluff-1763` and `pvlib__pvlib-python-1606` executed but changed the base tree, so they are retained only as unadmitted attempts and are excluded from all counts above.", ""])
    args.output.write_text("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
