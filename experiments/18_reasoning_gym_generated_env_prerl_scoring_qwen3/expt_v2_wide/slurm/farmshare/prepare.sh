#!/bin/bash
# TLDR: one-time setup in the OnDemand JupyterLab terminal (a compute node with internet): reuse v1's CPU venv, GSM8K file and Qwen3 snapshots (fetch any that are missing), build the v2 items (they must match the frozen probe's hashes), CPU tests.
# usage: bash $HOME/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/prepare.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"
unset HF_HUB_OFFLINE   # downloads happen here, jobs stay offline
# 1. CPU venv (v1's; built here if v1 never ran: python3.12 from /usr/bin, pycosat compiles with the node's gcc)
if [ ! -x $E18A_VENV/bin/python ]; then /usr/bin/python3.12 -m venv $E18A_VENV; fi
$E18A_VENV/bin/pip install -q "reasoning-gym==0.1.25" numpy pyarrow pytest
$E18A_VENV/bin/python -c "import importlib.metadata as m; print('reasoning-gym', m.version('reasoning-gym'))"
# 2. GSM8K test parquet at the pinned revision (v1's copy if present)
mkdir -p "$(dirname $GSM8K_PARQUET)"
[ -f $GSM8K_PARQUET ] || curl -sSL -o $GSM8K_PARQUET "https://huggingface.co/datasets/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/test-00000-of-00001.parquet"
echo "ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59  $GSM8K_PARQUET" | sha256sum -c -
# 3. Qwen3-0.6B / 1.7B snapshots at the pinned revisions (skipped when v1's are there with the right REVISION)
$FS_HF/bin/python - <<'PY'
import os
from huggingface_hub import snapshot_download
M = {"qwen3_0p6b": ("Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"),
     "qwen3_1p7b": ("Qwen/Qwen3-1.7B", "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e")}
for tag, (repo, rev) in M.items():
    d = os.path.join(os.environ["MODELS_DIR"], tag)
    rf = os.path.join(d, "REVISION")
    if os.path.exists(rf) and open(rf).read().strip() == rev:
        print(tag, "present at", rev[:12]); continue
    snapshot_download(repo, revision=rev, local_dir=d, allow_patterns=["*.json", "*.safetensors", "*.txt", "merges.txt", "vocab.json", "tokenizer*"])
    open(rf, "w").write(rev + "\n")
    print(tag, "->", d)
PY
# 4. Items: every environment in families_v2.json + 6 targets; refuses items that differ from probe_v2.jsonl
$E18A_VENV/bin/python $CODE/build.py --out $RUN --gsm8k-parquet $GSM8K_PARQUET
N=$($E18A_VENV/bin/python -c "import json; d=json.load(open('$CODE/families_v2.json')); print(d['n_envs'] + 6)")
echo "item sets: $(ls $RUN/items/*.jsonl | wc -l) (expect $N)"
# 5. CPU tests (probe rules, generators, verifiers, metric code, fake-model end to end)
cd $E18V2_HOME/code && PYTHONPATH=src $E18A_VENV/bin/python -m pytest -q -p no:cacheprovider tests/test_e18a_v2_wide.py
echo "PREPARE OK"
