"""TLDR: POST HOC (not in the frozen protocol; carries no verdict): task-bootstrap intervals for the mixed-group-share forecast error of each arm at every target rung, and an onset table (first rung whose realized or forecast mixed share reaches experiment 08's 0.05 gate), read from per_task_forecasts_e15.csv.gz."""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_e15 as a15  # noqa: E402

GATE = 0.05  # experiment 08's validation mixed-group-share readiness gate
ARMS = ("irt_2pl", "irt_1pl", "b1_last_rung", "b2_scalar_curve")


def main() -> None:
    rows = defaultdict(list)
    with gzip.open(HERE / "results/per_task_forecasts_e15.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            if r["outcome"] == "kernel_binary" and r["trend_form"] == "log1p_ratio":
                rows[(r["frac"], r["size"])].append(r)
    rng = np.random.default_rng([a15.SEED, 2])
    idx = rng.integers(0, a15.N_TASKS, size=(a15.BOOT, a15.N_TASKS))
    out = {"note": "post hoc, computed after the frozen primary analysis; no verdict", "gate": GATE, "draws": a15.BOOT, "per_rung": {}, "pooled": {}, "onset": {}}
    err = {}
    for (frac, size), rs in rows.items():
        k = np.array([float(r["successes"]) for r in rs])
        n = np.array([float(r["attempts"]) for r in rs])
        realized = ((k > 0) & (k < n)).astype(float)
        entry = {"realized_mixed_share": float(realized.mean()), "arms": {}}
        for arm in ARMS:
            p = np.array([float(r[f"p_{arm}"]) for r in rs])
            expected = 1 - p**a15.G - (1 - p) ** a15.G
            e_boot = np.abs(expected[idx].mean(1) - realized[idx].mean(1))
            err[(frac, size, arm)] = e_boot
            entry["arms"][arm] = {"expected_mixed_share": float(expected.mean()), "signed_error": float(expected.mean() - realized.mean()),
                                  "abs_error": float(abs(expected.mean() - realized.mean())),
                                  "abs_error_boot_lo": float(np.percentile(e_boot, 2.5)), "abs_error_boot_hi": float(np.percentile(e_boot, 97.5))}
        out["per_rung"][f"{frac}|{size}"] = entry
    for frac in ("0.25", "0.5", "0.75", "1.0"):
        sizes = [s for s in a15.SIZES if (frac, s) in rows]
        block = {}
        for b in ("b1_last_rung", "b2_scalar_curve"):
            for arm in ("irt_2pl", "irt_1pl"):
                d = np.mean([err[(frac, s, b)] - err[(frac, s, arm)] for s in sizes], axis=0)
                point = float(np.mean([out["per_rung"][f"{frac}|{s}"]["arms"][b]["abs_error"] - out["per_rung"][f"{frac}|{s}"]["arms"][arm]["abs_error"] for s in sizes]))
                block[f"{b}-minus-{arm}"] = {"point": point, "lo": float(np.percentile(d, 2.5)), "hi": float(np.percentile(d, 97.5)),
                                             "test": f"paired task bootstrap of the absolute mixed-share error, {a15.BOOT} draws, {a15.N_TASKS} tasks; p-val=n/a"}
        out["pooled"][frac] = {"sizes": sizes, "comparisons": block}
    # Onset: first rung whose realized mixed share reaches the gate (all rungs), and the first *target* rung at which each
    # arm's forecast expected share reaches it (targets start at 25%, so an onset at Base or 12.5% cannot be forecast).
    data = a15.load_real()
    for s in a15.SIZES:
        realized_by_rung = {f: a15.rung_truth(data, s, f, "kernel_binary")["realized_mixed_share"] for f in data["rungs"][s]}
        first_real = next((f for f in a15.FRACS if realized_by_rung.get(f, 0) >= GATE), None)
        first_fc = {arm: next((f for f in ("0.25", "0.5", "0.75", "1.0") if out["per_rung"][f"{f}|{s}"]["arms"][arm]["expected_mixed_share"] >= GATE), None) for arm in ARMS}
        out["onset"][s] = {"realized_by_rung": realized_by_rung, "first_rung_realized_at_gate": first_real, "first_target_rung_forecast_at_gate": first_fc}
    (HERE / "results/posthoc_mixed_share_e15.json").write_text(json.dumps(out, indent=1) + "\n")
    for frac, blk in out["pooled"].items():
        print(frac, {k: f"{v['point']:+.4f} [{v['lo']:+.4f}, {v['hi']:+.4f}]" for k, v in blk["comparisons"].items()})
    for s, o in out["onset"].items():
        print(s, "realized at gate:", o["first_rung_realized_at_gate"], "forecast at gate:", o["first_target_rung_forecast_at_gate"])
    for key, e in out["per_rung"].items():
        if key.startswith("1.0|"):
            print(key, "realized", round(e["realized_mixed_share"], 4), {a: (round(v["expected_mixed_share"], 3), round(v["abs_error"], 3)) for a, v in e["arms"].items()})


if __name__ == "__main__":
    main()
