#!/bin/bash
# rl4cv e21 (mercury1 port): vLLM vs trainer log-prob mismatch diagnostic. One GPU (RTX A4000 16GB), released at exit.
export CUDA_VISIBLE_DEVICES=${GPU:-8} HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
W=/lfs/mercury1/0/brando9/rl4cv_e21_logprob_mismatch; PY=/lfs/mercury1/0/brando9/vb120/venv_cu129/bin/python
M=$W/ckpt/step_658; PK=$W/pack
cd $W; mkdir -p out
$PY -c "import json,vllm,torch,transformers;print(json.dumps({'vllm':vllm.__version__,'torch':torch.__version__,'transformers':transformers.__version__,'gpu':torch.cuda.get_device_name(0),'model':'$M','T':0.6,'top_p':0.95,'top_k':20,'max_tokens':3072,'host':'mercury1'}))" > out/versions.json
g(){ $PY gen.py --model $M --packs $PK --dtype $1 --mode $2 --gpu-util $4 --out out/gen_$3.jsonl > out/gen_$3.log 2>&1; }
s(){ $PY score.py --model $M --gen out/gen_$1.jsonl --dtype $2 $4 --out out/score_$1__$3.json > out/score_$1__$3.log 2>&1; }
g bfloat16 processed_logprobs bf16proc 0.85 && s bf16proc bfloat16 bf16 && s bf16proc bfloat16 bf16_lmheadfp32 --lm-head-fp32 && s bf16proc float32 fp32
g bfloat16 raw_logprobs bf16raw 0.85 && s bf16raw bfloat16 bf16
g float32 processed_logprobs fp32proc 0.85 && s fp32proc float32 fp32 && s fp32proc bfloat16 bf16
echo ALLDONE > out/DONE
