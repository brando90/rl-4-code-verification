"""Compute the frozen validation readiness gates from complete per-cell binary results."""
import argparse
import csv
import json
import math
from pathlib import Path


def truth(value):
    if value in (True, 1, "1", "True", "true"): return True
    if value in (False, 0, "0", "False", "false"): return False
    raise ValueError(f"Unknown Boolean: {value!r}")


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    d = 1 + z*z/n
    middle = (p + z*z/(2*n)) / d
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return [max(0.0, middle-half), min(1.0, middle+half)]


def summarize(rows, ids):
    assert len(ids) == len(set(ids)) == 135
    expected = {(tid, k) for tid in ids for k in range(8)}
    index = {}
    for row in rows:
        key = (row["task_id"], int(row["sample_idx"]))
        assert key in expected, ("unexpected cell", key)
        assert key not in index, ("duplicate cell", key)
        value = float(row["binary_success"])
        assert value in (0., 1.), ("unknown/nonbinary result", key)
        index[key] = (int(value), truth(row["extracted"]), truth(row["capped"]))
    missing = sorted(expected - index.keys())
    result = dict(status="INCOMPLETE" if missing else "COMPLETE", known_cells=len(index),
                  declared_cells=1080, missing_cells=missing, test_split_opened=False)
    if missing:
        result["readiness"] = "INCOMPLETE"
        return result
    counts = [sum(index[(tid, k)][0] for k in range(8)) for tid in ids]
    mixed = sum(0 < n < 8 for n in counts)
    extracted = sum(r[1] for r in index.values())
    capped = sum(r[2] for r in index.values())
    gates = dict(extraction=extracted >= 972, truncation=capped <= 108, mixed=mixed >= 7)
    result.update(readiness="PASS" if all(gates.values()) else "FAIL", gates=gates,
        extracted=extracted, capped=capped, mixed_tasks=mixed, tasks=135,
        mixed_share=mixed/135, mixed_share_wilson95=wilson(mixed,135),
        success_count=sum(counts), success_rate=sum(counts)/1080,
        success_count_histogram={str(k): counts.count(k) for k in range(9)},
        pass_at_8_tasks=sum(n>0 for n in counts), all_pass_tasks=sum(n==8 for n in counts),
        target_band_tasks_2_to_6=sum(2<=n<=6 for n in counts),
        binary_accuracy_25_percent_reached=sum(counts)>=270,
        meeting_criteria_source="D-017: 2..6 successes per8attempts; binary accuracy milestone is distinct from unmeasured SCSC",
        threshold_source="Experiment 08 PROTOCOL.md section 9: >=972 extracted, <=108 capped, >=7 mixed tasks; all1080 known",
        p_value=None, uncertainty="Wilson95 over135 validation tasks; two training seeds are reported separately",
        limitation="Readiness proxy, not evidence that an RL training run improves performance; not a cross-size selection")
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("cells");parser.add_argument("ids");parser.add_argument("out")
    args=parser.parse_args()
    result=summarize(list(csv.DictReader(open(args.cells))),Path(args.ids).read_text().splitlines())
    Path(args.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
