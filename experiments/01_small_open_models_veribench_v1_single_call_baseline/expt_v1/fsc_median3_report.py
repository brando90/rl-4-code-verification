#!/usr/bin/env python3
# TLDR: Summarize experiment 01's FSC repeat correction: per model, single-repeat FSC vs locked median-of-3
# FSC on the same items, paired task-bootstrap 95% interval (seed 20261007, 10,000 draws), sign-flip
# permutation p-value, items resting on < 3 repeats, Qwen3-14B's SCSC recompute, spend; zero model calls.
from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
LABELS = ["qwen3.5-0.8b", "qwen3.5-2b", "qwen3.5-4b", "qwen3.5-9b", "qwen3-1.7b", "qwen3-4b", "qwen3-8b",
          "qwen3-14b", "qwen3.6-27b-local"]
NAMES = {"qwen3.5-0.8b": "Qwen3.5-0.8B", "qwen3.5-2b": "Qwen3.5-2B", "qwen3.5-4b": "Qwen3.5-4B",
         "qwen3.5-9b": "Qwen3.5-9B", "qwen3-1.7b": "Qwen3-1.7B", "qwen3-4b": "Qwen3-4B", "qwen3-8b": "Qwen3-8B",
         "qwen3-14b": "Qwen3-14B", "qwen3.6-27b-local": "Qwen3.6-27B (local route control)"}
CONFIGS = ("H2_sol_high", "H2_opus55_max")
SEED, DRAWS = 20261007, 10_000
MAIN_CELL_14B = "hardware_set_real__my_interrupt_preempt"
N_TASKS = 896


def bootstrap_mean(values: list[float], rng: random.Random, draws: int = DRAWS) -> tuple[float, float]:
    n = len(values)
    means = []
    for _ in range(draws):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[int(0.025 * draws)], means[int(0.975 * draws) - 1]


def signflip_p(diffs: list[float], rng: random.Random, draws: int = DRAWS) -> float:
    """Two-sided paired sign-flip permutation test; null: paired differences are symmetric about 0."""
    observed = abs(sum(diffs))
    hits = 0
    for _ in range(draws):
        total = sum(d if rng.random() < 0.5 else -d for d in diffs)
        hits += abs(total) >= observed - 1e-12
    return (hits + 1) / (draws + 1)


def main() -> int:
    rng = random.Random(SEED)
    rows, summary, all_diffs = [], {}, []
    for label in LABELS:
        path = RESULTS / f"fsc_median3_{label}.json"
        if not path.exists():
            print(f"{label}: missing {path.name}", file=sys.stderr)
            continue
        d = json.loads(path.read_text())
        complete = {k: v for k, v in d["per_task"].items() if v["complete"]}
        paired = {k: v for k, v in complete.items() if v.get("FSC_single_repeat") is not None}
        old = [v["FSC_single_repeat"] for v in paired.values()]
        new = [v["FSC"] for v in paired.values()]
        diffs = [n - o for o, n in zip(old, new)]
        all_diffs += diffs
        lo, hi = bootstrap_mean(diffs, rng) if diffs else (float("nan"), float("nan"))
        p = signflip_p(diffs, rng) if diffs else float("nan")
        lt3_any = sum(1 for v in complete.values() if any(v["repeats"][c] < 3 for c in CONFIGS))
        lt3 = {c: sum(1 for v in complete.values() if v["repeats"][c] < 3) for c in CONFIGS}
        rep_sd = []
        for v in complete.values():
            for c in CONFIGS:
                s = v["member_repeat_scores_0_5"][c]
                if len(s) >= 2:
                    rep_sd.append(statistics.pstdev(s))
        newly_complete = [k for k, v in complete.items() if v.get("FSC_single_repeat") is None]
        summary[label] = {
            "n_items_judged": d["n_items_judged"], "n_items_complete": len(complete), "n_paired": len(paired),
            "mean_FSC_single_repeat": statistics.fmean(old) if old else None,
            "mean_FSC_median3_paired": statistics.fmean(new) if new else None,
            "mean_FSC_median3_all_complete": d["mean_FSC_complete_items"],
            "mean_paired_delta": statistics.fmean(diffs) if diffs else None,
            "delta_ci95_task_bootstrap": [lo, hi], "p_signflip_permutation": p,
            "mean_abs_change": statistics.fmean(abs(x) for x in diffs) if diffs else None,
            "n_items_changed": sum(1 for x in diffs if abs(x) > 1e-12),
            "n_complete_items_with_lt3_repeats_any_member": lt3_any,
            "n_complete_items_with_lt3_repeats_per_member": lt3,
            "mean_within_member_repeat_sd_0_5": statistics.fmean(rep_sd) if rep_sd else None,
            "items_newly_complete_vs_single_repeat": newly_complete,
            "items_with_missing_repeats": d["items_with_missing_repeats"],
            "charges_usd_total_suite": d["charges_usd_total"],
            "charges_usd_r23": round(sum(v for k, v in d["charges_usd_per_member_and_part"].items()
                                         if k.endswith("@r23")), 6),
            "status_counts": d["status_counts_per_member_and_part"],
        }
        if label == "qwen3-14b" and MAIN_CELL_14B in d["per_task"]:
            cell = d["per_task"][MAIN_CELL_14B]
            scsc = (1.0 * 1.0 * cell["FSC"]) ** (1 / 3)
            summary[label]["main_cell"] = {
                "item": MAIN_CELL_14B, "FSC_single_repeat": cell.get("FSC_single_repeat"),
                "FSC_median3": cell["FSC"], "member_medians_0_5": cell["member_medians_0_5"],
                "member_repeat_scores_0_5": cell["member_repeat_scores_0_5"],
                "SCSC_cell": scsc, "SCSC_mean_over_896": scsc / N_TASKS,
                "SCSC_cell_single_repeat": (cell["FSC_single_repeat"] ** (1 / 3)) if cell.get("FSC_single_repeat") else None,
                "SCSC_mean_over_896_single_repeat": (cell["FSC_single_repeat"] ** (1 / 3)) / N_TASKS if cell.get("FSC_single_repeat") else None}
        s = summary[label]
        rows.append(f"| {NAMES[label]} | {s['n_paired']} | {s['mean_FSC_single_repeat']:.3f} | "
                    f"{s['mean_FSC_median3_paired']:.3f} | {s['mean_paired_delta']:+.3f} [{lo:+.3f}, {hi:+.3f}] "
                    f"p-val={p:.3f} | {s['mean_abs_change']:.3f} | {s['n_items_changed']}/{s['n_paired']} | "
                    f"{lt3_any} | {s['charges_usd_r23']:.2f} |")
    pooled = {}
    if all_diffs:
        lo, hi = bootstrap_mean(all_diffs, rng)
        pooled = {"n": len(all_diffs), "mean_delta": statistics.fmean(all_diffs), "ci95": [lo, hi],
                  "p_signflip_permutation": signflip_p(all_diffs, rng),
                  "mean_abs_change": statistics.fmean(abs(x) for x in all_diffs)}
    order_old = sorted(summary, key=lambda l: summary[l]["mean_FSC_single_repeat"])
    order_new = sorted(summary, key=lambda l: summary[l]["mean_FSC_median3_all_complete"])
    out = {"seed": SEED, "bootstrap_draws": DRAWS, "unit": "judged item (task); paired on items complete under both",
           "per_model": summary, "pooled_paired_delta": pooled,
           "fsc_order_single_repeat_ascending": order_old, "fsc_order_median3_ascending": order_new,
           "fsc_order_unchanged": order_old == order_new}
    (RESULTS / "fsc_median3_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    header = ("| Model | n (paired items) | FSC, 1 repeat | FSC, median of 3 | Δ (new − old) [95% task bootstrap] | "
              "mean abs change | items changed | complete items on < 3 repeats (any member) | repeats 2–3 spend (USD) |\n"
              "|---|---:|---:|---:|---|---:|---:|---:|---:|")
    print(header + "\n" + "\n".join(rows))
    print(json.dumps({"pooled": pooled, "order_unchanged": out["fsc_order_unchanged"],
                      "order_old": order_old, "order_new": order_new}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
