#!/usr/bin/env bash
# TLDR: Complete the frozen CPU matrix, forecast n4 prospectively, and analyze all 384 cells.
set -euo pipefail
cd /lfs/skampere1/0/brando9/rl4cv_e16_night2/rl-4-code-verification
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
export e16_module=experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2
export e16_out=experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3
while [[ ! -f "$e16_out/gate.json" ]]; do
    if ! tmux has-session -t rl4cv-e16-night2-cpu-preflight 2>/dev/null; then
        echo 'preflight ended without gate receipt'; exit 1
    fi
    sleep 5
done
.venv/bin/python - <<'PY'
import importlib,json
from pathlib import Path
from rl4cv.forecast import freeze_forecast,verify_forecast
r=importlib.import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.run')
out=r.HERE/'results/pilot_v3'
assert verify_forecast(out/'gate.json') and r.read(out/'gate.json')['passed'], 'decorrelation gate failed'
manifest={'expected_cells':384,'budget_dollars':0,'device':'cpu','nice':10,'threads_per_process':1,'max_processes':8,
 'source_hashes':{p.name:r.sha(p) for p in r.HERE.glob('*.py')},'protocol_sha256':r.sha(r.HERE/'PROTOCOL.md'),
 'cells':[{'scale':s,'env':e.name,'seed':seed,'tokens':b*r.BATCH*r.GROUP*r.K,'status':'pending'}
          for s in r.SCALES for e in r.specs(out) for seed in (0,1) for b in r.STEPS]}
if not (out/'manifest.json').exists(): freeze_forecast(manifest,out,'manifest')
PY
for scale in n1 n2 n3; do
    for env in {0..15}; do
        for seed in 0 1; do printf '%s %s %s\n' "$scale" "$env" "$seed"; done
    done
done | xargs -P 8 -n 3 bash -c 'nice -n 10 .venv/bin/python -u -m "$e16_module.run" rl --scale "$1" --env "$2" --seed "$3" > "$e16_out/${1}_env${2}_seed${3}.log" 2>&1' _
nice -n 10 .venv/bin/python -u -m "$e16_module.analyze" freeze
for env in {0..15}; do
    for seed in 0 1; do printf '%s %s\n' "$env" "$seed"; done
done | xargs -P 8 -n 2 bash -c 'nice -n 10 .venv/bin/python -u -m "$e16_module.run" rl --scale n4 --env "$1" --seed "$2" > "$e16_out/n4_env${1}_seed${2}.log" 2>&1' _
nice -n 10 .venv/bin/python -u -m "$e16_module.analyze" report
