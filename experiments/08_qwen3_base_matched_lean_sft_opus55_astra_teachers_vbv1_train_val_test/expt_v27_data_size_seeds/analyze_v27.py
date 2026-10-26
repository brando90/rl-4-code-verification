"""V27 analysis: per-run and per-rung pass@1 / pass@8, rung-to-rung gains vs seed spread and vs experiment 17's curve.

Per-attempt success is expt_v16's criterion (expt_v6/analyze.evaluate = kernel_binary + the inherited non-vacuity gate).
CIs: 95% task bootstrap, 10,000 draws, numpy seed 0, all samples of a task kept together; differences are paired on the
same draws. The 100% rung is the two Sherlock v4 seeds scored in expt_v16; SNAP ladder rungs come from the committed
expt_v1 ladder cells. A system whose files are missing is reported as missing, never imputed. Readout rules: PROTOCOL.md.

usage:
  python analyze_v27.py --v27-root <extracted expt_v27_results.tgz> --v16-data <dir with v16_*/raw.jsonl + scores/> --out results
  python analyze_v27.py --system NAME:LABEL:RAW:SCORES ... --out <dir>     (explicit systems, e.g. the stand-in test)
Needs numpy and the repo's src + external/veribench_scorer importable (as for expt_v16).
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
E08 = HERE.parent
FRACTIONS = ["f0p125", "f0p25", "f0p5", "f1p0"]
PERCENT = {"f0p125": "12.5%", "f0p25": "25%", "f0p5": "50%", "f1p0": "100%"}
SEEDS = (20260830, 20260831)
RUNGS = {f: [f"v27_{f}_s{s}" for s in SEEDS] for f in FRACTIONS[:3]}
RUNGS["f1p0"] = [f"v16_v4_{s}" for s in SEEDS]
SNAP = {f: f"sft_1p7B_{f}" for f in FRACTIONS}
# Measured 100% seed spread of the v4 recipe (expt_v16): 58 vs 52 of 1,080 cells; 24 vs 18 of 135 tasks.
BAR_PASS1, BAR_PASS8 = 6 / 1080, 6 / 135
# Experiment 17's corrected budget-and-scale curve fit on the <=50% ladder rungs of all sizes (rl4cv.utility_model,
# BUDGET_SCALE_ONLY): U = b0 + bN * log(N/1.7)/log(4/1.7) + bC * C/(C + C0); Base 1.7B validation pass rate is 0.
E17_BETA, E17_C0 = (-0.05764724, 0.02252774, 0.1284338), 1.442549
BUDGET_M = {"f0p125": 0.720775, "f0p25": 1.442549, "f0p5": 2.884708, "f1p0": 5.752936}
STEPS = [("f0p125", "f0p25"), ("f0p25", "f0p5"), ("f0p5", "f1p0"), ("f0p125", "f1p0")]


def e17_prediction(fraction, scale=1.7):
    c = BUDGET_M[fraction]
    x_n = math.log(scale / 1.7) / math.log(4.0 / 1.7)
    return E17_BETA[0] + E17_BETA[1] * x_n + E17_BETA[2] * c / (c + E17_C0)


def ci(x):
    return [float(v) for v in np.quantile(x, [0.025, 0.975])]


def stats(m, draws):
    s = dict(successes=int(m.sum()), cells=int(m.size), pass_at_1=float(m.mean()), pass_at_1_ci95=ci(m.mean(1)[draws].mean(1)))
    if m.shape[1] == 8:
        solved = (m.max(1) > 0).astype(float)
        s.update(pass_at_8_tasks=int(solved.sum()), pass_at_8=float(solved.mean()), pass_at_8_ci95=ci(solved[draws].mean(1)))
    return s


def rung_vectors(mats, labels):
    """Per-task pooled pass@1 (all samples of all seeds) and seed-mean pass@8 (mean over seeds of solved-in-8)."""
    pooled = np.concatenate([mats[x] for x in labels], axis=1)
    solved = np.mean([(mats[x].max(1) > 0).astype(float) for x in labels], axis=0)
    return pooled.mean(1), solved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v27-root", type=Path, help="extracted expt_v27_results.tgz (gen/<label>/raw.jsonl, score/<label>/scores)")
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
        for label in RUNGS["f1p0"]:
            systems[label] = (label, a.v16_data / label / "raw.jsonl", a.v16_data / label / "scores")
    if a.v27_root:
        for f in FRACTIONS[:3]:
            for label in RUNGS[f]:
                systems[label] = (label, a.v27_root / "gen" / label / "raw.jsonl", a.v27_root / "score" / label / "scores")
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
                   finish_reason_length=sum(r.get("finish_reason") == "length" for r in raw),
                   mean_generated_tokens=float(np.mean([r["generated_tokens"] for r in raw])))
        summary[name] = res
    for f, label in SNAP.items():
        rows = list(csv.DictReader((E08 / f"expt_v1/results/ladder/{label}_validation_cells.csv").open()))
        idx = {(r["task_id"], int(r["sample_idx"])): float(r["kernel_binary"] or 0) for r in rows}
        mats[label] = np.array([[idx[(t, k)] for k in range(8)] for t in ids])
        summary[label] = dict(stats(mats[label], draws), source=f"expt_v1/results/ladder/{label}_validation_cells.csv (kernel_binary)")

    rungs, vec = {}, {}
    for f in FRACTIONS:
        have = [x for x in RUNGS[f] if x in mats]
        if len(have) != 2:
            rungs[f] = dict(complete=False, seeds_present=have)
            continue
        p1, s8 = rung_vectors(mats, have)
        vec[f] = (p1, s8)
        a1 = [summary[x]["pass_at_1"] for x in have]
        a8 = [summary[x]["pass_at_8"] for x in have]
        pred = e17_prediction(f)
        rungs[f] = dict(complete=True, seeds=have, pass_at_1_pooled=float(p1.mean()), pass_at_1_pooled_ci95=ci(p1[draws].mean(1)),
            pass_at_8_seed_mean=float(s8.mean()), pass_at_8_seed_mean_ci95=ci(s8[draws].mean(1)),
            pass_at_1_by_seed=a1, pass_at_8_by_seed=a8, seed_spread_pass_at_1=float(abs(a1[0] - a1[1])),
            seed_spread_pass_at_8=float(abs(a8[0] - a8[1])),
            e17_prediction_raw=pred, e17_prediction_floored=max(pred, 0.0))
        r = rungs[f]
        d = p1 - r["e17_prediction_floored"]
        r.update(observed_minus_e17=float(d.mean()), observed_minus_e17_ci95=ci(d[draws].mean(1)),
                 e17_inside_ci=r["pass_at_1_pooled_ci95"][0] <= r["e17_prediction_floored"] <= r["pass_at_1_pooled_ci95"][1])
        snap = mats[SNAP[f]].mean(1)
        dd = p1 - snap
        r.update(minus_snap_ladder_rung=float(dd.mean()), minus_snap_ladder_rung_ci95=ci(dd[draws].mean(1)))
    done = [f for f in FRACTIONS if f in vec]
    e17 = dict(rungs=done, rmse_pp=100 * float(np.sqrt(np.mean([rungs[f]["observed_minus_e17"] ** 2 for f in done]))) if done else None,
               inside_ci=sum(rungs[f]["e17_inside_ci"] for f in done),
               curve=f"U = {E17_BETA[0]} + {E17_BETA[1]}*x_N + {E17_BETA[2]}*C/(C+{E17_C0}); 1.7B: x_N = 0; floored at 0 for pass@1")

    gains = {}
    for lo, hi in STEPS:
        if lo not in vec or hi not in vec:
            continue
        d1 = vec[hi][0] - vec[lo][0]
        d8 = vec[hi][1] - vec[lo][1]
        bar1 = max(BAR_PASS1, rungs[lo]["seed_spread_pass_at_1"], rungs[hi]["seed_spread_pass_at_1"])
        bar8 = max(BAR_PASS8, rungs[lo]["seed_spread_pass_at_8"], rungs[hi]["seed_spread_pass_at_8"])
        g = dict(pass_at_1_gain=float(d1.mean()), pass_at_1_gain_ci95=ci(d1[draws].mean(1)), pass_at_1_bar=bar1,
                 pass_at_8_gain=float(d8.mean()), pass_at_8_gain_ci95=ci(d8[draws].mean(1)), pass_at_8_bar=bar8,
                 e17_predicted_gain=rungs[hi]["e17_prediction_floored"] - rungs[lo]["e17_prediction_floored"])
        g["observed_minus_e17_gain"] = g["pass_at_1_gain"] - g["e17_predicted_gain"]
        for k in ("pass_at_1", "pass_at_8"):
            above, excl = g[f"{k}_gain"] > g[f"{k}_bar"], g[f"{k}_gain_ci95"][0] > 0
            g[f"{k}_verdict"] = "data effect" if above and excl else "not distinguishable from seed noise"
        gains[f"{PERCENT[lo]} -> {PERCENT[hi]}"] = g

    out = dict(summary=summary, rungs=rungs, gains=gains, e17=e17, missing=missing,
               bars=dict(pass_at_1=BAR_PASS1, pass_at_8=BAR_PASS8, source="expt_v16 100% seed spread; raised to a rung's own spread if larger"),
               bootstrap="task resampling, 10,000 draws, numpy seed 0", test_split_opened=False,
               metric="per-attempt binary success: kernel_binary with the inherited non-vacuity gate (expt_v6/analyze.evaluate)")
    (a.out / "summary_v27.json").write_text(json.dumps(out, indent=2) + "\n")
    pct = lambda v: f"{100 * v:.2f}%"
    pts = lambda v: f"{100 * v:+.2f}"
    rng = lambda v: f"[{pct(v[0])}, {pct(v[1])}]"
    rngp = lambda v: f"[{pts(v[0])}, {pts(v[1])}]"
    lines = ["| System | Successes / cells | pass@1 [95% CI] | pass@8 tasks / 135 [95% CI] | length-capped | mean tokens |",
             "|---|---|---|---|---|---|"]
    for f in FRACTIONS:
        for k in RUNGS[f] + [SNAP[f]]:
            if k not in summary:
                continue
            s = summary[k]
            p8 = f"{s['pass_at_8_tasks']} ({pct(s['pass_at_8'])}) {rng(s['pass_at_8_ci95'])}"
            cap = s.get("finish_reason_length", "-")
            tok = f"{s['mean_generated_tokens']:.0f}" if "mean_generated_tokens" in s else "-"
            lines.append(f"| {PERCENT[f]} {k} | {s['successes']} / {s['cells']} | {pct(s['pass_at_1'])} {rng(s['pass_at_1_ci95'])} | {p8} | {cap} | {tok} |")
    lines += ["", "| Rung | pooled pass@1 [95% CI] | seed-mean pass@8 [95% CI] | seed spread pass@1 / pass@8 | E17 (floored) | inside CI | minus SNAP ladder rung, pts [CI] |",
              "|---|---|---|---|---|---|---|"]
    for f in FRACTIONS:
        r = rungs[f]
        if not r["complete"]:
            lines.append(f"| {PERCENT[f]} | incomplete ({len(r['seeds_present'])}/2 seeds) | | | {pct(max(e17_prediction(f), 0))} | | |")
            continue
        lines.append(f"| {PERCENT[f]} | {pct(r['pass_at_1_pooled'])} {rng(r['pass_at_1_pooled_ci95'])} | {pct(r['pass_at_8_seed_mean'])} "
                     f"{rng(r['pass_at_8_seed_mean_ci95'])} | {100 * r['seed_spread_pass_at_1']:.2f} / {100 * r['seed_spread_pass_at_8']:.2f} pts "
                     f"| {pct(r['e17_prediction_floored'])} | {'yes' if r['e17_inside_ci'] else 'no'} "
                     f"| {pts(r['minus_snap_ladder_rung'])} {rngp(r['minus_snap_ladder_rung_ci95'])} |")
    lines += ["", "| Step | pass@1 gain, pts [95% CI] (bar) | verdict | pass@8 gain, pts [95% CI] (bar) | verdict | E17 predicted gain | observed - E17 |",
              "|---|---|---|---|---|---|---|"]
    for k, g in gains.items():
        lines.append(f"| {k} | {pts(g['pass_at_1_gain'])} {rngp(g['pass_at_1_gain_ci95'])} ({100 * g['pass_at_1_bar']:.2f}) | {g['pass_at_1_verdict']} "
                     f"| {pts(g['pass_at_8_gain'])} {rngp(g['pass_at_8_gain_ci95'])} ({100 * g['pass_at_8_bar']:.2f}) | {g['pass_at_8_verdict']} "
                     f"| {pts(g['e17_predicted_gain'])} | {pts(g['observed_minus_e17_gain'])} |")
    if e17["rungs"]:
        lines += ["", f"E17 curve over {len(e17['rungs'])} rungs: RMSE {e17['rmse_pp']:.2f} pts; prediction inside the pooled 95% CI at {e17['inside_ci']}/{len(e17['rungs'])} rungs."]
    if missing:
        lines += ["", "Missing systems: " + "; ".join(f"{k}: {v}" for k, v in missing.items())]
    (a.out / "tables_v27.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
