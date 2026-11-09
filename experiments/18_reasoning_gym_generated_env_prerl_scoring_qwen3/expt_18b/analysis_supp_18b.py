"""Experiment 18b supplementary tables and plots (descriptive, added after the frozen analyze.py ran; no frozen number is changed).

    python analysis_supp_18b.py --root results --out-md results/supp_18b.md --plots results/plots

Reads results/results_18b.json (the frozen analyze.py output), eval_pre.json, post/*.json, train_logs/*.train_summary.json and
forecasts_18b.json. Writes the per env x seed table (held-out pass rate pre/post, gain, in-env gain, training tokens), a token-vs-gain
check and four plots.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
COMPS = ["rg/gsm_symbolic", "rg/calendar_arithmetic", "rg/time_intervals", "rg/syllogism", "rg/base_conversion", "gsm8k/test256"]


def rn(e, s):
    return e.replace("/", "__") + f"__s{s}"


def spearman(a, b):
    def rk(x):
        x = np.asarray(x, float)
        o = np.argsort(x, kind="mergesort")
        r = np.empty(len(x))
        i = 0
        while i < len(x):
            j = i
            while j + 1 < len(x) and x[o[j + 1]] == x[o[i]]:
                j += 1
            r[o[i : j + 1]] = (i + j) / 2 + 1
            i = j + 1
        return r

    return float(np.corrcoef(rk(a), rk(b))[0, 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="results")
    ap.add_argument("--out-md", default="results/supp_18b.md")
    ap.add_argument("--plots", default="results/plots")
    a = ap.parse_args()
    root = Path(a.root)
    res = json.loads((root / "results_18b.json").read_text())
    fc = json.loads((HERE / "forecasts_18b.json").read_text())
    pre = json.loads((root / "eval_pre.json").read_text())
    pre_mean = float(np.mean([pre["sets"][c]["pass_rate"] for c in COMPS]))
    envs = fc["selected"]
    rows, tok = [], {}
    for e in envs:
        for s in (0, 1):
            r = res["runs"][f"{e}|{s}"]
            post = json.loads((root / "post" / f"post_{rn(e, s)}.json").read_text())
            ts = json.loads((root / "train_logs" / f"{rn(e, s)}.train_summary.json").read_text())
            post_mean = float(np.mean([post["sets"][c]["pass_rate"] for c in COMPS]))
            logs = [json.loads(l) for l in (root / "train_logs" / f"{rn(e, s)}.train_log.jsonl").read_text().splitlines() if l.strip()]
            rew0 = float(np.mean([l["mean_reward"] for l in logs[:5]]))
            rew1 = float(np.mean([l["mean_reward"] for l in logs[-5:]]))
            tok[(e, s)] = ts["response_tokens"]
            rows.append(dict(env=e, seed=s, pre=pre_mean, post=post_mean, gain=r["gain"], ci=r["gain_ci95"], in_env=r.get("gain_in_env"),
                             tokens=ts["response_tokens"], rew0=rew0, rew1=rew1, skipped=sum(1 for l in logs if not l.get("stepped", True))))
    L = ["## Per env x seed (held-out target = mean of 6 components; pre is the same base-model value for every run)", "",
         f"Base model held-out pass rate (6-component mean, 8 samples x 256 items per component): {pre_mean:.3f}.", "",
         "| env | seed | pre | post | gain [95% CI, items] | in-env gain | train response tokens | train reward first 5 / last 5 steps | skipped steps |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['env']} | {r['seed']} | {r['pre']:.3f} | {r['post']:.3f} | {r['gain']:+.3f} [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}] | "
                 f"{r['in_env']:+.3f} | {r['tokens']:,} | {r['rew0']:.2f} / {r['rew1']:.2f} | {r['skipped']} |")
    g0 = np.array([res["runs"][f"{e}|0"]["gain"] for e in envs])
    g1 = np.array([res["runs"][f"{e}|1"]["gain"] for e in envs])
    d = np.abs(g0 - g1)
    L += ["", f"Seed agreement: mean |seed0 - seed1| gain {d.mean():.3f}, max {d.max():.3f} ({envs[int(d.argmax())]}); Pearson {np.corrcoef(g0, g1)[0, 1]:+.3f}; "
              f"same sign in {int(((g0 > 0) == (g1 > 0)).sum())}/16 envs.",
          f"Gain range over envs: {min(res['env_gain'].values()):+.3f} to {max(res['env_gain'].values()):+.3f}; "
          f"{sum(v > 0 for v in res['env_gain'].values())}/16 envs have positive 2-seed gain."]
    tm = np.array([np.mean([tok[(e, 0)], tok[(e, 1)]]) for e in envs])
    gm = np.array([res["env_gain"][e] for e in envs])
    L += ["", f"Descriptive check (not a frozen test): Spearman of env mean training response tokens vs gain {spearman(tm, gm):+.3f}; "
              f"training response tokens per run range {int(tm.min()):,} to {int(tm.max()):,} (mean of 2 seeds)."]
    gs = np.array([np.mean([res["runs"][f"{e}|{s}"]["gain_gsm8k"] for s in (0, 1)]) for e in envs])
    gr = np.array([np.mean([res["runs"][f"{e}|{s}"]["gain_rg5"] for s in (0, 1)]) for e in envs])
    L += [f"GSM8K-only gain is negative in {int((gs < 0).sum())}/16 envs; the RG-5 gain is positive in {int((gr > 0).sum())}/16.",
          "", "## Paired Spearman differences (frozen analyze.py output)", "", "| comparison | diff | 95% CI |", "|---|---|---|"]
    for k, v in res["paired_spearman_diff"].items():
        L.append(f"| {k} | {v['diff']:+.3f} | [{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}] |")
    Path(a.out_md).write_text("\n".join(L) + "\n")

    out = Path(a.plots)
    out.mkdir(parents=True, exist_ok=True)
    names = list(res["forecasts"])
    y = np.arange(len(names))[::-1]
    sp = np.array([res["forecasts"][n]["spearman"] for n in names])
    lo = np.array([res["forecasts"][n]["spearman_ci95"][0] for n in names])
    hi = np.array([res["forecasts"][n]["spearman_ci95"][1] for n in names])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(sp, y, xerr=[sp - lo, hi - sp], fmt="o", color="#1f5fa8", capsize=3)
    ax.axvline(0, color="grey", lw=0.8)
    ax.axvline(res["noise_ceiling"]["max_forecast_spearman"], color="#c0392b", ls="--", lw=1, label="noise ceiling (max reachable)")
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("Spearman, forecast vs held-out gain (16 envs, 95% bootstrap CI)")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "spearman_ci.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(y, [res["forecasts"][n]["regret_top1"] for n in names], color="#1f5fa8")
    ax.axvline(res["random_expected_regret_top1"], color="#c0392b", ls="--", label="random pick (expected)")
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("top-1 regret (best env gain minus picked env gain; lower is better)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "regret_top1.png", dpi=150)
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for ax, n in zip(axs, ["rho_h", "H_only"]):
        sec = fc["forecasts"][n]
        x = [sec[e] for e in envs]
        ax.scatter(x, gm, color="#1f5fa8")
        for e, xi, gi in zip(envs, x, gm):
            ax.annotate(e.replace("rg/", ""), (xi, gi), fontsize=6, xytext=(2, 2), textcoords="offset points")
        ax.set_xlabel(f"forecast {n}")
        ax.set_ylabel("2-seed held-out gain")
        ax.set_title(f"{n}: Spearman {res['forecasts'][n]['spearman']:+.2f}")
    fig.tight_layout()
    fig.savefig(out / "forecast_vs_gain.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(g0, g1, color="#1f5fa8")
    lim = [min(g0.min(), g1.min()) - 0.03, max(g0.max(), g1.max()) + 0.03]
    ax.plot(lim, lim, color="grey", lw=0.8)
    ax.set_xlabel("seed 0 gain")
    ax.set_ylabel("seed 1 gain")
    ax.set_title(f"seed-seed Spearman {res['noise_ceiling']['seed_spearman']:+.2f}")
    fig.tight_layout()
    fig.savefig(out / "seed_seed.png", dpi=150)
    plt.close(fig)
    print("SUPP OK")


if __name__ == "__main__":
    main()
