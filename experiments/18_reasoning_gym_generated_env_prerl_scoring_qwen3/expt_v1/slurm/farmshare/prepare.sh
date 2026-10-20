#!/bin/bash
# TLDR: one-time setup in the OnDemand JupyterLab terminal (a compute node with internet): CPU venv, GSM8K + model downloads at pinned revisions, item build, CPU tests.
# usage: bash $HOME/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/prepare.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"
unset HF_HUB_OFFLINE   # downloads happen here, jobs stay offline
# 1. CPU venv (python3.12 from /usr/bin, not Jupyter's 3.14; pycosat compiles with the node's gcc)
if [ ! -x $E18A_VENV/bin/python ]; then /usr/bin/python3.12 -m venv $E18A_VENV; fi
$E18A_VENV/bin/pip install -q --upgrade pip
$E18A_VENV/bin/pip install -q "reasoning-gym==0.1.25" numpy pyarrow pytest
$E18A_VENV/bin/python -c "import importlib.metadata as m; print('reasoning-gym', m.version('reasoning-gym'))"
# 2. GSM8K test parquet at the pinned revision
G=$E18A_HOME/gsm8k_test.parquet
[ -f $G ] || curl -sSL -o $G "https://huggingface.co/datasets/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/test-00000-of-00001.parquet"
echo "ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59  $G" | sha256sum -c -
# 3. Model snapshots at the pinned revisions (weights, config, tokenizer only)
$FS_HF/bin/python - <<'PY'
import os
from huggingface_hub import snapshot_download
M = {"qwen3_0p6b": ("Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"),
     "qwen3_1p7b": ("Qwen/Qwen3-1.7B", "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"),
     "qwen3_4b": ("Qwen/Qwen3-4B", "1cfa9a7208912126459214e8b04321603b3df60c")}
for tag, (repo, rev) in M.items():
    d = os.path.join(os.environ["MODELS_DIR"], tag)
    snapshot_download(repo, revision=rev, local_dir=d, allow_patterns=["*.json", "*.safetensors", "*.txt", "merges.txt", "vocab.json", "tokenizer*"])
    open(os.path.join(d, "REVISION"), "w").write(rev + "\n")
    print(tag, "->", d, sorted(os.listdir(d))[:8])
PY
# 4. Items: 38 sets x 256 (frozen); refuses a GSM8K file with another sha256
$E18A_VENV/bin/python $CODE/build.py --out $RUN --gsm8k-parquet $G
ls $RUN/items/*.jsonl | wc -l   # expect 38
# 5. CPU tests (generators, verifiers, metric code, fake-model end to end)
cd $E18A_HOME/code && PYTHONPATH=src $E18A_VENV/bin/python -m pytest -q -p no:cacheprovider tests/test_e18a_reasoning_gym.py
echo "PREPARE OK"
