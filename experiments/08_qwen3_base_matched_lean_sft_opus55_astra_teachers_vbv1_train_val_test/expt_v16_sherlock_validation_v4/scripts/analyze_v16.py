"""Score summary for the two Sherlock 08 v4 checkpoints and Base on VeriBench V1 validation (135 tasks x 8).

Uses the inherited per-attempt binary criterion (expt_v6/analyze.evaluate = kernel_binary + non-vacuity gate) on the
scorer output of score_v16.sh, adds task-bootstrap 95% CIs (10,000 draws, seed 0, all 8 samples of a task kept together)
for pass@1 (mean over 8 samples) and pass@8 (task solved by any of 8), and paired task-bootstrap differences against
the committed SNAP rungs (expt_v1 ladder cells CSVs: sft_1p7B_f1p0 = same corpus/updates/Base revision, base_1p7B_e05).

usage: python analyze_v16.py --data <dir with <label>/raw.jsonl and <label>/scores/<label>_s<k>/> --out ../results
"""
import argparse
import csv
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
E08 = HERE.parents[1]
LABELS = {"v16_v4_20260830": "v4 seed 20260830 (Sherlock)", "v16_v4_20260831": "v4 seed 20260831 (Sherlock)",
          "v16_base": "Qwen3-1.7B-Base (Sherlock)"}
SNAP = {"sft_1p7B_f1p0": "v1 sft_1p7B_f1p0 step 658 (SNAP)", "base_1p7B_e05": "Qwen3-1.7B-Base e05 (SNAP)"}


def ci(x):
    return [float(v) for v in np.quantile(x, [0.025, 0.975])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=HERE.parent / "results")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    os.environ["TINY_RUN_ROOT"] = str(a.out)
    sys.path.insert(0, str(E08 / "expt_v6"))
    import analyze
    analyze.RUN = a.out
    ids = (E08 / "expt_v1/results/split/vbv1_validation_task_ids.txt").read_text().splitlines()
    draws = np.random.default_rng(0).integers(0, 135, (10000, 135))
    mats, summary = {}, {}
    for label in LABELS:
        raw_path = a.data / label / "raw.jsonl"
        raw = analyze.read(raw_path)
        scored = analyze.collect(raw_path, a.data / label / "scores", label)
        res, _ = analyze.evaluate(label, raw, scored, ids)
        cells = list(csv.DictReader((a.out / "analysis" / f"{label}_cells.csv").open()))
        m = np.array([float(c["binary_success"]) for c in cells]).reshape(135, 8)
        mats[label] = m
        ext = {}
        for r in raw:
            ext[r["extraction"]] = ext.get(r["extraction"], 0) + 1
        res.update(pass_at_1=float(m.mean()), pass_at_1_ci95=ci(m.mean(1)[draws].mean(1)),
                   pass_at_8=float((m.max(1) > 0).mean()), pass_at_8_ci95=ci((m.max(1) > 0)[draws].mean(1)),
                   extraction_counts=ext, finish_reason_length=sum(r.get("finish_reason") == "length" for r in raw))
        summary[label] = res
    for label in SNAP:
        rows = list(csv.DictReader((E08 / f"expt_v1/results/ladder/{label}_validation_cells.csv").open()))
        idx = {(r["task_id"], int(r["sample_idx"])): float(r["kernel_binary"]) for r in rows}
        m = np.array([[idx[(t, k)] for k in range(8)] for t in ids])
        mats[label] = m
        summary[label] = dict(successes=int(m.sum()), pass_at_1=float(m.mean()), pass_at_1_ci95=ci(m.mean(1)[draws].mean(1)),
                              pass_at_8_tasks=int((m.max(1) > 0).sum()), pass_at_8=float((m.max(1) > 0).mean()),
                              pass_at_8_ci95=ci((m.max(1) > 0)[draws].mean(1)),
                              source=f"expt_v1/results/ladder/{label}_validation_cells.csv (kernel_binary)")
    pooled = np.concatenate([mats["v16_v4_20260830"], mats["v16_v4_20260831"]], axis=1)
    summary["v4_two_seed_pool"] = dict(successes=int(pooled.sum()), cells=int(pooled.size), pass_at_1=float(pooled.mean()),
                                       pass_at_1_ci95=ci(pooled.mean(1)[draws].mean(1)),
                                       note="16 samples per task (8 per seed); pass@8 not defined for the pool")
    diffs = {}
    for x, y in [("v16_v4_20260830", "sft_1p7B_f1p0"), ("v16_v4_20260831", "sft_1p7B_f1p0"),
                 ("v16_v4_20260830", "v16_v4_20260831"), ("v16_v4_20260830", "v16_base"),
                 ("v16_v4_20260831", "v16_base"), ("v16_base", "base_1p7B_e05")]:
        d1 = mats[x].mean(1) - mats[y].mean(1)
        d8 = (mats[x].max(1) > 0).astype(float) - (mats[y].max(1) > 0).astype(float)
        diffs[f"{x} - {y}"] = dict(pass_at_1_diff=float(d1.mean()), pass_at_1_diff_ci95=ci(d1[draws].mean(1)),
                                   pass_at_8_diff=float(d8.mean()), pass_at_8_diff_ci95=ci(d8[draws].mean(1)))
    d1 = pooled.mean(1) - mats["sft_1p7B_f1p0"].mean(1)
    diffs["v4_two_seed_pool - sft_1p7B_f1p0"] = dict(pass_at_1_diff=float(d1.mean()), pass_at_1_diff_ci95=ci(d1[draws].mean(1)))
    out = dict(summary=summary, paired_differences=diffs, bootstrap="task resampling, 10,000 draws, numpy seed 0",
               metric="per-attempt binary success: kernel_binary with the inherited non-vacuity gate (expt_v6/analyze.evaluate)",
               test_split_opened=False)
    (a.out / "summary_v16.json").write_text(json.dumps(out, indent=2) + "\n")
    pct = lambda v: f"{100 * v:.2f}%"
    lines = ["| System | Successes / 1080 | pass@1 (mean of 8) [95% CI] | pass@8 tasks / 135 [95% CI] |", "|---|---|---|---|"]
    for k, name in {**LABELS, **SNAP}.items():
        s = summary[k]
        t = s.get("pass_at_8_tasks", round(s["pass_at_8"] * 135))
        lines.append(f"| {name} | {s['successes']} | {pct(s['pass_at_1'])} [{pct(s['pass_at_1_ci95'][0])}, {pct(s['pass_at_1_ci95'][1])}] "
                     f"| {t} ({pct(s['pass_at_8'])}) [{pct(s['pass_at_8_ci95'][0])}, {pct(s['pass_at_8_ci95'][1])}] |")
    lines += ["", "| Paired difference (task bootstrap) | pass@1 diff [95% CI] | pass@8 diff [95% CI] |", "|---|---|---|"]
    for k, d in diffs.items():
        p8 = f"{pct(d['pass_at_8_diff'])} [{pct(d['pass_at_8_diff_ci95'][0])}, {pct(d['pass_at_8_diff_ci95'][1])}]" if "pass_at_8_diff" in d else "n/a"
        lines.append(f"| {k} | {pct(d['pass_at_1_diff'])} [{pct(d['pass_at_1_diff_ci95'][0])}, {pct(d['pass_at_1_diff_ci95'][1])}] | {p8} |")
    (a.out / "tables_v16.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
