#!/bin/bash
#SBATCH -J e20_eval_gen
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 04:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/eval/logs/%x_%j.log
# TLDR: Experiment 20 evaluation generation (export LABEL, MODEL_DIR): 135 D-013 validation tasks x 8 samples with the frozen
# v12 evaluation sampler (gen.sh settings: seed 91, temperature 0.6, top-p 0.95, top-k 20, 12,288 tokens, thinking on),
# the same route as experiment 08 v16; output $E20/eval/<LABEL>/raw.jsonl.
set -euo pipefail
E20=$SCRATCH/rl4cv_sherlock/e20; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$B/rl4cv_gen
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif
: "${LABEL:?} ${MODEL_DIR:?}"
OUT=$E20/eval/$LABEL; mkdir -p $OUT $B/cache
IDS=$G/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_validation_task_ids.txt
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | tee $OUT/gpu.txt
sha256sum $MODEL_DIR/*.safetensors | tee $OUT/model_sha256.txt
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
PROBE="import torch; x=torch.ones(4, device='cuda'); print(torch.cuda.get_device_name(0), (x*2).sum().item())"
if apptainer exec --nv $SIF env LD_LIBRARY_PATH=$CL python3 -c "$PROBE"; then LDENV=",LD_LIBRARY_PATH=$CL"; elif apptainer exec --nv $SIF python3 -c "$PROBE"; then LDENV=""; else echo "CUDA init failed"; exit 3; fi
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env PYTHONPATH=$G/src,VERIBENCH_ROOT=$G/external/veribench,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=4,VLLM_WORKER_MULTIPROC_METHOD=spawn,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,HF_HOME=$B/cache/hf$LDENV \
  $SIF python3 -m rl4cv.veribench.generate --pack $B/run/validation_pack --task-ids $IDS --model $MODEL_DIR --label e20_eval_$LABEL \
  --samples 8 --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 \
  --batch 128 --tensor-parallel-size 1 --gpu-memory-utilization 0.85 --out $OUT/raw.jsonl
T1=$(date +%s)
module load python/3.12.1 >/dev/null 2>&1 || true
python3 - "$OUT" "$T0" "$T1" "${SLURM_JOB_ID:-none}" <<'PY'
import json,sys,collections
out,t0,t1,job=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
rows=[json.loads(l) for l in open(out+'/raw.jsonl') if l.strip()]
toks=[r['generated_tokens'] for r in rows]
s=dict(job=job,wall_s=t1-t0,cells=len(rows),declared_cells=1080,tasks=len({r['task_id'] for r in rows}),gen_tokens=sum(toks),mean_tokens=sum(toks)/len(toks),
  truncated=sum(r['truncated'] for r in rows),finish=dict(collections.Counter(r['finish_reason'] for r in rows)),extraction=dict(collections.Counter(r['extraction'] for r in rows)))
json.dump(s,open(out+'/timing.json','w'),indent=1);print(json.dumps(s))
PY
PYTHONPATH=$SCRATCH/rl4cv_sherlock/grading/rl4cv/src python3 -m rl4cv.veribench.jobs --gen $OUT/raw.jsonl --out-root $OUT/jobs --name eval_$LABEL | tail -1
