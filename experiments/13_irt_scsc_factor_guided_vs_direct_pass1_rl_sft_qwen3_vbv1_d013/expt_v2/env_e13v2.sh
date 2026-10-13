#!/usr/bin/env bash
# TLDR: Keep experiment-13 version-2 caches and temporary files in its owned work root.
export WR=/lfs/skampere1/0/brando9/rl4cv_e13v2
export PATH="$WR/venv/bin:$HOME/.elan/bin:$PATH"
export TMPDIR="$WR/tmp"
export PIP_CACHE_DIR="$WR/cache/pip"
export HF_HOME="$WR/cache/huggingface"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export PYTHONPATH="$WR/rl-4-code-verification/src"
export E13_LAKE_DIR=/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src
export E13_SCORER_ROOT=/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench_scorer
export VERIBENCH_ROOT=/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench
