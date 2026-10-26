"""Plot registered G0 ranking and calibration from saved held-out predictions without refitting any model."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main(root: Path) -> None:
    gate = json.loads((root / "primary_g0.json").read_text())
    selected = gate["selected_model"]
    if selected is None:
        (root / "plot_receipt.json").write_text(json.dumps({"status": "unavailable: no selected converged G0 model"}) + "\n")
        return
    rows = list(csv.DictReader((root / "primary_g0_predictions.csv").open(newline="")))
    y = np.array([float(r["observed_active"]) for r in rows])
    if len(rows) != 539 or set(np.unique(y)) != {0, 1}:
        raise ValueError("A complete 539-task binary outcome table with both classes is required")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), layout="constrained")
    models = [(selected, selected.replace("_", " "), "#0072B2"),
              ("features_only", "features only", "#D55E00"),
              ("panel_strict_rate", "panel pass rate", "#009E73")]
    bins = []
    for name, label, color in models:
        if not gate["models"][name]["status"].startswith("available"):
            continue
        key = "panel_rate" if name == "panel_strict_rate" else "active_" + name
        p = np.array([float(r[key]) for r in rows])
        order = np.argsort(-p, kind="stable")
        last = np.r_[np.flatnonzero(np.diff(p[order]) != 0), len(p) - 1]
        tp, fp = np.cumsum(y[order])[last], np.cumsum(1 - y[order])[last]
        axes[0].plot(np.r_[0, fp / (1-y).sum()], np.r_[0, tp / y.sum()],
                     color=color, label=f"{label}: AUC {gate['models'][name]['auc']:.3f}")
        if name == "panel_strict_rate":
            continue  # The registered panel alternative is a ranking score, not a probability forecast.
        b = np.minimum((p * 10).astype(int), 9)
        points = []
        for i in range(10):
            keep = b == i
            if not keep.any():
                continue
            row = dict(model=name, bin=i, tasks=int(keep.sum()), predicted=float(p[keep].mean()), observed=float(y[keep].mean()))
            bins.append(row); points.append(row)
        axes[1].plot([r["predicted"] for r in points], [r["observed"] for r in points],
                     "o-", color=color, label=f"{label}: ECE {gate['models'][name]['ece']:.3f}")
    for ax in axes:
        ax.plot([0, 1], [0, 1], linestyle="--", color="0.6", linewidth=1)
        ax.set(xlim=(0, 1), ylim=(0, 1))
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="lower right", fontsize=8)
    axes[0].set(xlabel="False-positive rate", ylabel="True-positive rate", title="Held-out active-group ranking")
    axes[1].set(xlabel="Mean predicted active probability", ylabel="Observed active share", title="Calibration: 10 fixed bins")
    verdict = "PASS" if gate["gate"]["passed"] else "FAIL"
    fig.suptitle(f"E20 CPU Phase 0 — G0 {verdict}; trainer FAILED\n539 train tasks, 400 groups, five grouped folds", fontsize=11)
    for suffix in ("png", "pdf"):
        fig.savefig(root / ("g0_ranking_calibration." + suffix), dpi=180)
    plt.close(fig)
    with (root / "g0_calibration_bins.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(bins[0])); writer.writeheader(); writer.writerows(bins)
    (root / "plot_receipt.json").write_text(json.dumps(dict(status="complete", tasks=len(rows),
        source="primary_g0_predictions.csv", limits="Points are binned held-out predictions; bootstrap intervals are in primary_g0.json"), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    main(parser.parse_args().results_dir)
