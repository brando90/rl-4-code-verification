"""V28 analysis (Llama-3.2 family replicate): pass@1 / pass@8 with task-bootstrap CIs, seed spread per size, paired differences.

Same criterion and statistics as analyze_v26.py: per-attempt success is expt_v6/analyze.evaluate (kernel_binary + the inherited
non-vacuity gate), no differential testing (no DT); 95% task bootstrap, 10,000 draws, numpy seed 0, all samples of a task kept
together; differences paired on the same draws. A system whose files are missing is reported as missing, never imputed.
The Qwen3 rows (V26/expt_v16, same columns) are read from the committed expt_v26 results/summary_v26.json for the cross-family table.

usage:
  python analyze_v28.py --v28-root <extracted expt_v28_results.tgz> --out results [--qwen-summary ../expt_v26_sherlock_seed_replicates/results/summary_v26.json]
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
SIZES = {"Llama-3.2-1B": [f"v28_llama1b_s{x}" for x in (20260830, 20260831, 20260832)],
         "Llama-3.2-3B": [f"v28_llama3b_s{x}" for x in (20260830, 20260831, 20260832)]}
NAMES = {f"v28_llama{n}b_s{x}": f"Llama-3.2-{n}B seed {x} (V28)" for n in (1, 3) for x in (20260830, 20260831, 20260832)}
QWEN_ROWS = {"pool_1.7B": "Qwen3-1.7B-Base pooled (3 seeds, V26/expt_v16)", "pool_4B": "Qwen3-4B-Base pooled (2 seeds, V26)",
             "v26_4b_s20260830": "Qwen3-4B-Base seed 20260830 (V26)", "v26_4b_s20260831": "Qwen3-4B-Base seed 20260831 (V26)",
             "v26_1p7b_s20260832": "Qwen3-1.7B-Base seed 20260832 (V26)"}
PAIRS = [("pool_Llama-3.2-3B", "pool_Llama-3.2-1B")] + [
    (f"v28_llama{n}b_s{x}", f"v28_llama{n}b_s{y}") for n in (1, 3) for x, y in ((20260831, 20260830), (20260832, 20260830), (20260832, 20260831))]


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
    ap.add_argument("--v28-root", type=Path, help="extracted expt_v28_results.tgz (gen/<label>/raw.jsonl, score/<label>/scores)")
    ap.add_argument("--qwen-summary", type=Path, help="expt_v26 results/summary_v26.json (Qwen3 reference rows)")
    ap.add_argument("--system", action="append", default=[], help="NAME:LABEL:RAW:SCORES (overrides defaults)")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    os.environ["TINY_RUN_ROOT"] = str(a.out)
    sys.path.insert(0, str(E08 / "expt_v6"))
    import analyze
    analyze.RUN = a.out
    systems = {}
    if a.v28_root:
        for label in [x for v in SIZES.values() for x in v]:
            systems[label] = (label, a.v28_root / "gen" / label / "raw.jsonl", a.v28_root / "score" / label / "scores")
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
    qwen = {}
    if a.qwen_summary:
        qs = json.loads(a.qwen_summary.read_text())["summary"]
        qwen = {k: qs[k] for k in QWEN_ROWS if k in qs}
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
    out = dict(summary=summary, qwen_reference=qwen, seed_spread=spread, paired_differences=diffs, missing=missing,
               bootstrap="task resampling, 10,000 draws, numpy seed 0", test_split_opened=False,
               metric="per-attempt binary success: kernel_binary with the inherited non-vacuity gate (expt_v6/analyze.evaluate)")
    (a.out / "summary_v28.json").write_text(json.dumps(out, indent=2) + "\n")
    pct = lambda v: f"{100 * v:.2f}%"
    rng = lambda v: f"[{pct(v[0])}, {pct(v[1])}]"
    lines = ["| System | Successes / samples | pass@1 [95% CI] | pass@8 tasks / 135 [95% CI] |", "|---|---|---|---|"]
    for k in list(NAMES) + [f"pool_{z}" for z in SIZES] + list(QWEN_ROWS):
        if k not in summary and k not in qwen:
            continue
        s = summary[k] if k in summary else qwen[k]
        p8 = f"{s['pass_at_8_tasks']} ({pct(s['pass_at_8'])}) {rng(s['pass_at_8_ci95'])}" if "pass_at_8" in s else "n/a"
        lines.append(f"| {NAMES.get(k) or QWEN_ROWS.get(k) or f"{k.replace('pool_', '')} pooled ({len(summary[k]['seeds'])} seeds)"} | {s['successes']} / {s['cells']} | {pct(s['pass_at_1'])} {rng(s['pass_at_1_ci95'])} | {p8} |")
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
    (a.out / "tables_v28.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
