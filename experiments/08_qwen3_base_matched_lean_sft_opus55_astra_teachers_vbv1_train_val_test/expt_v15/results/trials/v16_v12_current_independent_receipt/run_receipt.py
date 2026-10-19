#!/usr/bin/env python3
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path


ROOT = Path("/lfs/skampere1/0/eth127/rl4cv_tiny_training")
TRIAL = ROOT / "adaptive_1p7b_campaign/trials/v16_v12_current_independent_receipt"
EXP = ROOT / "repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
RAW = ROOT / "corpus_training_v12/validation/v12_current/raw.jsonl"
SCORED = ROOT / "corpus_training_v12/validation/v12_current/scored.jsonl"
RECORDED = ROOT / "corpus_training_v12/analysis/v12_current_summary.json"
IDS = EXP / "expt_v1/results/split/vbv1_validation_task_ids.txt"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main() -> int:
    started = time.time()
    terminal_path = TRIAL / "terminal.json"
    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["TINY_RUN_ROOT"] = str(ROOT)
        sys.path[:0] = [str(ROOT / "repo/src"), str(EXP / "expt_v6")]
        import analyze

        analyze.RUN = TRIAL / "raw"
        analyze.RUN.mkdir(parents=True, exist_ok=True)
        expected = json.loads(RECORDED.read_text())
        ids = IDS.read_text().splitlines()
        raw_rows = analyze.read(RAW)
        scored_rows = analyze.read(SCORED)
        recomputed, vector = analyze.evaluate("v12_current", raw_rows, scored_rows, ids)
        compared = ["declared_cells", "scored_cells", "successes", "success_rate"]
        passed = all(recomputed[key] == expected[key] for key in compared)
        input_hash = hashlib.sha256(
            (digest(RAW) + digest(SCORED) + json.dumps(expected, sort_keys=True)).encode()
        ).hexdigest()
        write(
            TRIAL / "receipt.json",
            {
                "status": "COMPLETE" if passed else "MISMATCH",
                "passed": passed,
                "input_hash": input_hash,
                "raw_path": str(RAW),
                "scored_path": str(SCORED),
                "recorded_summary_path": str(RECORDED),
                "recomputed": recomputed,
                "recorded": {key: expected[key] for key in compared},
                "source_hashes_path": str(TRIAL / "sources/SHA256SUMS"),
                "declared_validation_ids": len(ids),
                "observed_unix": time.time(),
            },
        )
        with (TRIAL / "per_cell_recompute.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["row_index", "frozen_evaluator_value"])
            for row_index, value in enumerate(vector):
                writer.writerow([row_index, json.dumps(value, sort_keys=True)])
        write(
            terminal_path,
            {
                "status": "COMPLETE" if passed else "FAILED",
                "phase": "independent_receipt_recompute",
                "started_unix": started,
                "ended_unix": time.time(),
                "test_split_opened": False,
                "paid_model_calls": 0,
                "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
            },
        )
        return 0 if passed else 2
    except Exception as exc:
        write(
            terminal_path,
            {
                "status": "FAILED",
                "phase": "independent_receipt_recompute",
                "started_unix": started,
                "ended_unix": time.time(),
                "error": repr(exc),
                "test_split_opened": False,
                "paid_model_calls": 0,
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
