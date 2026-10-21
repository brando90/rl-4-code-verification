#!/bin/bash
# TLDR: Split the 539 sorted D-013 train task ids into 4 chunk files for the Phase 0a generation array (135/135/135/134).
set -euo pipefail
E20=$SCRATCH/rl4cv_sherlock/e20; B=$SCRATCH/rl4cv_sherlock/v4_validation/rl4cv_gen
MAN=$B/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_split_manifest.csv
mkdir -p $E20/phase0/ids
# train ids from the manifest's split column (identical to the committed vbv1_train_task_ids.txt, verified locally)
python3 -c "import csv,sys; print('\n'.join(sorted(r['task_id'] for r in csv.DictReader(open(sys.argv[1])) if r['split']=='train')))" $MAN > $E20/phase0/ids/train_ids_sorted.txt
[ "$(wc -l < $E20/phase0/ids/train_ids_sorted.txt)" = 539 ] || { echo "expected 539 train ids"; exit 3; }
split -n l/4 -d -a 1 $E20/phase0/ids/train_ids_sorted.txt $E20/phase0/ids/chunk_
for i in 0 1 2 3; do mv $E20/phase0/ids/chunk_$i $E20/phase0/ids/chunk_$i.txt; echo "chunk_$i: $(wc -l < $E20/phase0/ids/chunk_$i.txt) tasks"; done
cat $E20/phase0/ids/chunk_?.txt | sort | cmp - $E20/phase0/ids/train_ids_sorted.txt && echo "chunks cover all 539 train ids exactly once"
sha256sum $E20/phase0/ids/*.txt
