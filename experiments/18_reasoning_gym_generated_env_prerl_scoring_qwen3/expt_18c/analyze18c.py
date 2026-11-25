"""Experiment 18c analysis: the 18b frozen analysis on 3 seeds of token-matched runs, plus the token-confound check (numpy only).

    python analyze18c.py --root $B/results --out $B/results/results_18c.json [--md results_18c_table.md]

Reads <root>/eval_pre.json, <root>/post/post_<run>.json and <root>/train/<run>.train_summary.json for every run (env x seed in 0,1,2), the
frozen forecasts_18c.json (identical to forecasts_18b.json) and, for the 18b cross-check, ../expt_18b/results/results_18b.json.
Primary: Spearman of the frozen rho_h forecast vs the 3-seed mean held-out gain (18b's `analyze`, unchanged). Added: 3-seed reliability,
the length-vs-gain Spearman (18b: +0.606), matched-only subset, cross-check with 18b.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18c as K18C  # noqa: E402

K = K18C.K
sys.path.insert(0, str(K18C.B18))
import analyze as A  # noqa: E402  (18b analysis, unchanged)

A.K.SEEDS = K18C.SEEDS  # analyze.py reads K.SEEDS at call time: 3 seeds
K.SEEDS = K18C.SEEDS

B18_RESULTS = K18C.B18 / "results" / "results_18b.json"
LENGTH_SPEARMAN_18B = 0.606  # 18b descriptive check: mean training response tokens vs gain (results_18b.md)


def reliability3(gains_by_seed: list[list[float]]) -> dict:
    """Mean pairwise seed-seed Spearman r over environments; Spearman-Brown reliability of the 3-seed mean 3r/(1+2r)."""
    rs = [A.spearman(gains_by_seed[i], gains_by_seed[j]) for i in range(len(gains_by_seed)) for j in range(i + 1, len(gains_by_seed))]
    r = float(np.mean(rs))
    rel = 3 * r / (1 + 2 * r) if r > -0.5 else float("nan")
    return {"pairwise_seed_spearman": rs, "mean_pairwise": r, "reliability_3seed": rel,
            "max_forecast_spearman": math.sqrt(max(rel, 0.0)) if not math.isnan(rel) else float("nan")}


def load_train(root: Path, envs: list[str]) -> dict:
    out = {}
    for e in envs:
        for s in K18C.SEEDS:
            p = root / "train" / f"{K.run_name(e, s)}.train_summary.json"
            if p.exists():
                j = json.loads(p.read_text())
                out[(e, s)] = {"steps": j["steps"], "tokens": j["response_tokens"], "rollouts": j["rollouts"], "stop": j["stop_reason"],
                               "run_class": j["run_class"], "distinct": j.get("distinct_questions_used"), "seconds": j["seconds"],
                               "len_per_rollout": j["response_tokens"] / j["rollouts"]}
    return out


def confound(envs: list[str], runs: dict, tr: dict) -> dict:
    used = [e for e in envs if any((e, s) in runs and (e, s) in tr for s in K18C.SEEDS)]
    g = np.array([np.mean([runs[(e, s)]["gain"] for s in K18C.SEEDS if (e, s) in runs]) for e in used])
    L = np.array([np.mean([tr[(e, s)]["len_per_rollout"] for s in K18C.SEEDS if (e, s) in tr]) for e in used])
    T = np.array([np.mean([tr[(e, s)]["tokens"] for s in K18C.SEEDS if (e, s) in tr]) for e in used])
    rng = np.random.default_rng(0)
    bl = []
    for _ in range(10_000):
        ix = rng.integers(0, len(used), len(used))
        bl.append(A.spearman(L[ix], g[ix]))
    return {"n_envs": len(used), "spearman_length_vs_gain": A.spearman(L, g), "spearman_length_vs_gain_ci95": A.pct_ci(bl),
            "spearman_total_tokens_vs_gain": A.spearman(T, g), "length_spearman_18b": LENGTH_SPEARMAN_18B,
            "classes": {c: sum(1 for v in tr.values() if v["run_class"] == c) for c in ("matched", "overshoot", "budget_limited")},
            "mean_total_tokens": float(np.mean([v["tokens"] for v in tr.values()])) if tr else None,
            "min_total_tokens": min((v["tokens"] for v in tr.values()), default=None),
            "max_total_tokens": max((v["tokens"] for v in tr.values()), default=None)}


def matched_subset(envs: list[str], fdoc: dict, runs: dict, tr: dict) -> dict:
    ok = [e for e in envs if all((e, s) in tr and tr[(e, s)]["run_class"] == "matched" and (e, s) in runs for s in K18C.SEEDS)]
    if len(ok) < 4:
        return {"n_envs": len(ok), "note": "fewer than 4 fully matched environments"}
    res = A.analyze(ok, fdoc["forecasts"], runs, fdoc["primary"], fdoc["secondary"], 2000)
    return {"n_envs": len(ok), "forecasts": {n: {k: r[k] for k in ("spearman", "spearman_ci95", "regret_top1", "pick")} for n, r in res["forecasts"].items()},
            "random_expected_regret_top1": res["random_expected_regret_top1"]}


def cross_18b(envs: list[str], runs: dict) -> dict:
    if not B18_RESULTS.exists():
        return {"note": "results_18b.json not found"}
    old = json.loads(B18_RESULTS.read_text())["env_gain"]
    new = {e: float(np.mean([runs[(e, s)]["gain"] for s in K18C.SEEDS if (e, s) in runs])) for e in envs if any((e, s) in runs for s in K18C.SEEDS)}
    used = [e for e in envs if e in new and e in old]
    return {"n_envs": len(used), "spearman_18c_vs_18b_env_gain": A.spearman([new[e] for e in used], [old[e] for e in used]),
            "mean_gain_18c": float(np.mean([new[e] for e in used])), "mean_gain_18b": float(np.mean([old[e] for e in used]))}


def render(res: dict, sec: list[dict]) -> str:
    f = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.3f}"
    lines = [A.render_md(res, sec), "## Token-confound check", ""]
    c = res["confound"]
    lines.append(f"- Spearman of mean response length per rollout vs 3-seed gain: {f(c['spearman_length_vs_gain'])} {c['spearman_length_vs_gain_ci95']} "
                 f"(18b: {f(c['length_spearman_18b'])}); total tokens vs gain {f(c['spearman_total_tokens_vs_gain'])}.")
    lines.append(f"- Run classes: {c['classes']}; realised tokens per run min {c['min_total_tokens']}, mean {c['mean_total_tokens']}, max {c['max_total_tokens']}.")
    r = res.get("reliability_3seed")
    if r:
        lines.append(f"- 3-seed reliability {f(r['reliability_3seed'])} (mean pairwise seed Spearman {f(r['mean_pairwise'])}); max forecast Spearman about {f(r['max_forecast_spearman'])}.")
    lines.append(f"- Cross-check with 18b: {res['cross_18b']}")
    lines.append(f"- Fully matched subset: {json.dumps(res['matched_subset'])[:1500]}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md")
    ap.add_argument("--n-boot", type=int, default=A.N_BOOT)
    args = ap.parse_args(argv)
    from rl4cv.forecast import verify_forecast

    if not verify_forecast(K18C.FORECASTS_PATH):
        raise SystemExit("forecasts_18c.json does not match its frozen sha256")
    fdoc = json.loads(K18C.FORECASTS_PATH.read_text())
    envs = fdoc["selected"]
    root = Path(args.root)
    pre, runs = A.collect(root, envs)
    tr = load_train(root, envs)
    res = A.analyze(envs, fdoc["forecasts"], runs, fdoc["primary"], fdoc["secondary"], args.n_boot)
    complete3 = [e for e in envs if all((e, s) in runs for s in K18C.SEEDS)]
    if len(complete3) >= 4:
        res["reliability_3seed"] = reliability3([[runs[(e, s)]["gain"] for e in complete3] for s in K18C.SEEDS])
    res["confound"] = confound(envs, runs, tr)
    res["matched_subset"] = matched_subset(envs, fdoc, runs, tr)
    res["cross_18b"] = cross_18b(envs, runs)
    res["runs"] = {f"{e}|{s}": {**r, **{"train": tr.get((e, s))}} for (e, s), r in runs.items()}
    res["forecasts_sha256"] = K18C.FORECASTS_PATH.with_suffix(".sha256").read_text().split()[0]
    Path(args.out).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    md = render(res, A.secondary_table(envs, runs))
    if args.md:
        Path(args.md).write_text(md, encoding="utf-8")
    print(md)
    print("ANALYZE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
