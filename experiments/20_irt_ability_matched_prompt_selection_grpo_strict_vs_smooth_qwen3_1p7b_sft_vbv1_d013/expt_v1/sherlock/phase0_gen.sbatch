#!/bin/bash
#SBATCH -J e20_p0_gen
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_SKU:L40S|GPU_SKU:H100_SXM5
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 04:30:00
#SBATCH --array=0-3
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/phase0/logs/%x_%A_%a.log
# TLDR: Experiment 20 Phase 0a: 539 D-013 train tasks x 8 samples of the 1.7B Lean SFT start policy (08 v4 seed 20260831),
# split into 4 task chunks (one GPU each, resumable: generate skips cells already in raw.jsonl). Estimated 1.6-2 h per
# chunk on an L40S (08 v16 measured 1,080 cells in 5,718 s), about 7 GPU-h total against the 10 GPU-h Phase 0 cap.
E20=$SCRATCH/rl4cv_sherlock/e20
bash $E20/code/gen_e20.sh $E20/phase0/ids/chunk_$SLURM_ARRAY_TASK_ID.txt $E20/phase0/gen/chunk_$SLURM_ARRAY_TASK_ID
