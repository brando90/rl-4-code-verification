"""TLDR: Build experiment 20's committed Phase 0 per-cell table on Sherlock by joining the generation receipts (materialize_e20.py), the frozen scorer's 32 per-task CSVs (strict = reward_kernel_binary of the scorer row, IC_tests, IC_proofs, theorem counts) and the partial-credit JSONs (experiment 13's factored_reward and its factors) into phase0_cells_e20.csv (4,312 rows; unmeasured cells keep status and reason, never a zero) plus a summary JSON with denominators."""
from __future__ import annotations

import csv
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

E20 = Path(os.environ.get("E20_ROOT", "/scratch/users/brando9/rl4cv_sherlock/e20"))
sys.path.insert(0, os.environ.get("RL4CV_SRC", "/scratch/users/brando9/rl4cv_sherlock/grading/rl4cv/src"))
from rl4cv.rewards import reward_kernel_binary  # noqa: E402
from rl4cv.veribench.jobs import read_scorer_per_task, scored_response  # noqa: E402

FIELDS = ("task_id", "sample_idx", "chunk", "status", "strict", "factored_reward", "IC_tests", "IC_proofs", "FSC", "compiles",
          "n_examples", "theorem_count", "proved_count", "declarations_ok", "implementation_and_examples_ok", "proved_fraction",
          "partial_status", "partial_note", "generated_tokens", "prompt_tokens", "capped", "finish_reason", "extraction",
          "lean_sha256", "lean_bytes", "seed")


def main() -> int:
    receipts = list(csv.DictReader((E20 / "phase0/phase0_gen_receipts.csv").open()))
    rows, counts = [], Counter()
    scorer, partial = {}, {}
    for c in range(4):
        for k in range(8):
            n = f"e20_p0_c{c}_s{k}"
            per = glob.glob(str(E20 / f"phase0/scores/{n}/*_per_task.csv"))
            scorer[(c, k)] = read_scorer_per_task(per[0]) if per else None
            pj = E20 / f"phase0/partial/{n}/partial_{n}.json"
            partial[(c, k)] = {r["task_id"]: r for r in json.loads(pj.read_text())["records"]} if pj.is_file() else None
    for r in receipts:
        c, k, t = int(r["chunk"]), int(r["sample_idx"]), r["task_id"]
        out = {"task_id": t, "sample_idx": k, "chunk": c, "generated_tokens": r["generated_tokens"], "prompt_tokens": r["prompt_tokens"],
               "capped": r["truncated"], "finish_reason": r["finish_reason"], "extraction": r["extraction"], "lean_sha256": r["lean_sha256"],
               "lean_bytes": r["lean_bytes"], "seed": r["seed"], "FSC": "unmeasured"}
        sc = scorer[(c, k)]
        row = sc.get(t) if sc else None
        gen_row = {"lean": "x" if r["lean_sha256"] else "", "truncated": r["truncated"] == "True"}
        if row is None:
            out.update(status="unscored", strict="", IC_tests="", IC_proofs="", compiles="", n_examples="", theorem_count="", proved_count="")
        elif row.get("scoring_status") != "scored":
            out.update(status=f"scorer:{row.get('scoring_status') or 'none'}", strict="", IC_tests="", IC_proofs="", compiles="", n_examples="", theorem_count="", proved_count="")
        else:
            s = scored_response(row, gen_row)
            out.update(status="measured", strict=int(reward_kernel_binary(s)), IC_tests=s.ic_tests, IC_proofs=round(s.ic_proofs, 6),
                       compiles=int(s.compiles), n_examples=s.n_examples, theorem_count=s.n_theorems_stated, proved_count=s.n_theorems_proved)
        pt = partial[(c, k)]
        x = pt.get(t) if pt else None
        if x is None:
            out.update(factored_reward="", partial_status="missing", partial_note="", declarations_ok="", implementation_and_examples_ok="", proved_fraction="")
        elif x["status"] == "measured":
            out.update(factored_reward=round(float(x["factored_reward"]), 6), partial_status="measured", partial_note=x.get("note", ""),
                       declarations_ok=round(float(x["declarations_ok"]), 6), implementation_and_examples_ok=int(bool(x["implementation_and_examples_ok"])),
                       proved_fraction=round(float(x["proved_fraction"]), 6))
            if out["status"] == "measured" and int(x["strict"]) != out["strict"]:
                counts["adapter_strict_disagrees"] += 1
        elif "malformed source" in str(x.get("error", "")):
            out.update(factored_reward=0.0, partial_status="parse_failure_zero_credit", partial_note=str(x.get("error", ""))[:120], declarations_ok="", implementation_and_examples_ok="", proved_fraction="")
        else:
            out.update(factored_reward="", partial_status="unresolved", partial_note=str(x.get("error", ""))[:120], declarations_ok="", implementation_and_examples_ok="", proved_fraction="")
        counts[out["status"]] += 1
        counts["partial:" + out["partial_status"]] += 1
        rows.append(out)
    rows.sort(key=lambda r: (r["task_id"], r["sample_idx"]))
    out_csv = E20 / "phase0/phase0_cells_e20.csv"
    with out_csv.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    measured = [r for r in rows if r["status"] == "measured"]
    per_task = Counter()
    for r in measured:
        per_task[r["task_id"]] += int(r["strict"])
    tasks = sorted({r["task_id"] for r in rows})
    summary = {"declared_cells": 4312, "rows": len(rows), "counts": dict(counts), "strict_successes": sum(int(r["strict"]) for r in measured),
               "strict_pass1": (sum(int(r["strict"]) for r in measured) / len(measured)) if measured else None,
               "tasks": len(tasks), "tasks_fully_measured": sum(1 for t in tasks if sum(1 for r in measured if r["task_id"] == t) == 8),
               "active_tasks_1_to_7": sum(1 for t in tasks if 1 <= per_task[t] <= 7), "solved_8_of_8": sum(1 for t in tasks if per_task[t] == 8),
               "capped": sum(1 for r in rows if r["capped"] == "True"), "no_lean": sum(1 for r in rows if not r["lean_sha256"]),
               "mean_generated_tokens": sum(float(r["generated_tokens"]) for r in rows) / len(rows),
               "max_prompt_tokens": max(int(r["prompt_tokens"]) for r in rows),
               "factored_measured": sum(1 for r in rows if r["partial_status"] == "measured"),
               "factored_mean_measured": (sum(float(r["factored_reward"]) for r in rows if r["factored_reward"] != "") / max(1, sum(1 for r in rows if r["factored_reward"] != ""))),
               "factored_strictly_between_0_1": sum(1 for r in rows if r["factored_reward"] not in ("", 0.0, 1.0) and 0 < float(r["factored_reward"]) < 1)}
    (E20 / "phase0/phase0_summary_e20.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
