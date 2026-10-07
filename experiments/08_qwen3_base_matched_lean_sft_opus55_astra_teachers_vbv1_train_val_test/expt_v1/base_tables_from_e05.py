"""Restrict experiment 05's per-task Qwen3 Base G=8 results to the D-013 validation and test splits (zero new model calls)."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
E05 = REPO / "experiments" / "05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk" / "expt_v1" / "results"
MODELS = ("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base")
G = 8


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def table(manifest: Path) -> dict:
    with open(manifest, encoding="utf-8", newline="") as fh:
        split_of = {r["task_id"]: (r["split"], int(r["core"])) for r in csv.DictReader(fh)}
    out: dict = {}
    for m in MODELS:
        with open(E05 / f"per_task_{m}_g8.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert {r["task_id"] for r in rows} == set(split_of), f"{m}: task ids differ from the split manifest"
        for split in ("validation", "test"):
            for scope, keep in (("all", lambda c: True), ("core", lambda c: c == 1), ("industryset", lambda c: c == 0)):
                sel = [r for r in rows if split_of[r["task_id"]][0] == split and keep(split_of[r["task_id"]][1])]
                n = len(sel)
                k_kb = [int(r["k_kernel_binary"]) for r in sel]
                k_ic = [int(r["k_ic_tests"]) for r in sel]
                mixed = sum(1 for k in k_kb if 0 < k < G)
                passat8 = sum(1 for k in k_kb if k > 0)
                lo, hi = wilson(mixed, n)
                out.setdefault(m, {}).setdefault(split, {})[scope] = {
                    "tasks": n,
                    "samples_present": sum(int(r["samples_present"]) for r in sel),
                    "kernel_binary_mixed_share": round(mixed / n, 4) if n else None,
                    "kernel_binary_mixed_share_wilson95": [round(lo, 4), round(hi, 4)],
                    "kernel_binary_pass_at_8_share": round(passat8 / n, 4) if n else None,
                    "kernel_binary_mean_pass_rate": round(sum(k_kb) / (G * n), 5) if n else None,
                    "ic_tests_mean_pass_rate": round(sum(k_ic) / (G * n), 5) if n else None,
                    "mean_proof_fraction": round(sum(float(r["mean_proof_fraction"]) for r in sel) / n, 5) if n else None,
                }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=HERE / "results" / "split" / "vbv1_split_manifest.csv")
    ap.add_argument("--out", type=Path, default=HERE / "results" / "base_qwen3_e05_on_d013_splits.json")
    args = ap.parse_args(argv)
    res = table(args.manifest)
    args.out.write_text(json.dumps({"source": "experiment 05 per-task G=8 CSVs (kernel-scored, no FSC)", "results": res}, indent=2) + "\n", encoding="utf-8")
    for m, by_split in res.items():
        for split, scopes in by_split.items():
            a = scopes["all"]
            print(f"{m:16s} {split:10s} n={a['tasks']:3d} mixed={a['kernel_binary_mixed_share']} {a['kernel_binary_mixed_share_wilson95']} pass@8={a['kernel_binary_pass_at_8_share']} ic_tests={a['ic_tests_mean_pass_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
