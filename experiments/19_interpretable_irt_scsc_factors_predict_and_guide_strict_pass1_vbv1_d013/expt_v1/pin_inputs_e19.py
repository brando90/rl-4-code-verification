"""TLDR: Write expt_v1/input_pins_e19.json, the SHA-256 of every input experiment 19 reads, at protocol lock; the analysis refuses to run if any input later differs."""

from __future__ import annotations

import json

import analyze_e19 as A
import data_e19 as D


def main() -> None:
    pins = {"note": "SHA-256 of every input experiment 19 reads, computed at protocol lock before any real-data analysis; "
                    "the test-split id list is read only to guard against leaks.",
            "sha256": {k: D.sha256_file(p) for k, p in A.INPUT_FILES.items()},
            "paths": {k: str(p.relative_to(D.REPO)) for k, p in A.INPUT_FILES.items()}}
    D.PINS_FILE.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n")
    print(json.dumps(pins, indent=1))


if __name__ == "__main__":
    main()
