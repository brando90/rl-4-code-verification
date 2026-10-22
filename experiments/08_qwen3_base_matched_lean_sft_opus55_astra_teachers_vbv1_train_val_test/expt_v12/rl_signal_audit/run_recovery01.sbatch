#!/bin/bash
#SBATCH -J rl4cv_v12_signal_recovery01
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=2G
#SBATCH -t 00:10:00
#SBATCH --output=/scratch/users/brando9/rl4cv_sherlock/v12_signal_audit_recovery01/job_%j.log
#SBATCH --error=/scratch/users/brando9/rl4cv_sherlock/v12_signal_audit_recovery01/job_%j.err
# TLDR: Recompute the existing v12 validation reward-signal audit on one CPU, with no GPU and no new generation.
set -euo pipefail
module load python/3.12.1 py-numpy/2.2.6_py312
export CUDA_VISIBLE_DEVICES="" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
cd /scratch/users/brando9/rl4cv_sherlock/v12_signal_audit_recovery01
export PYTHONPATH="$PWD"
python3 signal_audit.py cells.csv ids.txt results
python3 - <<'PY'
import hashlib, json
from pathlib import Path
r = Path("results")
paths = [*sorted(r.glob("*")), Path("cells.csv"), Path("ids.txt"), Path("signal_audit.py"), Path("rl4cv/experience.py")]
(r / "manifest.json").write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2) + "\n")
print("manifest_ok", len(paths))
PY
