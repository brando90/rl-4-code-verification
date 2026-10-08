#!/usr/bin/env python3
# TLDR: Add the G = 8 probe's judged channels (`scsc`, and `fsc_compiled` where measured) beside the kernel
# channels: re-collect the two judged models' scored JSONL with the exported FSC (never overwriting the
# pre-judging file), run rl4cv.probe per split for all 8 models x 4 channels, copy the per-split summaries
# into results/summaries/, and write results/probe_channels_summary.json with the overall rows (the
# published group-weighted formula plus the pooled single-environment values), the unmeasured counts, the
# per-cell table of the 11 judged cells and the Gate G1 / seed-split check; zero model calls.
from __future__ import annotations

import json
import shutil
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "src"))
from rl4cv.probe import load_scored, measure_channel, to_markdown      # noqa: E402
from rl4cv.veribench.collect import collect                            # noqa: E402

GEN_OUT = Path("/lfs/skampere1/0/brando9/rl4cv_e01/out")
RESULTS = HERE / "results"
SUMMARIES = RESULTS / "summaries"
LABELS = ["qwen3.5-0.8b", "qwen3.5-2b", "qwen3.5-4b", "qwen3.5-9b", "qwen3-1.7b", "qwen3-4b", "qwen3-8b", "qwen3-14b"]
NAMES = {"qwen3.5-0.8b": "Qwen3.5-0.8B", "qwen3.5-2b": "Qwen3.5-2B", "qwen3.5-4b": "Qwen3.5-4B",
         "qwen3.5-9b": "Qwen3.5-9B", "qwen3-1.7b": "Qwen3-1.7B", "qwen3-4b": "Qwen3-4B", "qwen3-8b": "Qwen3-8B",
         "qwen3-14b": "Qwen3-14B"}
JUDGED = ["qwen3.5-9b", "qwen3-14b"]
CHANNELS = ["kernel_binary", "proof_fraction", "scsc", "fsc_compiled"]
GATE_PASS, GATE_FAIL = 0.20, 0.05


def scored_path(label: str) -> Path:
    """The judged models' re-collected file (with FSC) when it exists, else the pre-judging file."""
    with_fsc = GEN_OUT / "scored" / f"scored_{label}_g8_with_fsc.jsonl"
    return with_fsc if with_fsc.exists() else GEN_OUT / "scored" / f"scored_{label}_g8.jsonl"


def recollect(label: str) -> Path:
    """Re-run rl4cv.veribench.collect with --fsc-root on the exported FSC; writes a NEW file beside the
    pre-judging one (the 10-01-2026 G = 1 precedent: scored_qwen3-14b_g1_with_fsc.jsonl)."""
    job = f"{label}_g8"
    out = GEN_OUT / "scored" / f"scored_{job}_with_fsc.jsonl"
    rows = collect(GEN_OUT / "raw" / f"gen_{job}.jsonl", GEN_OUT / "scores", job, GEN_OUT / "fsc")
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return out


def overall(table: dict) -> dict:
    """The published 'overall' formula (results.md, 10-01-2026): group-weighted means of the per-split
    mean reward, mixed-group share, rho and H over the fully measured groups; plus the max per-split
    mixed-group share and the splits at or above the Gate G1 pass threshold."""
    rows = [e for e in table.values() if e.get("n_groups")]
    n = sum(e["n_groups"] for e in rows)
    out = {"n_groups_measured": n,
           "n_groups_excluded_unmeasured": sum(e.get("n_groups_excluded_unmeasured", 0) for e in table.values()),
           "n_tasks_declared": sum(e.get("n_tasks_declared", 0) for e in table.values())}
    for key in ("mean_reward", "q_mixed_empirical", "rho", "H"):
        out[key] = (sum(e["n_groups"] * e[key] for e in rows) / n) if n else None
    per_split = {s: e["q_mixed_empirical"] for s, e in table.items() if e.get("n_groups")}
    out["max_split_q_mixed"] = max(per_split.values()) if per_split else None
    out["splits_at_or_above_0.20"] = sorted(s for s, q in per_split.items() if q >= GATE_PASS - 1e-12)
    out["splits_argmax"] = sorted(s for s, q in per_split.items() if per_split and q == out["max_split_q_mixed"] and q > 0)
    return out


def main() -> int:
    SUMMARIES.mkdir(parents=True, exist_ok=True)
    report = {"labels": {}, "cells": [], "fsc_root_exports": {}}
    for label in JUDGED:
        exports = sorted((GEN_OUT / "fsc").glob(f"{label}_g8_s*.json"))
        report["fsc_root_exports"][label] = [p.name for p in exports]
        if exports:
            recollect(label)
    for label in LABELS:
        path = scored_path(label)
        rows = load_scored(path)
        entry = {"scored_jsonl": str(path), "n_rows": len(rows),
                 "n_cells_ic_tests_1": sum(1 for r in rows if (r.get("IC_tests") or 0) == 1.0),
                 "n_cells_proving": sum(1 for r in rows if (r.get("IC_tests") or 0) * (r.get("IC_proofs") or 0) > 0),
                 "n_cells_fsc_judged": sum(1 for r in rows if r.get("FSC") is not None),
                 # IC_tests = 1 but IC_proofs = 0: outside the locked judge scope; fsc_compiled stays null.
                 "n_cells_ic_tests_1_not_proving": sum(1 for r in rows if (r.get("IC_tests") or 0) == 1.0
                                                       and (r.get("IC_proofs") or 0) == 0.0),
                 "n_cells_reward_null": {ch: sum(1 for r in rows if (r.get("rewards") or {}).get(ch) is None)
                                         for ch in CHANNELS},
                 "channels": {}}
        for ch in CHANNELS:
            table = measure_channel(rows, ch, None, "split")
            pooled = measure_channel(rows, ch)["all"]
            out = SUMMARIES / f"rho_h_{label}_g8_{ch}.json"
            if ch in ("kernel_binary", "proof_fraction"):
                # Published 10-01-2026 from the host copy; copy it unchanged and check we reproduce it.
                host = GEN_OUT / "summaries" / f"rho_h_{label}_g8_{ch}.json"
                host_table = json.loads(host.read_text())
                same = all(abs(host_table[s][k] - table[s][k]) < 1e-9 for s in table
                           for k in ("mean_reward", "q_mixed_empirical", "rho", "H") if k in table[s])
                entry["channels"].setdefault(ch, {})["reproduces_host_summary"] = same
                shutil.copy(host, out)
                shutil.copy(host.with_suffix(".md"), out.with_suffix(".md"))
            else:
                out.write_text(json.dumps(table, indent=2) + "\n")
                out.with_suffix(".md").write_text(to_markdown(table, ch) + "\n")
            entry["channels"].setdefault(ch, {}).update(overall(table))
            entry["channels"][ch]["pooled_single_environment"] = {
                k: pooled.get(k) for k in ("n_groups", "mean_reward", "q_mixed_empirical", "rho", "H")}
        report["labels"][label] = entry
        if label in JUDGED:
            fsc_path = RESULTS / f"fsc_probe_{label}.json"
            if fsc_path.exists():
                d = json.loads(fsc_path.read_text())
                for item, row in sorted(d["per_task"].items()):
                    scored = next((r for r in rows if r["task_id"] == row["task_id"]
                                   and int(r["sample_idx"]) == int(row["sample_idx"])), {})
                    report["cells"].append({
                        "model": label, "item": item, "task_id": row["task_id"], "sample_idx": row["sample_idx"],
                        "split": row["split"], "IC_tests": row["IC_tests"], "IC_proofs": row["IC_proofs"],
                        "member_repeat_scores_0_5": row["member_repeat_scores_0_5"],
                        "member_medians_0_5": row["member_medians_0_5"], "FSC": row["FSC"], "complete": row["complete"],
                        "SCSC": row.get("SCSC"), "rewards_in_scored_jsonl": scored.get("rewards")})
                entry["fsc_probe"] = {k: d[k] for k in ("n_items_declared", "n_items_judged", "n_items_complete",
                                                        "mean_FSC_complete_items", "charges_usd_total", "runs")}
    # Gate G1 is locked on kernel_binary; report whether scsc changes the >= 0.20 split set (experiment 02 seeds).
    gate = {}
    for label in LABELS:
        kb = report["labels"][label]["channels"]["kernel_binary"]
        sc = report["labels"][label]["channels"]["scsc"]
        gate[label] = {"kernel_binary_max_split": kb["max_split_q_mixed"], "kernel_binary_splits_ge_0.20": kb["splits_at_or_above_0.20"],
                       "scsc_max_split": sc["max_split_q_mixed"], "scsc_splits_ge_0.20": sc["splits_at_or_above_0.20"],
                       "scsc_groups_excluded": sc["n_groups_excluded_unmeasured"],
                       "same_split_set": kb["splits_at_or_above_0.20"] == sc["splits_at_or_above_0.20"]}
    kb_pass = any(v["kernel_binary_max_split"] and v["kernel_binary_max_split"] >= GATE_PASS for v in gate.values())
    report["gate_g1"] = {"locked_channel": "kernel_binary", "verdict": "PASS" if kb_pass else "see results.md",
                         "per_model": gate,
                         "seed_splits_union_kernel_binary": sorted({s for v in gate.values() for s in v["kernel_binary_splits_ge_0.20"]}),
                         "seed_splits_union_scsc": sorted({s for v in gate.values() for s in v["scsc_splits_ge_0.20"]})}
    report["gate_g1"]["seed_splits_unchanged_under_scsc"] = (
        report["gate_g1"]["seed_splits_union_kernel_binary"] == report["gate_g1"]["seed_splits_union_scsc"])
    (RESULTS / "probe_channels_summary.json").write_text(json.dumps(report, indent=1) + "\n")

    def fmt(x, nd=4):
        return "—" if x is None else f"{x:.{nd}f}"
    print("| Model | Channel | Mean reward | Mixed-group share (overall) | ρ (overall) | H (overall) | "
          "Max per-split mixed-group share | Groups measured / 128 |\n|---|---|---:|---:|---:|---:|---:|---:|")
    for label in LABELS:
        for ch in ("scsc", "fsc_compiled"):
            o = report["labels"][label]["channels"][ch]
            arg = ", ".join(f"`{s}`" for s in o["splits_argmax"][:1])
            extra = f" ({arg}" + (f", {len(o['splits_at_or_above_0.20']) - 1} others ≥0.20)" if len(o["splits_at_or_above_0.20"]) > 1 else ")") if o["splits_argmax"] else ""
            print(f"| {NAMES[label]} | {ch} | {fmt(o['mean_reward'])} | {fmt(o['q_mixed_empirical'])} | {fmt(o['rho'], 2)} | "
                  f"{fmt(o['H'])} | {fmt(o['max_split_q_mixed'])}{extra} | {o['n_groups_measured']}/{o['n_tasks_declared']} |")
    print(json.dumps(report["gate_g1"], indent=1))
    for c in report["cells"]:
        print(c["model"], c["item"], c["member_repeat_scores_0_5"], "FSC", c["FSC"], "SCSC", c["SCSC"], c["rewards_in_scored_jsonl"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
