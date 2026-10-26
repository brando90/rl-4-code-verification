"""V26 analysis: pass@1 / pass@8 with task-bootstrap CIs, seed spread per size, paired differences (PROTOCOL.md).

Per-attempt success is expt_v16's criterion (expt_v6/analyze.evaluate = kernel_binary + the inherited non-vacuity gate).
CIs: 95% task bootstrap, 10,000 draws, numpy seed 0, all samples of a task kept together; differences are paired on the
same draws. Sherlock 1.7B v4 seeds come from the expt_v16 scores; SNAP rungs from the committed expt_v1 ladder cells.
A system whose files are missing is reported as missing, never imputed.

usage:
  python analyze_v26.py --v26-root <extracted expt_v26_results.tgz> --v16-data <dir with v16_*/raw.jsonl + scores/> --out results
  python analyze_v26.py --system NAME:LABEL:RAW:SCORES ... --out <dir>     (explicit systems, e.g. the stand-in test)
Needs numpy and the repo's src + external/veribench_scorer importable (as for expt_v16).
"""
import argparse
import csv
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
E08 = HERE.parent
SIZES = {"1.7B": ["v16_v4_20260830", "v16_v4_20260831", "v26_1p7b_s20260832"],
         "4B": ["v26_4b_s20260830", "v26_4b_s20260831"]}
NAMES = {"v16_v4_20260830": "1.7B v4 seed 20260830 (Sherlock, expt_v16)",
         "v16_v4_20260831": "1.7B v4 seed 20260831 (Sherlock, expt_v16)",
         "v26_1p7b_s20260832": "1.7B v4 recipe seed 20260832 (Sherlock, V26)",
         "v26_4b_s20260830": "4B v4 recipe seed 20260830 (Sherlock, V26)",
         "v26_4b_s20260831": "4B v4 recipe seed 20260831 (Sherlock, V26)"}
SNAP = {"sft_1p7B_f1p0": "1.7B sft_1p7B_f1p0 step 658 (SNAP)", "sft_4B_f1p0": "4B sft_4B_f1p0 step 658 (SNAP)",
        "base_4B_e05": "Qwen3-4B-Base e05 (SNAP)"}
PAIRS = [("v26_1p7b_s20260832", "v16_v4_20260830"), ("v26_1p7b_s20260832", "v16_v4_20260831"),
         ("v26_1p7b_s20260832", "sft_1p7B_f1p0"), ("v26_4b_s20260830", "sft_4B_f1p0"),
         ("v26_4b_s20260831", "sft_4B_f1p0"), ("v26_4b_s20260830", "v26_4b_s20260831"),
         ("pool_4B", "pool_1.7B"), ("pool_4B", "sft_4B_f1p0"), ("pool_1.7B", "sft_1p7B_f1p0")]


def ci(x):
    return [float(v) for v in np.quantile(x, [0.025, 0.975])]


def stats(m, draws):
    s = dict(successes=int(m.sum()), cells=int(m.size), pass_at_1=float(m.mean()), pass_at_1_ci95=ci(m.mean(1)[draws].mean(1)))
    if m.shape[1] == 8:
        solved = (m.max(1) > 0).astype(float)
        s.update(pass_at_8_tasks=int(solved.sum()), pass_at_8=float(solved.mean()), pass_at_8_ci95=ci(solved[draws].mean(1)))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v26-root", type=Path, help="extracted expt_v26_results.tgz (gen/<label>/raw.jsonl, score/<label>/scores)")
    ap.add_argument("--v16-data", type=Path, help="expt_v16 data dir (<label>/raw.jsonl, <label>/scores)")
    ap.add_argument("--system", action="append", default=[], help="NAME:LABEL:RAW:SCORES (overrides defaults)")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    os.environ["TINY_RUN_ROOT"] = str(a.out)
    sys.path.insert(0, str(E08 / "expt_v6"))
    import analyze
    analyze.RUN = a.out
    systems = {}
    if a.v16_data:
        for label in SIZES["1.7B"][:2]:
            systems[label] = (label, a.v16_data / label / "raw.jsonl", a.v16_data / label / "scores")
    if a.v26_root:
        for label in SIZES["1.7B"][2:] + SIZES["4B"]:
            systems[label] = (label, a.v26_root / "gen" / label / "raw.jsonl", a.v26_root / "score" / label / "scores")
    for spec in a.system:
        name, label, raw, scores = spec.split(":")
        systems[name] = (label, Path(raw), Path(scores))
    ids = (E08 / "expt_v1/results/split/vbv1_validation_task_ids.txt").read_text().splitlines()
    assert len(ids) == 135
    draws = np.random.default_rng(0).integers(0, 135, (10000, 135))
    mats, summary, missing = {}, {}, {}
    for name, (label, raw_path, scores_dir) in systems.items():
        n_scores = len(list(scores_dir.glob(f"{label}_s*/scsc_*_per_task.csv"))) if scores_dir.exists() else 0
        if not raw_path.exists() or n_scores != 8:
            missing[name] = f"raw {'present' if raw_path.exists() else 'missing'}, {n_scores}/8 sample score files"
            continue
        raw = analyze.read(raw_path)
        scored = analyze.collect(raw_path, scores_dir, label)
        res, _ = analyze.evaluate(label, raw, scored, ids)
        cells = list(csv.DictReader((a.out / "analysis" / f"{label}_cells.csv").open()))
        m = np.array([float(c["binary_success"]) for c in cells]).reshape(135, 8)
        mats[name] = m
        ext = {}
        for r in raw:
            ext[r["extraction"]] = ext.get(r["extraction"], 0) + 1
        res.update(stats(m, draws), label=label, extraction_counts=ext,
                   finish_reason_length=sum(r.get("finish_reason") == "length" for r in raw))
        summary[name] = res
    for label in SNAP:
        rows = list(csv.DictReader((E08 / f"expt_v1/results/ladder/{label}_validation_cells.csv").open()))
        idx = {(r["task_id"], int(r["sample_idx"])): float(r["kernel_binary"] or 0) for r in rows}
        mats[label] = np.array([[idx[(t, k)] for k in range(8)] for t in ids])
        summary[label] = dict(stats(mats[label], draws), source=f"expt_v1/results/ladder/{label}_validation_cells.csv (kernel_binary)")
    spread = {}
    for size, labels in SIZES.items():
        have = [x for x in labels if x in mats]
        if not have:
            continue
        p1 = np.array([summary[x]["pass_at_1"] for x in have])
        p8 = np.array([summary[x]["pass_at_8"] for x in have])
        pool = np.concatenate([mats[x] for x in have], axis=1)
        mats[f"pool_{size}"] = pool
        summary[f"pool_{size}"] = dict(stats(pool, draws), seeds=have, note=f"{pool.shape[1]} samples per task; pass@8 only for 8")
        spread[size] = dict(seeds=have, n=len(have), pass_at_1=p1.tolist(), pass_at_8=p8.tolist(),
                            pass_at_1_mean=float(p1.mean()), pass_at_1_sd=float(p1.std(ddof=1)) if len(have) > 1 else None,
                            pass_at_1_range=float(p1.max() - p1.min()), pass_at_8_mean=float(p8.mean()),
                            pass_at_8_sd=float(p8.std(ddof=1)) if len(have) > 1 else None, pass_at_8_range=float(p8.max() - p8.min()))
    diffs = {}
    for x, y in PAIRS:
        if x not in mats or y not in mats:
            continue
        d1 = mats[x].mean(1) - mats[y].mean(1)
        d = dict(pass_at_1_diff=float(d1.mean()), pass_at_1_diff_ci95=ci(d1[draws].mean(1)))
        if mats[x].shape[1] == 8 and mats[y].shape[1] == 8:
            d8 = (mats[x].max(1) > 0).astype(float) - (mats[y].max(1) > 0).astype(float)
            d.update(pass_at_8_diff=float(d8.mean()), pass_at_8_diff_ci95=ci(d8[draws].mean(1)))
        diffs[f"{x} - {y}"] = d
    out = dict(summary=summary, seed_spread=spread, paired_differences=diffs, missing=missing,
               bootstrap="task resampling, 10,000 draws, numpy seed 0", test_split_opened=False,
               metric="per-attempt binary success: kernel_binary with the inherited non-vacuity gate (expt_v6/analyze.evaluate)")
    (a.out / "summary_v26.json").write_text(json.dumps(out, indent=2) + "\n")
    pct = lambda v: f"{100 * v:.2f}%"
    rng = lambda v: f"[{pct(v[0])}, {pct(v[1])}]"
    lines = ["| System | Successes / cells | pass@1 [95% CI] | pass@8 tasks / 135 [95% CI] |", "|---|---|---|---|"]
    for k in list(NAMES) + ["pool_1.7B", "pool_4B"] + list(SNAP) + [n for n in summary if n not in NAMES and n not in SNAP and not n.startswith("pool_")]:
        if k not in summary:
            continue
        s = summary[k]
        p8 = f"{s['pass_at_8_tasks']} ({pct(s['pass_at_8'])}) {rng(s['pass_at_8_ci95'])}" if "pass_at_8" in s else "n/a"
        lines.append(f"| {NAMES.get(k, SNAP.get(k, k))} | {s['successes']} / {s['cells']} | {pct(s['pass_at_1'])} {rng(s['pass_at_1_ci95'])} | {p8} |")
    lines += ["", "| Seed spread | Seeds | pass@1 mean (SD) [range] | pass@8 mean (SD) [range] |", "|---|---|---|---|"]
    for size, s in spread.items():
        sd1 = "-" if s["pass_at_1_sd"] is None else pct(s["pass_at_1_sd"])
        sd8 = "-" if s["pass_at_8_sd"] is None else pct(s["pass_at_8_sd"])
        lines.append(f"| {size} | {s['n']} | {pct(s['pass_at_1_mean'])} ({sd1}) [{pct(s['pass_at_1_range'])}] "
                     f"| {pct(s['pass_at_8_mean'])} ({sd8}) [{pct(s['pass_at_8_range'])}] |")
    lines += ["", "| Paired difference (task bootstrap) | pass@1 diff [95% CI] | pass@8 diff [95% CI] |", "|---|---|---|"]
    for k, d in diffs.items():
        p8 = f"{pct(d['pass_at_8_diff'])} {rng(d['pass_at_8_diff_ci95'])}" if "pass_at_8_diff" in d else "n/a"
        lines.append(f"| {k} | {pct(d['pass_at_1_diff'])} {rng(d['pass_at_1_diff_ci95'])} | {p8} |")
    if missing:
        lines += ["", "Missing systems: " + "; ".join(f"{k}: {v}" for k, v in missing.items())]
    (a.out / "tables_v26.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
