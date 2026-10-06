"""Analyze fixed-panel paired final outcomes with task bootstrap intervals and explicit missing-cell bounds."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random

from prepare_panel import CONDITIONS, PANEL_SIZE, PREFIX, canonical, declared_cells, digest, strict_json

STATUSES = ("completed", "task_failure", "infrastructure_failure", "missing")
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 0


def validate_manifest(manifest):
    """Require an intact declared design, never derive a denominator from outcomes."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    body = {key: value for key, value in manifest.items() if key != "design_sha256"}
    if manifest.get("design_sha256") != digest(body):
        raise ValueError("manifest checksum mismatch")
    if manifest.get("schema_version") != 1 or manifest.get("experiment") != "06_swebench_lite_factor_feedback_matched_budget":
        raise ValueError("wrong manifest schema or experiment")
    task_ids, models = manifest.get("task_ids"), manifest.get("models")
    if not isinstance(task_ids, list) or len(task_ids) != PANEL_SIZE or any(not isinstance(t, str) or not t for t in task_ids) or len(set(task_ids)) != PANEL_SIZE:
        raise ValueError("manifest must declare exactly eight distinct tasks")
    if not isinstance(models, list) or not models or any(not isinstance(m, str) or not m.strip() for m in models) or len(set(models)) != len(models):
        raise ValueError("manifest must declare distinct exact models")
    if manifest.get("conditions") != list(CONDITIONS):
        raise ValueError("manifest conditions differ from the frozen design")
    if manifest.get("selection") != {"method": "ascending_sha256_of_prefix_plus_instance_id", "prefix": PREFIX, "panel_size": PANEL_SIZE}:
        raise ValueError("manifest selection differs from the frozen design")
    if manifest.get("cells") != declared_cells(task_ids, models):
        raise ValueError("manifest does not declare every design cell exactly once")
    return manifest


def read_receipts(path, manifest_sha256):
    raw = Path(path).read_bytes()
    if Path(path).suffix.lower() == ".jsonl":
        rows = [strict_json(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        if not rows:
            raise ValueError("empty JSON Lines has no manifest binding; use a bound JSON envelope with empty receipts")
    else:
        value = strict_json(raw)
        if not isinstance(value, dict):
            raise ValueError("JSON receipts require an envelope with manifest_sha256 and receipts")
        if value.get("manifest_sha256") != manifest_sha256:
            raise ValueError("receipt bundle is missing its byte hash or belongs to a different manifest")
        rows = value.get("receipts")
        if isinstance(rows, list):
            rows = [{"manifest_sha256": manifest_sha256, **row} if isinstance(row, dict) else row for row in rows]
    if not isinstance(rows, list):
        raise ValueError("receipts must be a bound envelope or bound JSON Lines")
    return rows, hashlib.sha256(raw).hexdigest()


def normalize_receipts(manifest, receipts, manifest_sha256):
    allowed = {(cell["model"], cell["instance_id"], cell["condition"], cell["step"]): cell for cell in manifest["cells"]}
    observed = {}
    for row in receipts:
        if not isinstance(row, dict):
            raise ValueError("every receipt must be an object")
        if type(row.get("step")) is not int:
            raise ValueError("receipt step must be an integer")
        fields = (row.get("model"), row.get("instance_id"), row.get("condition"), row["step"])
        if any(not isinstance(value, str) for value in fields[:3]) or fields not in allowed:
            raise ValueError("receipt refers to an undeclared cell")
        if fields in observed:
            raise ValueError("duplicate receipt for a declared cell; consolidate infrastructure retries first")
        if row.get("manifest_sha256") != manifest_sha256:
            raise ValueError("receipt missing exact manifest byte hash or belongs to a different manifest")
        if "cell_id" in row and row["cell_id"] != allowed[fields]["cell_id"]:
            raise ValueError("receipt cell ID mismatch")
        status, resolved = row.get("status"), row.get("resolved")
        if status not in STATUSES:
            raise ValueError("receipt status must distinguish task and infrastructure failures")
        if "resolved" not in row or (resolved is not None and type(resolved) is not bool):
            raise ValueError("resolved must be a boolean or explicit null")
        if status == "completed" and resolved is None:
            raise ValueError("completed receipt requires a measured outcome")
        if status in ("infrastructure_failure", "missing") and resolved is not None:
            raise ValueError("missing/infrastructure outcomes must be null")
        if status == "task_failure" and resolved is True:
            raise ValueError("task failure cannot claim a resolved task")
        observed[fields] = {**allowed[fields], "status": status, "resolved": resolved}
    normalized = []
    for cell in manifest["cells"]:
        key = (cell["model"], cell["instance_id"], cell["condition"], cell["step"])
        normalized.append(observed.get(key, {**cell, "status": "missing", "resolved": None}))
    return normalized


def percentile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def bootstrap_interval(values):
    if not values:
        return None
    rng = random.Random(BOOTSTRAP_SEED)
    draws = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(BOOTSTRAP_DRAWS))
    return [percentile(draws, 0.025), percentile(draws, 0.975)]


def exact_paired_swap_test(differences):
    """Compute the two-sided exact paired label-swap null, omitting inert ties."""
    discordant = [d for d in differences if d]
    if not differences:
        return None
    n = len(discordant)
    observed = abs(sum(discordant))
    extreme = sum(math.comb(n, positives) for positives in range(n + 1) if abs(2 * positives - n) >= observed)
    return extreme / (2 ** n)


def paired_comparison(task_ids, by_task, comparator):
    complete = []
    pair_rows = []
    lower_sum = upper_sum = 0
    for task_id in task_ids:
        vector = by_task[(task_id, "vector")]["resolved"]
        other = by_task[(task_id, comparator)]["resolved"]
        difference = None if vector is None or other is None else int(vector) - int(other)
        if difference is not None:
            complete.append(difference)
        lower = (0 if vector is None else int(vector)) - (1 if other is None else int(other))
        upper = (1 if vector is None else int(vector)) - (0 if other is None else int(other))
        lower_sum += lower
        upper_sum += upper
        pair_rows.append({"instance_id": task_id, "vector_resolved": vector, f"{comparator}_resolved": other, "difference": difference, "bounds": [lower, upper]})
    return {"comparison": f"vector_minus_{comparator}", "declared_tasks": len(task_ids), "complete_pairs": len(complete), "missing_pairs": len(task_ids) - len(complete), "complete_pair_mean_difference": sum(complete) / len(complete) if complete else None, "bootstrap_95_interval": bootstrap_interval(complete), "exact_paired_swap_p_value": exact_paired_swap_test(complete), "null": "zero paired difference; exchange vector and comparator labels independently within each measured task", "full_denominator_bounds": [lower_sum / len(task_ids), upper_sum / len(task_ids)], "pairs": pair_rows}


def analyze(manifest, receipts, manifest_sha256=None):
    validate_manifest(manifest)
    if manifest_sha256 is None:
        manifest_sha256 = hashlib.sha256(canonical(manifest) + b"\n").hexdigest()
    normalized = normalize_receipts(manifest, receipts, manifest_sha256)
    final = [cell for cell in normalized if cell["step"] == 2]
    per_model = {}
    for model in manifest["models"]:
        model_rows = [row for row in final if row["model"] == model]
        by_task = {(row["instance_id"], row["condition"]): row for row in model_rows}
        counts = {}
        for condition in CONDITIONS:
            rows = [row for row in model_rows if row["condition"] == condition]
            outcomes = [row["resolved"] for row in rows if row["resolved"] is not None]
            successes = sum(outcomes)
            counts[condition] = {"declared_tasks": len(rows), "measured_tasks": len(outcomes), "resolved_tasks": successes, "unresolved_measured_tasks": len(outcomes) - successes, "unmeasured_tasks": len(rows) - len(outcomes), "measured_resolved_rate": successes / len(outcomes) if outcomes else None, "full_denominator_rate_bounds": [successes / len(rows), (successes + len(rows) - len(outcomes)) / len(rows)], "status_counts": {status: sum(row["status"] == status for row in rows) for status in STATUSES}}
        per_model[model] = {"conditions": counts, "primary": paired_comparison(manifest["task_ids"], by_task, "scalar"), "secondary": paired_comparison(manifest["task_ids"], by_task, "ordinary")}
    coverage = {"declared_cells": len(normalized), "received_cells": len(receipts), "status_counts": {status: sum(cell["status"] == status for cell in normalized) for status in STATUSES}}
    return {"schema_version": 1, "manifest_sha256": manifest_sha256, "source": manifest["source"], "statistics": {"resampling_unit": "task", "bootstrap_draws": BOOTSTRAP_DRAWS, "bootstrap_seed": BOOTSTRAP_SEED, "interval_method": "percentile 95%", "test": "two-sided exact paired label swap", "limitations": "Intervals use complete measured task pairs from this one fixed run; they do not cover missing outcomes, task-selection uncertainty, model-generation variability, or generalization beyond this panel. Full-denominator bounds include every missing outcome."}, "cell_coverage": coverage, "per_model": per_model, "non_final_cells": [cell for cell in normalized if cell["step"] != 2], "final_cells": final}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--outcomes", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.output.resolve() in (args.manifest.resolve(), args.outcomes.resolve()):
            raise ValueError("analysis output must be distinct from both inputs")
        manifest_bytes = args.manifest.read_bytes()
        manifest = validate_manifest(strict_json(manifest_bytes))
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        receipts, source_hash = read_receipts(args.outcomes, manifest_sha256)
        result = analyze(manifest, receipts, manifest_sha256)
        result["outcomes_sha256"] = source_hash
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(result) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.exit(2, f"analysis failed: {exc}\n")
    print(json.dumps({"manifest_sha256": result["manifest_sha256"], "final_cells": len(result["final_cells"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
