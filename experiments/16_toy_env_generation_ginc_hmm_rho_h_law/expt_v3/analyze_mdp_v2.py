"""Score the Night 3 known-MDP run (mdp_v2) against PROTOCOL.md (Night 3 addendum).

Gate, separation, T1, T2 and the verdict as in analyze_mdp.py, read at s6 with the law fit on s1-s5; plus
bootstrap intervals on allocation regret (resampling start-policy repeats and seeds) and the noise-free
rho/H diagnostic.

    python analyze_mdp_v2.py --run results/mdp_v2 [--boot 2000]
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

SCALE_ORDER = ["s1", "s2", "s3", "s4", "s5", "s6"]
HELD = "s6"


def spearman(a, b) -> float:
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def load(run: Path):
    rows = lambda pat: [json.loads(x) for f in sorted(run.glob(pat)) for x in f.read_text().splitlines() if x.strip()]  # noqa: E731
    starts = [json.loads(f.read_text()) for f in sorted(run.glob("start_*.json"))]
    return rows("probe_*.jsonl"), rows("rl_*.jsonl"), starts


class Data:
    """Arrays indexed [scale][rep] -> per-candidate probe values, and [scale][rep][seed] -> utilities."""

    def __init__(self, probe, rl):
        self.envs = sorted({p["env"] for p in probe})
        self.budgets = sorted({r["budget"] for r in rl})
        self.n_params = {p["scale"]: p["n_params"] for p in probe}
        self.reps = sorted({p["rep"] for p in probe})
        self.seeds = sorted({r["seed"] for r in rl})
        self.pr = {(p["scale"], p["rep"], p["env"]): p for p in probe}
        self.u = {(r["scale"], r["rep"], r["seed"], r["env"], r["budget"]): r["utility"] for r in rl}
        self.orc = {(r["scale"], r["rep"], r["seed"], r["env"]): r["oracle_exact_grad_utility"] for r in rl if r["budget"] == self.budgets[-1]}
        missing = [(s, r, d, e, b) for s in SCALE_ORDER for r in self.reps for d in self.seeds for e in self.envs for b in self.budgets
                   if (s, r, d, e, b) not in self.u]
        if missing:
            raise SystemExit(f"{len(missing)} RL rows missing, e.g. {missing[:3]}")

    def full_draw(self):
        return {s: [(r, list(self.seeds)) for r in self.reps] for s in SCALE_ORDER}

    def random_draw(self, rng):
        return {s: [(int(r), [int(x) for x in rng.choice(self.seeds, len(self.seeds))]) for r in rng.choice(self.reps, len(self.reps))]
                for s in SCALE_ORDER}

    def cells(self, draw, noise_free=False):
        """Observations for every (scale, env, budget) under a draw of repeats and seeds; also feature lookups."""
        rk, hk = ("rho_noise_free", "H_noise_free") if noise_free else ("rho", "H")
        obs, feats = [], {}
        for s in SCALE_ORDER:
            for e in self.envs:
                ps = [self.pr[(s, r, e)] for r, _ in draw[s]]
                rho = float(np.exp(np.mean([np.log(max(p[rk], 1e-12)) for p in ps])))
                H = float(np.mean([p[hk] for p in ps]))
                feats[(s, e)] = {"rho": rho, "H": H, "mean_reward": float(np.mean([p["mean_reward"] for p in ps])),
                                 "q_mixed_empirical": float(np.mean([p["q_mixed_empirical"] for p in ps])),
                                 "success_rate": float(np.mean([p["success_rate"] for p in ps])),
                                 "admission_rate": float(np.mean([p["admission_rate"] for p in ps])),
                                 "oracle": float(np.mean([self.orc[(s, r, d, e)] for r, ds in draw[s] for d in ds]))}
                for b in self.budgets:
                    us = [self.u[(s, r, d, e, b)] for r, ds in draw[s] for d in ds]
                    obs.append(Observation(scale=self.n_params[s] / 1e6, env=e, budget=b / 1e3, utility=float(np.mean(us)), rho=rho, H=H))
        return obs, feats


def score(data: Data, draw, noise_free=False) -> dict:
    obs, feats = data.cells(draw, noise_free)
    held = data.n_params[HELD] / 1e6
    train = [o for o in obs if o.scale != held]
    test = [o for o in obs if o.scale == held]
    fits = {fs.name: fit_utility_model(train, fs) for fs in (RHO_H, RHO_ONLY, H_ONLY, BUDGET_SCALE_ONLY)}
    label = best_training_label(train)
    f = lambda key: feature_rule(lambda o: feats[(HELD, o.env)][key])  # noqa: E731
    regret = {
        "rho-H law": allocation_regret(test, model_rule(fits["rho-H"])),
        "rho-only": allocation_regret(test, model_rule(fits["rho-only"])),
        "H-only": allocation_regret(test, model_rule(fits["H-only"])),
        "uniform random": uniform_portfolio_regret(test),
        "best fixed from s1-s5": allocation_regret(test, fixed_label_rule(label)),
        "highest start success": allocation_regret(test, f("mean_reward")),
        "highest mixed-group share": allocation_regret(test, f("q_mixed_empirical")),
        "exact-gradient oracle": allocation_regret(test, f("oracle")),
    }
    return {"obs": obs, "feats": feats, "train": train, "test": test, "fits": fits, "label": label,
            "regret_pts": {k: 100 * v for k, v in regret.items()}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/mdp_v2")
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    run = HERE / args.run
    probe, rl, starts = load(run)
    data = Data(probe, rl)
    full = score(data, data.full_draw())
    obs, feats, test, fits = full["obs"], full["feats"], full["test"], full["fits"]
    bmax = max(o.budget for o in test)
    last = [o for o in test if o.budget == bmax]
    res = {"n_obs": len(obs), "n_rl_rows": len(rl), "n_probes": len(probe), "held_out": HELD, "held_out_n_params": data.n_params[HELD]}

    sv = defaultdict(list)
    for s in starts:
        sv[s["scale"]].append(s["target_value"])
    res["start_target_value"] = {s: {"n_params": data.n_params[s], "mean": float(np.mean(sv[s])), "reps": [round(v, 3) for v in sv[s]]} for s in SCALE_ORDER}

    res["gate_positive_s6_max_budget"] = sum(o.utility > 0 for o in last)
    res["gate_pass"] = res["gate_positive_s6_max_budget"] >= 3
    lr_all, h_all = [np.log(p["rho"]) for p in probe if p["rho"] > 0], [p["H"] for p in probe if p["rho"] > 0]
    res["corr_logrho_H_all_probes"] = float(np.corrcoef(lr_all, h_all)[0, 1])
    res["corr_logrho_H_noise_free"] = float(np.corrcoef([np.log(p["rho_noise_free"]) for p in probe if p["rho_noise_free"] > 0],
                                                         [p["H_noise_free"] for p in probe if p["rho_noise_free"] > 0])[0, 1])
    res["separation_pass"] = abs(res["corr_logrho_H_all_probes"]) < 0.85
    res["positive_cells"] = f"{sum(o.utility > 0 for o in obs)}/{len(obs)}"

    res["fits"] = {}
    for name, m in fits.items():
        preds = [m.predict_obs(o) for o in test]
        err = np.array(preds) - np.array([o.utility for o in test])
        res["fits"][name] = {"rmse_pts": 100 * float(np.sqrt(np.mean(err**2))), "rank_accuracy": pairwise_rank_accuracy(test, preds),
                             "coefficients": m.coefficients()}
    choice = full["regret_pts"]
    res["best_fixed_label"] = full["label"]
    res["choice_regret_pts"] = choice
    t1 = res["fits"]["rho-H"]["rmse_pts"] < res["fits"]["budget-scale-only"]["rmse_pts"] and \
        res["fits"]["rho-H"]["rank_accuracy"] > res["fits"]["budget-scale-only"]["rank_accuracy"]
    law = choice["rho-H law"]
    base_keys = ["best fixed from s1-s5", "highest start success", "highest mixed-group share"]
    t2_random = law < choice["uniform random"]
    t2_all = t2_random and all(law < choice[k] for k in base_keys)
    res["T1"], res["T2_beats_random"], res["T2_beats_all_baselines"] = t1, t2_random, t2_all
    res["verdict"] = ("NOT YET MEANINGFUL" if not res["gate_pass"] else "SUCCESS" if t1 and t2_all
                      else "CHOICE ONLY" if t2_random else "NO ADVANTAGE")

    # bootstrap
    rng = np.random.default_rng(1617)
    boot = defaultdict(list)
    for _ in range(args.boot):
        r = score(data, data.random_draw(rng))["regret_pts"]
        for k, v in r.items():
            boot[k].append(v)
    ci = lambda xs: [float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))]  # noqa: E731
    res["bootstrap"] = {"n": args.boot, "regret_ci95_pts": {k: ci(v) for k, v in boot.items()},
                        "law_minus_baseline_ci95_pts": {k: ci(np.array(boot["rho-H law"]) - np.array(v)) for k, v in boot.items() if k != "rho-H law"},
                        "share_law_lower": {k: float(np.mean(np.array(boot["rho-H law"]) < np.array(v))) for k, v in boot.items() if k != "rho-H law"}}

    # s6 table, seed/repeat spread, oracle agreement
    m = fits["rho-H"]
    runs = {e: [data.u[(HELD, r, d, e, int(bmax * 1e3))] for r in data.reps for d in data.seeds] for e in data.envs}
    rep_means = {e: [float(np.mean([data.u[(HELD, r, d, e, int(bmax * 1e3))] for d in data.seeds])) for r in data.reps] for e in data.envs}
    pick = max(last, key=m.predict_obs)
    best = max(last, key=lambda o: o.utility)
    orc = {e: feats[(HELD, e)]["oracle"] for e in data.envs}
    res["s6_max_budget"] = {
        "budget_k_tokens": bmax, "law_pick": pick.env, "law_pick_utility_pts": 100 * pick.utility,
        "law_pick_run_sd_pts": 100 * float(np.std(runs[pick.env], ddof=1)), "law_pick_repeat_means_pts": [round(100 * x, 2) for x in rep_means[pick.env]],
        "observed_best": best.env, "observed_best_utility_pts": 100 * best.utility, "oracle_pick": max(orc, key=orc.get),
        "mean_over_candidates_pts": 100 * float(np.mean([o.utility for o in last])),
        "spearman_law_vs_observed": spearman([m.predict_obs(o) for o in last], [o.utility for o in last]),
        "spearman_law_vs_oracle": spearman([m.predict_obs(o) for o in last], [orc[o.env] for o in last]),
        "spearman_observed_vs_oracle": spearman([o.utility for o in last], [orc[o.env] for o in last]),
        "table": sorted(([o.env, round(100 * o.utility, 2), round(100 * float(np.std(runs[o.env], ddof=1)), 2), round(100 * m.predict_obs(o), 2),
                          round(100 * orc[o.env], 2), round(o.rho), round(feats[(HELD, o.env)].get("rho_nf", 0)), round(o.H, 3),
                          round(feats[(HELD, o.env)]["success_rate"], 3)] for o in last), key=lambda r: -r[1]),
    }

    # noise-free diagnostic: same fitted law, noise-free features at s6
    _, feats_nf = data.cells(data.full_draw(), noise_free=True)
    rows, err_std, err_nf = [], [], []
    for o in last:
        nf = feats_nf[(HELD, o.env)]
        p_std = m.predict(o.scale, o.budget, o.rho, o.H)
        p_nf = m.predict(o.scale, o.budget, nf["rho"], nf["H"])
        rows.append({"env": o.env, "rho": o.rho, "rho_noise_free": nf["rho"], "rho_ratio": o.rho / nf["rho"], "H": o.H, "H_noise_free": nf["H"],
                     "pred_std_pts": 100 * p_std, "pred_noise_free_pts": 100 * p_nf, "observed_pts": 100 * o.utility})
        if "_sg0.5" in o.env:
            err_std.append(abs(p_std - o.utility))
            err_nf.append(abs(p_nf - o.utility))
    for r in res["s6_max_budget"]["table"]:
        r[6] = round(feats_nf[(HELD, r[0])]["rho"])
    nf_full = score(data, data.full_draw(), noise_free=True)
    res["noise_diagnostic"] = {
        "s6_rows": rows,
        "noisy_mae_pts_standard_rho": 100 * float(np.mean(err_std)), "noisy_mae_pts_noise_free_rho": 100 * float(np.mean(err_nf)),
        "mean_rho_ratio_noisy": float(np.exp(np.mean([np.log(r["rho_ratio"]) for r in rows if "_sg0.5" in r["env"]]))),
        "diagnostic_law_fit_on_noise_free_regret_pts": nf_full["regret_pts"]["rho-H law"],
        "diagnostic_law_fit_on_noise_free_pick": max([o for o in nf_full["test"] if o.budget == bmax], key=nf_full["fits"]["rho-H"].predict_obs).env,
    }
    (run / "analysis_mdp_v2.json").write_text(json.dumps(res, indent=1))
    (run / "analysis_mdp_v2.md").write_text(to_md(res))
    print(to_md(res))
    return 0


def to_md(r: dict) -> str:
    s6, b, nd = r["s6_max_budget"], r["bootstrap"], r["noise_diagnostic"]
    L = [f"# expt_v3 known-MDP, Night 3 (mdp_v2): verdict {r['verdict']}", "",
         "Start target value by scale (mean of 3 repeats): " + ", ".join(f"{k} ({v['n_params']} params) {v['mean']:.3f}" for k, v in r["start_target_value"].items()) + ".",
         f"Gate: {r['gate_positive_s6_max_budget']} of 22 candidates positive at s6, {s6['budget_k_tokens']:.1f}k tokens ({'pass' if r['gate_pass'] else 'fail'}). "
         f"Positive cells overall: {r['positive_cells']}.",
         f"corr(log rho, H) over all {r['n_probes']} probes: {r['corr_logrho_H_all_probes']:.3f} ({'separated' if r['separation_pass'] else 'collinear'}); "
         f"noise-free probes: {r['corr_logrho_H_noise_free']:.3f}.",
         f"T1 {r['T1']}, T2 beats random {r['T2_beats_random']}, T2 beats all baselines {r['T2_beats_all_baselines']}.", "",
         "| features | RMSE at s6 (pts) | rank acc |", "|---|---|---|"]
    L += [f"| {k} | {v['rmse_pts']:.2f} | {v['rank_accuracy']:.3f} |" for k, v in r["fits"].items()]
    L += ["", f"| choice rule at s6 | mean regret (pts) | 95% CI ({b['n']} bootstrap) | law minus rule, 95% CI | share law lower |", "|---|---|---|---|---|"]
    for k, v in r["choice_regret_pts"].items():
        lo, hi = b["regret_ci95_pts"][k]
        d = b["law_minus_baseline_ci95_pts"].get(k)
        L.append(f"| {k} | {v:.2f} | [{lo:.2f}, {hi:.2f}] | " + (f"[{d[0]:+.2f}, {d[1]:+.2f}] | {b['share_law_lower'][k]:.2f}" if d else "- | -") + " |")
    L += ["", f"Best fixed label from s1-s5: {r['best_fixed_label']}.",
          f"Law pick {s6['law_pick']}: {s6['law_pick_utility_pts']:+.2f} pts (SD over 15 runs {s6['law_pick_run_sd_pts']:.2f}; repeat means {s6['law_pick_repeat_means_pts']}); "
          f"observed best {s6['observed_best']} {s6['observed_best_utility_pts']:+.2f}; oracle pick {s6['oracle_pick']}; mean over candidates {s6['mean_over_candidates_pts']:+.2f}.",
          f"Spearman at s6: law vs observed {s6['spearman_law_vs_observed']:.2f}, law vs oracle {s6['spearman_law_vs_oracle']:.2f}, observed vs oracle {s6['spearman_observed_vs_oracle']:.2f}.", "",
          f"Noise diagnostic (same fitted law): noisy candidates' rho is {nd['mean_rho_ratio_noisy']:.1f}x their noise-free twin (geometric mean); "
          f"mean abs prediction error on noisy candidates {nd['noisy_mae_pts_standard_rho']:.2f} pts with standard rho vs {nd['noisy_mae_pts_noise_free_rho']:.2f} with noise-free rho. "
          f"Diagnostic law fit on noise-free features: regret {nd['diagnostic_law_fit_on_noise_free_regret_pts']:.2f} pts, pick {nd['diagnostic_law_fit_on_noise_free_pick']}.", "",
          "| env (s6, max budget) | observed U (pts) | SD 15 runs | law pred | oracle U | rho | rho noise-free | H | start success |", "|---|---|---|---|---|---|---|---|---|"]
    L += ["| " + " | ".join(str(x) for x in row) + " |" for row in s6["table"]]
    L += ["", "| noisy env | rho | rho noise-free | pred (std rho) | pred (noise-free rho) | observed |", "|---|---|---|---|---|---|"]
    L += [f"| {x['env']} | {x['rho']:.0f} | {x['rho_noise_free']:.0f} | {x['pred_std_pts']:+.2f} | {x['pred_noise_free_pts']:+.2f} | {x['observed_pts']:+.2f} |"
          for x in nd["s6_rows"] if "_sg0.5" in x["env"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
