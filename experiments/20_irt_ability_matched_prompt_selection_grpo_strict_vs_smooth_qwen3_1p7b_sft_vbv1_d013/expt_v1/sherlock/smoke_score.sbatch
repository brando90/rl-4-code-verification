#!/bin/bash
#SBATCH -J e20_smoke_score
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH -t 00:45:00
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%j.log
# TLDR: Pipeline smoke before Phase 0a data exist: copy 3 trials of experiment 08 v16's validation job v16_v4_20260831_s0
# (one with strict = 1 if available) into a tiny job dir, score it with score_e20.sh (frozen scorer + D-109 capture) and
# with partial_credit_e20.py (experiment 13 adapter), then compare strict with v16's recorded per-task values.
set -uo pipefail
E20=$SCRATCH/rl4cv_sherlock/e20; B=$SCRATCH/rl4cv_sherlock/v4_validation; G=$SCRATCH/rl4cv_sherlock/grading
SRC=$B/score_v16/v16_v4_20260831/jobs/v16_v4_20260831_s0; CSV=$(ls $B/score_v16/v16_v4_20260831/scores/v16_v4_20260831_s0/*per_task.csv | head -1)
type module >/dev/null 2>&1 || source /etc/profile >/dev/null 2>&1 || true; module load python/3.12.1 >/dev/null 2>&1 || true
S=$E20/smoke; rm -rf $S; mkdir -p $S/jobs/smoke_s0
python3 - "$SRC" "$CSV" "$S/jobs/smoke_s0" <<'PY'
import csv, shutil, sys
from pathlib import Path
src, csvp, dst = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
rows = list(csv.DictReader(open(csvp)))
pos = [r["task"] for r in rows if r["IC_ap"] == "1.0" and r["IC_pp"] == "1.0"][:1]
neg = [r["task"] for r in rows if not (r["IC_ap"] == "1.0" and r["IC_pp"] == "1.0") and (src / r["task"] / "verifier/solution.lean").stat().st_size > 0][:2]
for t in pos + neg:
    shutil.copytree(src / t, dst / t)
print("smoke trials:", pos + neg)
PY
t0=$(date +%s); bash $E20/code/score_e20.sh $S/jobs/smoke_s0 $B/run/validation_pack $S/scores/smoke_s0; rc1=$?; echo "scorer rc=$rc1 $(( $(date +%s)-t0 ))s"
export PYTHONPATH="$G/rl4cv/src" PATH="$G/bin:$PATH" RL4CV_SRC=$G/rl4cv/src E20_GRADING=$G CUDA_VISIBLE_DEVICES=""
t0=$(date +%s); python3.12 $E20/code/partial_credit_e20.py --job-dir $S/jobs/smoke_s0 --out $S/partial/partial_smoke_s0.json --evidence-root $S/partial/compiler_diagnostics; rc2=$?; echo "adapter rc=$rc2 $(( $(date +%s)-t0 ))s"
python3 - "$CSV" "$S/scores/smoke_s0" "$S/partial/partial_smoke_s0.json" <<'PY'
import csv, glob, json, sys
ref = {r["task"]: r for r in csv.DictReader(open(sys.argv[1]))}
new = {r["task"]: r for r in csv.DictReader(open(glob.glob(sys.argv[2] + "/*per_task.csv")[0]))}
part = {r["task_id"]: r for r in json.load(open(sys.argv[3]))["records"]}
for t in sorted(new):
    s_ref = float(ref[t]["IC_ap"] == "1.0" and ref[t]["IC_pp"] == "1.0"); s_new = float(new[t]["IC_ap"] == "1.0" and new[t]["IC_pp"] == "1.0")
    print(f"{t}: v16 strict={s_ref} e20 scorer strict={s_new} adapter strict={part[t].get('strict')} factored={part[t].get('factored_reward')} status={part[t]['status']} {part[t].get('error','')[:80]}")
PY
echo "evidence dirs: $(ls -d $S/scores/smoke_s0/compiler_diagnostics/call_* 2>/dev/null | wc -l) scorer calls, $(ls -d $S/partial/compiler_diagnostics/call_* 2>/dev/null | wc -l) adapter calls"
ls $S/scores/smoke_s0/compiler_diagnostics/ | head -3; cat $(ls -d $S/scores/smoke_s0/compiler_diagnostics/call_* | head -1)/execution.json | head -30
