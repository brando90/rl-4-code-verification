#!/usr/bin/env python3
"""TLDR: Compute experiment 02A v3's PROTOCOL § 6 analysis from the scored cells and the generated-Lean screen (per-teacher declared / measured / unmeasured / kept, observed yield, measured-cell Wilson interval, missing-outcome bounds, union and overlap, failure taxonomy, kept-file lengths under the Qwen3 tokenizer, charges) and apply the locked decision rule; writes analysis_v3.json and a Markdown fragment for results.md."""
from __future__ import annotations

import argparse
import glob
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

TEACHER_ORDER = ("anthropic", "openai", "google")
TEACHER_LABEL = {"anthropic": "Claude Fable 5.1 (`anthropic/claude-fable-5-1-no-fallback`, compute_effort max)",
                 "openai": "GPT-6 Astra (`openai/gpt-6-astra-max`, reasoning_effort max)",
                 "google": "Gemini 4 Argon (`google/gemini-4-argon`, reasoning_effort high, T 1.0)"}
CLASSES = ("kept", "vacuous_theorem", "unproved_theorem", "forbidden_axiom", "no_theorem", "no_example", "no_typecheck", "no_lean", "unscored", "unmeasured")
SUFFICIENT_PAIRS, SUFFICIENT_TASKS, INSUFFICIENT_PAIRS = 1024, 512, 300
TOKENIZER_GLOB = "/lfs/skampere1/0/brando9/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/*/tokenizer.json"


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def verdict_of(pairs: int, tasks: int) -> str:
    if pairs >= SUFFICIENT_PAIRS and tasks >= SUFFICIENT_TASKS:
        return "SUFFICIENT"
    if pairs < INSUFFICIENT_PAIRS:
        return "INSUFFICIENT"
    return "PARTIAL"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", type=Path, required=True)
    ap.add_argument("--screen", type=Path, required=True)
    ap.add_argument("--declared-manifest", type=Path, required=True)
    ap.add_argument("--runs-state", type=Path, required=True)
    ap.add_argument("--job-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md-out", type=Path, required=True)
    ap.add_argument("--tokenizer", default=None)
    a = ap.parse_args()
    rows = [json.loads(l) for l in a.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    declared_ids = [t["task_id"] for t in json.loads(a.declared_manifest.read_text())["tasks"]]
    n_declared = len(declared_ids)
    declared_set = set(declared_ids)
    screen = json.loads(a.screen.read_text())
    excluded = set(screen.get("excluded_cells", []))
    state = json.loads(a.runs_state.read_text())
    tok_path = a.tokenizer or (glob.glob(TOKENIZER_GLOB) or [None])[0]
    tokenizer = None
    if tok_path:
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file(tok_path)
    by_teacher: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["task_id"] in declared_set:
            by_teacher[r["teacher"]].append(r)
    per_teacher, kept_pairs_pre, kept_pairs_post = {}, [], []
    for t in TEACHER_ORDER:
        cells = by_teacher.get(t, [])
        ids = {c["task_id"] for c in cells}
        missing = sorted(declared_set - ids)
        classes = Counter(c["failure_class"] for c in cells)
        classes["unmeasured"] += len(missing)
        measured = [c for c in cells if c.get("served")]
        unmeasured_ids = sorted(set(missing) | {c["task_id"] for c in cells if not c.get("served")})
        kept = [c for c in cells if c.get("kernel_binary") == 1.0]
        kept_post = [c for c in kept if f"{t}/{c['task_id']}" not in excluded]
        kept_pairs_pre += [(t, c["task_id"]) for c in kept]
        kept_pairs_post += [(t, c["task_id"]) for c in kept_post]
        n_meas, n_unm, n_kept = len(measured), len(unmeasured_ids), len(kept_post)
        lo, hi = wilson(n_kept, n_meas)
        lengths, n_thms = [], []
        for c in kept_post:
            p = a.job_root / f"{t}_s0" / c["task_id"] / "verifier" / "solution.lean"
            text = p.read_text(encoding="utf-8")
            if tokenizer is not None:
                lengths.append(len(tokenizer.encode(text).ids))
            n_thms.append(c.get("n_theorems_stated") or 0)
        charges = sum((c.get("cost_usd") or 0.0) for c in cells)
        run = state["runs"].get(f"main/{t}", {})
        per_teacher[t] = {
            "label": TEACHER_LABEL[t], "run_id": run.get("run_id"), "selector": run.get("selector"), "kwargs": run.get("kwargs"),
            "declared": n_declared, "measured": n_meas, "unmeasured": n_unm, "unmeasured_task_ids": unmeasured_ids,
            "kept_pre_screen": len(kept), "kept": n_kept, "screen_excluded": len(kept) - n_kept,
            "observed_yield": n_kept / n_declared, "measured_cell_yield": (n_kept / n_meas) if n_meas else None,
            "measured_cell_yield_wilson95": [lo, hi] if n_meas else None,
            "missing_outcome_bounds": {"all_unmeasured_fail": n_kept / n_declared, "all_unmeasured_succeed": (n_kept + n_unm) / n_declared},
            "failure_taxonomy": {k: classes.get(k, 0) for k in CLASSES},
            "truncated_cells": sum(1 for c in cells if c.get("truncated")),
            "kept_file_tokens_qwen3": {"n": len(lengths), "mean": statistics.fmean(lengths) if lengths else None, "median": statistics.median(lengths) if lengths else None,
                                       "min": min(lengths) if lengths else None, "max": max(lengths) if lengths else None},
            "kept_theorems_per_file": {"mean": statistics.fmean(n_thms) if n_thms else None, "median": statistics.median(n_thms) if n_thms else None,
                                       "min": min(n_thms) if n_thms else None, "max": max(n_thms) if n_thms else None},
            "charges_usd_reported": round(charges, 4),
            "generated_tokens_mean": statistics.fmean([c["generated_tokens"] for c in cells if c.get("generated_tokens") is not None]) if any(c.get("generated_tokens") is not None for c in cells) else None,
        }
    kept_tasks_post = {tid for _, tid in kept_pairs_post}
    kept_by_task = defaultdict(set)
    for t, tid in kept_pairs_post:
        kept_by_task[tid].add(t)
    overlap = {f"{x}&{y}": sum(1 for s in kept_by_task.values() if x in s and y in s) for i, x in enumerate(TEACHER_ORDER) for y in TEACHER_ORDER[i + 1:]}
    overlap["all_three"] = sum(1 for s in kept_by_task.values() if len(s) == 3)
    n_pairs, n_tasks = len(kept_pairs_post), len(kept_tasks_post)
    total_unm = sum(per_teacher[t]["unmeasured"] for t in TEACHER_ORDER)
    unm_tasks = set()
    for t in TEACHER_ORDER:
        unm_tasks |= set(per_teacher[t]["unmeasured_task_ids"])
    v_low = verdict_of(n_pairs, n_tasks)
    v_high = verdict_of(n_pairs + total_unm, len(kept_tasks_post | unm_tasks))
    verdict = v_low if v_low == v_high else "UNRESOLVED"
    out = {
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "n_declared_tasks": n_declared, "n_teachers": len(TEACHER_ORDER),
        "declared_cells": n_declared * len(TEACHER_ORDER), "per_teacher": per_teacher,
        "union": {"kept_pairs_pre_screen": len(kept_pairs_pre), "kept_pairs": n_pairs, "distinct_tasks_kept": n_tasks, "screen_excluded_pairs": len(kept_pairs_pre) - n_pairs,
                  "overlap": overlap, "tasks_kept_by_k_teachers": dict(Counter(len(s) for s in kept_by_task.values()))},
        "decision": {"rule": f"SUFFICIENT if kept pairs >= {SUFFICIENT_PAIRS} and distinct tasks >= {SUFFICIENT_TASKS}; INSUFFICIENT if kept pairs < {INSUFFICIENT_PAIRS}; else PARTIAL; "
                             "UNRESOLVED when the missing-outcome bounds fall on different sides of a threshold",
                     "verdict_all_unmeasured_fail": v_low, "verdict_all_unmeasured_succeed": v_high, "verdict": verdict,
                     "unmeasured_cells_total": total_unm},
        "charges_usd_reported_total": round(sum(per_teacher[t]["charges_usd_reported"] for t in TEACHER_ORDER), 4),
        "tokenizer": tok_path,
    }
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    md = []
    md.append("| Teacher | Declared | Measured | Unmeasured | Kept (post-screen) | Observed yield kept/declared | Measured-cell yield [Wilson 95%] | Bounds (all unmeasured fail / succeed) | Charge (USD, gateway-reported) |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for t in TEACHER_ORDER:
        p = per_teacher[t]
        w = p["measured_cell_yield_wilson95"]
        md.append(f"| {p['label']} | {p['declared']} | {p['measured']} | {p['unmeasured']} | {p['kept']} | {p['observed_yield']:.3f} | "
                  + (f"{p['measured_cell_yield']:.3f} [{w[0]:.3f}, {w[1]:.3f}] (n = {p['measured']} tasks)" if w else "n/a")
                  + f" | {p['missing_outcome_bounds']['all_unmeasured_fail']:.3f} / {p['missing_outcome_bounds']['all_unmeasured_succeed']:.3f} | {p['charges_usd_reported']:.2f} |")
    md.append("")
    md.append(f"**Union:** {n_pairs} kept (task, teacher) pairs ({len(kept_pairs_pre)} before the generated-Lean screen, {len(kept_pairs_pre) - n_pairs} excluded) over {n_tasks} distinct tasks of {n_declared}; "
              f"overlap: {', '.join(f'{k} = {v}' for k, v in overlap.items())}. **Verdict: {verdict}** (all-unmeasured-fail {v_low}, all-unmeasured-succeed {v_high}; {total_unm} unmeasured cells).")
    md.append("")
    md.append("| Failure class | " + " | ".join(TEACHER_ORDER) + " |")
    md.append("|---|" + "---|" * len(TEACHER_ORDER))
    for cls in CLASSES:
        md.append(f"| {cls} | " + " | ".join(str(per_teacher[t]["failure_taxonomy"][cls]) for t in TEACHER_ORDER) + " |")
    md.append("")
    md.append("| Teacher | Kept files | Qwen3 tokens mean / median / min / max | Theorems per kept file mean / median / min / max | Truncated cells |")
    md.append("|---|---|---|---|---|")
    for t in TEACHER_ORDER:
        p, L, T = per_teacher[t], per_teacher[t]["kept_file_tokens_qwen3"], per_teacher[t]["kept_theorems_per_file"]
        md.append(f"| {t} | {p['kept']} | " + (f"{L['mean']:.0f} / {L['median']:.0f} / {L['min']} / {L['max']}" if L["n"] else "n/a")
                  + " | " + (f"{T['mean']:.2f} / {T['median']} / {T['min']} / {T['max']}" if T["mean"] is not None else "n/a") + f" | {p['truncated_cells']} |")
    a.md_out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"kept_pairs": n_pairs, "distinct_tasks": n_tasks, "verdict": verdict, "per_teacher_kept": {t: per_teacher[t]["kept"] for t in TEACHER_ORDER},
                      "unmeasured": {t: per_teacher[t]["unmeasured"] for t in TEACHER_ORDER}, "charges": out["charges_usd_reported_total"]}))


if __name__ == "__main__":
    main()
