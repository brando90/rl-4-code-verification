"""Score the known-MDP sanity run (expt_v3) against PROTOCOL.md: gate, rho/H separation, T1, T2, oracle agreement.

    python analyze_mdp.py --run results/mdp_v1   # writes analysis_mdp.json and analysis_mdp.md in the run folder
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
    model_rule,
    pairwise_rank_accuracy,
    uniform_portfolio_regret,
)


def spearman(a, b) -> float:
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def load(run: Path):
    probe = [json.loads(x) for f in sorted(run.glob("probe_*.jsonl")) for x in f.read_text().splitlines() if x.strip()]
    rl = [json.loads(x) for f in sorted(run.glob("rl_*.jsonl")) for x in f.read_text().splitlines() if x.strip()]
    return probe, rl, json.loads((run / "meta.json").read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/mdp_v1")
    run = HERE / ap.parse_args().run
    probe, rl, meta = load(run)
    pr = {(p["n_params"], p["env"]): p for p in probe}
    by, orc = defaultdict(list), defaultdict(list)
    for r in rl:
        by[(r["n_params"], r["env"], r["budget"])].append(r["utility"])
        if r["budget"] == max(meta["budgets"]):
            orc[(r["n_params"], r["env"])].append(r["oracle_exact_grad_utility"])
    obs, excluded = [], set()
    for (n, env, b), us in sorted(by.items()):
        p = pr[(n, env)]
        if p["rho"] <= 0:
            excluded.add((n, env))
            continue
        obs.append(Observation(scale=n / 1e6, env=env, budget=b / 1e3, utility=float(np.mean(us)), rho=p["rho"], H=p["H"]))
    scales = sorted({o.scale for o in obs})
    held = scales[-1]
    held_n = int(round(held * 1e6))
    train = [o for o in obs if o.scale != held]
    test = [o for o in obs if o.scale == held]
    bmax = max(o.budget for o in test)
    last = [o for o in test if o.budget == bmax]
    res = {"n_obs": len(obs), "excluded_rho_zero": sorted(map(list, excluded)), "held_out_n_params": held_n}

    # gate and separation
    res["gate_positive_n4_max_budget"] = sum(o.utility > 0 for o in last)
    res["gate_pass"] = res["gate_positive_n4_max_budget"] >= 3
    lr_all = [np.log(p["rho"]) for p in probe if p["rho"] > 0]
    h_all = [p["H"] for p in probe if p["rho"] > 0]
    res["corr_logrho_H_all_probes"] = float(np.corrcoef(lr_all, h_all)[0, 1])
    res["corr_logrho_H_by_scale"] = {}
    for s in scales:
        ps = [p for p in probe if p["n_params"] == int(round(s * 1e6)) and p["rho"] > 0]
        res["corr_logrho_H_by_scale"][str(int(round(s * 1e6)))] = float(np.corrcoef([np.log(p["rho"]) for p in ps], [p["H"] for p in ps])[0, 1])
    res["separation_pass"] = abs(res["corr_logrho_H_all_probes"]) < 0.85
    res["positive_cells"] = f"{sum(o.utility > 0 for o in obs)}/{len(obs)}"

    # T1 / T2
    fits = {}
    for fs in (RHO_H, RHO_ONLY, H_ONLY, BUDGET_SCALE_ONLY):
        m = fit_utility_model(train, fs)
        preds = [m.predict_obs(o) for o in test]
        err = np.array(preds) - np.array([o.utility for o in test])
        fits[fs.name] = {"rmse_pts": 100 * float(np.sqrt(np.mean(err**2))), "rank_accuracy": pairwise_rank_accuracy(test, preds),
                         "regret_pts": 100 * allocation_regret(test, model_rule(m)), "coefficients": m.coefficients()}
    res["fits"] = fits
    label = best_training_label(train)
    feat_p = lambda o: pr[(held_n, o.env)]["mean_reward"]  # noqa: E731
    feat_q = lambda o: pr[(held_n, o.env)]["q_mixed_empirical"]  # noqa: E731
    oracle_u = {env: float(np.mean(orc[(held_n, env)])) for (n, env) in orc if n == held_n}
    choice = {
        "rho-H law": fits["rho-H"]["regret_pts"],
        "rho-only": fits["rho-only"]["regret_pts"],
        "H-only": fits["H-only"]["regret_pts"],
        "uniform random": 100 * uniform_portfolio_regret(test),
        f"best fixed from n1-n3 ({label})": 100 * allocation_regret(test, fixed_label_rule(label)),
        "highest start success": 100 * allocation_regret(test, feature_rule(feat_p)),
        "highest mixed-group share": 100 * allocation_regret(test, feature_rule(feat_q)),
        "exact-gradient oracle": 100 * allocation_regret(test, feature_rule(lambda o: oracle_u[o.env])),
    }
    res["choice_regret_pts"] = choice
    t1 = fits["rho-H"]["rmse_pts"] < fits["budget-scale-only"]["rmse_pts"] and fits["rho-H"]["rank_accuracy"] > fits["budget-scale-only"]["rank_accuracy"]
    law = choice["rho-H law"]
    base_keys = [k for k in choice if k.startswith(("best fixed", "highest"))]
    t2_random = law < choice["uniform random"]
    t2_all = t2_random and all(law < choice[k] for k in base_keys)
    res["T1"], res["T2_beats_random"], res["T2_beats_all_baselines"] = t1, t2_random, t2_all
    if not res["gate_pass"]:
        verdict = "NOT YET MEANINGFUL"
    elif t1 and t2_all:
        verdict = "SUCCESS"
    elif t2_random:
        verdict = "CHOICE ONLY"
    else:
        verdict = "NO ADVANTAGE"
    res["verdict"] = verdict

    # n4 table at the largest budget, seed spread, oracle agreement
    m = fit_utility_model(train, RHO_H)
    seeds = {env: by[(held_n, env, int(bmax * 1e3))] for env in (o.env for o in last)}
    pick = max(last, key=m.predict_obs)
    best = max(last, key=lambda o: o.utility)
    res["n4_max_budget"] = {
        "budget_k_tokens": bmax, "law_pick": pick.env, "law_pick_utility_pts": 100 * pick.utility,
        "law_pick_seed_sd_pts": 100 * float(np.std(seeds[pick.env], ddof=1)),
        "observed_best": best.env, "observed_best_utility_pts": 100 * best.utility,
        "oracle_pick": max(oracle_u, key=oracle_u.get),
        "mean_over_candidates_pts": 100 * float(np.mean([o.utility for o in last])),
        "spearman_law_vs_oracle": spearman([m.predict_obs(o) for o in last], [oracle_u[o.env] for o in last]),
        "spearman_observed_vs_oracle": spearman([o.utility for o in last], [oracle_u[o.env] for o in last]),
        "spearman_law_vs_observed": spearman([m.predict_obs(o) for o in last], [o.utility for o in last]),
        "spearman_observed_vs_logrho": spearman([o.utility for o in last], [np.log(o.rho) for o in last]),
        "spearman_observed_vs_H": spearman([o.utility for o in last], [o.H for o in last]),
        "table": sorted(([o.env, round(100 * o.utility, 2), round(100 * float(np.std(seeds[o.env], ddof=1)), 2), round(100 * m.predict_obs(o), 2),
                          round(100 * oracle_u[o.env], 2), round(o.rho), round(o.H, 3), round(pr[(held_n, o.env)]["success_rate"], 3),
                          round(pr[(held_n, o.env)]["admission_rate"], 3)] for o in last), key=lambda r: -r[1]),
    }
    noisy = [o for o in last if "_sg0.5" in o.env]
    clean = [o for o in last if "_sg0.0" in o.env]
    res["noise_trap"] = {"mean_logrho_noisy_minus_clean": float(np.mean([np.log(o.rho) for o in noisy]) - np.mean([np.log(o.rho) for o in clean])),
                         "mean_U_noisy_pts": 100 * float(np.mean([o.utility for o in noisy])), "mean_U_clean_pts": 100 * float(np.mean([o.utility for o in clean])),
                         "mean_pred_noisy_pts": 100 * float(np.mean([m.predict_obs(o) for o in noisy])), "mean_pred_clean_pts": 100 * float(np.mean([m.predict_obs(o) for o in clean]))}
    res["start_policies"] = meta["scales"]
    (run / "analysis_mdp.json").write_text(json.dumps(res, indent=1))
    (run / "analysis_mdp.md").write_text(to_md(res))
    print(to_md(res))
    return 0


def to_md(r: dict) -> str:
    n4 = r["n4_max_budget"]
    L = [f"# expt_v3 known-MDP sanity: verdict {r['verdict']}", "",
         f"Gate: {r['gate_positive_n4_max_budget']} of 22 candidates positive at n4, {n4['budget_k_tokens']:.1f}k tokens ({'pass' if r['gate_pass'] else 'fail'}). "
         f"Positive cells overall: {r['positive_cells']}.",
         f"corr(log rho, H) over all probes: {r['corr_logrho_H_all_probes']:.3f} ({'separated' if r['separation_pass'] else 'collinear'}); by scale: "
         + ", ".join(f"{k}: {v:.3f}" for k, v in r["corr_logrho_H_by_scale"].items()), "",
         "| features | RMSE at n4 (pts) | rank acc | regret (pts) |", "|---|---|---|---|"]
    for k, v in r["fits"].items():
        L.append(f"| {k} | {v['rmse_pts']:.2f} | {v['rank_accuracy']:.3f} | {v['regret_pts']:.2f} |")
    L += ["", "| choice rule at n4 | mean regret (pts) |", "|---|---|"]
    L += [f"| {k} | {v:.2f} |" for k, v in r["choice_regret_pts"].items()]
    L += ["", f"Law pick {n4['law_pick']}: {n4['law_pick_utility_pts']:+.2f} pts (5-seed SD {n4['law_pick_seed_sd_pts']:.2f}); observed best {n4['observed_best']} "
          f"{n4['observed_best_utility_pts']:+.2f}; oracle pick {n4['oracle_pick']}; mean over candidates {n4['mean_over_candidates_pts']:+.2f}.",
          f"Spearman at n4: law vs observed {n4['spearman_law_vs_observed']:.2f}, law vs oracle {n4['spearman_law_vs_oracle']:.2f}, observed vs oracle {n4['spearman_observed_vs_oracle']:.2f}, "
          f"observed vs log rho {n4['spearman_observed_vs_logrho']:.2f}, observed vs H {n4['spearman_observed_vs_H']:.2f}.",
          f"Noise trap: noisy candidates have log rho {r['noise_trap']['mean_logrho_noisy_minus_clean']:+.2f} vs clean; observed U {r['noise_trap']['mean_U_noisy_pts']:+.2f} vs {r['noise_trap']['mean_U_clean_pts']:+.2f} pts; "
          f"law predicts {r['noise_trap']['mean_pred_noisy_pts']:+.2f} vs {r['noise_trap']['mean_pred_clean_pts']:+.2f}.", "",
          "| env | observed U (pts) | seed SD | law pred | exact-grad oracle U | rho | H | start success | admitted |", "|---|---|---|---|---|---|---|---|---|"]
    L += ["| " + " | ".join(str(x) for x in row) + " |" for row in n4["table"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
