#!/bin/bash
# TLDR: GPU smoke for experiment 18a v2: Qwen3-1.7B (largest) on the top level of 12 spread-out families + 2 targets, 8 items x 4 samples, embeddings, scoring, a smoke analysis; prints throughput and a GPU-h bound.
#SBATCH -J e18v2_smoke
#SBATCH -p gpu
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 00:45:00
#SBATCH -o logs/%x_%j.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com
set -euo pipefail
source $HOME/e18a_v2/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v2_wide/slurm/farmshare/env.sh
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
SETS=$($E18A_VENV/bin/python -c "
import json; f = json.load(open('$CODE/families_v2.json'))['families']
pick = [f[round(i * (len(f) - 1) / 11)] for i in range(12)]
print(','.join([f'rg/{x[\"family\"]}/L{max(x[\"levels\"])}' for x in pick] + ['rg/gsm_symbolic', 'gsm8k/test256']))")
echo "smoke sets: $SETS"
TAG=qwen3_1p7b
rm -rf $RUN/raw_smoke $RUN/scored_smoke $RUN/emb_smoke $RUN/results_smoke
source $FS_HF/bin/activate
python -c "import vllm, transformers, torch; print('vllm', vllm.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)"
python $CODE/generate.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --sets $SETS --limit-items 8 --n 4 --out-subdir smoke
python $CODE/embed.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --limit-items 8 --out-subdir smoke
deactivate
$E18A_VENV/bin/python $CODE/score.py --run $RUN --model-tag $TAG --raw-subdir smoke --sets $SETS
$E18A_VENV/bin/python $CODE/analyze.py --run $RUN --subdir smoke --smoke-group-size 4
$E18A_VENV/bin/python - <<'PY'
import json, os
run = os.environ["RUN"]
rows = [json.loads(l) for l in open(f"{run}/results_smoke/envs_18a_v2.jsonl")] + [json.loads(l) for l in open(f"{run}/results_smoke/targets_18a_v2.jsonl")]
print(f"{'set':36s} pass  tag  capped  mean_tok")
for r in rows:
    print(f"{r['env_id']:36s} {r['pass_rate']:.2f}  {r['answer_tag_rate']:.2f}  {r['capped_rate']:.2f}  {r['mean_generated_tokens']:.0f}")
t = [json.loads(l) for l in open(f"{run}/raw_smoke/qwen3_1p7b/timing.jsonl")]
toks, secs = sum(x["generated_tokens"] for x in t), sum(x["seconds"] for x in t)
mean_tok = toks / sum(x["responses"] for x in t)
n_sets = json.load(open(os.path.join(os.environ["CODE"], "families_v2.json")))["n_envs"] + 6
print(f"smoke: {toks} tokens in {secs:.0f}s ({toks/secs:.0f} tok/s at tiny batch, a lower bound); mean {mean_tok:.0f} tok/response")
print(f"1.7B full run upper bound at this rate: {n_sets*4096*mean_tok/(toks/secs)/3600:.1f} GPU-h for {n_sets} sets (full batches run several times faster)")
PY
echo "SMOKE OK"
