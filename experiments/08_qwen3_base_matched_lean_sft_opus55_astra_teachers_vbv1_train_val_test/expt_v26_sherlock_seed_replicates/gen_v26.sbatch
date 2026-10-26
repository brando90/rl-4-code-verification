#!/bin/bash
#SBATCH -J rl4cv_v26_gen
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
# Validation generation for one V26 checkpoint: AT-476's gen.sh command with the frozen v12 settings (135 tasks x 8),
# reading the checkpoint from runs/<run>/hf, then materializing the 8 per-sample Lean job dirs for scoring.
# usage (from the experiment dir, via submit.sh): sbatch -t <wall> gen_v26.sbatch <run> <label>
# Resumable: rerunning the same command skips cells already in gen/<label>/raw.jsonl.
set -euo pipefail
RUN=$1; L=$2; TAG=v0.30.0
EXP=${SLURM_SUBMIT_DIR:?}; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$B/rl4cv_gen; GR=$SCRATCH/rl4cv_sherlock/grading
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_$TAG.sif
IDS=$G/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_validation_task_ids.txt
MODEL=$EXP/runs/$RUN/hf; OUT=$EXP/gen/$L
grep -q '"status": "COMPLETE"' $EXP/runs/$RUN/result.json || { echo "training $RUN not COMPLETE"; exit 5; }
mkdir -p $OUT $EXP/cache
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | tee $OUT/gpu.txt
# Driver 550 is CUDA 12.4 and the image is CUDA 13.0: try the image's forward-compat libcuda first, then the host's.
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
PROBE="import torch; x=torch.ones(4, device='cuda'); print(torch.cuda.get_device_name(0), (x*2).sum().item())"
if apptainer exec --nv $SIF env LD_LIBRARY_PATH=$CL python3 -c "$PROBE"; then LDENV=",LD_LIBRARY_PATH=$CL"
elif apptainer exec --nv $SIF python3 -c "$PROBE"; then LDENV=""
else echo "CUDA init failed with and without forward compat"; exit 3; fi
echo "ldenv=$LDENV" | tee -a $OUT/gpu.txt
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env PYTHONPATH=$G/src,VERIBENCH_ROOT=$G/external/veribench,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=4,VLLM_WORKER_MULTIPROC_METHOD=spawn,FLASHINFER_WORKSPACE_BASE=$EXP/cache/flashinfer,XDG_CACHE_HOME=$EXP/cache,VLLM_CACHE_ROOT=$EXP/cache/vllm,TRITON_CACHE_DIR=$EXP/cache/triton,HF_HOME=$EXP/cache/hf$LDENV \
  $SIF python3 -m rl4cv.veribench.generate --pack $B/run/validation_pack --task-ids $IDS --model $MODEL --label $L \
  --samples 8 --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 \
  --batch 128 --tensor-parallel-size 1 --gpu-memory-utilization 0.85 --out $OUT/raw.jsonl
T1=$(date +%s)
module load python/3.12.1 >/dev/null 2>&1 || true
PY=$(command -v python3.12 || command -v python3)
$PY - "$OUT" "$T0" "$T1" "${SLURM_JOB_ID:-none}" <<'PY'
import json,sys,collections
out,t0,t1,job=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
rows=[json.loads(l) for l in open(out+'/raw.jsonl') if l.strip()]
toks=[r['generated_tokens'] for r in rows]
per=collections.Counter(r['task_id'] for r in rows)
s=dict(job=job,wall_s=t1-t0,cells=len(rows),tasks=len(per),gen_tokens=sum(toks),max_tokens=max(toks),
  mean_tokens=sum(toks)/len(toks),truncated=sum(r['truncated'] for r in rows),finish=dict(collections.Counter(r['finish_reason'] for r in rows)),
  extraction=dict(collections.Counter(r['extraction'] for r in rows)),tok_per_s=sum(toks)/(t1-t0),
  complete=len(rows)==1080 and len(per)==135 and set(per.values())=={8})
json.dump(s,open(out+'/timing.json','w'),indent=1);print(json.dumps(s))
sys.exit(0 if s['complete'] else 4)
PY
# Materialize the per-sample Lean job dirs exactly as AT-477 did (score_v16.sh), for score_one.sh.
W=$EXP/score; rm -rf $W/$L/jobs; mkdir -p $W/$L
PYTHONPATH=$GR/rl4cv/src $PY -m rl4cv.veribench.jobs --gen $OUT/raw.jsonl --out-root $W/$L/jobs --name $L | tail -1
for k in 0 1 2 3 4 5 6 7; do test -d $W/$L/jobs/${L}_s$k || { echo "missing job dir ${L}_s$k"; exit 6; }; done
echo "gen+materialize OK $L"
