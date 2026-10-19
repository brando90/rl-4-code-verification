#!/usr/bin/env bash
set -euo pipefail

ROOT=/lfs/skampere1/0/eth127/rl4cv_tiny_training
EXP="$ROOT/repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v17"
RUN="$ROOT/corpus_training_v17"
PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python

mkdir -p "$RUN"
if ! env CUDA_VISIBLE_DEVICES= TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 "$PY" -u "$EXP/assemble.py" >"$RUN/assembly.log" 2>&1; then
  /usr/bin/python3 - "$RUN/terminal.json" <<'PY'
import json,sys,time
from pathlib import Path
p=Path(sys.argv[1]);p.write_text(json.dumps({'status':'ASSEMBLY_FAILED','ended_unix':time.time(),'test_split_opened':False},indent=2)+'\n')
PY
  exit 1
fi
set +e
env CUDA_VISIBLE_DEVICES= TOKENIZERS_PARALLELISM=false "$PY" -u "$EXP/dispatch.py"
code=$?
set -e
/usr/bin/python3 - "$RUN" "$(dirname "$0")" "$code" <<'PY'
import json
import shutil
import sys
import time
from pathlib import Path

run = Path(sys.argv[1])
trial = Path(sys.argv[2])
exit_code = int(sys.argv[3])
source = run / 'adapt' / 'terminal.json'
if not source.exists():
    source = run / 'terminal.json'
destination = trial / 'terminal.json'
if source.exists():
    shutil.copyfile(source, destination)
    payload = json.loads(destination.read_text())
else:
    payload = {
        'status': 'LAUNCHER_EXITED_WITHOUT_TERMINAL',
        'test_split_opened': False,
    }
payload['launcher_exit_code'] = exit_code
payload['launcher_ended_unix'] = time.time()
destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
PY
exit "$code"
