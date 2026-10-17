#!/usr/bin/env bash
# TLDR: Run v3 offline with every mutable cache and temporary file outside immutable v2.
export E13_V3_ROOT=/lfs/skampere1/0/brando9/rl4cv_e13v3
export PATH=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin:$HOME/.elan/bin:$PATH
export TMPDIR=$E13_V3_ROOT/tmp
export HF_HOME=$E13_V3_ROOT/cache/huggingface
export XDG_CACHE_HOME=$E13_V3_ROOT/cache
export TRITON_CACHE_DIR=$E13_V3_ROOT/cache/triton
export TORCH_EXTENSIONS_DIR=$E13_V3_ROOT/cache/torch_extensions
export TORCH_HOME=$E13_V3_ROOT/cache/torch
export CUDA_CACHE_PATH=$E13_V3_ROOT/cache/cuda
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1 WANDB_MODE=disabled
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export NEMO_RL_PY_EXECUTABLES_SYSTEM=1
export PYTHONPATH=$E13_V3_ROOT/rl-4-code-verification/src
export E13_LAKE_DIR=/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src
export E13_SCORER_ROOT=/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench_scorer
export VERIBENCH_ROOT=/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench
