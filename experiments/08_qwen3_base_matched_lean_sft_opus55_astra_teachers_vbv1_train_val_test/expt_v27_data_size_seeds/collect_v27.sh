#!/bin/bash
# TLDR: Terminal collector (afterany): tar every V27 receipt, step table, subset record, generation, score and log (no
# weights) into one $SCRATCH file, with a job-state table, whatever succeeded or failed.
set -uo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
OUT=$SCRATCH/rl4cv_sherlock/expt_v27_results.tgz
ids=$(tail -n +2 jobs_v27.tsv | cut -f2 | grep -v "^${SLURM_JOB_ID}$" | paste -sd,)
sacct -j "$ids" -X -P --format=JobID,JobName%30,Partition,State,ExitCode,Elapsed,Start,End,NodeList,AllocTRES%60 > sacct_v27.txt 2>&1
{ for d in score/*/scores/*/; do [ -d "$d" ] && echo "$d $(ls $d | grep -c '^scsc_.*_per_task.csv')"; done; } > score_inventory.txt
files=$(ls -d prepare_receipt.json runs.tsv jobs_v27.tsv sacct_v27.txt score_inventory.txt data/subsets.json logs \
  runs/*/identity.json runs/*/result.json runs/*/steps.csv runs/*/progress.json runs/*/weights_manifest.json runs/*/hf/config.json \
  gen/*/raw.jsonl gen/*/timing.json gen/*/gpu.txt score/*/scores score/logs 2>/dev/null)
tar czf $OUT.tmp $files && mv $OUT.tmp $OUT
sha256sum $OUT | tee $OUT.sha256
echo "collected $(echo $files | wc -w) paths; runs complete: $(grep -l COMPLETE runs/*/result.json 2>/dev/null | wc -l)/6; score files: $(ls score/*/scores/*/scsc_*_per_task.csv 2>/dev/null | wc -l)/48"
