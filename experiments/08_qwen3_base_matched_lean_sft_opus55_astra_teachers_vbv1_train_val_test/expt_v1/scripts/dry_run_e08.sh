#!/usr/bin/env bash
# TLDR: PROTOCOL § 12.5 disposable NeMo RL dry run for experiment 08 on Qwen3-1.7B-Base: the first 16 examples of S in the frozen order, 8 steps of
# global batch 2, with the fixed 16-example set evaluated as the (never otherwise used) validation set before step 1 and after step 8 (eval mode,
# no dropout) so the mean loss decrease is measured; loss-token counts per step come from TensorBoard; the step_8 checkpoint is exported to
# Hugging Face format and must load in vLLM and generate on the two preflight train tasks with extraction working. Outputs stay under
# $WORK/dry_run and are excluded from S and from every evaluation; production restarts from the Base weights.
# Usage: bash dry_run_e08.sh <gpu_id>
set -uo pipefail
GPU="${1:?gpu id}"
WORK="${E08_WORK:-/lfs/skampere1/0/brando9/rl4cv_e08}"
REPO="$WORK/rl-4-code-verification"; EXP="$REPO/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
NEMO="$WORK/nemo_rl"; D="$WORK/dry_run"; mkdir -p "$D"
ts() { date -u +%FT%TZ; }
head -16 "$WORK/sft/s_v1_nemo.jsonl" > "$D/train16.jsonl"
cp "$D/train16.jsonl" "$D/val16.jsonl"
[ "$(wc -l < "$D/train16.jsonl")" = 16 ] || { echo "need 16 examples" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="$GPU" HF_HOME="$WORK/cache/huggingface" HF_HUB_OFFLINE=1 UV_CACHE_DIR="$WORK/cache/uv" UV_PYTHON_INSTALL_DIR="$WORK/cache/uv_python"
export RAY_TMPDIR="/tmp/user/$(id -u)/e08ray_dry"; mkdir -p "$RAY_TMPDIR"
export E08_MODEL_PATH="$WORK/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
export E08_CHECKPOINT_DIR="$D/checkpoints" E08_LOG_DIR="$D/logs" E08_TENSORBOARD_DIR="$D/tb" E08_RUN_NAME="rl4cv-e08-dry-run" E08_TRAIN_JSONL="$D/train16.jsonl" E08_VAL_JSONL="$D/val16.jsonl"
unset PYTHONPATH
rm -rf "$D/checkpoints" "$D/logs" "$D/tb" "$D/hf_step_8"
echo "[$(ts)] dry run: 16 examples, 8 steps, GPU $GPU"
cd "$NEMO"
uv run examples/run_sft.py --config "$EXP/expt_v1/configs/e08_sft_1.7B.yaml" sft.max_num_steps=8 sft.val_period=8 sft.val_batches=8 sft.val_global_batch_size=2 sft.val_at_start=true \
  > "$D/train.log" 2>&1
RC=$?; echo "[$(ts)] training exit=$RC"
[ "$RC" = 0 ] && [ -d "$D/checkpoints/step_8" ] || { echo "dry run training failed" >&2; exit 1; }
echo "[$(ts)] exporting step_8"
CUDA_VISIBLE_DEVICES="" uv run examples/converters/convert_dcp_to_hf.py --config "$D/checkpoints/step_8/config.yaml" --dcp-ckpt-path "$D/checkpoints/step_8/policy/weights" --hf-ckpt-path "$D/hf_step_8" > "$D/export.log" 2>&1 || { echo "export failed" >&2; exit 1; }
for f in tokenizer.json tokenizer_config.json vocab.json merges.txt generation_config.json; do [ -f "$D/hf_step_8/$f" ] || cp "$E08_MODEL_PATH/$f" "$D/hf_step_8/$f" 2>/dev/null || true; done
echo "[$(ts)] vLLM generation on the two preflight train tasks"
export PYTHONPATH="$REPO/src" VERIBENCH_ROOT="$REPO/external/veribench" PATH="/usr/local/cuda-12.8/bin:$PATH"
E103_PACK=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896
rm -f "$D/gen_preflight.jsonl"
CUDA_VISIBLE_DEVICES="$GPU" "$WORK/venv_gen/bin/python" -m rl4cv.veribench.generate --pack "$E103_PACK" --model "$D/hf_step_8" --thinking on --seed 91 --stop-token '<|im_end|>' \
  --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --batch 1024 --samples 1 --task-ids "$WORK/preflight_ids.txt" --label dry_run_step8 --out "$D/gen_preflight.jsonl" > "$D/vllm.log" 2>&1 || { echo "vLLM generation failed" >&2; exit 1; }
echo "[$(ts)] dry run done"
