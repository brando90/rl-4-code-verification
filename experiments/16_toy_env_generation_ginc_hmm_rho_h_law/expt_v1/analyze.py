"""Fit the rho–H utility law (paper Eq. 7, rl4cv.utility_model) on the experiment 16 pilot and score both success tests.

Usage:
    python analyze.py --run results/pilot_v1

Test 1 (scale transfer): fit on the smaller scales, predict the largest scale's utility curves
(RMSE, pairwise rank accuracy, allocation regret), plus leave-one-scale-out.
Test 2 (environment choice): at the held-out scale, does the law's pick beat a uniformly random
candidate, the best fixed environment from the smaller scales, and simple pre-RL rules
(highest starting success, highest mixed-group share)?
Writes <run>/analysis.json and <run>/analysis.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from rl4cv.utility_model import (  # noqa: E402
    BUDGET_SCALE_ONLY,
    H_ONLY,
    RHO_H,
    RHO_ONLY,
    Observation,
    allocation_regret,
    best_training_label,
    feature_rule,
    fit_utility_model,
    fixed_label_rule,
    leave_one_scale_out,
    model_rule,
    pairwise_rank_accuracy,
    uniform_portfolio_regret,
)


def spearman(a, b) -> float:
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def load(run: Path, tag: str = ""):
    probe, rl = [], []
    for f in sorted(run.glob(f"*_probe_{tag + '_' if tag else ''}[0-9]*.jsonl")):
        probe += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    for f in sorted(run.glob(f"*_rl_{tag + '_' if tag else ''}[0-9]*.jsonl")):
        rl += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    metas = {json.loads(f.read_text())["scale"]: json.loads(f.read_text()) for f in sorted(run.glob("*_meta.json"))}
    return probe, rl, metas


def observations(probe, rl, target: str):
    pr = {(p["n_params"], p["env"]): p for p in probe}
    by = defaultdict(list)
    for r in rl:
        if r["step"] > 0:
            by[(r["n_params"], r["env"], r["tokens"])].append(r["utility"][target])
    obs, seed_gaps, excluded = [], [], set()
    for (n, env, tok), us in sorted(by.items()):
        p = pr[(n, env)]
        if p["rho"] <= 0:
            excluded.add((n, env))
            continue
        if len(us) > 1:
            seed_gaps.append(abs(us[0] - us[1]))
        obs.append(Observation(scale=n / 1e6, env=env, budget=tok / 1e3, utility=float(np.mean(us)), rho=p["rho"], H=p["H"]))
    return obs, seed_gaps, sorted(excluded), pr


def analyze_target(probe, rl, target: str) -> dict:
    obs, seed_gaps, excluded, pr = observations(probe, rl, target)
    scales = sorted({o.scale for o in obs})
    held = scales[-1]
    train = [o for o in obs if o.scale != held]
    test = [o for o in obs if o.scale == held]
    out = {"target": target, "scales_M_params": scales, "held_out_scale": held, "n_obs": len(obs),
           "excluded_rho_zero": excluded,
           "seed_gap_mean_abs": float(np.mean(seed_gaps)) if seed_gaps else None,
           "utility_sd_across_envs_at_held_max_budget": None}
    bmax = max(o.budget for o in test)
    last = [o for o in test if o.budget == bmax]
    out["utility_sd_across_envs_at_held_max_budget"] = float(np.std([o.utility for o in last]))

    fits = {}
    for fs in (RHO_H, RHO_ONLY, H_ONLY, BUDGET_SCALE_ONLY):
        m = fit_utility_model(train, fs)
        preds = [m.predict_obs(o) for o in test]
        err = np.array(preds) - np.array([o.utility for o in test])
        fits[fs.name] = {
            "rmse_pts": 100 * float(np.sqrt(np.mean(err**2))),
            "rank_accuracy": pairwise_rank_accuracy(test, preds),
            "regret_pts": 100 * allocation_regret(test, model_rule(m)),
            "coefficients": m.coefficients(),
        }
        try:
            lo = leave_one_scale_out(obs, fs)
            fits[fs.name]["loso"] = {"rmse_pts": 100 * lo.rmse, "rank_accuracy": lo.rank_accuracy, "regret_pts": 100 * lo.mean_regret}
        except ValueError as e:
            fits[fs.name]["loso"] = {"error": str(e)}
    out["fits"] = fits

    held_n = int(round(held * 1e6))
    feat_p = lambda o: pr[(held_n, o.env)]["mean_reward"]  # noqa: E731
    feat_q = lambda o: pr[(held_n, o.env)]["q_mixed_empirical"]  # noqa: E731
    label = best_training_label(train)
    out["choice"] = {
        "law_rho_H_regret_pts": fits["rho-H"]["regret_pts"],
        "uniform_random_regret_pts": 100 * uniform_portfolio_regret(test),
        "best_fixed_env_from_small_scales": label,
        "best_fixed_env_regret_pts": 100 * allocation_regret(test, fixed_label_rule(label)),
        "highest_start_success_regret_pts": 100 * allocation_regret(test, feature_rule(feat_p)),
        "highest_q_mixed_regret_pts": 100 * allocation_regret(test, feature_rule(feat_q)),
    }
    m = fit_utility_model(train, RHO_H)
    pick = max(last, key=m.predict_obs)
    best = max(last, key=lambda o: o.utility)
    out["held_scale_max_budget"] = {
        "budget_k_tokens": bmax,
        "law_pick": pick.env, "law_pick_utility_pts": 100 * pick.utility,
        "oracle_best": best.env, "oracle_utility_pts": 100 * best.utility,
        "mean_over_candidates_pts": 100 * float(np.mean([o.utility for o in last])),
        "table": sorted(([o.env, round(100 * o.utility, 2), round(100 * m.predict_obs(o), 2), round(o.rho, 1), round(o.H, 3),
                          round(pr[(held_n, o.env)]["mean_reward"], 3)] for o in last), key=lambda r: -r[1]),
    }
    corr = {}
    for s in scales:
        so = [o for o in obs if o.scale == s and o.budget == max(x.budget for x in obs if x.scale == s)]
        n = int(round(s * 1e6))
        u = [o.utility for o in so]
        corr[str(n)] = {
            "spearman_U_logrho": spearman(u, [np.log(o.rho) for o in so]),
            "spearman_U_H": spearman(u, [o.H for o in so]),
            "spearman_U_start_success": spearman(u, [pr[(n, o.env)]["mean_reward"] for o in so]),
            "mean_U_pts": 100 * float(np.mean(u)),
            "max_U_pts": 100 * float(np.max(u)),
        }
    out["per_scale_correlations_max_budget"] = corr
    return out


def to_md(res: dict, metas: dict, rl: list) -> str:
    L = []
    names = list(rl[0]["target_acc"].keys())
    start = {r["n_params"]: r["target_acc"] for r in rl if r["step"] == 0}
    L.append("| scale | params | pretrain loss | " + " | ".join(f"start greedy acc {n}" for n in names) + " |")
    L.append("|---|---|---|" + "---|" * len(names))
    for s, m in sorted(metas.items()):
        a = start.get(m["n_params"], {})
        L.append(f"| {s} | {m['n_params']:,} | {m['pretrain_final_loss_mean_last50']:.3f} | " + " | ".join(f"{a.get(n, float('nan')):.3f}" for n in names) + " |")
    env_gain = defaultdict(list)
    smax = max(r["step"] for r in rl)
    base = {(r["n_params"], r["env"], r["seed"]): r.get("env_acc") for r in rl if r["step"] == 0}
    for r in rl:
        if r["step"] == smax and r.get("env_acc") is not None:
            env_gain[r["n_params"]].append(r["env_acc"] - base[(r["n_params"], r["env"], r["seed"])])
    if env_gain:
        L.append("\nIn-environment held-out accuracy gain after the largest budget, mean over envs and seeds (pts): "
                 + ", ".join(f"{n:,} params {100*np.mean(g):+.1f}" for n, g in sorted(env_gain.items())) + ".")
    for t in res["targets"]:
        L.append(f"\n### Target {t['target']}\n")
        L.append(f"Held-out scale {t['held_out_scale']*1e6:,.0f} params; {t['n_obs']} observations; mean |seed0 − seed1| utility gap "
                 f"{100*(t['seed_gap_mean_abs'] or 0):.2f} pts; SD of utility across envs at held scale, max budget "
                 f"{100*t['utility_sd_across_envs_at_held_max_budget']:.2f} pts; excluded (ρ = 0): {t['excluded_rho_zero'] or 'none'}.\n")
        L.append("| features | RMSE (pts) | rank acc | regret (pts) | LOSO RMSE | LOSO rank acc | LOSO regret | coefficients |")
        L.append("|---|---|---|---|---|---|---|---|")
        for name, f in t["fits"].items():
            lo = f["loso"]
            co = ", ".join(f"{k}={v:+.4f}" for k, v in f["coefficients"].items())
            L.append(f"| {name} | {f['rmse_pts']:.2f} | {f['rank_accuracy']:.3f} | {f['regret_pts']:.2f} | "
                     f"{lo.get('rmse_pts', float('nan')):.2f} | {lo.get('rank_accuracy', float('nan')):.3f} | {lo.get('regret_pts', float('nan')):.2f} | {co} |")
        c = t["choice"]
        L.append("\n| choice rule at held-out scale | mean regret (pts, lower is better) |")
        L.append("|---|---|")
        L.append(f"| ρ–H law (Eq. 7) | {c['law_rho_H_regret_pts']:.2f} |")
        L.append(f"| uniform random candidate | {c['uniform_random_regret_pts']:.2f} |")
        L.append(f"| best fixed env from small scales ({c['best_fixed_env_from_small_scales']}) | {c['best_fixed_env_regret_pts']:.2f} |")
        L.append(f"| highest start success | {c['highest_start_success_regret_pts']:.2f} |")
        L.append(f"| highest mixed-group share | {c['highest_q_mixed_regret_pts']:.2f} |")
        h = t["held_scale_max_budget"]
        L.append(f"\nAt the held-out scale and the largest budget ({h['budget_k_tokens']:.1f}k generated tokens): law pick {h['law_pick']} "
                 f"({h['law_pick_utility_pts']:+.2f} pts), oracle {h['oracle_best']} ({h['oracle_utility_pts']:+.2f} pts), "
                 f"candidate mean {h['mean_over_candidates_pts']:+.2f} pts.\n")
        L.append("| env | observed U (pts) | predicted U (pts) | ρ | H | start success |")
        L.append("|---|---|---|---|---|---|")
        for r in h["table"]:
            L.append(f"| {r[0]} | {r[1]:+.2f} | {r[2]:+.2f} | {r[3]:,.0f} | {r[4]:.3f} | {r[5]:.3f} |")
        L.append("\n| scale (params) | Spearman(U, log ρ) | Spearman(U, H) | Spearman(U, start success) | mean U | max U |")
        L.append("|---|---|---|---|---|---|")
        for n, cc in t["per_scale_correlations_max_budget"].items():
            L.append(f"| {int(n):,} | {cc['spearman_U_logrho']:+.2f} | {cc['spearman_U_H']:+.2f} | {cc['spearman_U_start_success']:+.2f} | {cc['mean_U_pts']:+.2f} | {cc['max_U_pts']:+.2f} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--tag", default="", help="'' for pilot v1 files, 'v2' for the v2 target files")
    args = ap.parse_args()
    probe, rl, metas = load(args.run, args.tag)
    targets = list(rl[0]["utility"].keys())
    res = {"run": str(args.run.name), "targets": [analyze_target(probe, rl, t) for t in targets]}
    (args.run / f"analysis{('_' + args.tag) if args.tag else ''}.json").write_text(json.dumps(res, indent=2) + "\n")
    md = to_md(res, metas, rl)
    (args.run / f"analysis{('_' + args.tag) if args.tag else ''}.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
