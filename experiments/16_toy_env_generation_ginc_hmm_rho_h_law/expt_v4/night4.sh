#!/usr/bin/env bash
# TLDR: Night 4 end to end on CPU: pilot -> frozen RL strength -> probes + alpha -> n1-n3 GRPO -> frozen n4 forecast -> n4 GRPO -> report.
# Run from the repository root while/after the expt_v2 pretrains write expt_v4/results/night4/{n1..n4}_meta.json.
# n4 (the slowest pretrain) is probed only after the n1-n3 GRPO matrix, so it stays off the critical path.
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=.:src
PY=${PY:-python}
P=${P:-4}
v2=experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.run
v4=experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v4.night4
out=experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v4/results/night4
export PY v2 v4 out
wait_for() { until test -f "$out/$1_meta.json"; do sleep 30; done; }
probe_alpha() {
    for s in "$@"; do echo "$s"; done |
        xargs -P "$P" -n 1 bash -c 'test -f "$out/$1_probe.json" || nice -n 10 $PY -u -m $v2 probe --scale "$1" --out "$out" > "$out/$1_probe.log" 2>&1; nice -n 10 $PY -u -m $v4 alpha --scale "$1" > "$out/$1_alpha.log" 2>&1' _
}
wait_for n3
# Night 2's frozen generated mixtures are reused unchanged.
test -f "$out/mixtures.json" || cp experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3/mixtures.json "$out/"
# 1. Pilot (n3, settings S2/S3, pilot seeds 100/101) and the frozen RL-strength choice.
for st in S2 S3; do for env in {0..15}; do for seed in 100 101; do echo "$st $env $seed"; done; done; done |
    xargs -P "$P" -n 3 bash -c 'nice -n 10 $PY -u -m $v4 pilot --setting "$1" --scale n3 --env "$2" --seed "$3" >> "$out/pilot.log" 2>&1' _
nice -n 10 $PY -u -m $v4 choose > "$out/choose.log" 2>&1
# 2. rho/H probes (expt_v2 code, unchanged) and alpha probes for n1-n3.
for s in n1 n2; do wait_for "$s"; done
probe_alpha n1 n2 n3
# 3. Main GRPO on n1-n3.
for s in n3 n2 n1; do for env in {0..15}; do for seed in 0 1 2; do echo "$s $env $seed"; done; done; done |
    xargs -P "$P" -n 3 bash -c 'nice -n 10 $PY -u -m $v4 rl --scale "$1" --env "$2" --seed "$3" >> "$out/rl.log" 2>&1' _
# 4. n4 probes, then the n4 forecast is frozen before any n4 trajectory.
wait_for n4
probe_alpha n4
nice -n 10 $PY -u -m $v4 freeze > "$out/freeze.log" 2>&1
for env in {0..15}; do for seed in 0 1 2; do echo "$env $seed"; done; done |
    xargs -P "$P" -n 2 bash -c 'nice -n 10 $PY -u -m $v4 rl --scale n4 --env "$1" --seed "$2" >> "$out/rl.log" 2>&1' _
nice -n 10 $PY -u -m $v4 report > "$out/report.log" 2>&1
echo night4 done
