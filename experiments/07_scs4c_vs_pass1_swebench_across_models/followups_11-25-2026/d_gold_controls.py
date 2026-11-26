"""Check D_gold execution receipts and phase-B control coverage without inventing missing task measurements."""

from __future__ import annotations

import json
import math


def same_behavior(left: dict, right: dict) -> bool | None:
    """Compare canonical JSON values or qualified exception types; execution failures stay unmeasured."""
    def signature(observation):
        if not isinstance(observation, dict):
            raise ValueError("observation must be an object")
        kind = observation.get("kind")
        if kind in ("timeout", "infrastructure_error"):
            return None
        if kind == "exception":
            name = observation.get("type")
            if not isinstance(name, str) or not name:
                raise ValueError("exception needs its qualified type")
            return kind, name
        if kind == "value" and "value" in observation:
            return kind, json.dumps(observation["value"], sort_keys=True, separators=(",", ":"), allow_nan=False)
        raise ValueError("unsupported observation; task adapter must explicitly serialize behavior")
    a, b = signature(left), signature(right)
    return None if a is None or b is None else a == b


def check_task(input_ids: list[str], runs: dict[str, dict[str, dict]]) -> dict:
    """Check controls before generation; score a candidate only with its complete frozen-input receipt."""
    if not input_ids or len(set(input_ids)) != len(input_ids):
        raise ValueError("nonempty unique frozen input IDs required")
    expected = set(input_ids)
    names = ("gold", "gold_repeat", "base") + (("candidate",) if "candidate" in runs else ())
    for name in names:
        if name not in runs or set(runs[name]) != expected:
            raise ValueError(f"{name} differs from the frozen input manifest")
    comparisons = {name: [same_behavior(runs["gold"][i], runs[name][i]) for i in input_ids]
                   for name in names if name != "gold"}
    unavailable = {name: sum(v is None for v in values) for name, values in comparisons.items()}
    if unavailable["gold_repeat"] or unavailable["base"]:
        return {"status": "unmeasured", "inputs": len(input_ids), "unmeasured_inputs": unavailable,
                "controls_pass": None, "d_gold": None}
    gold_rate = sum(comparisons["gold_repeat"]) / len(input_ids)
    base_disagreements = sum(not v for v in comparisons["base"])
    controls = gold_rate >= .99 and base_disagreements >= 1
    candidate = comparisons.get("candidate")
    candidate_measured = candidate is not None and not unavailable["candidate"]
    return {"status": "controls_passed" if controls else "control_failed", "inputs": len(input_ids),
            "gold_repeat_agreement": gold_rate, "base_disagreements": base_disagreements,
            "controls_pass": controls, "candidate_measured": candidate_measured,
            "d_gold": sum(candidate) / len(input_ids) if controls and candidate_measured else None}


def admission(declared_tasks: list[str], receipts: dict[str, dict]) -> dict:
    """Retain the full declared denominator and distinguish unknown controls from failed controls."""
    if not declared_tasks or len(set(declared_tasks)) != len(declared_tasks):
        raise ValueError("nonempty unique task manifest required")
    if not set(receipts).issubset(declared_tasks):
        raise ValueError("receipt outside declared task manifest")
    passed = sum(r.get("controls_pass") is True for r in receipts.values())
    failed = sum(r.get("controls_pass") is False for r in receipts.values())
    unknown = len(declared_tasks) - passed - failed
    required = math.ceil(.9 * len(declared_tasks))
    return {"declared": len(declared_tasks), "passed": passed, "failed": failed, "unmeasured": unknown,
            "required": required, "admitted": passed >= required,
            "coverage_bounds": [passed / len(declared_tasks), (passed + unknown) / len(declared_tasks)]}
