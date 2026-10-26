"""Experiment 18a analysis as frozen in PROTOCOL.md: per (set, model) pass rate, rho, H and alignment, then analyses 1-5.

Reads <run>/scored/<model_tag>/*.jsonl and <run>/emb/<model_tag>/centroids.npz; writes <out>/envs_18a.jsonl (schema
envs_18a/v1, the file 18b reads), <out>/targets_18a.jsonl and <out>/summary_18a.json. Usage:

    python analyze.py --run ~/e18a/run --out ~/e18a/run/results
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18a_common as C  # noqa: E402

sys.path.insert(0, str(C.repo_src()))
from rl4cv.experience import groups_from_records, measure_environment  # noqa: E402

SCHEMA = "envs_18a/v1"
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


def analyze(run: Path, out: Path, scored_subdir: str = "", emb_subdir: str = "", smoke_group_size: int = 0) -> dict:
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
            row["group_size"] = group_size  # measure_environment reports the mean group size as a float
            if spec.kind == "env":
                a = align.get(spec.set_id, {})
                row["alignment"] = a.get("alignment")
                row["alignment_by_target"] = a.get("alignment_by_target")
                row["alignment_mid"] = align_mid.get(spec.set_id, {}).get("alignment")
                row["in_learnable_band"] = bool(BAND[0] <= row["pass_rate"] <= BAND[1] and row["rho"] > 0)
                env_rows.append(row)
            else:
                row["schema"] = "targets_18a/v1"
                tgt_rows.append(row)

    summary = summarize(env_rows, tgt_rows, tags, missing)
    out.mkdir(parents=True, exist_ok=True)
    C.write_jsonl_atomic(out / "envs_18a.jsonl", env_rows)
    C.write_jsonl_atomic(out / "targets_18a.jsonl", tgt_rows)
    C.write_json_atomic(out / "summary_18a.json", summary)
    return summary


def summarize(env_rows: list[dict], tgt_rows: list[dict], tags: list[str], missing: list[dict]) -> dict:
    """Analyses 1-5 of PROTOCOL.md on complete cells only."""
    cell = {(r["env_id"], r["model_tag"]): r for r in env_rows if r["complete"]}
    envs = sorted({r["env_id"] for r in env_rows}, key=lambda e: C.sets_by_id()[e].set_index)
    s: dict = {"schema": "summary_18a/v1", "models": tags, "incomplete_cells": missing}

    # 1. difficulty transfer across sizes
    pairs = {}
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            a, b = tags[i], tags[j]
            common = [e for e in envs if (e, a) in cell and (e, b) in cell]
            x = [cell[(e, a)]["pass_rate"] for e in common]
            y = [cell[(e, b)]["pass_rate"] for e in common]
            pairs[f"{a}~{b}"] = {"n_envs": len(common), "spearman": spearman(x, y) if len(common) > 2 else None,
                                 "ci95": spearman_ci(x, y) if len(common) > 2 else None}
    common_all = [e for e in envs if all((e, t) in cell for t in tags)]
    w = (kendalls_w(np.array([[cell[(e, t)]["pass_rate"] for e in common_all] for t in tags]))
         if len(tags) >= 2 and len(common_all) > 2 else None)
    verdict = None
    vals = [p["spearman"] for p in pairs.values() if p["spearman"] is not None]
    if len(vals) == 3:
        if any(v < 0.4 for v in vals):
            verdict = "fails"
        elif all(p["spearman"] >= 0.7 and p["ci95"][0] > 0.5 for p in pairs.values()):
            verdict = "transfers"
        else:
            verdict = "partial"
    s["analysis1_difficulty_transfer"] = {"pairwise": pairs, "kendalls_w": w, "n_envs_all_models": len(common_all),
                                          "verdict": verdict}

    # 2. within-family difficulty
    fam_out = {}
    for tag in tags:
        per = {}
        for _, fam, _ in C.TRAIN_FAMILIES:
            lv = [(L, cell[(f"rg/{fam}/L{L}", tag)]["pass_rate"]) for L in C.LEVELS if (f"rg/{fam}/L{L}", tag) in cell]
            if len(lv) < 2:
                continue
            ps = [p for _, p in lv]
            per[fam] = {"pass_by_level": {f"L{L}": p for L, p in lv},
                        "spearman_level_pass": spearman([L for L, _ in lv], ps),
                        "monotone": all(ps[k + 1] <= ps[k] + MONOTONE_TOL for k in range(len(ps) - 1))}
        fam_out[tag] = {"families": per, "n_monotone": sum(v["monotone"] for v in per.values()), "n_families": len(per)}
    s["analysis2_within_family"] = fam_out

    # 3. learnable band
    band = {t: sorted(e for e in envs if (e, t) in cell and cell[(e, t)]["in_learnable_band"]) for t in tags}
    jac = {}
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            A, B = set(band[tags[i]]), set(band[tags[j]])
            jac[f"{tags[i]}~{tags[j]}"] = len(A & B) / len(A | B) if A | B else None
    mean_level = {t: (float(np.mean([C.sets_by_id()[e].level for e in band[t]])) if band[t] else None) for t in tags}
    s["analysis3_learnable_band"] = {"definition": f"{BAND[0]} <= pass_rate <= {BAND[1]} and rho > 0",
                                     "envs": band, "count": {t: len(v) for t, v in band.items()}, "jaccard": jac,
                                     "mean_level_in_band": mean_level}

    # 4. coordinates
    coords = ["pass_rate", "rho", "H", "alignment"]
    coord_out = {}
    for tag in tags:
        es = [e for e in envs if (e, tag) in cell and cell[(e, tag)].get("alignment") is not None]
        mat = {}
        for i, a in enumerate(coords):
            for b in coords[i + 1 :]:
                mat[f"{a}~{b}"] = spearman([cell[(e, tag)][a] for e in es], [cell[(e, tag)][b] for e in es]) if len(es) > 2 else None
        coord_out[tag] = {"n_envs": len(es), "spearman": mat}
    s["analysis4_coordinates"] = coord_out

    # 5. target baseline
    s["analysis5_targets"] = {f"{r['env_id']}|{r['model_tag']}": {k: r[k] for k in ("pass_rate", "pass_rate_ci95", "rho", "H",
                                                                                    "answer_tag_rate", "complete")}
                              for r in tgt_rows}
    return s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", help="default <run>/results")
    ap.add_argument("--subdir", default="", help="smoke only: read scored_<subdir> and emb_<subdir>")
    ap.add_argument("--smoke-group-size", type=int, default=0,
                    help="smoke only: samples per item used; cells count as complete at the observed item count")
    args = ap.parse_args(argv)
    run = Path(args.run)
    out = Path(args.out) if args.out else run / ("results" + (f"_{args.subdir}" if args.subdir else ""))
    summary = analyze(run, out, args.subdir, args.subdir, args.smoke_group_size)
    a1 = summary["analysis1_difficulty_transfer"]
    print(json.dumps({"verdict": a1["verdict"], "kendalls_w": a1["kendalls_w"],
                      "pairwise": {k: v["spearman"] for k, v in a1["pairwise"].items()},
                      "band_count": summary["analysis3_learnable_band"]["count"],
                      "incomplete_cells": len(summary["incomplete_cells"])}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
