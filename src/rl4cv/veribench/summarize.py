"""Summarize a scored VeriBench run: factor means with explicit denominators, failure taxonomy and probe signal.

Reports, per label: declared cells, scored cells, cut-off (length) and unextracted cells, and the
means of IC_tests, IC_proofs, FSC and SCSC over (a) scored cells and (b) all declared cells with
unmeasured cells shown separately, never folded into zeros. FSC and SCSC are reported only
over cells that carry a judge score (SCSC is exact without a judge when IC_tests * IC_proofs = 0).
For multi-sample probes it also reports per-channel success, pass@k and the share of mixed groups.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return (float(np.mean(xs)), len(xs)) if xs else (None, 0)


def summarize(rows: list[dict]) -> dict:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_label[str(r.get("label"))].append(r)
    out = {}
    for label, rs in by_label.items():
        scored = [r for r in rs if r.get("status") == "scored"]
        scsc_vals = []
        for r in scored:
            ic = (r.get("IC_tests") or 0.0) * (r.get("IC_proofs") or 0.0)
            if ic == 0:
                scsc_vals.append(0.0)
            elif r.get("FSC") is not None:
                scsc_vals.append((ic * r["FSC"]) ** (1 / 3))
            else:
                scsc_vals.append(None)
        s = {
            "cells_declared": len(rs),
            "cells_scored": len(scored),
            "cells_unscored": len(rs) - len(scored),
            "cells_cut_off_at_length": sum(1 for r in rs if r.get("truncated")),
            "cells_no_lean_extracted": sum(1 for r in rs if r.get("extraction") == "no_lean_block"),
            "compile_rate_scored": _mean([1.0 if r.get("compiles") else 0.0 for r in scored])[0],
            "IC_tests": _mean([r.get("IC_tests") for r in scored]),
            "IC_proofs": _mean([r.get("IC_proofs") for r in scored]),
            "FSC_judged": _mean([r.get("FSC") for r in scored]),
            "SCSC_exact_where_available": _mean(scsc_vals),
            "mean_generated_tokens": _mean([r.get("generated_tokens") for r in rs])[0],
        }
        samples = sorted({int(r["sample_idx"]) for r in rs})
        if len(samples) > 1:
            by_task: dict[str, list[dict]] = defaultdict(list)
            for r in scored:
                by_task[r["task_id"]].append(r)
            channels = sorted({c for r in scored for c in (r.get("rewards") or {})})
            probe = {}
            for c in channels:
                succ, passk, mixed, n = [], [], [], 0
                for tid, trs in by_task.items():
                    vals = [(r.get("rewards") or {}).get(c) for r in trs]
                    if len(trs) != len(samples) or any(v is None for v in vals):
                        continue
                    n += 1
                    succ.append(float(np.mean(vals)))
                    passk.append(1.0 if max(vals) > 0 else 0.0)
                    mixed.append(1.0 if (max(vals) - min(vals)) > 1e-12 else 0.0)
                probe[c] = {
                    "tasks_fully_measured": n,
                    "mean_reward": float(np.mean(succ)) if succ else None,
                    "pass_at_k_any_positive": float(np.mean(passk)) if passk else None,
                    "share_of_mixed_groups": float(np.mean(mixed)) if mixed else None,
                }
            s["probe_k"] = len(samples)
            s["probe"] = probe
        out[label] = s
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--scored", required=True, type=Path, nargs="+")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    rows = [json.loads(line) for p in args.scored for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = summarize(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
