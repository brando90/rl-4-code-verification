# TLDR: paths and venvs shared by every experiment 18a FarmShare script (source it; nothing runs).
export E18A_HOME=${E18A_HOME:-$HOME/e18a}
export CODE=$E18A_HOME/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1
export RUN=$E18A_HOME/run
export MODELS_DIR=$E18A_HOME/models
export HF_HOME=$HOME/hf_cache
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
export FS_HF=$HOME/venvs/fs_hf      # shared vLLM 0.32.0 + transformers 5.19.0 (AT-615); its activate sets CUDA_HOME, VLLM_USE_FLASHINFER_SAMPLER=0
export E18A_VENV=$HOME/venvs/e18a   # CPU: reasoning-gym 0.1.25, numpy, pyarrow, pytest
mkdir -p $E18A_HOME/logs
# model tag for array index i of gen.sbatch: tag shard nshards
e18a_task() { sed -n "$(( $1 + 2 ))p" $CODE/slurm/farmshare/tasks.tsv; }
