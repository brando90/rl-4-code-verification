"""Experiment 18a v2 (wide) analysis as frozen in PROTOCOL_v2.md: per (set, model) metrics as in v1, then analyses 1-7.

Reads <run>/scored/<model_tag>/*.jsonl and <run>/emb/<model_tag>/centroids.npz; writes <out>/envs_18a_v2.jsonl (schema
envs_18a_v2/v1, v1's envs_18a/v1 fields plus item diversity), <out>/targets_18a_v2.jsonl and <out>/summary_18a_v2.json.
Usage:

    python analyze.py --run ~/e18a_v2/run --out ~/e18a_v2/run/results [--v1-envs expt_v1/results/envs_18a.jsonl]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18v2_common as C  # noqa: E402

sys.path.insert(0, str(C.repo_src()))
from rl4cv.experience import groups_from_records, measure_environment  # noqa: E402

SCHEMA = "envs_18a_v2/v1"
LOW_DIVERSITY = 64  # sensitivity cut: environments with fewer distinct questions
N_RANDOM_SUBSETS = 10_000
N_BOOT = 10_000
BAND = (0.1, 0.9)
MONOTONE_TOL = 0.02


# ---------- statistics ----------

def rankdata(x) -> np.ndarray:
    """Average ranks (1-based), ties share their mean rank."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(a, b) -> float:
    ra, rb = rankdata(a), rankdata(b)
    if np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def spearman_ci(a, b, n_boot: int = N_BOOT, seed: int = 0) -> list[float]:
    """Percentile bootstrap over paired observations (environments)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(a), len(a))
        v = spearman(a[idx], b[idx])
        if not np.isnan(v):
            vals.append(v)
    if not vals:
        return [float("nan"), float("nan")]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def spearman_cluster_ci(a, b, clusters, n_boot: int = N_BOOT, seed: int = 0) -> list[float]:
    """Percentile bootstrap that resamples whole clusters (families), since levels of one family are not independent."""
    a, b, clusters = np.asarray(a, float), np.asarray(b, float), np.asarray(clusters)
    names = sorted(set(clusters.tolist()))
    members = [np.flatnonzero(clusters == n) for n in names]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(names), len(names))
        idx = np.concatenate([members[i] for i in pick])
        v = spearman(a[idx], b[idx])
        if not np.isnan(v):
            vals.append(v)
    if not vals:
        return [float("nan"), float("nan")]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def transfer_verdict(rho: float | None, ci: list[float] | None) -> str | None:
    """v1's rule for one pair: transfers if rho >= 0.7 and CI low > 0.5; fails if rho < 0.4; else partial."""
    if rho is None or ci is None or np.isnan(rho):
        return None
    if rho < 0.4:
        return "fails"
    return "transfers" if rho >= 0.7 and ci[0] > 0.5 else "partial"


def eta_squared(values, groups) -> float | None:
    """Share of the variance of values that lies between groups (one-way ANOVA eta^2)."""
    v, g = np.asarray(values, float), np.asarray(groups)
    if len(v) < 3 or np.var(v) == 0:
        return None
    grand = v.mean()
    between = sum(len(v[g == k]) * (v[g == k].mean() - grand) ** 2 for k in set(g.tolist()))
    return float(between / ((v - grand) ** 2).sum())


def kendalls_w(matrix: np.ndarray) -> float:
    """Kendall's W for m raters (rows) ranking n objects (columns), average ranks, no tie correction."""
    m, n = matrix.shape
    ranks = np.vstack([rankdata(r) for r in matrix])
    s = float(np.square(ranks.sum(0) - m * (n + 1) / 2.0).sum())
    return 12.0 * s / (m**2 * (n**3 - n))


def item_bootstrap_ci(item_means: np.ndarray, n_boot: int = N_BOOT, seed: int = 0) -> list[float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(item_means), (n_boot, len(item_means)))
    boots = item_means[idx].mean(1)
    return [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]


# ---------- per-cell metrics ----------

def cell_metrics(rows: list[dict], n_items: int | None, group_size: int) -> dict:
    """All per-(set, model) numbers from scored rows; rho/H exactly via rl4cv.experience.measure_environment.

    n_items=None (smoke runs only) takes the observed item count as the expected one.
    """
    by_item: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_item[r["item_id"]].append(r)
    if n_items is None:
        n_items = len(by_item)
    complete = len(by_item) == n_items and all(len(v) == group_size for v in by_item.values())
    recs = [{"item_id": r["item_id"], "pass": r["pass"], "score": r["score"], "generated_tokens": r["generated_tokens"],
             "admitted": not r["capped"]} for r in rows]
    m_pass = measure_environment(groups_from_records(recs, reward_key="pass", group_key="item_id")).to_dict()
    m_score = measure_environment(groups_from_records(recs, reward_key="score", group_key="item_id")).to_dict()
    item_pass = np.array([np.mean([x["pass"] for x in v]) for v in by_item.values()])
    out = {
        "complete": bool(complete),
        "n_items_observed": len(by_item),
        "pass_rate": float(np.mean([r["pass"] for r in rows])),
        "pass_rate_ci95": item_bootstrap_ci(item_pass),
        "mean_score": float(np.mean([r["score"] for r in rows])),
        "answer_tag_rate": float(np.mean([bool(r["has_answer_tag"]) for r in rows])),
        "capped_rate": float(np.mean([bool(r["capped"]) for r in rows])),
        "frac_items_all_fail": float(np.mean(item_pass == 0.0)),
        "frac_items_all_pass": float(np.mean(item_pass == 1.0)),
        "score_errors": int(sum(1 for r in rows if r.get("score_error"))),
    }
    out.update(m_pass)
    out["rho_score"] = m_score["rho"]
    out["H_score"] = m_score["H"]
    out["format_dominated"] = out["answer_tag_rate"] < 0.5
    return out


# ---------- alignment ----------

def alignment_scores(set_ids: list[str], centroids: np.ndarray, env_ids: list[str], target_ids: list[str]) -> dict:
    """alignment(e) = cos(mu_e - c, tau), c = mean of all set centroids, tau = mean_T (mu_T - c) (PROTOCOL.md)."""
    pos = {s: i for i, s in enumerate(set_ids)}
    use = [pos[s] for s in env_ids + target_ids]
    c = centroids[use].mean(0)
    tvecs = {t: centroids[pos[t]] - c for t in target_ids}
    tau = np.mean(list(tvecs.values()), axis=0)

    def cos(u, v):
        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
        return float(u @ v / (nu * nv)) if nu > 0 and nv > 0 else float("nan")

    out = {}
    for e in env_ids:
        d = centroids[pos[e]] - c
        out[e] = {"alignment": cos(d, tau), "alignment_by_target": {t: cos(d, v) for t, v in tvecs.items()}}
    return out


# ---------- main ----------

def load_rows(path: Path) -> list[dict]:
    return list(C.read_jsonl(path)) if path.exists() else []


def analyze(run: Path, out: Path, scored_subdir: str = "", emb_subdir: str = "", smoke_group_size: int = 0,
            v1_envs: Path | None = None) -> dict:
    manifest = json.loads((run / "items" / "manifest.json").read_text())
    metas = {m["set_id"]: m for m in manifest["sets"]}
    specs = [s for s in C.all_sets() if s.set_id in metas]
    env_specs = [s for s in specs if s.kind == "env"]
    tgt_specs = [s for s in specs if s.kind == "target"]
    scored_root = run / (f"scored_{scored_subdir}" if scored_subdir else "scored")
    emb_root = run / (f"emb_{emb_subdir}" if emb_subdir else "emb")
    tags = [t for t in C.MODELS if (scored_root / t).is_dir()]
    group_size = smoke_group_size or manifest["group_size"]

    env_rows, tgt_rows, missing = [], [], []
    for tag in tags:
        model = C.MODELS[tag]
        align, align_mid = {}, {}
        npz = emb_root / tag / "centroids.npz"
        if npz.exists() and tgt_specs:
            z = np.load(npz)
            sids = [str(s) for s in z["set_ids"]]
            env_ids = [s.set_id for s in env_specs if s.set_id in sids]
            tgt_ids = [s.set_id for s in tgt_specs if s.set_id in sids]
            align = alignment_scores(sids, z["last"], env_ids, tgt_ids)
            align_mid = alignment_scores(sids, z["mid"], env_ids, tgt_ids)
        for spec in specs:
            meta = metas[spec.set_id]
            rows = load_rows(scored_root / tag / f"{spec.file_stem}.jsonl")
            if not rows:
                missing.append({"set_id": spec.set_id, "model_tag": tag, "responses": 0})
                continue
            mets = cell_metrics(rows, None if smoke_group_size else meta["n_items"], group_size)
            if not mets["complete"]:
                missing.append({"set_id": spec.set_id, "model_tag": tag, "responses": len(rows),
                                "items": mets["n_items_observed"]})
            row = {"schema": SCHEMA, "env_id": spec.set_id, "family": spec.family, "category": spec.category,
                   "level": spec.level, "rg_version": manifest["rg_version"], "rg_config": meta.get("rg_config"),
                   "probe_seed": spec.seed, "train_seed_base_suggestion": spec.seed + 1_000_000,
                   "n_items": meta["n_items"], "group_size": group_size, "model": model["id"],
                   "model_revision": model["revision"], "model_tag": tag, "model_size_b": model["size_b"]}
            row.update(mets)
            row["unique_questions"] = meta.get("unique_questions")
            row["top_answer_share"] = meta.get("top_answer_share")
            row["group_size"] = group_size  # measure_environment reports the mean group size as a float
            if spec.kind == "env":
                a = align.get(spec.set_id, {})
                row["alignment"] = a.get("alignment")
                row["alignment_by_target"] = a.get("alignment_by_target")
                row["alignment_mid"] = align_mid.get(spec.set_id, {}).get("alignment")
                row["in_learnable_band"] = bool(BAND[0] <= row["pass_rate"] <= BAND[1] and row["rho"] > 0)
                env_rows.append(row)
            else:
                row["schema"] = "targets_18a_v2/v1"
                tgt_rows.append(row)

    v1_rows = list(C.read_jsonl(v1_envs)) if v1_envs and Path(v1_envs).exists() else None
    summary = summarize(env_rows, tgt_rows, tags, missing, v1_rows)
    out.mkdir(parents=True, exist_ok=True)
    C.write_jsonl_atomic(out / "envs_18a_v2.jsonl", env_rows)
    C.write_jsonl_atomic(out / "targets_18a_v2.jsonl", tgt_rows)
    C.write_json_atomic(out / "summary_18a_v2.json", summary)
    return summary


def _stats(cell: dict, envs: list[str], tags: list[str]) -> dict:
    """The numbers v1 reports, on a subset of environments: size transfer, monotone share, band share, coordinates."""
    by = C.sets_by_id()
    out: dict = {"n_envs": len(envs), "n_families": len({by[e].family for e in envs})}
    if len(tags) >= 2:
        a, b = tags[0], tags[1]
        common = [e for e in envs if (e, a) in cell and (e, b) in cell]
        x = [cell[(e, a)]["pass_rate"] for e in common]
        y = [cell[(e, b)]["pass_rate"] for e in common]
        fams = [by[e].family for e in common]
        rho = spearman(x, y) if len(common) > 2 else None
        ci_f = spearman_cluster_ci(x, y, fams) if len(common) > 2 and len(set(fams)) > 1 else None
        ci_e = spearman_ci(x, y) if len(common) > 2 else None
        out["size_transfer"] = {"pair": f"{a}~{b}", "n_envs": len(common), "spearman": rho, "ci95_family": ci_f,
                                "ci95_env": ci_e, "verdict": transfer_verdict(rho, ci_f)}
    mono, band, coords = {}, {}, {}
    for t in tags:
        fams: dict[str, list[tuple[int, float]]] = {}
        for e in envs:
            if (e, t) in cell:
                fams.setdefault(by[e].family, []).append((by[e].level, cell[(e, t)]["pass_rate"]))
        per = {f: all(p2 <= p1 + MONOTONE_TOL for (_, p1), (_, p2) in zip(sorted(v), sorted(v)[1:]))
               for f, v in fams.items() if len(v) >= 2}
        mono[t] = {"n_monotone": sum(per.values()), "n_families": len(per),
                   "share": (sum(per.values()) / len(per)) if per else None}
        es = [e for e in envs if (e, t) in cell]
        inb = [e for e in es if cell[(e, t)]["in_learnable_band"]]
        band[t] = {"count": len(inb), "n_envs": len(es), "share": (len(inb) / len(es)) if es else None}
        ea = [e for e in es if cell[(e, t)].get("alignment") is not None]
        names = ["pass_rate", "rho", "H", "alignment"]
        coords[t] = {f"{u}~{v}": (spearman([cell[(e, t)][u] for e in ea], [cell[(e, t)][v] for e in ea]) if len(ea) > 2 else None)
                     for i, u in enumerate(names) for v in names[i + 1:]}
    out["monotone"], out["band"], out["coordinates"] = mono, band, coords
    return out


def summarize(env_rows: list[dict], tgt_rows: list[dict], tags: list[str], missing: list[dict],
              v1_rows: list[dict] | None = None) -> dict:
    """Analyses 1-7 of PROTOCOL_v2.md on complete cells only."""
    by = C.sets_by_id()
    cell = {(r["env_id"], r["model_tag"]): r for r in env_rows if r["complete"]}
    envs = sorted({r["env_id"] for r in env_rows}, key=lambda e: by[e].set_index)
    s: dict = {"schema": "summary_18a_v2/v1", "models": tags, "incomplete_cells": missing,
               "n_envs": len(envs), "n_families": len({by[e].family for e in envs})}
    full = _stats(cell, envs, tags)

    # 1. size transfer 0.6B -> 1.7B over all environments (Q2, primary), per category descriptive
    cats = {}
    for cat in sorted({by[e].category for e in envs}):
        ce = [e for e in envs if by[e].category == cat]
        if len(ce) >= 8 and len(tags) >= 2:
            x = [cell[(e, tags[0])]["pass_rate"] for e in ce if (e, tags[0]) in cell and (e, tags[1]) in cell]
            y = [cell[(e, tags[1])]["pass_rate"] for e in ce if (e, tags[0]) in cell and (e, tags[1]) in cell]
            cats[cat] = {"n_envs": len(x), "spearman": spearman(x, y) if len(x) > 2 else None}
    s["analysis1_size_transfer"] = dict(full.get("size_transfer", {}), by_category=cats)

    # 2. within-family difficulty, 3. learnable band, 4. coordinates (v1's analyses 2-4 at full width)
    s["analysis2_within_family"] = full["monotone"]
    band_sets = {t: {e for e in envs if (e, t) in cell and cell[(e, t)]["in_learnable_band"]} for t in tags}
    jac = None
    if len(tags) >= 2:
        A, B = band_sets[tags[0]], band_sets[tags[1]]
        jac = len(A & B) / len(A | B) if A | B else None
    s["analysis3_learnable_band"] = {
        "definition": f"{BAND[0]} <= pass_rate <= {BAND[1]} and rho > 0",
        "count": {t: len(v) for t, v in band_sets.items()}, "share": {t: full["band"][t]["share"] for t in tags},
        "jaccard": jac, "envs": {t: sorted(v, key=lambda e: by[e].set_index) for t, v in band_sets.items()},
        "mean_level_in_band": {t: (float(np.mean([by[e].level for e in v])) if v else None) for t, v in band_sets.items()}}
    s["analysis4_coordinates"] = full["coordinates"]

    # 5. target baselines
    s["analysis5_targets"] = {f"{r['env_id']}|{r['model_tag']}": {k: r[k] for k in ("pass_rate", "pass_rate_ci95", "rho", "H",
                                                                                    "answer_tag_rate", "complete")}
                              for r in tgt_rows}

    # 6. does the 8-family picture hold across all families (Q1)
    v1e = [e for e in envs if by[e].family in C.V1_FAMILIES]
    other = [e for e in envs if by[e].family not in C.V1_FAMILIES]
    sv1, sot = _stats(cell, v1e, tags), _stats(cell, other, tags)
    checks = {}
    if "size_transfer" in sv1 and "size_transfer" in sot:
        checks["a_same_transfer_verdict"] = sv1["size_transfer"]["verdict"] == sot["size_transfer"]["verdict"]
    checks["b_monotone_share_within_0.25"] = all(
        sv1["monotone"][t]["share"] is not None and sot["monotone"][t]["share"] is not None
        and abs(sv1["monotone"][t]["share"] - sot["monotone"][t]["share"]) <= 0.25 for t in tags)
    checks["c_band_share_within_0.20"] = all(
        sv1["band"][t]["share"] is not None and sot["band"][t]["share"] is not None
        and abs(sv1["band"][t]["share"] - sot["band"][t]["share"]) <= 0.20 for t in tags)
    sign_ok = True
    for t in tags:
        for k, v in sv1["coordinates"][t].items():
            w = sot["coordinates"][t].get(k)
            if v is not None and w is not None and not np.isnan(v) and abs(v) >= 0.3 and np.sign(v) != np.sign(w):
                sign_ok = False
    checks["d_coordinate_signs_agree"] = sign_ok
    if checks.get("a_same_transfer_verdict") is None:
        verdict = None
    elif not checks["a_same_transfer_verdict"]:
        verdict = "does_not_hold"
    else:
        verdict = "holds" if all(checks.values()) else "partially_holds"
    # how typical is the v1 subset among random 8-family subsets (size-transfer rho)
    typ = None
    fam_list = sorted({by[e].family for e in envs})
    if len(tags) >= 2 and len(fam_list) > 8 and sv1.get("size_transfer", {}).get("spearman") is not None:
        rng = np.random.default_rng(0)
        fam_envs = {f: [e for e in envs if by[e].family == f and (e, tags[0]) in cell and (e, tags[1]) in cell] for f in fam_list}
        vals = []
        for _ in range(N_RANDOM_SUBSETS):
            pick = rng.choice(len(fam_list), 8, replace=False)
            es = [e for i in pick for e in fam_envs[fam_list[i]]]
            if len(es) > 2:
                v = spearman([cell[(e, tags[0])]["pass_rate"] for e in es], [cell[(e, tags[1])]["pass_rate"] for e in es])
                if not np.isnan(v):
                    vals.append(v)
        if vals:
            r1 = sv1["size_transfer"]["spearman"]
            pct = float(np.mean(np.array(vals) <= r1))
            typ = {"v1_subset_spearman": r1, "random_8_family_median": float(np.median(vals)),
                   "random_8_family_p05_p95": [float(np.percentile(vals, 5)), float(np.percentile(vals, 95))],
                   "v1_percentile": pct, "atypical": bool(pct < 0.05 or pct > 0.95), "n_subsets": len(vals)}
    s["analysis6_eight_family_picture"] = {"v1_families": sv1, "other_families": sot, "checks": checks,
                                           "verdict": verdict, "v1_subset_typicality": typ}

    # 7. robustness: family share of variance, low-diversity and format-dominated exclusions, v1 replication
    rob: dict = {"eta2_family_pass_rate": {t: eta_squared([cell[(e, t)]["pass_rate"] for e in envs if (e, t) in cell],
                                                          [by[e].family for e in envs if (e, t) in cell]) for t in tags}}
    keep = [e for e in envs if all((e, t) in cell and (cell[(e, t)].get("unique_questions") or 0) >= LOW_DIVERSITY for t in tags)]
    rob["without_low_diversity"] = _stats(cell, keep, tags).get("size_transfer")
    keep = [e for e in envs if all((e, t) in cell and not cell[(e, t)]["format_dominated"] for t in tags)]
    rob["without_format_dominated"] = _stats(cell, keep, tags).get("size_transfer")
    if v1_rows:
        v1c = {(r["env_id"], r["model_tag"]): r["pass_rate"] for r in v1_rows if r.get("complete")}
        rep = {}
        for t in tags:
            shared = [e for e in envs if (e, t) in cell and (e, t) in v1c]
            if len(shared) > 2:
                a = [v1c[(e, t)] for e in shared]
                b = [cell[(e, t)]["pass_rate"] for e in shared]
                rep[t] = {"n_cells": len(shared), "spearman": spearman(a, b),
                          "mean_abs_diff": float(np.mean(np.abs(np.array(a) - np.array(b))))}
        rob["v1_replication_new_seeds"] = rep
    s["analysis7_robustness"] = rob
    return s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", help="default <run>/results")
    ap.add_argument("--subdir", default="", help="smoke only: read scored_<subdir> and emb_<subdir>")
    ap.add_argument("--v1-envs", help="expt_v1 results/envs_18a.jsonl, for the same-family replication check")
    ap.add_argument("--smoke-group-size", type=int, default=0,
                    help="smoke only: samples per item used; cells count as complete at the observed item count")
    args = ap.parse_args(argv)
    run = Path(args.run)
    out = Path(args.out) if args.out else run / ("results" + (f"_{args.subdir}" if args.subdir else ""))
    summary = analyze(run, out, args.subdir, args.subdir, args.smoke_group_size,
                      Path(args.v1_envs) if args.v1_envs else None)
    a1 = summary["analysis1_size_transfer"]
    print(json.dumps({"size_transfer": {k: a1.get(k) for k in ("spearman", "ci95_family", "verdict")},
                      "eight_family_picture": summary["analysis6_eight_family_picture"]["verdict"],
                      "band_count": summary["analysis3_learnable_band"]["count"],
                      "n_envs": summary["n_envs"], "incomplete_cells": len(summary["incomplete_cells"])}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
