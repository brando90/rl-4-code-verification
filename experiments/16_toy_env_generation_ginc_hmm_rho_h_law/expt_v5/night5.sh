#!/usr/bin/env bash
# TLDR: Night 5 = Night 4 replicated on INDEPENDENT start checkpoints (E16_PRETRAIN_SEED=1: new init, new pretraining docs draw, new batch order), same frozen S2 strength, same rules. Stage-wise, resumable.
# Usage (repo root): bash .../night5.sh <stage>   stage in: pretrain-small | pretrain-n4 | probes | rl13 | freeze | rl4 | report
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=.:src
PY=${PY:-python}; P=${P:-4}
v2=experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.run
v4=experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v4.night4
out=experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v5/results/night5
export PY v2 v4 out
case "$1" in
pretrain-small) for s in n1 n2 n3; do echo $s; done | xargs -P "$P" -n 1 bash -c 'E16_PRETRAIN_SEED=1 nice -n 10 $PY -u -m $v2 pretrain --scale "$1" --out "$out" >> "$out/$1_pretrain.log" 2>&1' _ ;;
pretrain-n4) E16_PRETRAIN_SEED=1 nice -n 10 $PY -u -m $v2 pretrain --scale n4 --out "$out" >> "$out/n4_pretrain.log" 2>&1 ;;
probes) shift; for s in "$@"; do echo "$s"; done | xargs -P "$P" -n 1 bash -c 'test -f "$out/$1_probe.json" || nice -n 10 $PY -u -m $v2 probe --scale "$1" --out "$out" > "$out/$1_probe.log" 2>&1; nice -n 10 $PY -u -m $v4 alpha --scale "$1" --out "$out" > "$out/$1_alpha.log" 2>&1' _ ;;
rl13) for s in n3 n2 n1; do for env in {0..15}; do for seed in 0 1 2; do echo "$s $env $seed"; done; done; done | xargs -P "$P" -n 3 bash -c 'nice -n 10 $PY -u -m $v4 rl --scale "$1" --env "$2" --seed "$3" --out "$out" >> "$out/rl.log" 2>&1' _ ;;
freeze) nice -n 10 $PY -u -m $v4 freeze --out "$out" > "$out/freeze.log" 2>&1 ;;
rl4) for env in {0..15}; do for seed in 0 1 2; do echo "$env $seed"; done; done | xargs -P "$P" -n 2 bash -c 'nice -n 10 $PY -u -m $v4 rl --scale n4 --env "$1" --seed "$2" --out "$out" >> "$out/rl.log" 2>&1' _ ;;
report) nice -n 10 $PY -u -m $v4 report --out "$out" > "$out/report.log" 2>&1 ;;
esac
