cd /lfs/mercury1/0/brando9/rl4cv_e21_logprob_mismatch
export CUDA_VISIBLE_DEVICES=9 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/lfs/mercury1/0/brando9/vb120/venv_cu129/bin/python
M=ckpt/step_658
$PY score.py --model $M --gen out/gen_bf16proc.jsonl --dtype float32 --eager --out out/score_bf16proc__fp32.json > out/score_bf16proc__fp32.log 2>&1
$PY score.py --model $M --gen out/gen_fp32proc.jsonl --dtype float32 --eager --out out/score_fp32proc__fp32.json > out/score_fp32proc__fp32.log 2>&1
echo done > out/DONE_B3
