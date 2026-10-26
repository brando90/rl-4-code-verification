#!/bin/bash
# TLDR: Sherlock setup on the LOGIN node (downloads only, ~10 min): reasoning-gym into $PYLIB for the image's python, pinned GSM8K parquet, the pinned Qwen3-1.7B snapshot (reuses 18a's copy when present). Then run tests with sbatch smoke.sbatch.
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ -f $SIF ] || { echo "missing $SIF (rebuild with AT-476 pull_image.sh)"; exit 2; }
[ -d $B/code/src/rl4cv ] || { echo "put the package in $B/code first (SUBMIT.md step 2)"; exit 2; }
if [ -d $SCRATCH/e18a/pylib/reasoning_gym ] && [ ! -d $PYLIB ]; then cp -r $SCRATCH/e18a/pylib $PYLIB; fi
apptainer exec $SIF python3 -m pip install -q --target $PYLIB --no-deps "reasoning-gym==0.1.25"
apptainer exec $SIF python3 -m pip install -q --target $PYLIB arckit==0.1.0 bfi==1.0.4 cellpylib==2.4.0 magiccube==0.3.0 pyfiglet==1.0.2 tabulate==0.9.0 zss pytz sympy pyyaml pyarrow pytest
if [ ! -f $GSM8K ]; then
  if [ -f $SCRATCH/e18a/gsm8k_test.parquet ]; then cp $SCRATCH/e18a/gsm8k_test.parquet $GSM8K
  else curl -sSL -o $GSM8K "https://huggingface.co/datasets/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/test-00000-of-00001.parquet"; fi
fi
echo "ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59  $GSM8K" | sha256sum -c -
mkdir -p $MODELS_DIR
if [ -f $SCRATCH/e18a/models/qwen3_1p7b/REVISION ] && [ ! -e $MODELS_DIR/qwen3_1p7b ]; then ln -s $SCRATCH/e18a/models/qwen3_1p7b $MODELS_DIR/qwen3_1p7b; fi
apptainer exec -B /scratch --env HF_HOME=$B/cache/hf,MODELS_DIR=$MODELS_DIR $SIF python3 - <<'PY'
import os
from huggingface_hub import snapshot_download
repo, rev = "Qwen/Qwen3-1.7B", "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
d = os.path.join(os.environ["MODELS_DIR"], "qwen3_1p7b")
if not os.path.exists(os.path.join(d, "REVISION")):
    snapshot_download(repo, revision=rev, local_dir=d, allow_patterns=["*.json", "*.safetensors", "*.txt", "tokenizer*"])
    open(os.path.join(d, "REVISION"), "w").write(rev + "\n")
print("qwen3_1p7b ->", d, open(os.path.join(d, "REVISION")).read().strip())
PY
echo "PREPARE (login) OK; next: sbatch smoke.sbatch"
