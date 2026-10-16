#!/usr/bin/env bash
# TLDR: Run four stronger CPU pretrains and freeze mixture proposals and decorrelation probes.
set -euo pipefail
cd /lfs/skampere1/0/brando9/rl4cv_e16_night2/rl-4-code-verification
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
module=experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.run
out=experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3
pids=()
for scale in n1 n2 n3 n4; do
    nice -n 10 .venv/bin/python -u -m "$module" pretrain --scale "$scale" > "$out/${scale}_pretrain.log" 2>&1 &
    pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
if ((failed)); then exit 1; fi
nice -n 10 .venv/bin/python -u -m "$module" base-probe --scale n3 > "$out/n3_base-probe.log" 2>&1
nice -n 10 .venv/bin/python -u -m "$module" mixtures
pids=()
for scale in n1 n2 n3 n4; do
    nice -n 10 .venv/bin/python -u -m "$module" probe --scale "$scale" > "$out/${scale}_probe.log" 2>&1 &
    pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
if ((failed)); then exit 1; fi
nice -n 10 .venv/bin/python -u -m "$module" gate
