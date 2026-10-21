#!/bin/bash
# TLDR: Experiment 20 Phase 0a generation on one Sherlock GPU: the experiment 08 v4 seed-20260831 Qwen3-1.7B Lean SFT
# checkpoint through rl4cv.veribench.generate with experiment 08 v12's frozen sampler (temperature 0.6, top-p 0.95,
# top-k 20, 12,288 new tokens, thinking on, seed 91, stop <|im_end|>), 8 samples per task, inside the vLLM 0.30.0 SIF.
# Copied from $SCRATCH/rl4cv_sherlock/v4_validation/rl4cv_gen/gen.sh (10-19-2026) with the pack, model and output
# parameterized; the sampler flags are byte-for-byte the same. usage: gen_e20.sh <task_ids_file> <out_dir>
set -euo pipefail
IDS=$1; OUT=$2
B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$B/rl4cv_gen; E20=$SCRATCH/rl4cv_sherlock/e20
SIF=$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif
MODEL=$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf; LABEL=e20_p0_v4_s20260831
PACK=$E20/phase0/train_pack
mkdir -p $OUT $B/cache
for k in $(env | cut -d= -f1 | grep -E 'API_KEY|AUTH_TOKEN|ACCESS_TOKEN|BEARER_TOKEN' || true); do unset $k; done
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | tee $OUT/gpu.txt
sha256sum $MODEL/model-00001-of-00002.safetensors $MODEL/model-00002-of-00002.safetensors | tee $OUT/model_sha256.txt
CL=/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/.singularity.d/libs
PROBE="import torch; x=torch.ones(4, device='cuda'); print(torch.cuda.get_device_name(0), (x*2).sum().item())"
if apptainer exec --nv $SIF env LD_LIBRARY_PATH=$CL python3 -c "$PROBE"; then LDENV=",LD_LIBRARY_PATH=$CL"
elif apptainer exec --nv $SIF python3 -c "$PROBE"; then LDENV=""
else echo "CUDA init failed with and without forward compat"; exit 3; fi
echo "ldenv=$LDENV" | tee -a $OUT/gpu.txt
T0=$(date +%s)
apptainer exec --nv -B /scratch,/home/groups --env PYTHONPATH=$G/src,VERIBENCH_ROOT=$G/external/veribench,HF_HUB_OFFLINE=1,TOKENIZERS_PARALLELISM=false,OMP_NUM_THREADS=4,VLLM_WORKER_MULTIPROC_METHOD=spawn,FLASHINFER_WORKSPACE_BASE=$B/cache/flashinfer,XDG_CACHE_HOME=$B/cache,VLLM_CACHE_ROOT=$B/cache/vllm,TRITON_CACHE_DIR=$B/cache/triton,HF_HOME=$B/cache/hf$LDENV \
  $SIF python3 -m rl4cv.veribench.generate --pack $PACK --task-ids $IDS --model $MODEL --label $LABEL \
  --samples 8 --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 \
  --batch 128 --tensor-parallel-size 1 --gpu-memory-utilization 0.85 --out $OUT/raw.jsonl
T1=$(date +%s)
module load python/3.12.1 >/dev/null 2>&1 || true
python3 - "$OUT" "$T0" "$T1" "${SLURM_JOB_ID:-none}" "$IDS" <<'PY'
import json,sys,collections
out,t0,t1,job,ids=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],sys.argv[5]
rows=[json.loads(l) for l in open(out+'/raw.jsonl') if l.strip()]
want=[l.strip() for l in open(ids) if l.strip()]
toks=[r['generated_tokens'] for r in rows]
s=dict(job=job,wall_s=t1-t0,cells=len(rows),declared_cells=8*len(want),tasks=len({r['task_id'] for r in rows}),declared_tasks=len(want),
  gen_tokens=sum(toks),max_tokens=max(toks),mean_tokens=sum(toks)/len(toks),truncated=sum(r['truncated'] for r in rows),
  finish=dict(collections.Counter(r['finish_reason'] for r in rows)),extraction=dict(collections.Counter(r['extraction'] for r in rows)),tok_per_s=sum(toks)/(t1-t0))
json.dump(s,open(out+'/timing.json','w'),indent=1);print(json.dumps(s))
PY
