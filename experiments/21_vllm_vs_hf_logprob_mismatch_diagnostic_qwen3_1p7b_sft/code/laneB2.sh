#!/bin/bash
export CUDA_VISIBLE_DEVICES=9 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
W=$PWD; PY=/lfs/mercury1/0/brando9/vb120/venv_cu129/bin/python; M=$W/ckpt/step_658
s(){ $PY score.py --model $M --gen out/gen_$1.jsonl --dtype $2 $4 --out out/score_$1__$3.json > out/score_$1__$3.log 2>&1; }
s fp32proc float32 fp32
s fp32proc bfloat16 bf16
s bf16proc float32 fp32
echo done > out/DONE_B2
