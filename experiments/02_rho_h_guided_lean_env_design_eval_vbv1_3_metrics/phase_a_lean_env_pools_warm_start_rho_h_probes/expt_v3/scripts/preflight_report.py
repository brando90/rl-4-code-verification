#!/usr/bin/env python3
"""TLDR: Summarize experiment 02A v3's preflight (PROTOCOL § 7): for each teacher's single live cell, join the harvested receipt (status, finish reason, delivered settings, charge) with the scorer read-back (compiles, IC_tests, IC_proofs, kernel_binary, failure class) into results/preflight.json with a PASS/FAIL per infrastructure criterion; zero model calls."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
TEACHERS = ("anthropic", "openai", "google")


def rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-root", type=Path, required=True, help="$WORK/raw/preflight")
    ap.add_argument("--scored-root", type=Path, required=True, help="dir holding scored_preflight_<teacher>.jsonl")
    ap.add_argument("--out", type=Path, default=EXP / "results" / "preflight.json")
    a = ap.parse_args()
    state = json.loads((EXP / "results" / "runs_state.json").read_text())
    out, all_ok = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "task_id": "mbpp__preflight_task_1", "teachers": {}}, True
    for t in TEACHERS:
        run = state["runs"].get(f"preflight/{t}", {})
        receipt = (rows(EXP / "results" / "receipts" / "preflight" / f"{t}.jsonl") or [{}])[0]
        cell = (rows(a.raw_root / t / "cells.jsonl") or [{}])[0]
        scored = (rows(a.scored_root / f"scored_preflight_{t}.jsonl") or [{}])[0]
        cfg = receipt.get("config") or {}
        checks = {
            "served_one_request": receipt.get("requests_sent") == 1 and cell.get("served") is True,
            "no_fallback": not receipt.get("fallback"),
            "selector_delivered": receipt.get("selector") == run.get("selector"),
            "max_tokens_delivered": str(cfg.get("max_tokens")) == run.get("kwargs", {}).get("max_tokens"),
            "effort_delivered": (cfg.get("compute_effort") or cfg.get("reasoning_effort")) == (run.get("kwargs", {}).get("compute_effort") or run.get("kwargs", {}).get("reasoning_effort")),
            "prompt_hash_matches_pack": cell.get("prompt_hash_matches_pack") is True,
            # A completion that arrives must come back through the service's collect-only read-back; a `model_error`
            # (the provider returned an error instead of a completion) is a recorded model outcome, not a transport fault.
            "lean_collected_by_service_when_measured": (cell.get("lean_source") == "service_collected") if receipt.get("status") == "measured" else True,
            "scored_end_to_end": scored.get("scored") is True or (receipt.get("status") != "measured" and scored.get("failure_class") == "no_lean"),
            "model_outcome_recorded": receipt.get("status") in {"measured", "incomplete", "model_error"},
        }
        if t == "google":
            checks["temperature_delivered"] = cfg.get("temperature") == 1.0
        ok = all(checks.values())
        all_ok &= ok
        out["teachers"][t] = {
            "run_id": run.get("run_id"), "selector": run.get("selector"), "kwargs_sent": run.get("kwargs"), "agent_status": receipt.get("status"),
            "finish_reason": cell.get("finish_reason"), "requests_sent": receipt.get("requests_sent"), "delivered_config": cfg,
            "provider_endpoint": receipt.get("provider_endpoint"), "usage": receipt.get("usage"), "cost_usd": receipt.get("cost_usd"),
            "wall_seconds": receipt.get("wall_seconds"), "extraction": receipt.get("extraction"), "lean_bytes": cell.get("lean_bytes"),
            "lean_sha256": cell.get("lean_sha256"), "service_solution_sha256": cell.get("solution_sha256_service"),
            "score": {k: scored.get(k) for k in ("compiles", "IC_tests", "IC_proofs", "n_examples", "n_theorems_stated", "n_theorems_proved",
                                                  "kernel_n_sorry_ax", "kernel_n_native_decide", "kernel_n_declared_axiom", "n_vacuous", "kernel_binary", "failure_class")},
            "infrastructure_checks": checks, "infrastructure_pass": ok,
        }
    out["charges_usd_reported_total"] = round(sum((v.get("cost_usd") or 0.0) for v in out["teachers"].values()), 4)
    out["verdict"] = "PASS" if all_ok else "FAIL"
    out["meaning"] = ("PASS means every teacher's preflight cell was served by exactly one request with the locked selector and settings, the prompt bytes "
                      "matched the pack, the service collected the file and the frozen scorer scored it end to end; the scientific outcome (kept or not) "
                      "is recorded but is not a pass criterion.")
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], **{t: {"status": v["agent_status"], "finish": v["finish_reason"], "cost": v["cost_usd"], "class": v["score"]["failure_class"],
                                                      "checks_failed": [k for k, ok in v["infrastructure_checks"].items() if not ok]} for t, v in out["teachers"].items()}}, indent=1))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
