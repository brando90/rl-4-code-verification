# TLDR: paths for every experiment 18c script on skampere2 (source it; nothing runs). Everything lives in $B = /lfs/skampere2/0/brando9/at3570.
export B=${B:-/lfs/skampere2/0/brando9/at3570}
export CODE=$B/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3
export C18=$CODE/expt_18c C18B=$CODE/expt_18b
export PY=/lfs/skampere2/0/brando9/rl4cv_e08_v3_gen/venv_gen/bin/python   # vllm 0.30.0, torch 2.13.0+cu130, transformers 5.18.0 (same stack as 18b's Sherlock image)
export PYTHONPATH=$B/pylib:$B/code/src
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 VLLM_WORKER_MULTIPROC_METHOD=spawn
export XDG_CACHE_HOME=$B/cache VLLM_CACHE_ROOT=$B/cache/vllm TRITON_CACHE_DIR=$B/cache/triton HF_HOME=$B/cache/hf PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export MODELS_DIR=$B/models GSM8K=$B/gsm8k_test.parquet
export RUNS=$B/runs RES=$B/results
mkdir -p $B/logs $RUNS $RES/post $RES/train $B/claims
c18_task() { sed -n "$(( $1 + 1 ))p" $C18/skampere/tasks.tsv; }
c18_run_name() { echo "${1//\//__}__s$2"; }   # must equal common18b.run_name (checked by the tests)
# wait until the GPU holds < 2 GB (nobody else on it), at most 30 min
c18_gpu_free() { for i in $(seq 1 90); do u=$(nvidia-smi -i $CUDA_VISIBLE_DEVICES --query-gpu=memory.used --format=csv,noheader,nounits | head -1); [ "${u:-99999}" -lt 2000 ] && return 0; sleep 20; done; return 1; }
