"""TLDR: Experiment 20's partial-credit runner on Sherlock: for every trial in one scorer job directory, run experiment 13's unchanged declaration adapter (DeclarationProbe.lean spans + the frozen scorer's compile and kernel check) to get experiment 13's factored_reward (src/rl4cv/e13.py, unchanged) with its d/t/p factors and the adapter's own strict value, under D-109 durable capture of every `lake env lean` call; writes <out>/partial_<job>.json with one record per trial (unresolved trials keep their error, never a zero)."""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, os.environ.get("RL4CV_SRC", "/scratch/users/brando9/rl4cv_sherlock/grading/rl4cv/src"))
from durable_capture import DurableCapture, atomic, clone, sha  # noqa: E402
import declaration_adapter as adapter  # noqa: E402

G = Path(os.environ.get("E20_GRADING", "/scratch/users/brando9/rl4cv_sherlock/grading"))


def instrumented_loader(capture):
    """Load each pinned module once and route its `lake env lean` subprocess calls through the durable capture."""
    original = adapter._load
    cache = {}

    def load(name, path):
        if name in cache:
            return cache[name]
        module = original(name, path)
        if name == "e13_pinned_scorer":
            module.compile_lean_file = clone(module.compile_lean_file, subprocess=capture)
            if hasattr(module, "kernel_axioms"):
                ka = module.kernel_axioms
                ka.run_probe = clone(ka.run_probe, subprocess=capture)
                ka.check_file = clone(ka.check_file, run_probe=ka.run_probe)
        elif name == "e13_kernel_axioms":
            module.run_probe = clone(module.run_probe, subprocess=capture)
            module.check_file = clone(module.check_file, run_probe=module.run_probe)
        cache[name] = module
        return module

    return load


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--job-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--evidence-root", type=Path, required=True)
    args = ap.parse_args()
    lean = G / "elan/toolchains/leanprover--lean4---v4.22.0/bin/lean"
    capture = DurableCapture(args.evidence_root, lean, dict(job_dir=str(args.job_dir.resolve()), experiment="20",
                                                            decision="D-109", stage="partial_credit_adapter"))
    adapter.subprocess = capture  # the DeclarationProbe `lake env lean --run` call
    adapter._load = instrumented_loader(capture)
    trials = sorted(p for p in args.job_dir.iterdir() if (p / "verifier/solution.lean").is_file())
    records = []
    for trial in trials:
        source = trial / "verifier/solution.lean"
        receipt = json.loads((trial / "receipt.json").read_text()) if (trial / "receipt.json").is_file() else {}
        truncated = bool(receipt.get("finish_reason") == "length")
        rec = {"task_id": trial.name, "sample_idx": receipt.get("sample_idx"), "source_sha256": sha(source),
               "source_bytes": source.stat().st_size, "truncated": truncated, "status": "measured"}
        t0 = time.monotonic()
        if source.stat().st_size == 0 or not source.read_text(encoding="utf-8").strip():
            rec.update(extracted=False, strict=0.0, factored_reward=0.0, compiles=False, n_examples=0, theorem_count=0,
                       proved_count=0, declarations_ok=0.0, implementation_and_examples_ok=False, proved_fraction=0.0,
                       d={"numerator": 0, "denominator": 0}, t={"numerator": 0, "denominator": 0}, p={"numerator": 0, "denominator": 0},
                       note="empty source: no Lean call")
        else:
            try:
                v = adapter.inspect_source(source, lake_dir=G / "lean_src", scorer_root=G / "veribench_scorer",
                                           expected_sha256=rec["source_sha256"], vacuous_count=0, truncated=truncated)
                dd, tt, pp = v["d"], v["t"], v["p"]
                rec.update(extracted=True, strict=float(v["strict"]), factored_reward=float(v["factored_reward"]),
                           compiles=bool(v["compile"]["success"] and v["kernel"]["probe_ok"]),
                           n_examples=sum(1 for d in v["declarations"] if d["is_example"]), theorem_count=pp["denominator"],
                           proved_count=pp["numerator"], declarations_ok=(dd["numerator"] / dd["denominator"]) if dd["denominator"] else 0.0,
                           implementation_and_examples_ok=bool(tt["denominator"] and tt["numerator"] == tt["denominator"]),
                           proved_fraction=(pp["numerator"] / pp["denominator"]) if pp["denominator"] else 0.0,
                           d=dd, t=tt, p=pp, kernel_probe_ok=bool(v["kernel"]["probe_ok"]), n_declarations=len(v["declarations"]),
                           axioms=v["axioms"])
            except Exception as exc:  # noqa: BLE001 - recorded, never scored as zero
                rec.update(status="unresolved_measurement", error_type=type(exc).__name__, error=str(exc)[:500])
        rec["wall_seconds"] = round(time.monotonic() - t0, 3)
        records.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("task_id", "sample_idx", "status", "strict", "factored_reward", "wall_seconds")}), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    atomic(args.out, {"job_dir": str(args.job_dir.resolve()), "adapter_sha256": sha(HERE / "declaration_adapter.py"),
                      "probe_sha256": sha(HERE / "DeclarationProbe.lean"), "n_trials": len(records),
                      "n_measured": sum(r["status"] == "measured" for r in records), "records": records})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
