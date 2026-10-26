"""TLDR: Copy VeriBench experiment 111's reference-consistency (RC) rows for experiment 19's 11 panel systems, train and validation tasks only, from a VeriBench clone at a pinned commit into this experiment's inputs, with source hashes; rows for experiment 109 systems, withheld rating-set tasks and test-split tasks are not copied."""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from pathlib import Path

import data_e19 as D

OUT = D.HERE / "results/inputs/rc_rows_panel_trainval.csv"
COLUMNS = ("system", "task_id", "split", "source", "typechecks", "statable", "n_tests", "tests_pass", "n_pbt", "pbt_survived",
           "n_obligations", "obligations_proved")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--veribench", type=Path, default=Path.home() / "veribench")
    args = ap.parse_args()
    split = D.load_split()
    gk = D._gold_key_to_task()
    rows, sources = [], {}
    for key, rel in D.RC_FILES.items():
        raw = subprocess.run(["git", "-C", str(args.veribench), "show", f"{D.VERIBENCH_RC_COMMIT}:{rel}"],
                             capture_output=True, check=True).stdout
        sources[key] = {"path": rel, "sha256": D.sha256_bytes(raw), "rows": 0, "copied": 0}
        for r in csv.DictReader(io.StringIO(raw.decode())):
            sources[key]["rows"] += 1
            s = D.RC_SYSTEM_MAP.get(r["system"])
            t = gk.get(r["gold_key"])
            if s is None or t is None or t in split.test_ids:
                continue
            rows.append({"system": s, "task_id": t, "split": split.split_of(t), "source": key,
                         # experiment 102 (TMLR) rows exist only for files that typecheck; experiment 103 rows say so
                         "typechecks": r.get("typechecks", "1") if key == "x103" else "1",
                         **{c: r.get(c, "") for c in COLUMNS[5:]}})
            sources[key]["copied"] += 1
    rows.sort(key=lambda r: (r["system"], r["task_id"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    prov = {"veribench_commit": D.VERIBENCH_RC_COMMIT, "sources": sources, "output": OUT.name,
            "output_sha256": D.sha256_file(OUT), "rows": len(rows),
            "excluded": "experiment 109 systems, test-split tasks; the 27 withheld rating-set tasks are absent at the source"}
    (OUT.parent / "rc_rows_panel_trainval_provenance.json").write_text(json.dumps(prov, indent=1, sort_keys=True) + "\n")
    print(json.dumps(prov, indent=1))


if __name__ == "__main__":
    main()
