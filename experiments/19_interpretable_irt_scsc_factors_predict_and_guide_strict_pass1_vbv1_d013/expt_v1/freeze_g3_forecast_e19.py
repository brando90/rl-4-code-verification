"""TLDR: G3 (PROTOCOL.md section 7): from the locked G1 primary model, freeze per-train-task forecasts of experiment 13's start policy's strict success probability and mixed-group probability (G = 8 and 16) for all 539 train tasks, plus the implied V4-G0 batch statistics, before any experiment 13 v4 generation exists."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.special import expit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from rl4cv.forecast import freeze_forecast  # noqa: E402


def g0_tasks(train_ids: list[str]) -> list[str]:
    """Experiment 13 v4's V4-G0 draw, as in its expt_v4/phase2/group_selection.py."""
    ids = sorted(train_ids)
    if len(ids) != 539 or len(set(ids)) != 539:
        raise ValueError("complete 539-task train manifest required")
    return np.random.default_rng(1304001).choice(ids, size=32, replace=False).tolist()


def mixed(p: np.ndarray, g: int) -> np.ndarray:
    return 1.0 - p**g - (1.0 - p) ** g


def build(analysis: dict, judgement: dict) -> dict:
    pm = analysis["G1"]["primary_model"]
    tasks, a, d, th0 = pm["tasks"], np.array(pm["a"]), np.array(pm["d"]), float(pm["theta0"])
    n_tr = analysis["panel"]["n_train_tasks"]
    train = tasks[:n_tr]
    if sorted(train) != train or len(train) != 539:
        raise RuntimeError("the primary model's first 539 items must be the sorted train tasks")
    p = expit(a[:n_tr] * th0 + d[:n_tr])
    q8, q16 = mixed(p, 8), mixed(p, 16)
    g0 = g0_tasks(train)
    idx = [train.index(t) for t in g0]
    q8g, q16g = float(np.mean(q8[idx])), float(np.mean(q16[idx]))
    return {
        "experiment": analysis["experiment"], "kind": "G3 prospective forecast for experiment 13 v4 (start policy sft_4B_f1p0)",
        "source_model": {"theta0": th0, "regularization": pm["regularization"], "analysis_inputs": analysis["inputs"]},
        "per_task": {"task_id": train, "p_strict": p.tolist(), "q_mixed_G8": q8.tolist(), "q_mixed_G16": q16.tolist()},
        "v4_g0": {"tasks": g0, "mean_q_mixed_G8": q8g, "mean_q_mixed_G16": q16g,
                  "implied_N8": 256 * q8g, "implied_N16": 256 * q16g, "implied_M8": 32 * q8g, "implied_M16": 16 * q16g},
        "train_pool": {"mean_q_mixed_G8_uniform": float(np.mean(q8)),
                       "mean_q_mixed_G8_top_quarter": float(np.mean(np.sort(q8)[::-1][: round(0.25 * len(q8))])),
                       "mean_p_strict": float(np.mean(p))},
        "judgement": judgement,
        "scoring": "when experiment 13 publishes per-task V4-G0 counts s of 32: Spearman(q8, unbiased per-task mixed "
                   "probability) and AUC(q8, 1[1 <= s <= 31]) over the 32 tasks; judgement probabilities by Brier score",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--analysis", type=Path, default=HERE / "results/analysis_e19.json")
    ap.add_argument("--judgement", type=Path, required=True, help="JSON with the judgemental probabilities and rationale")
    args = ap.parse_args()
    analysis = json.loads(args.analysis.read_text())
    if analysis.get("synthetic"):
        raise RuntimeError("refusing to freeze a forecast from synthetic data")
    fc = build(analysis, json.loads(args.judgement.read_text()))
    print(freeze_forecast(fc, HERE / "forecasts", "e19_g3_forecast_v4_g0", outcomes_observed=False))
    print(json.dumps({k: fc[k] for k in ("v4_g0", "train_pool")}, indent=1)[:2000])


if __name__ == "__main__":
    main()
