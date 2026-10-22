"""Summarize E20 Phase 0 cells without recoding missing smooth rewards as zero.

Strict metrics require the full declared 539 x 8 cohort.  Smooth-reward metrics are
reported on their finite observed cohort, with explicit denominator, missingness and
[0,1] full-manifest mean bounds.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import Counter
from pathlib import Path
import numpy as np

DECLARED_CELLS, SAMPLES, TASKS, GROUPS = 4312, 8, 539, 400


def finite01(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and 0 <= x <= 1 else None


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, (np.bool_, bool)): return bool(x)
    if isinstance(x, (np.integer, int)): return int(x)
    if isinstance(x, (np.floating, float)): return float(x) if math.isfinite(float(x)) else None
    return x


def smooth_reason(row):
    """Preserve the exact available adapter status/note; never infer an outcome."""
    status, note = row.get("partial_status", "missing") or "missing", row.get("partial_note", "") or ""
    return f"{status}: {note}" if note else status


def metric_summary(name, rows, vals, group_of, group_index, weights, declared_n, bounded=False):
    observed = [(r, v) for r, v in zip(rows, vals) if v is not None]
    n = len(observed)
    if not n:
        return dict(mean=None, lo=None, hi=None, p_value=None, declared_n=declared_n,
                    measured_n=0, missing_n=declared_n, valid_bootstrap_draws=0,
                    sample_index_means=[None] * SAMPLES,
                    sample_index_n=[0] * SAMPLES, sd_across_eight_sample_index_means=None,
                    full_manifest_mean_lower=0.0 if bounded else None,
                    full_manifest_mean_upper=1.0 if bounded else None)
    sums = np.zeros(len(group_index)); counts = np.zeros(len(group_index))
    by_sample = [[] for _ in range(SAMPLES)]
    for r, value in observed:
        i = group_index[group_of[r["task_id"]]]
        sums[i] += value; counts[i] += 1
        by_sample[int(r["sample_idx"])].append(value)
    den = weights @ counts
    valid = den > 0
    draws = (weights[valid] @ sums) / den[valid]
    lo, hi = (np.percentile(draws, [2.5, 97.5]).tolist() if len(draws) else (None, None))
    means = [float(np.mean(x)) if x else None for x in by_sample]
    present = [x for x in means if x is not None]
    out = dict(mean=float(sum(v for _, v in observed) / n), lo=lo, hi=hi, p_value=None,
               declared_n=declared_n, measured_n=n, missing_n=declared_n - n,
               valid_bootstrap_draws=int(valid.sum()), requested_bootstrap_draws=int(len(weights)),
               sample_index_means=means, sample_index_n=[len(x) for x in by_sample],
               sd_across_eight_sample_index_means=float(np.std(present, ddof=1)) if len(present) >= 2 else None)
    if bounded:
        total = sum(v for _, v in observed)
        out.update(full_manifest_mean_lower=float(total / declared_n),
                   full_manifest_mean_upper=float((total + (declared_n - n)) / declared_n))
    return out


def summarize(scores: Path, tasks: Path) -> dict:
    rows = list(csv.DictReader(scores.open(newline="")))
    task_rows = list(csv.DictReader(tasks.open(newline="")))
    group_of = {r["task_id"]: r["group_id"] for r in task_rows}
    expected = {(t, k) for t in group_of for k in range(SAMPLES)}
    keys = [(r.get("task_id"), int(r["sample_idx"])) for r in rows]
    if len(rows) != DECLARED_CELLS or len(group_of) != TASKS or len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError("Expected exactly the 539 train tasks and eight saved generations per task")
    groups = sorted(set(group_of.values()))
    if len(groups) != GROUPS: raise ValueError("Expected the 400 frozen D-013 train groups")
    if any(r.get("FSC") not in ("", "unmeasured") for r in rows):
        raise ValueError("No formal-specification-coverage judge calls were authorized")
    strict = [finite01(r.get("strict")) if r.get("status") == "measured" else None for r in rows]
    if any(v not in (0.0, 1.0) for v in strict):
        raise ValueError("Missing or nonbinary strict evidence: strict G0 requires all 4,312 declared cells")
    smooth, registered_zero = [], Counter()
    for r in rows:
        p, v = r.get("partial_status"), finite01(r.get("factored_reward"))
        if p == "parse_failure_zero_credit":
            if v != 0.0: raise ValueError("Malformed-source registered zero must have factored_reward=0")
            registered_zero["malformed_source_registered_zero"] += 1
            smooth.append(v)
        elif p == "measured":
            if v is None: raise ValueError("Measured smooth reward must be finite in [0,1]")
            smooth.append(v)
        else:
            smooth.append(None)
    # Strict-related fields are measured on every declared strict cell.  Smooth is metric-specific.
    native = {
        "strict": strict,
        "IC_tests": [finite01(r.get("IC_tests")) for r in rows],
        "IC_proofs": [finite01(r.get("IC_proofs")) for r in rows],
        "compiles": [finite01(r.get("compiles")) for r in rows],
        "capped": [1.0 if r.get("capped") == "True" else 0.0 if r.get("capped") == "False" else None for r in rows],
        "factored_reward": smooth,
    }
    if any(v is None for k, xs in native.items() if k != "factored_reward" for v in xs):
        raise ValueError("Missing strict-associated measured field; do not publish a partial strict summary")
    group_index = {g: i for i, g in enumerate(groups)}
    rng = np.random.default_rng(20261021)
    weights = rng.multinomial(GROUPS, np.full(GROUPS, 1 / GROUPS), size=10000)
    metrics = {name: metric_summary(name, rows, vals, group_of, group_index, weights, DECLARED_CELLS,
                                    bounded=(name == "factored_reward")) for name, vals in native.items()}
    task_strict = Counter()
    for r, v in zip(rows, strict): task_strict[r["task_id"]] += int(v)
    both = [r for r in rows if r.get("adapter_strict", "") != ""]
    confusion = Counter(f"scorer_{r['strict']}_adapter_{r['adapter_strict']}" for r in both)
    missing_rows = [dict(task_id=r["task_id"], sample_idx=int(r["sample_idx"]), strict_status=r.get("status"),
                         partial_status=r.get("partial_status"), status=r.get("partial_status"),
                         note=r.get("partial_note", ""), reason=smooth_reason(r))
                    for r, v in zip(rows, smooth) if v is None]
    return clean(dict(
        declared_cells=DECLARED_CELLS, received_rows=len(rows), train_tasks=TASKS, train_groups=GROUPS,
        strict_declared_cells=DECLARED_CELLS, strict_measured_cells=DECLARED_CELLS, strict_missing_cells=0,
        smooth_declared_cells=DECLARED_CELLS, smooth_measured_cells=sum(v is not None for v in smooth),
        smooth_missing_cells=sum(v is None for v in smooth),
        measured_joint_cells=sum(v is not None for v in smooth),
        measured_strict_and_reward=sum(v is not None for v in smooth), # legacy alias, never a complete-cohort claim
        successes=int(sum(strict)), active_tasks=sum(0 < k < SAMPLES for k in task_strict.values()),
        fully_solved_tasks=sum(k == SAMPLES for k in task_strict.values()),
        strict_success_count_histogram=dict(sorted(Counter(task_strict.values()).items())),
        status_counts=dict(Counter(r.get("status") for r in rows)),
        score_statuses=dict(Counter(f"{r.get('status')}/{r.get('partial_status')}" for r in rows)),
        strict_status_counts=dict(Counter(r.get("status") for r in rows)),
        partial_status_counts=dict(Counter(r.get("partial_status") for r in rows)),
        smooth_status_counts=dict(Counter(r.get("partial_status") for r in rows)),
        smooth_missing_status_counts=dict(Counter(r.get("partial_status") for r, v in zip(rows, smooth) if v is None)),
        smooth_missing_reason_counts=dict(Counter(x["reason"] for x in missing_rows)),
        smooth_missingness_likelihood="ignored via observation mask; conditional on observed smooth cells; missing-at-random not established",
        smooth_registered_zero_reason_counts=dict(registered_zero),
        missing_strict_cells=[], missing_smooth_cells=missing_rows, missing_cells=missing_rows,
        no_lean=sum(not r.get("lean_sha256") for r in rows), generated_tokens=sum(int(r.get("generated_tokens") or 0) for r in rows),
        scorer_adapter_compared=len(both), scorer_adapter_confusion=dict(confusion),
        scorer_adapter_disagreements=sum(r.get("strict") != r.get("adapter_strict") for r in both),
        metrics=metrics, FSC="unmeasured: zero judge calls", SCSC="unmeasured: FSC unavailable",
        bootstrap=dict(draws=10000, seed=20261021, unit="D-013 train task group", groups=GROUPS,
                       finite_weight_denominators=True,
                       limits="metric-specific observed rows; no refitting or new generation; smooth missingness is not assumed at random"),
        repeatability="One final deterministic score per generation; sample-index variation is generation variation, not repeated-score uncertainty",
        hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (scores, tasks)}))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", type=Path, required=True); ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    args.out.write_text(json.dumps(summarize(args.scores, args.tasks), indent=2, sort_keys=True, allow_nan=False) + "\n")
