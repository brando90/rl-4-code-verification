#!/bin/bash
# TLDR: Sherlock fallback setup on the LOGIN node (downloads only): reasoning-gym into $PYLIB for the image's python, GSM8K + models at pinned revisions; the item build runs as a CPU job (cpu.sbatch build).
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ -f $SIF ] || { echo "missing $SIF (rebuild with AT-476 pull_image.sh)"; exit 2; }
# pycosat has no wheel; the image has no compiler, and e18a_common registers a stub (no family here uses SAT)
apptainer exec $SIF python3 -m pip install -q --target $PYLIB --no-deps "reasoning-gym==0.1.25"
apptainer exec $SIF python3 -m pip install -q --target $PYLIB arckit==0.1.0 bfi==1.0.4 cellpylib==2.4.0 magiccube==0.3.0 pyfiglet==1.0.2 tabulate==0.9.0 zss pytz sympy pyyaml pyarrow pytest
G=$B/gsm8k_test.parquet
[ -f $G ] || curl -sSL -o $G "https://huggingface.co/datasets/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/test-00000-of-00001.parquet"
echo "ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59  $G" | sha256sum -c -
apptainer exec -B /scratch --env HF_HOME=$B/cache/hf,MODELS_DIR=$MODELS_DIR $SIF python3 - <<'PY'
import os
from huggingface_hub import snapshot_download
M = {"qwen3_0p6b": ("Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"),
     "qwen3_1p7b": ("Qwen/Qwen3-1.7B", "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e")}
for tag, (repo, rev) in M.items():
    d = os.path.join(os.environ["MODELS_DIR"], tag)
    snapshot_download(repo, revision=rev, local_dir=d, allow_patterns=["*.json", "*.safetensors", "*.txt", "tokenizer*"])
    open(os.path.join(d, "REVISION"), "w").write(rev + "\n")
    print(tag, "->", d)
PY
echo "PREPARE (login) OK; next: sbatch cpu.sbatch build"
