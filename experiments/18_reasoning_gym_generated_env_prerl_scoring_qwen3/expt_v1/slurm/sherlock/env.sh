# TLDR: paths for the Sherlock fallback of experiment 18a (AT-476 Apptainer image route); source it, nothing runs.
export B=$SCRATCH/e18a
export CODE=$B/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1
export RUN=$B/run MODELS_DIR=$B/models PYLIB=$B/pylib
export SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif   # vllm 0.30.0, torch 2.13.0+cu130 (AT-476)
mkdir -p $B/logs $B/cache
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
APPENV="PYTHONPATH=$PYLIB:$B/code/src,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=4,VLLM_WORKER_MULTIPROC_METHOD=spawn,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,HF_HOME=$B/cache/hf"
# Driver 550 (CUDA 12.4) vs image CUDA 13.0: use the image's forward-compat libcuda when it initialises (as gen.sh in AT-476).
e18a_ldenv() {
  local P="import torch; x=torch.ones(4, device='cuda'); print(torch.cuda.get_device_name(0), (x*2).sum().item())"
  if apptainer exec --nv $SIF env LD_LIBRARY_PATH=$CL python3 -c "$P" >&2; then echo ",LD_LIBRARY_PATH=$CL"
  elif apptainer exec --nv $SIF python3 -c "$P" >&2; then echo ""
  else echo "CUDA init failed with and without forward compat" >&2; return 3; fi
}
e18a_py() { apptainer exec -B /scratch --env "$APPENV" $SIF python3 "$@"; }   # CPU steps
e18a_task() { sed -n "$(( $1 + 2 ))p" $CODE/slurm/farmshare/tasks.tsv; }
