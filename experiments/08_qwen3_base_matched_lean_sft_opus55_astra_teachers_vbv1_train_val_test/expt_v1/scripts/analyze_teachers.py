#!/usr/bin/env python3
"""TLDR: Experiment 08 teacher-run analysis (runbook § 6.3) from `scored_cells.jsonl`, the generated-Lean screen and the SFT stats: per teacher and sample the declared / measured / unmeasured / kept counts with a Wilson 95% interval on kept / measured (unit = task), union coverage over tasks and per family, the failure taxonomy, kept-file Qwen3 token lengths, overlap between teachers, and the total reported charge; writes `teacher_analysis.json` and a Markdown fragment for `results.md` (runs in the transformers interpreter; zero model calls)."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
os.environ.setdefault("HF_HOME", str(WORK / "cache" / "huggingface"))
TEACHERS = ("opus55", "astra")
SAMPLES = ("s1", "s2", "s3", "s4")
N_TRAIN = 539


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float | None, float | None, float | None]:
    if n == 0:
        return None, None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(p, 4), round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)


def qstats(xs: list[int]) -> dict:
    if not xs:
        return {"n": 0}
    xs = sorted(xs)
    return {"n": len(xs), "mean": round(st.mean(xs)), "median": xs[len(xs) // 2], "p90": xs[int(0.9 * len(xs))], "max": xs[-1], "total": sum(xs)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", type=Path, default=EXP / "results" / "scored_cells.jsonl")
    ap.add_argument("--screen", type=Path, default=EXP / "results" / "generated_lean_screen.json")
    ap.add_argument("--sft-stats", type=Path, default=EXP / "results" / "sft_set_stats.json")
    ap.add_argument("--job-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=EXP / "results" / "teacher_analysis.json")
    ap.add_argument("--md-out", type=Path, default=EXP / "results" / "teacher_analysis.md")
    a = ap.parse_args(argv)
    from template_check import load_tokenizers

    tok = load_tokenizers(["8B"])["8B"]["tokenizer"]
    rows = [json.loads(l) for l in a.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("phase", "main") == "main"]
    screen = json.loads(a.screen.read_text()) if a.screen.exists() else {"excluded_cells": {}}
    sft = json.loads(a.sft_stats.read_text()) if a.sft_stats.exists() else {}
    with (EXP / "results" / "split" / "vbv1_split_manifest.csv").open(encoding="utf-8", newline="") as fh:
        family = {r["task_id"]: r["family"] for r in csv.DictReader(fh) if r["split"] == "train"}
    per_run, kept_tasks, kept_lengths, taxonomy = {}, {t: set() for t in TEACHERS}, {t: [] for t in TEACHERS}, {t: {} for t in TEACHERS}
    charges = {}
    for t in TEACHERS:
        for s in SAMPLES:
            cells = [r for r in rows if r["teacher"] == t and r["r"] == s]
            measured = [r for r in cells if r.get("served")]
            kept = [r for r in cells if r.get("kernel_binary") == 1.0]
            eligible = [r for r in kept if r.get("extraction_consistent") is True and f"{t}/{s}/{r['task_id']}" not in screen.get("excluded_cells", {})]
            p, lo, hi = wilson(len(kept), len(measured))
            per_run[f"{t}/{s}"] = {"declared": N_TRAIN, "harvested": len(cells), "measured": len(measured), "unmeasured": N_TRAIN - len(measured), "kept": len(kept),
                                   "kept_eligible_after_consistency_and_screen": len(eligible), "kept_over_measured": p, "wilson95": [lo, hi],
                                   "kept_over_declared": round(len(kept) / N_TRAIN, 4), "truncated": sum(1 for r in cells if r.get("truncated")),
                                   "charges_usd_reported": round(sum(r.get("cost_usd") or 0.0 for r in cells), 2),
                                   "generated_tokens_mean": round(st.mean([r["generated_tokens"] for r in measured if r.get("generated_tokens")]), 0) if measured else None}
            charges[f"{t}/{s}"] = per_run[f"{t}/{s}"]["charges_usd_reported"]
            for r in cells:
                taxonomy[t][r["failure_class"]] = taxonomy[t].get(r["failure_class"], 0) + 1
            for r in kept:
                kept_tasks[t].add(r["task_id"])
                lean = (a.job_root / (f"{t}_{s}_rec1_s0" if r.get("recovered") else f"{t}_{s}_s0") / r["task_id"] / "verifier" / "solution.lean").read_text(encoding="utf-8")
                kept_lengths[t].append(len(tok(lean, add_special_tokens=False)["input_ids"]))
    union = kept_tasks["opus55"] | kept_tasks["astra"]
    both = kept_tasks["opus55"] & kept_tasks["astra"]
    fam_union: dict[str, dict] = {}
    for tid, f in family.items():
        d = fam_union.setdefault(f, {"tasks": 0, "covered": 0})
        d["tasks"] += 1
        d["covered"] += int(tid in union)
    for f, d in fam_union.items():
        d["share"] = round(d["covered"] / d["tasks"], 4)
    out = {"written_utc": stamp(), "n_cells_scored": len(rows), "n_declared": N_TRAIN * len(TEACHERS) * len(SAMPLES), "per_run": per_run,
           "per_teacher_tasks_kept_any_sample": {t: len(kept_tasks[t]) for t in TEACHERS},
           "union_coverage": {"tasks_with_a_kept_file": len(union), "of": N_TRAIN, "share": round(len(union) / N_TRAIN, 4), "wilson95": list(wilson(len(union), N_TRAIN)[1:])},
           "overlap": {"both_teachers": len(both), "opus55_only": len(kept_tasks["opus55"] - kept_tasks["astra"]), "astra_only": len(kept_tasks["astra"] - kept_tasks["opus55"]),
                       "neither": N_TRAIN - len(union)},
           "per_family_union_coverage": dict(sorted(fam_union.items())), "failure_taxonomy": taxonomy,
           "kept_file_tokens_qwen3": {t: qstats(kept_lengths[t]) for t in TEACHERS},
           "charges_usd_reported": {"per_run": charges, "total": round(sum(charges.values()), 2)},
           "sft_set": {k: sft.get(k) for k in ("n_examples", "n_distinct_tasks", "per_teacher", "assistant_tokens", "exclusions_by_reason")} if sft else None}
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["| Teacher / sample | Declared | Measured | Unmeasured | Kept | Kept / measured [Wilson 95%] | Truncated | Charge (USD) |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in per_run.items():
        lines.append(f"| {k} | {v['declared']} | {v['measured']} | {v['unmeasured']} | {v['kept']} | {v['kept_over_measured']} [{v['wilson95'][0]}, {v['wilson95'][1]}] | {v['truncated']} | {v['charges_usd_reported']} |")
    lines += ["", f"Union coverage: {len(union)} / {N_TRAIN} train tasks have at least one kept file (share {out['union_coverage']['share']}, Wilson 95% {out['union_coverage']['wilson95']}); "
              f"both teachers {len(both)}, opus55 only {out['overlap']['opus55_only']}, astra only {out['overlap']['astra_only']}, neither {out['overlap']['neither']}. "
              f"Total reported charge {out['charges_usd_reported']['total']} USD."]
    a.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"union": out["union_coverage"], "overlap": out["overlap"], "charges_total": out["charges_usd_reported"]["total"],
                      "per_run_kept": {k: v["kept"] for k, v in per_run.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
