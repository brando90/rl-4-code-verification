#!/usr/bin/env bash
# TLDR: Launch experiment 05 on skampere1 in tmux session rl4cv-e05-qwen3-base-g8: a preflight window, or one window per Qwen3 Base model on its planned GPUs.
# Usage: bash launch_e05.sh preflight   # 5 tasks x 2 samples on Qwen3-1.7B-Base, GPU $PF_GPU (default 7)
#        bash launch_e05.sh all         # the full run; re-running resumes (refuses to start a model whose window is still alive)
# GPU plan (PROTOCOL.md; override after re-checking nvidia-smi): GPUS_1P7B=0, GPUS_4B=1,2, GPUS_8B=3,5,6.
set -euo pipefail
MODE="${1:?preflight|all}"
WORK=/lfs/skampere1/0/brando9/rl4cv_e05
REPO=$WORK/rl-4-code-verification
E01=/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification
VB103=/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private
HERE=$REPO/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1
SESSION=rl4cv-e05-qwen3-base-g8
mkdir -p "$WORK/logs" "$WORK/out"

# Experiment 01's validated environment, read-only: vLLM venv (CUDA 12.8 fix in its activate), pinned checkouts, Lean project.
cat > "$WORK/env_e05.sh" <<EOF
source $E01/.venv/bin/activate
export PYTHONPATH=$REPO/src
export PACK=$VB103/packs/vbv1_896
export TASK_IDS=$VB103/task_ids_vbv1.txt
export LAKE_DIR=$E01/external/veribench_scorer/veribench_dataset/lean_src
export SCORER=$E01/external/veribench_scorer
export VERIBENCH_ROOT=$E01/external/veribench
export OUT=$WORK/out
export PATH=\$HOME/.elan/bin:\$PATH
EOF

tmux has-session -t "$SESSION" 2>/dev/null || tmux new-session -d -s "$SESSION" -n control "bash"

window() {  # $1 = window name, $2 = delay seconds, $3.. = run_model_e05.sh args
  local name="$1" delay="$2"; shift 2
  if tmux list-windows -t "$SESSION" -F '#W' | grep -qx "$name"; then
    echo "window $name is still alive; not starting a second writer" >&2; return 0
  fi
  local log="$WORK/logs/driver_${name}.log"
  tmux new-window -d -t "$SESSION" -n "$name" \
    "bash -c 'sleep $delay; source $WORK/env_e05.sh; set -o pipefail; bash $HERE/run_model_e05.sh $* 2>&1 | tee -a $log; echo EXIT=\$? >> $log; exec bash'"
  echo "started window $name (delay ${delay}s) -> $log"
}

if [ "$MODE" = preflight ]; then
  window preflight 0 Qwen/Qwen3-1.7B-Base ea980cb0a6c2ae4b936e82123acc929f1cec04c1 qwen3-1.7b-base "${PF_GPU:-7}" preflight
elif [ "$MODE" = all ]; then
  # Staggered starts avoid concurrent flashinfer JIT-cache writes (experiment 01's 27B shard crash).
  window qwen3-1.7b-base 0   Qwen/Qwen3-1.7B-Base ea980cb0a6c2ae4b936e82123acc929f1cec04c1 qwen3-1.7b-base "${GPUS_1P7B:-0}" all
  window qwen3-4b-base   240 Qwen/Qwen3-4B-Base   906bfd4b4dc7f14ee4320094d8b41684abff8539 qwen3-4b-base   "${GPUS_4B:-1,2}" all
  window qwen3-8b-base   480 Qwen/Qwen3-8B-Base   49e3418fbbbca6ecbdf9608b4d22e5a407081db4 qwen3-8b-base   "${GPUS_8B:-3,5,6}" all
else
  echo "mode must be preflight or all" >&2; exit 2
fi
tmux list-windows -t "$SESSION"
