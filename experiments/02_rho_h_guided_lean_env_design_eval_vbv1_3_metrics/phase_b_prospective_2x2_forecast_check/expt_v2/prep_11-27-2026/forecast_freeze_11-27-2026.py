"""Prepare a 02B v2 forecast freeze. Refuse an incomplete prediction and refuse any outcome read.

The default command writes nothing. A freeze happens only with --commit-freeze, a complete
prediction, and outcomes_observed left false. OpenR1-Math coefficients cannot stand in for Lean probes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[5] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rl4cv.forecast import freeze_forecast

PREDICTION_KEYS = (
    "winning_environment",
    "expected_external_test_delta",
    "rho_full_file",
    "H_full_file",
    "rho_theorem_completion",
    "H_theorem_completion",
    "standardizer_source",
)
OUTCOME_MARKERS = ("outcome", "scored", "pass_at", "utility", "reward_mean")


def skeleton() -> dict:
    return {
        "experiment": "02B v2",
        "status": "NOT_FROZEN",
        "model": {
            "id": "Qwen/Qwen3-1.7B-Base",
            "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        },
        "arms": ["full_file", "theorem_completion"],
        "seeds_per_arm": 2,
        "optimizer_steps": 64,
        "reward": "kernel_binary",
        "lean": "4.22.0",
        "veribench_in_training": False,
        "prediction": None,
        "outcomes_read": False,
    }


def assert_ready(forecast: dict, *, outcomes_observed: bool, outcome_paths: list[str]) -> dict:
    if outcomes_observed or forecast.get("outcomes_read"):
        raise ValueError("a prospective forecast must be frozen before its outcomes are observed")
    for path in outcome_paths:
        lowered = path.lower()
        if any(marker in lowered for marker in OUTCOME_MARKERS):
            raise ValueError(f"refusing to read an outcome path: {path}")
        if Path(path).exists() and "forecast" not in Path(path).name:
            raise ValueError(f"refusing to open {path}; this command reads the forecast file only")
    prediction = forecast.get("prediction")
    if not isinstance(prediction, dict):
        raise ValueError("prediction is empty; do not invent a winning environment or a delta")
    missing = [key for key in PREDICTION_KEYS if prediction.get(key) is None]
    if missing:
        raise ValueError("prediction is missing " + ", ".join(missing))
    if prediction.get("winning_environment") not in {"full_file", "theorem_completion"}:
        raise ValueError("winning_environment must be one of the two locked arms")
    if prediction.get("standardizer_source") == "paper_frozen_14b_model":
        raise ValueError("OpenR1-Math coefficients are not Lean-fold standardizers")
    if prediction.get("synthetic"):
        raise ValueError("a synthetic prediction cannot be frozen into the experiment ledger")
    return prediction


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forecast", type=Path, help="JSON with a completed prediction. Omit to print the skeleton.")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--commit-freeze", action="store_true")
    parser.add_argument("--outcomes-observed", action="store_true")
    parser.add_argument("--outcome-path", action="append", default=[])
    args = parser.parse_args(argv)
    if args.forecast is None:
        print(json.dumps(skeleton(), indent=2))
        print("NOT FROZEN: pass --forecast after the pre-RL probes exist, and do not read a training outcome first.")
        return 2
    forecast = json.loads(args.forecast.read_text())
    try:
        assert_ready(forecast, outcomes_observed=args.outcomes_observed, outcome_paths=args.outcome_path)
    except ValueError as error:
        print(f"NOT FROZEN: {error}")
        return 2
    if not args.commit_freeze:
        print("NOT FROZEN: prediction is complete on paper; pass --commit-freeze only before any training outcome is read.")
        return 2
    if args.out_dir is None:
        print("NOT FROZEN: --out-dir is required")
        return 2
    # The caller has asserted, in this flag, that no outcome was read. freeze_forecast
    # also refuses outcomes_observed=True.
    try:
        entry = freeze_forecast(forecast, args.out_dir, "02b_v2_environment_choice", outcomes_observed=False)
    except FileExistsError as error:
        print(f"NOT FROZEN: {error}")
        return 2
    print(json.dumps(entry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
