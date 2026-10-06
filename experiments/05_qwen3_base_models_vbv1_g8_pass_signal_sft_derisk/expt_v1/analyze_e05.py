"""Analyze experiment 05: per-task pass counts at G=8, mixed-group shares with intervals, verdicts and the experiment 01 comparison.

Usage (on the host that holds the scored JSONL files):

    python analyze_e05.py --task-ids task_ids_vbv1.txt --probe-ids probe_task_ids.txt \\
        --base qwen3-1.7b-base=scored_qwen3-1.7b-base_g8.jsonl ... \\
        --post-trained qwen3-1.7b-base=/lfs/.../rl4cv_e01/out/scored/scored_qwen3-1.7b_g8.jsonl ... \\
        --out-dir expt_v1/results

Statistics follow PROTOCOL.md: the unit is the task (8 samples each). Shares carry 95% Wilson intervals and a one-sided
exact binomial p-value for H0: share >= 0.05; mean pass rates carry a 95% task-bootstrap interval (10,000 resamples,
seed 0). A task with any unscored sample is unmeasured: it stays in the declared denominator and is listed, never zero.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

CORE_SPLITS = ("easy_set", "cs_set", "humaneval_set", "realcode_set", "security_set")
K = 8
THRESH_FAIL, THRESH_PASS = 0.05, 0.20  # experiment 01 gate G1, reused (PROTOCOL.md)
Z = 1.959963984540054


def split_of(tid: str) -> str:
    return tid.split("__", 1)[0]


def wilson(x: int, n: int) -> tuple[float | None, float | None]:
    if n == 0:
        return None, None
    p = x / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def binom_cdf(x: int, n: int, p: float) -> float:
    """P(X <= x) for X ~ Binomial(n, p): the one-sided exact p-value for H0: share >= p."""
    return float(sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(x + 1)))


def bootstrap_mean(vals: list[float], seed: int = 0, b: int = 10_000) -> tuple[float | None, float | None]:
    if not vals:
        return None, None
    a = np.asarray(vals, dtype=float)
    idx = np.random.default_rng(seed).integers(0, len(a), size=(b, len(a)))
    m = a[idx].mean(axis=1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def channel_value(r: dict, ch: str) -> float | None:
    if r.get("status") != "scored":
        return None
    if ch == "ic_tests":
        return r.get("IC_tests")
    return (r.get("rewards") or {}).get(ch)


def per_task(rows: list[dict], ids: list[str]) -> dict[str, dict]:
    """Per declared task: the 8 values per channel, or None when any sample is missing/unscored/unmeasured."""
    by = defaultdict(dict)
    for r in rows:
        by[r["task_id"]][int(r["sample_idx"])] = r
    out = {}
    for t in ids:
        samples = by.get(t, {})
        rec = {"n_rows": len(samples)}
        for ch in ("kernel_binary", "ic_tests", "proof_fraction"):
            vals = [channel_value(samples[k], ch) if k in samples else None for k in range(K)]
            rec[ch] = None if any(v is None for v in vals) else [float(v) for v in vals]
        out[t] = rec
    return out


def channel_stats(tasks: dict[str, dict], ch: str, subset: list[str]) -> dict:
    measured = [t for t in subset if tasks[t][ch] is not None]
    unmeasured = [t for t in subset if tasks[t][ch] is None]
    n = len(measured)
    kpos = [sum(1 for v in tasks[t][ch] if v > 0) for t in measured]
    mixed = [1 if (max(tasks[t][ch]) - min(tasks[t][ch])) > 1e-12 else 0 for t in measured]
    allpass = [1 if min(tasks[t][ch]) >= 1.0 - 1e-12 else 0 for t in measured]
    rates = [float(np.mean(tasks[t][ch])) for t in measured]
    xm, xp, xa = sum(mixed), sum(1 for k in kpos if k >= 1), sum(allpass)
    return {
        "tasks_declared": len(subset),
        "tasks_measured": n,
        "tasks_unmeasured": unmeasured,
        "pass_count_histogram": {str(k): c for k, c in sorted(Counter(kpos).items())},
        "mixed_groups": xm,
        "mixed_share": xm / n if n else None,
        "mixed_share_wilson95": wilson(xm, n),
        "mixed_share_p_one_sided_vs_0.05": binom_cdf(xm, n, THRESH_FAIL) if n else None,
        "pass_at_8_tasks": xp,
        "pass_at_8_share": xp / n if n else None,
        "pass_at_8_wilson95": wilson(xp, n),
        "all_pass_tasks": xa,
        "all_pass_share": xa / n if n else None,
        "all_pass_wilson95": wilson(xa, n),
        "mean_reward": float(np.mean(rates)) if rates else None,
        "mean_reward_task_bootstrap95": bootstrap_mean(rates),
    }


def verdict(s: float | None) -> str:
    if s is None:
        return "unmeasured"
    if s < THRESH_FAIL:
        return "SFT warm start needed"
    if s >= THRESH_PASS:
        return "RL from Base viable"
    return "marginal"


def execution_stats(rows: list[dict], n_declared: int) -> dict:
    scored = [r for r in rows if r.get("status") == "scored"]
    both = [r for r in scored if (r.get("IC_tests") or 0) * (r.get("IC_proofs") or 0) > 0]
    return {
        "cells_declared": n_declared,
        "cells_present": len(rows),
        "cells_scored": len(scored),
        "cells_cut_off_at_length": sum(1 for r in rows if r.get("truncated")),
        "cells_no_lean_extracted": sum(1 for r in rows if r.get("extraction") == "no_lean_block"),
        "cells_compiling": sum(1 for r in scored if r.get("compiles")),
        "mean_generated_tokens": float(np.mean([r["generated_tokens"] for r in rows])) if rows else None,
        "IC_tests_mean": float(np.mean([r.get("IC_tests") or 0.0 for r in scored])) if scored else None,
        "IC_proofs_mean": float(np.mean([r.get("IC_proofs") or 0.0 for r in scored])) if scored else None,
        "SCSC": "exact 0.0 on every scored cell" if not both else "unmeasured on the listed cells (FSC not judged)",
        "cells_ic_tests_x_ic_proofs_positive_fsc_unmeasured": [f"{r['task_id']}#s{r['sample_idx']}" for r in both],
    }


def paired(base: dict[str, dict], post: dict[str, dict], ids: list[str], seed: int = 0, b: int = 10_000) -> dict:
    both = [t for t in ids if base[t]["kernel_binary"] is not None and post[t]["kernel_binary"] is not None]
    mb = np.array([1 if max(base[t]["kernel_binary"]) != min(base[t]["kernel_binary"]) else 0 for t in both])
    mp = np.array([1 if max(post[t]["kernel_binary"]) != min(post[t]["kernel_binary"]) else 0 for t in both])
    n = len(both)
    if n == 0:
        return {"tasks": 0}
    d = mb - mp
    idx = np.random.default_rng(seed).integers(0, n, size=(b, n))
    boots = d[idx].mean(axis=1)
    b01, b10 = int(((mb == 1) & (mp == 0)).sum()), int(((mb == 0) & (mp == 1)).sum())
    m = b01 + b10
    p = 1.0 if m == 0 else min(1.0, 2 * binom_cdf(min(b01, b10), m, 0.5))
    return {
        "tasks": n,
        "mixed_share_base": float(mb.mean()),
        "mixed_share_post_trained": float(mp.mean()),
        "difference_base_minus_post": float(d.mean()),
        "difference_paired_task_bootstrap95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
        "discordant_base_only": b01,
        "discordant_post_only": b10,
        "p_exact_mcnemar_two_sided": p,
    }


def fmt_ci(x, ci, digits=3):
    if x is None:
        return "unmeasured"
    lo, hi = ci
    return f"{x:.{digits}f} [{lo:.{digits}f}, {hi:.{digits}f}]"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--task-ids", required=True, type=Path)
    ap.add_argument("--probe-ids", required=True, type=Path)
    ap.add_argument("--base", nargs="+", required=True, help="label=scored.jsonl for each Base model")
    ap.add_argument("--post-trained", nargs="*", default=[], help="label=scored.jsonl (experiment 01 G=8 probe) keyed by the Base label")
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args(argv)

    ids = [l.strip() for l in args.task_ids.read_text().splitlines() if l.strip() and not l.startswith("#")]
    probe = [l.strip() for l in args.probe_ids.read_text().splitlines() if l.strip()]
    subsets = {"all_896": ids, "core_614": [t for t in ids if split_of(t) in CORE_SPLITS],
               "industry_282": [t for t in ids if split_of(t) not in CORE_SPLITS]}
    post = dict(a.split("=", 1) for a in args.post_trained)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    report = {"condition": "rl4cv-e05-qwen3-base-vbv1-g8-v1", "thresholds": {"fail_below": THRESH_FAIL, "pass_at_or_above": THRESH_PASS,
              "source": "experiment 01 PROTOCOL.md gate G1, reused by experiment 05 PROTOCOL.md"}, "models": {}}
    md = ["| Model | Tasks measured | Mixed share `kernel_binary` [95% Wilson] | p (H0 ≥ 0.05) | pass@8 share | all-pass share | Mean pass rate [95% bootstrap] | Mixed share `ic_tests` | Verdict |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for spec in args.base:
        label, path = spec.split("=", 1)
        rows = load(Path(path))
        tasks = per_task(rows, ids)
        m = {"scored_path": path, "execution": execution_stats(rows, len(ids) * K), "channels": {}}
        for ch in ("kernel_binary", "ic_tests", "proof_fraction"):
            m["channels"][ch] = {name: channel_stats(tasks, ch, sub) for name, sub in subsets.items()}
        kb = m["channels"]["kernel_binary"]["all_896"]
        m["verdict"] = verdict(kb["mixed_share"])
        if label in post:
            ptasks = per_task(load(Path(post[label])), probe)
            m["paired_vs_post_trained_on_e01_probe_128"] = {"post_trained_scored_path": post[label],
                                                            **paired({t: tasks[t] for t in probe}, ptasks, probe)}
        report["models"][label] = m
        ic = m["channels"]["ic_tests"]["all_896"]
        p = kb["mixed_share_p_one_sided_vs_0.05"]
        md.append(f"| {label} | {kb['tasks_measured']}/{kb['tasks_declared']} | {fmt_ci(kb['mixed_share'], kb['mixed_share_wilson95'])} | "
                  f"{'n/a' if p is None else f'{p:.2g}'} | {fmt_ci(kb['pass_at_8_share'], kb['pass_at_8_wilson95'])} | "
                  f"{fmt_ci(kb['all_pass_share'], kb['all_pass_wilson95'])} | {fmt_ci(kb['mean_reward'], kb['mean_reward_task_bootstrap95'], 4)} | "
                  f"{fmt_ci(ic['mixed_share'], ic['mixed_share_wilson95'])} | **{m['verdict']}** |")
        with (args.out_dir / f"per_task_{label}_g8.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["task_id", "split", "core", "samples_present", "k_kernel_binary", "k_ic_tests", "mean_proof_fraction"])
            for t in ids:
                rec = tasks[t]
                k = lambda ch: "" if rec[ch] is None else sum(1 for v in rec[ch] if v > 0)
                pf = "" if rec["proof_fraction"] is None else f"{np.mean(rec['proof_fraction']):.4f}"
                w.writerow([t, split_of(t), int(split_of(t) in CORE_SPLITS), rec["n_rows"], k("kernel_binary"), k("ic_tests"), pf])

    (args.out_dir / "analysis_e05.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "analysis_e05_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
