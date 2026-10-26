"""TLDR: Amendment 01's pre-registered descriptive token-cap sensitivity for G1: recompute the primary AUC, the two heuristic AUCs and the two IRT-specific contrasts without the validation tasks where the start policy hit the 12,288-token cap on at least 4 of 8 samples; reads only the run's per-task G1 table and the pinned start-policy file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import analyze_e19 as A
import data_e19 as D

HERE = Path(__file__).resolve().parent
CAP_MIN = 4
SEED = 20261021


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--analysis", type=Path, default=HERE / "results/analysis_e19.json")
    ap.add_argument("--out", type=Path, default=HERE / "results/sensitivity_cap_e19.json")
    args = ap.parse_args()
    r = json.loads(args.analysis.read_text())
    if r.get("synthetic"):
        raise RuntimeError("refusing to run the sensitivity on synthetic output")
    split = D.load_split()
    start = D.load_start_policy(split)
    pt = r["G1"]["per_task"]
    if pt["task_id"] != start.tasks:
        raise RuntimeError("per-task G1 table and start-policy file disagree on task order")
    k = np.array(pt["k"], float)
    if not np.array_equal(k, start.k):
        raise RuntimeError("per-task G1 table and start-policy file disagree on successes")
    keep = start.k_capped < CAP_MIN
    tasks = [t for t, kp in zip(start.tasks, keep) if kp]
    mixed = ((k >= 1) & (k <= A.G - 1)).astype(float)[keep]
    p = np.array(pt["p_irt_2pl"])[keep]
    scores = {"q8_irt_2pl": 1 - p**A.G - (1 - p) ** A.G,
              "panel_strict_rate": np.array(pt["panel_strict_rate"])[keep],
              "panel_mean_smooth": np.array(pt["panel_mean_smooth"])[keep]}
    groups, _ = A.group_index(tasks, split.group)
    rng = np.random.default_rng(SEED)
    B = {n: np.empty(A.BOOT) for n in scores}
    for b in range(A.BOOT):
        idx = A.boot_indices(groups, rng)
        for n, s in scores.items():
            B[n][b] = A.auc(s[idx], mixed[idx])
    est = {n: A.auc(s, mixed) for n, s in scores.items()}
    out = {"amendment": "AMENDMENT_01 section 5 (descriptive; does not change the G1 verdict)",
           "excluded_rule": f"start-policy k_capped >= {CAP_MIN} of 8", "n_tasks": int(keep.sum()),
           "n_excluded": int((~keep).sum()), "mixed": int(mixed.sum()), "not_mixed": int(len(mixed) - mixed.sum()),
           "n_groups": len(groups), "boot": A.BOOT, "seed": SEED,
           "auc": {n: {"estimate": est[n], "ci95": A.ci(B[n])} for n in scores},
           "primary_share_draws_le_0_70": float(np.mean(B["q8_irt_2pl"] <= A.AUC_GATE)),
           "contrasts": {f"q8_irt_2pl_minus_{h}": A.contrast(est["q8_irt_2pl"] - est[h], B["q8_irt_2pl"] - B[h])
                         for h in ("panel_strict_rate", "panel_mean_smooth")}}
    args.out.write_text(json.dumps(A.to_jsonable(out), indent=1, sort_keys=True) + "\n")
    print(json.dumps(A.to_jsonable(out), indent=1))


if __name__ == "__main__":
    main()
