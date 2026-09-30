"""Measure rho, H and diagnostics per environment and reward channel from a scored probe JSONL.

Usage:
    python -m rl4cv.probe --scored results/scored_g8.jsonl --channel kernel_binary \\
        [--envs envs.json | --group-by split] --out results/rho_h_kernel_binary.json

`envs.json` maps environment names to task-id lists (for example the four 2x2 cells). With
`--group-by split` each VeriBench split is one environment; with neither, all tasks form one
environment. Groups whose reward is unmeasured for any sample (a missing judge score, an
unscored cell) are excluded from rho/H and counted in `n_groups_excluded_unmeasured`, so a
partial judge pass can never masquerade as zero signal.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from rl4cv.experience import Response, measure_environment


def load_scored(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def measure_channel(rows: list[dict], channel: str, envs: dict[str, list[str]] | None = None, group_by: str | None = None) -> dict:
    by_task: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_task[r["task_id"]].append(r)
    if envs is None:
        if group_by:
            envs = defaultdict(list)
            for tid, rs in by_task.items():
                envs[str(rs[0].get(group_by))].append(tid)
            envs = dict(envs)
        else:
            envs = {"all": sorted(by_task)}
    result = {}
    for env, tids in envs.items():
        groups, excluded, missing = [], 0, 0
        for tid in tids:
            rs = by_task.get(tid)
            if not rs:
                missing += 1
                continue
            vals = [(r.get("rewards") or {}).get(channel) for r in rs]
            if any(v is None for v in vals) or any(r.get("status") != "scored" for r in rs):
                excluded += 1
                continue
            groups.append([Response(float(v), int(r["generated_tokens"]), bool(r["admitted"])) for v, r in zip(vals, rs)])
        entry = {"n_tasks_declared": len(tids), "n_tasks_missing": missing, "n_groups_excluded_unmeasured": excluded}
        if groups:
            entry.update(measure_environment(groups).to_dict())
        else:
            entry["note"] = "no fully measured groups"
        result[env] = entry
    return result


def to_markdown(table: dict, channel: str) -> str:
    cols = ["n_groups", "mean_reward", "q_mixed_empirical", "admission_rate", "mean_generated_tokens", "rho", "H", "top_decile_mass_share", "n_groups_excluded_unmeasured"]
    lines = [f"| env ({channel}) | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for env, e in table.items():
        cells = []
        for c in cols:
            v = e.get(c)
            cells.append("—" if v is None else (f"{v:.4g}" if isinstance(v, float) else str(v)))
        lines.append(f"| {env} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--envs", type=Path)
    ap.add_argument("--group-by", default=None)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    envs = json.loads(args.envs.read_text()) if args.envs else None
    table = measure_channel(load_scored(args.scored), args.channel, envs, args.group_by)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(table, indent=2) + "\n")
    args.out.with_suffix(".md").write_text(to_markdown(table, args.channel) + "\n")
    print(to_markdown(table, args.channel))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
