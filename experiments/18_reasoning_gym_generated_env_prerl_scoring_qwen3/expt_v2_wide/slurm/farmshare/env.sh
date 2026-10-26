# TLDR: paths and venvs shared by every experiment 18a v2 FarmShare script (source it; nothing runs).
export E18V2_HOME=${E18V2_HOME:-$HOME/e18a_v2}
export CODE=$E18V2_HOME/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide
export RUN=$E18V2_HOME/run
export MODELS_DIR=${MODELS_DIR:-$HOME/e18a/models}   # v1's pinned Qwen3-0.6B/1.7B snapshots (prepare.sh fetches them if missing)
export GSM8K_PARQUET=${GSM8K_PARQUET:-$HOME/e18a/gsm8k_test.parquet}
export HF_HOME=$HOME/hf_cache
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
export FS_HF=$HOME/venvs/fs_hf      # shared vLLM 0.32.0 + transformers 5.19.0 (AT-615)
export E18A_VENV=$HOME/venvs/e18a   # v1's CPU venv: reasoning-gym 0.1.25 (+ pycosat), numpy, pyarrow, pytest
# The same two lines fs_hf's activate sets: without them vLLM dies at warmup (no nvcc; flashinfer JIT vs nvcc 13.4).
export CUDA_HOME=$FS_HF/lib/python3.12/site-packages/nvidia/cu13
export VLLM_USE_FLASHINFER_SAMPLER=0
mkdir -p $E18V2_HOME/logs
# model tag for array index i of gen.sbatch: tag shard nshards
e18v2_task() { sed -n "$(( $1 + 2 ))p" $CODE/slurm/farmshare/tasks.tsv; }
