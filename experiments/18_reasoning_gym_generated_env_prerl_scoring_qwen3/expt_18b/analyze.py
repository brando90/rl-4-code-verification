"""Experiment 18b analysis: realised held-out gain per environment vs the frozen forecasts (numpy only).

    python analyze.py --root $B/results --out $B/results/results_18b.json [--md results_18b_table.md]

Reads <root>/eval_pre.json (base model) and <root>/post/post_<run>.json for every run (run = env x seed), forecasts_18b.json and
selection_18b.json from this directory. Gain per run = mean over the 6 target components (equal weights) of post - pre pass rate.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18b as K  # noqa: E402

N_BOOT = 10_000


# ----- statistics (numpy only) -----
def ranks(x) -> np.ndarray:
    """Average ranks (1-based), ties share the mean rank."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        r[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(a, b) -> float:
    ra, rb = ranks(a), ranks(b)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def kendall_tau_b(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    conc = disc = ta = tb = 0
    for i in range(n):
        for j in range(i + 1, n):
            da, db = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
            if da == 0 and db == 0:
                continue
            if da == 0:
                ta += 1
            elif db == 0:
                tb += 1
            elif da == db:
                conc += 1
            else:
                disc += 1
    denom = math.sqrt((conc + disc + ta) * (conc + disc + tb))
    return float("nan") if denom == 0 else (conc - disc) / denom


def pick_gain(scores, gains, k: int = 1) -> float:
    """Mean realised gain of the top-k scored environments; ties at the cut average their gains (k=1: all tied-top envs)."""
    scores, gains = np.asarray(scores, float), np.asarray(gains, float)
    order = np.argsort(-scores, kind="mergesort")
    cut = scores[order[k - 1]]
    sure = [i for i in range(len(scores)) if scores[i] > cut]
    tied = [i for i in range(len(scores)) if scores[i] == cut]
    need = k - len(sure)
    return float((gains[sure].sum() + gains[tied].mean() * need) / k)


def regret(scores, gains, k: int = 1) -> float:
    gains = np.asarray(gains, float)
    best = float(np.sort(gains)[::-1][:k].mean())
    return best - pick_gain(scores, gains, k)


def random_expected_regret(gains, k: int = 1) -> float:
    gains = np.asarray(gains, float)
    return float(np.sort(gains)[::-1][:k].mean() - gains.mean())


def pct_ci(v) -> list[float | None]:
    v = np.asarray([x for x in v if not math.isnan(x)])
    if len(v) == 0:
        return [None, None]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def noise_ceiling(g0, g1) -> dict:
    r = spearman(g0, g1)
    sb = 2 * r / (1 + r) if not math.isnan(r) and r > -1 else float("nan")
    return {"seed_spearman": r, "spearman_brown_2seed": sb,
            "max_forecast_spearman": math.sqrt(max(sb, 0.0)) if not math.isnan(sb) else float("nan")}


# ----- gains from eval files -----
def run_gain(pre: dict, post: dict, comps=K.TARGET_IDS) -> dict:
    g = {c: post["sets"][c]["pass_rate"] - pre["sets"][c]["pass_rate"] for c in comps}
    tag = {c: post["sets"][c]["tag_rate"] - pre["sets"][c]["tag_rate"] for c in comps}
    rg5 = [c for c in comps if c != K.C.GSM8K_ID]
    return {"gain": float(np.mean(list(g.values()))), "gain_gsm8k": g[K.C.GSM8K_ID], "gain_rg5": float(np.mean([g[c] for c in rg5])),
            "by_component": g, "tag_change": float(np.mean(list(tag.values())))}


def run_gain_ci(pre: dict, post: dict, n_boot: int = 1000, seed: int = 0) -> list[float | None]:
    rng = np.random.default_rng(seed)
    comps = K.TARGET_IDS
    a = {c: np.asarray(pre["sets"][c]["item_pass"]) for c in comps}
    b = {c: np.asarray(post["sets"][c]["item_pass"]) for c in comps}
    out = []
    for _ in range(n_boot):
        tot = 0.0
        for c in comps:
            ix = rng.integers(0, len(a[c]), len(a[c]))
            tot += b[c][ix].mean() - a[c][ix].mean()
        out.append(tot / len(comps))
    return pct_ci(out)


def collect(root: Path, envs: list[str]) -> tuple[dict, dict]:
    pre = json.loads((root / "eval_pre.json").read_text())
    runs: dict[tuple[str, int], dict] = {}
    for e in envs:
        for s in K.SEEDS:
            p = root / "post" / f"post_{K.run_name(e, s)}.json"
            if p.exists():
                post = json.loads(p.read_text())
                r = run_gain(pre, post)
                r["gain_ci95"] = run_gain_ci(pre, post)
                key = "env:" + e
                if key in post["sets"] and key in pre["sets"]:
                    r["gain_in_env"] = post["sets"][key]["pass_rate"] - pre["sets"][key]["pass_rate"]
                runs[(e, s)] = r
    return pre, runs


def analyze(envs: list[str], forecasts: dict, runs: dict, primary: list[str], secondary: list[str], n_boot: int = N_BOOT) -> dict:
    complete = [e for e in envs if all((e, s) in runs for s in K.SEEDS)]
    env_gain = {e: float(np.mean([runs[(e, s)]["gain"] for s in K.SEEDS if (e, s) in runs])) for e in envs if any((e, s) in runs for s in K.SEEDS)}
    used = [e for e in envs if e in env_gain]
    gains = np.array([env_gain[e] for e in used])
    out: dict = {"n_envs": len(used), "n_envs_two_seeds": len(complete), "env_gain": env_gain,
                 "best_env": used[int(np.argmax(gains))], "mean_gain": float(gains.mean())}
    if len(complete) >= 3:
        out["noise_ceiling"] = noise_ceiling([runs[(e, 0)]["gain"] for e in complete], [runs[(e, 1)]["gain"] for e in complete])
    rng = np.random.default_rng(0)
    boots = [rng.integers(0, len(used), len(used)) for _ in range(n_boot)]
    fc_tables: dict = {}
    sp_boot: dict[str, np.ndarray] = {}
    for name in primary + secondary:
        sc = np.array([forecasts[name][e] for e in used], float)
        row = {"spearman": spearman(sc, gains), "kendall_tau_b": kendall_tau_b(sc, gains), "regret_top1": regret(sc, gains, 1),
               "regret_top3": regret(sc, gains, min(3, len(used))), "pick": used[int(np.argmax(sc))]}
        bs, bk, br1, br3 = [], [], [], []
        for ix in boots:
            s_, g_ = sc[ix], gains[ix]
            bs.append(spearman(s_, g_))
            bk.append(kendall_tau_b(s_, g_))
            br1.append(regret(s_, g_, 1))
            br3.append(regret(s_, g_, min(3, len(ix))))
        sp_boot[name] = np.array(bs)
        row.update(spearman_ci95=pct_ci(bs), kendall_ci95=pct_ci(bk), regret_top1_ci95=pct_ci(br1), regret_top3_ci95=pct_ci(br3),
                   beats_random=bool(pct_ci(bs)[0] is not None and pct_ci(bs)[0] > 0))
        fc_tables[name] = row
    out["forecasts"] = fc_tables
    out["random_expected_regret_top1"] = random_expected_regret(gains, 1)
    out["random_expected_regret_top3"] = random_expected_regret(gains, min(3, len(used)))
    out["paired_spearman_diff"] = {f"rho_h-{o}": {"diff": fc_tables["rho_h"]["spearman"] - fc_tables[o]["spearman"],
                                                  "ci95": pct_ci(sp_boot["rho_h"] - sp_boot[o])}
                                   for o in primary if o != "rho_h"}
    ceil = out.get("noise_ceiling", {}).get("spearman_brown_2seed")
    out["cannot_rank"] = bool(ceil is None or math.isnan(ceil) or ceil < 0.3)
    return out


def secondary_table(envs: list[str], runs: dict) -> list[dict]:
    rows = []
    for e in envs:
        rs = [runs[(e, s)] for s in K.SEEDS if (e, s) in runs]
        if not rs:
            continue
        rows.append({"env": e, "n_seeds": len(rs), "gain": float(np.mean([r["gain"] for r in rs])),
                     "gain_gsm8k": float(np.mean([r["gain_gsm8k"] for r in rs])), "gain_rg5": float(np.mean([r["gain_rg5"] for r in rs])),
                     "tag_change": float(np.mean([r["tag_change"] for r in rs])),
                     "gain_in_env": float(np.mean([r["gain_in_env"] for r in rs if "gain_in_env" in r])) if any("gain_in_env" in r for r in rs) else None})
    return rows


def render_md(res: dict, sec: list[dict]) -> str:
    f = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.3f}"
    ci = lambda c: "n/a" if c[0] is None else f"[{c[0]:+.2f}, {c[1]:+.2f}]"
    lines = [f"Envs with outcomes: {res['n_envs']} ({res['n_envs_two_seeds']} with both seeds). Mean gain {f(res['mean_gain'])}; best env {res['best_env']}.", ""]
    nc = res.get("noise_ceiling")
    if nc:
        lines.append(f"Noise ceiling: seed-seed Spearman {f(nc['seed_spearman'])}, 2-seed reliability {f(nc['spearman_brown_2seed'])}, max forecast Spearman about {f(nc['max_forecast_spearman'])}.")
    if res["cannot_rank"]:
        lines.append("**Reliability below 0.3: this test cannot rank environments; read the correlations as descriptive.**")
    lines += ["", "| forecast | Spearman [95% CI] | Kendall [95% CI] | regret top-1 [CI] | regret top-3 | pick |", "|---|---|---|---|---|---|"]
    for n, r in res["forecasts"].items():
        lines.append(f"| {n} | {f(r['spearman'])} {ci(r['spearman_ci95'])} | {f(r['kendall_tau_b'])} {ci(r['kendall_ci95'])} | "
                     f"{f(r['regret_top1'])} {ci(r['regret_top1_ci95'])} | {f(r['regret_top3'])} | {r['pick']} |")
    lines.append(f"\nRandom pick expected regret: top-1 {f(res['random_expected_regret_top1'])}, top-3 {f(res['random_expected_regret_top3'])}.\n")
    lines += ["| env | seeds | gain | GSM8K gain | RG-5 gain | tag-rate change | in-env gain |", "|---|---|---|---|---|---|---|"]
    for r in sec:
        lines.append(f"| {r['env']} | {r['n_seeds']} | {f(r['gain'])} | {f(r['gain_gsm8k'])} | {f(r['gain_rg5'])} | {f(r['tag_change'])} | {f(r['gain_in_env'])} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    args = ap.parse_args(argv)
    fdoc = json.loads(K.FORECASTS_PATH.read_text())
    from rl4cv.forecast import verify_forecast

    if not verify_forecast(K.FORECASTS_PATH):
        raise SystemExit("forecasts_18b.json does not match its frozen sha256")
    envs = fdoc["selected"]
    pre, runs = collect(Path(args.root), envs)
    res = analyze(envs, fdoc["forecasts"], runs, fdoc["primary"], fdoc["secondary"], args.n_boot)
    res["runs"] = {f"{e}|{s}": r for (e, s), r in runs.items()}
    res["forecasts_sha256"] = K.FORECASTS_PATH.with_suffix(".sha256").read_text().split()[0]
    Path(args.out).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    md = render_md(res, secondary_table(envs, runs))
    if args.md:
        Path(args.md).write_text(md, encoding="utf-8")
    print(md)
    print("ANALYZE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
