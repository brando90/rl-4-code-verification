#!/bin/bash
W=/lfs/skampere1/0/brando9/rl4cv_e23_fp16_smoke; cd $W
export PATH=/lfs/skampere1/0/brando9/.local/bin:$PATH UV_CACHE_DIR=/lfs/skampere1/0/brando9/rl4cv_e22_mismatch_fix/uv_cache
uv venv --python 3.12 venv > logs/venv.log 2>&1
uv pip install --python venv/bin/python vllm==0.30.0 transformers==5.17.0 trl==1.16.0 scipy==1.18.1 >> logs/venv.log 2>&1
echo SETUP_DONE rc=$? >> logs/venv.log
