#!/bin/bash
#SBATCH -J e25_stage2a
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 16
#SBATCH --mem=128G
#SBATCH -t 04:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e25ckpt/logs/%x_%j.log
# TLDR: Stage 2a of the checkpoint-reuse plan on one Sherlock L40S/H100: the fp16 GRPO trainer (stage2a/train_e25ckpt.py) with the real strict Lean
# reward, kept checkpoints, steplog.jsonl and the mismatch gate. Defaults are the tiny dry run (2 updates, 2 groups, 1024 new tokens); override with
# sbatch --export=ALL,UPDATES=8,NGROUPS=16,MAXTOK=12288,SAVEAT=8,NAME=gate8 ... for the 8-update gate run at the frozen sizes.
set -uo pipefail
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Slurm must assign the GPU}"
UPDATES=${UPDATES:-2}; GROUPS_PER=${NGROUPS:-2}; MAXTOK=${MAXTOK:-1024}; SAVEAT=${SAVEAT:-1,2}; NAME=${NAME:-dry}
E20=$SCRATCH/rl4cv_sherlock/e20; E25=$SCRATCH/rl4cv_sherlock/e25ckpt; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$SCRATCH/rl4cv_sherlock/grading
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif; VENV=$E20/venv_trl
SRC=$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf          # the Exp 20 start policy (08 expt_v4 seed 20260831, Qwen3-1.7B Lean SFT)
START=$E25/start_fp16; RUNS=$E25/runs/$NAME
mkdir -p $E25/logs $RUNS $B/cache
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN|OAUTH_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
# fp16 start dir: symlinked weights and tokenizer files, config.json torch_dtype/dtype set to float16 (as Exp 23/24)
if true; then
  mkdir -p $START
  for f in $SRC/*; do [ "$(basename $f)" = config.json ] || ln -sf $f $START/; done
  sed -E 's/"(torch_dtype|dtype)": *"[a-z0-9]+"/"\1": "float16"/' $SRC/config.json > $START/config.json
fi
grep -E '"(torch_)?dtype"' $START/config.json
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
ENV="PYTHONPATH=$E25/code:$E20/code:$G/rl4cv/src,E20_CODE=$E20/code,VERIBENCH_ROOT=$B/rl4cv_gen/external/veribench,RL4CV_SRC=$G/rl4cv/src,E20_ROOT=$E20,E20_GRADING=$G,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=8,VLLM_WORKER_MULTIPROC_METHOD=spawn,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,HF_HOME=$B/cache/hf,LD_LIBRARY_PATH=$CL,PATH=$VENV/bin:$G/bin:/usr/local/bin:/usr/bin:/bin"
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env $ENV $SIF python $E25/code/train_e25ckpt.py --arm A --seed 0 --run-root $RUNS \
  --model $START --pack $E20/phase0/train_pack --train-ids $E20/phase0/ids/train_ids_sorted.txt \
  --updates $UPDATES --groups-per-update $GROUPS_PER --max-new-tokens $MAXTOK --save-at $SAVEAT --full-state-every $UPDATES \
  --dtype float16 --loss-scale 16384 --smoke --abort-on-gate
rc=$?
echo "stage2a rc=$rc wall=$(( $(date +%s)-T0 ))s name=$NAME"
cat $RUNS/A_s0/checkpoints_check.json $RUNS/A_s0/smoke_logprob_check.json 2>/dev/null | head -30
tail -3 $RUNS/A_s0/log.jsonl 2>/dev/null | cut -c1-900; wc -l $RUNS/A_s0/steplog.jsonl 2>/dev/null
exit $rc
