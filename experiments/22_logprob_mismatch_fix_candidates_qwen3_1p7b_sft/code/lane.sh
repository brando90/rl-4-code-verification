#!/bin/bash
# rl4cv e22: lane runner. usage: lane.sh GPU LANE
export CUDA_VISIBLE_DEVICES=$1 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_USE_FLASHINFER_SAMPLER=0
W=/lfs/skampere1/0/brando9/rl4cv_e22_mismatch_fix; PY=$W/venv/bin/python; M=$W/ckpt/step_658; PK=$W/pack
cd $W; mkdir -p out
$PY -c "import json,vllm,torch,transformers;print(json.dumps({'vllm':vllm.__version__,'torch':torch.__version__,'transformers':transformers.__version__,'gpu':torch.cuda.get_device_name(0),'model':'$M','T':0.6,'top_p':0.95,'top_k':20,'max_tokens':3072,'host':'skampere1'}))" > out/versions_lane$2.json
g(){ $PY gen.py --model $M --packs $PK --dtype $1 --mode processed_logprobs --gpu-util $3 --out out/gen_$2.jsonl > out/gen_$2.log 2>&1; }
s(){ $PY score.py --model $M --gen out/gen_$1.jsonl --dtype $2 $4 --out out/score_$1__$3.json > out/score_$1__$3.log 2>&1; }
if [ $2 = A ]; then
  g bfloat16 bf16proc 0.4 && s bf16proc bfloat16 bf16 && s bf16proc float16 fp16 && s bf16proc bfloat16 bf16_lmheadfp32 --lm-head-fp32 && s bf16proc float32 fp32
  g float16 fp16proc 0.4 && s fp16proc float16 fp16 && s fp16proc bfloat16 bf16 && s fp16proc float32 fp32
else
  g float32 fp32proc 0.5 && s fp32proc float32 fp32 && s fp32proc bfloat16 bf16 && s fp32proc float16 fp16
fi
echo done > out/DONE_$2
