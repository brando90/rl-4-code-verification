"""Write generation rows into VeriBench's Harbor job layout for its scorer, and read the scorer's per-task output back.

Job layout (experiment 103 `materialize.py`): `<job>/<task_id>/verifier/solution.lean`,
`<job>/<task_id>/config.json` = {"task": {"path": "tasks/<task_id>"}}, plus transport-only
`reward.json` and a `receipt.json`. VeriBench's scorer maps trials to tasks through
config.json, so each sample index gets its own job directory (one trial per task per job).
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

from rl4cv.rewards import ScoredResponse


def materialize_jobs(rows: Iterable[Mapping], out_root: str | Path, name: str) -> dict[int, Path]:
    """Create one job directory per sample index; an unextracted or cut-off answer is written as an empty file."""
    out_root = Path(out_root)
    by_sample: dict[int, list[Mapping]] = defaultdict(list)
    for r in rows:
        by_sample[int(r["sample_idx"])].append(r)
    jobs = {}
    for k, rs in sorted(by_sample.items()):
        job = out_root / f"{name}_s{k}"
        if job.exists():
            raise FileExistsError(f"{job} exists; job directories are write-once")
        for r in rs:
            trial = job / r["task_id"]
            (trial / "verifier").mkdir(parents=True)
            lean = r.get("lean") or ""
            (trial / "verifier" / "solution.lean").write_text(lean, encoding="utf-8")
            (trial / "verifier" / "reward.json").write_text(
                json.dumps({"collected": int(bool(lean.strip())), "note": "transport only; factors come from the VeriBench scorer"}) + "\n"
            )
            (trial / "config.json").write_text(json.dumps({"task": {"path": f"tasks/{r['task_id']}"}, "model": r.get("model"), "sample_idx": k}, indent=2) + "\n")
            receipt = {
                "task_id": r["task_id"],
                "sample_idx": k,
                "finish_reason": r.get("finish_reason"),
                "measured": r.get("measured"),
                "extraction": r.get("extraction"),
                "generated_tokens": r.get("generated_tokens"),
                "solution_sha256": hashlib.sha256(lean.encode()).hexdigest() if lean else None,
                "prompt_sha256": r.get("prompt_sha256"),
            }
            (trial / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        jobs[k] = job
    return jobs


def _f(x: str | None) -> float | None:
    if x is None or x == "" or x == "None":
        return None
    return float(x)


def _i(x: str | None) -> int | None:
    v = _f(x)
    return None if v is None else int(round(v))


# The frozen scorer pinned by experiment 103 (commit 59059a20d) still writes the pre-rename column
# names; the staged rename maps IC_ap -> IC_tests, IC_pp -> IC_proofs and TC -> FSC.
LEGACY_FACTOR_KEYS = {"IC_tests": "IC_ap", "IC_proofs": "IC_pp", "FSC": "TC"}


def _factor(row: Mapping, name: str) -> float:
    """A factor value under its current name or the frozen scorer's legacy name (0.0 when absent)."""
    for key in (name, LEGACY_FACTOR_KEYS.get(name)):
        if key and key in row:
            v = _f(row.get(key))
            return 0.0 if v is None else v
    return 0.0


def read_scorer_per_task(csv_path: str | Path) -> dict[str, dict]:
    """Index the scorer's `<stem>_per_task.csv` by task directory name."""
    with Path(csv_path).open(newline="", encoding="utf-8") as fh:
        return {row["task"]: row for row in csv.DictReader(fh)}


def scored_response(row: Mapping, gen_row: Mapping, fsc: float | None = None) -> ScoredResponse:
    """Combine the scorer's per-task row with the generation receipt into a ScoredResponse.

    IC_tests and IC_proofs are taken exactly as the scorer computed them; theorem counts come from
    the kernel summary (`kernel_n_theorems`, `kernel_n_honest`) when present.
    """
    ic_tests = _factor(row, "IC_tests")
    ic_proofs = _factor(row, "IC_proofs")
    n_thm = _i(row.get("kernel_n_theorems"))
    if n_thm is None:
        n_thm = _i(row.get("agent_n_thm")) or 0
    n_honest = _i(row.get("kernel_n_honest"))
    if n_honest is None:
        n_honest = int(round(ic_proofs * n_thm))
    compiles = str(row.get("agent_compiles")).lower() == "true"
    n_ex = _i(row.get("agent_n_ex")) or 0
    s = ScoredResponse(
        extracted=bool(gen_row.get("lean")),
        compiles=compiles,
        n_examples=n_ex,
        n_theorems_stated=n_thm,
        n_theorems_proved=n_honest,
        fsc=fsc,
        truncated=bool(gen_row.get("truncated")),
    )
    if abs(s.ic_tests - ic_tests) > 1e-9:
        raise ValueError(f"IC_tests mismatch for {row.get('task')}: scorer {ic_tests}, reconstructed {s.ic_tests}")
    return s


def main(argv: list[str] | None = None) -> int:
    """CLI: materialize one scorer job directory per sample index from a generation JSONL."""
    import argparse

    ap = argparse.ArgumentParser(description="Write VeriBench scorer job directories from generation rows")
    ap.add_argument("--gen", required=True, type=Path)
    ap.add_argument("--out-root", required=True, type=Path)
    ap.add_argument("--name", required=True)
    args = ap.parse_args(argv)
    rows = [json.loads(line) for line in args.gen.read_text(encoding="utf-8").splitlines() if line.strip()]
    jobs = materialize_jobs(rows, args.out_root, args.name)
    for k, path in jobs.items():
        print(f"sample {k}: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
