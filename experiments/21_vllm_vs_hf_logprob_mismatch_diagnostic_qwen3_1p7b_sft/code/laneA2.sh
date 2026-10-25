#!/bin/bash
# e21 round 2 on GPU8: fix lm_head fp32 dtype bug; bf16 raw logprobs gen with flashinfer sampler off (its JIT build failed)
export CUDA_VISIBLE_DEVICES=8 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True VLLM_USE_FLASHINFER_SAMPLER=0
W=$PWD; PY=/lfs/mercury1/0/brando9/vb120/venv_cu129/bin/python; M=$W/ckpt/step_658; PK=$W/pack
g(){ $PY gen.py --model $M --packs $PK --dtype $1 --mode $2 --gpu-util $4 --out out/gen_$3.jsonl > out/gen_$3.log 2>&1; }
s(){ $PY score.py --model $M --gen out/gen_$1.jsonl --dtype $2 $4 --out out/score_$1__$3.json > out/score_$1__$3.log 2>&1; }
s bf16proc bfloat16 bf16_lmheadfp32 --lm-head-fp32
g bfloat16 raw_logprobs bf16raw 0.85 && s bf16raw bfloat16 bf16
echo done > out/DONE_A2
