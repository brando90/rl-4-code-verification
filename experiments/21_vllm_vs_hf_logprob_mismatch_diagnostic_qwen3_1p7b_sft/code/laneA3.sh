cd /lfs/mercury1/0/brando9/rl4cv_e21_logprob_mismatch
export CUDA_VISIBLE_DEVICES=8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/lfs/mercury1/0/brando9/vb120/venv_cu129/bin/python
M=ckpt/step_658
$PY score.py --model $M --gen out/gen_bf16proc.jsonl --dtype bfloat16 --lm-head-fp32 --out out/score_bf16proc__bf16_lmheadfp32.json > out/score_bf16proc__bf16_lmheadfp32.log 2>&1
$PY score.py --model $M --gen out/gen_bf16raw.jsonl --dtype bfloat16 --T 1.0 --out out/score_bf16raw__bf16_T1.json > out/score_bf16raw__bf16_T1.log 2>&1
echo done > out/DONE_A3
