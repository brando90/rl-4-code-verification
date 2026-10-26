#!/usr/bin/env bash
set -euo pipefail

trial_dir=/lfs/skampere1/0/eth127/rl4cv_tiny_training/adaptive_1p7b_campaign/trials/v16_v12_current_independent_receipt
protocol_sha256=$(sha256sum "$trial_dir/PROTOCOL.md" | awk '{print $1}')
started_unix=$(python3 -c 'import time; print(time.time())')
python3 - "$trial_dir" "$protocol_sha256" "$started_unix" <<'PY'
import json
import sys
from pathlib import Path

trial_dir = Path(sys.argv[1])
manifest = {
    "trial_id": "v16_v12_current_independent_receipt",
    "phase": "independent_receipt_recompute",
    "pid": None,
    "session": "rl4cv-adaptive-v16-independent-v12",
    "summary_path": None,
    "terminal_path": str(trial_dir / "terminal.json"),
    "raw_path": "/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v12/validation/v12_current/raw.jsonl",
    "scored_path": "/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v12/validation/v12_current/scored.jsonl",
    "receipt_path": str(trial_dir / "receipt.json"),
    "protocol_path": str(trial_dir / "PROTOCOL.md"),
    "protocol_sha256": sys.argv[2],
    "source_revision": "frozen V6 evaluator paths and source hashes in sources/SHA256SUMS",
    "started_unix": float(sys.argv[3]),
    "paid_model_calls": 0,
    "gpu": None,
    "test_split_opened": False,
}
(trial_dir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
PY
exec env -u OPENAI_API_KEY -u OPENAI_BASE_URL -u OPENAI_API_BASE CUDA_VISIBLE_DEVICES= TINY_RUN_ROOT=/lfs/skampere1/0/eth127/rl4cv_tiny_training \
  python3 "$trial_dir/run_receipt.py" >"$trial_dir/launcher.log" 2>&1
