#!/bin/bash
# TLDR: GPU smoke for experiment 18a: Qwen3-4B (largest) on 10 sets x 8 items x 4 samples, embeddings, scoring and a smoke analysis; prints throughput.
#SBATCH -J e18a_smoke
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
source $HOME/e18a/code/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1/slurm/farmshare/env.sh
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
SETS=rg/basic_arithmetic/L3,rg/leg_counting/L3,rg/simple_equations/L3,rg/coin_flip/L3,rg/letter_counting/L3,rg/word_sorting/L3,rg/family_relationships/L3,rg/mini_sudoku/L3,rg/gsm_symbolic,gsm8k/test256
TAG=qwen3_4b
rm -rf $RUN/raw_smoke $RUN/scored_smoke $RUN/emb_smoke $RUN/results_smoke
source $FS_HF/bin/activate
python -c "import vllm, transformers, torch; print('vllm', vllm.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)"
python $CODE/generate.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --sets $SETS --limit-items 8 --n 4 --out-subdir smoke
python $CODE/embed.py --run $RUN --model-tag $TAG --model-path $MODELS_DIR/$TAG --limit-items 8 --out-subdir smoke
deactivate
$E18A_VENV/bin/python $CODE/score.py --run $RUN --model-tag $TAG --raw-subdir smoke
$E18A_VENV/bin/python $CODE/analyze.py --run $RUN --subdir smoke --smoke-group-size 4
$E18A_VENV/bin/python - <<'PY'
import json, os
run = os.environ["RUN"]
rows = [json.loads(l) for l in open(f"{run}/results_smoke/envs_18a.jsonl")] + [json.loads(l) for l in open(f"{run}/results_smoke/targets_18a.jsonl")]
print(f"{'set':28s} pass  tag  capped  mean_tok")
for r in rows:
    print(f"{r['env_id']:28s} {r['pass_rate']:.2f}  {r['answer_tag_rate']:.2f}  {r['capped_rate']:.2f}  {r['mean_generated_tokens']:.0f}")
t = [json.loads(l) for l in open(f"{run}/raw_smoke/qwen3_4b/timing.jsonl")]
toks, secs = sum(x["generated_tokens"] for x in t), sum(x["seconds"] for x in t)
mean_tok = toks / sum(x["responses"] for x in t)
print(f"smoke: {toks} tokens in {secs:.0f}s ({toks/secs:.0f} tok/s at tiny batch, a lower bound); mean {mean_tok:.0f} tok/response")
print(f"4B full run upper bound at this rate: {155648*mean_tok/(toks/secs)/3600:.1f} GPU-h (full batches run several times faster)")
PY
echo "SMOKE OK"
