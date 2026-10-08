#!/usr/bin/env python3
"""TLDR: Assemble experiment 02A v3's final scored cells: for each teacher take the sharded main read-back rows, swap in the recovery read-back for the cells whose main attempt was positively unserved, verify every row against the final cells and its Lean hash, write results/scored_cells.jsonl (no file contents) and a consolidated job view `<job-root-final>/<teacher>_s0/<task_id>` for the downstream screen, analysis and SFT steps; zero model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

TEACHERS = ("anthropic", "openai", "google")
DROP_KEYS = ("lean",)


def rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e02a_v3"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--jobs-final", type=Path, required=True)
    a = ap.parse_args()
    W = a.work
    state = json.loads((W / "rl-4-code-verification/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/results/runs_state.json").read_text())
    out_rows, summary = [], {}
    for t in TEACHERS:
        final = {c["task_id"]: c for c in rows(W / "raw/final" / t / "cells.jsonl")}
        replaced = set(state["runs"].get(f"final/{t}", {}).get("replaced_by_recovery", []))
        # Read-back shards: the first attempt wrote `main_<t>_k<i>.jsonl` (Anthropic finished before the 10-08-2026 reboot);
        # the resumed scoring wrote `main_<t>_r<j>.jsonl` over symlinked job views. Both name their job dir `<shard>_s0`.
        scored_main, shard_of = {}, {}
        shards = sorted((W / "scored").glob(f"main_{t}_r*.jsonl")) or sorted((W / "scored").glob(f"main_{t}_k*.jsonl"))
        for shard in shards:
            name = shard.stem
            for r in rows(shard):
                if r["task_id"] in scored_main:
                    raise RuntimeError(f"{t}/{r['task_id']}: read back twice ({shard_of[r['task_id']]} and {name})")
                scored_main[r["task_id"]] = r
                shard_of[r["task_id"]] = name
        summary_shards = [s.stem for s in shards]
        scored_rec = {r["task_id"]: r for r in rows(W / "scored" / f"scored_rec_{t}.jsonl")}
        missing = sorted(set(final) - set(scored_main))
        if missing:
            raise RuntimeError(f"{t}: {len(missing)} final cells have no main read-back row, e.g. {missing[:3]}")
        view = a.jobs_final / f"{t}_s0"
        view.mkdir(parents=True, exist_ok=True)
        for tid, cell in final.items():
            if tid in replaced:
                if tid not in scored_rec:
                    raise RuntimeError(f"{t}/{tid}: replaced by recovery but no recovery read-back row")
                r, src = dict(scored_rec[tid]), W / "jobs" / f"rec_{t}_s0" / tid
                r["attempt"] = "recovery"
            else:
                r, src = dict(scored_main[tid]), W / "jobs" / f"{shard_of[tid]}_s0" / tid
                r["attempt"] = "main"
            src = src.resolve()          # resume shards are symlinks to the first attempt's materialized trial dirs
            lean_path = src / "verifier" / "solution.lean"
            lean = lean_path.read_text(encoding="utf-8") if lean_path.exists() else ""
            if (hashlib.sha256(lean.encode("utf-8")).hexdigest() if lean else None) != cell.get("lean_sha256"):
                raise RuntimeError(f"{t}/{tid}: Lean hash in job dir differs from the final cell")
            if r.get("lean_sha256") != cell.get("lean_sha256"):
                raise RuntimeError(f"{t}/{tid}: scored row hash differs from the final cell")
            link = view / tid
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(src.resolve(), target_is_directory=True)
            for k in DROP_KEYS:
                r.pop(k, None)
            r.update(served=cell["served"], status=cell["status"], requests_sent_total=cell.get("requests_sent_total", cell.get("requests_sent")),
                     cost_usd=cell.get("cost_usd"), run_id=cell["run_id"])
            out_rows.append(r)
        classes = Counter(r["failure_class"] for r in out_rows if r["teacher"] == t)
        summary[t] = {"n": sum(classes.values()), "classes": dict(classes), "replaced_by_recovery": sorted(replaced), "readback_shards": summary_shards}
        if sum(classes.values()) != len(final):
            raise RuntimeError(f"{t}: {sum(classes.values())} rows for {len(final)} final cells")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        for r in sorted(out_rows, key=lambda r: (r["teacher"], r["task_id"])):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    (a.out.with_suffix(".summary.json")).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps({t: {k: v for k, v in s.items() if k != "replaced_by_recovery"} for t, s in summary.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
