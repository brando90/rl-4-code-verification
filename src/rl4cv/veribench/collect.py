"""Join generation receipts, VeriBench scorer output and (optionally) FSC judge scores into one scored JSONL.

Inputs:
    --gen          generation JSONL from rl4cv.veribench.generate (one row per task x sample)
    --scores-root  directory holding one scorer out-dir per sample job, named <job-name>_s<k>/,
                   each containing the scorer's *_per_task.csv (VeriBench score_scsc.py --out-dir)
    --fsc-root     optional directory of <job-name>_s<k>.json files mapping task_id -> FSC in [0, 1]
                   (exported from experiment 103's judge controller); tasks absent from a file are unjudged

Every generation row appears in the output. A row with no scorer entry is kept with
status "unscored" so the full denominator survives; it is never silently dropped.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rl4cv.rewards import REWARD_CHANNELS, needs_judge
from rl4cv.veribench.jobs import read_scorer_per_task, scored_response


def _per_task_csv(d: Path) -> Path:
    found = sorted(d.glob("*_per_task.csv"))
    if len(found) != 1:
        raise FileNotFoundError(f"expected exactly one *_per_task.csv in {d}, found {len(found)}")
    return found[0]


def collect(gen_path: Path, scores_root: Path, job_name: str, fsc_root: Path | None = None) -> list[dict]:
    gen = [json.loads(line) for line in gen_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    samples = sorted({int(r["sample_idx"]) for r in gen})
    scorer = {k: read_scorer_per_task(_per_task_csv(scores_root / f"{job_name}_s{k}")) for k in samples}
    fsc: dict[int, dict] = {}
    if fsc_root is not None:
        for k in samples:
            p = fsc_root / f"{job_name}_s{k}.json"
            fsc[k] = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    out = []
    for g in gen:
        k = int(g["sample_idx"])
        row = {
            "task_id": g["task_id"],
            "sample_idx": k,
            "label": g.get("label"),
            "model": g.get("model"),
            "revision": g.get("revision"),
            "generated_tokens": g["generated_tokens"],
            "admitted": g["admitted"],
            "truncated": g["truncated"],
            "measured": g["measured"],
            "extraction": g["extraction"],
        }
        srow = scorer[k].get(g["task_id"])
        if srow is None:
            row.update(status="unscored")
            out.append(row)
            continue
        f = fsc.get(k, {}).get(g["task_id"])
        s = scored_response(srow, g, fsc=None if f is None else float(f))
        row.update(
            status="scored",
            compiles=s.compiles,
            n_examples=s.n_examples,
            n_theorems_stated=s.n_theorems_stated,
            n_theorems_proved=s.n_theorems_proved,
            IC_tests=s.ic_tests,
            IC_proofs=s.ic_proofs,
            FSC=s.fsc,
            split=srow.get("split"),
        )
        rewards = {}
        for name, fn in REWARD_CHANNELS.items():
            if needs_judge(s, name) and s.fsc is None:
                rewards[name] = None  # a judge score is required and absent: unmeasured, not zero
            else:
                try:
                    rewards[name] = fn(s)
                except ValueError:
                    rewards[name] = None
        row["rewards"] = rewards
        out.append(row)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gen", required=True, type=Path)
    ap.add_argument("--scores-root", required=True, type=Path)
    ap.add_argument("--job-name", required=True)
    ap.add_argument("--fsc-root", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    rows = collect(args.gen, args.scores_root, args.job_name, args.fsc_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    n_unscored = sum(1 for r in rows if r["status"] == "unscored")
    print(f"wrote {len(rows)} rows ({n_unscored} unscored) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
