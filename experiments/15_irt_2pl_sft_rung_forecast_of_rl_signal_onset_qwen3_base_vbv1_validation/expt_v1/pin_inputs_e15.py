"""TLDR: Write input_pins_e15.json, the SHA-256 of every file experiment 15 reads (validation-split per-task files of experiments 05/08, split id lists, manifests); it never lists or reads a test-split file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
E08 = "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results"
SIZE_TAG = {"1.7B": "1p7B", "4B": "4B", "8B": "8B", "14B": "14B"}
SFT_FRACS = ("0.125", "0.25", "0.5", "0.75", "1.0")


def input_files() -> list[str]:
    files = ["split/vbv1_validation_task_ids.txt", "split/vbv1_test_task_ids.txt", "ladder_manifest.json",
             "ladder_manifest_base14b.json", "sft_schedule.json"]
    files += [f"ladder/base_{SIZE_TAG[s]}_e05_validation_per_task.csv" for s in ("1.7B", "4B", "8B")]
    files.append("ladder/base14b_validation_per_task.csv")
    files += [f"ladder/sft_{SIZE_TAG[s]}_f{f.replace('.', 'p')}_validation_per_task.csv" for s in SIZE_TAG for f in SFT_FRACS]
    # Outcome files live under ladder/; none of them may be a test-split file. The split id lists hold no outcomes.
    assert not any("test" in Path(f).name for f in files if f.startswith("ladder/"))
    return files


def main() -> None:
    root = REPO / E08
    pins = {f: hashlib.sha256((root / f).read_bytes()).hexdigest() for f in input_files()}
    out = HERE / "input_pins_e15.json"
    out.write_text(json.dumps({"root": E08, "note": "SHA-256 of every input file experiment 15 reads, computed 10-14-2026 "
                               "before any outcome was analysed; test-split files are never listed or read.",
                               "sha256": pins}, indent=1, sort_keys=True) + "\n")
    val = set((root / "split/vbv1_validation_task_ids.txt").read_text().split())
    test = set((root / "split/vbv1_test_task_ids.txt").read_text().split())
    print(len(pins), "pins;", len(val), "validation ids;", len(test), "test ids;", len(val & test), "overlap")
    print("input_pins_e15.json sha256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
