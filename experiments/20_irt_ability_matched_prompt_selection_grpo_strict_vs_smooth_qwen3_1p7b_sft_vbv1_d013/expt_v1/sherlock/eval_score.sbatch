#!/bin/bash
#SBATCH -J e20_eval_score
#SBATCH -p normal
#SBATCH -c 1
#SBATCH --mem=16G
#SBATCH -t 03:00:00
#SBATCH --array=0-7
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brando.science@gmail.com
#SBATCH -o /scratch/users/brando9/rl4cv_sherlock/e20/eval/logs/%x_%A_%a.log
# TLDR: Experiment 20 evaluation scoring (export LABEL): the 8 sample jobs of one evaluation through score_e20.sh (frozen
# scorer 59059a2 --skip-tc + D-109 capture); submitted with --dependency=afterok:<eval_gen job>. Resumable.
E20=$SCRATCH/rl4cv_sherlock/e20; B=$SCRATCH/rl4cv_sherlock/v4_validation
: "${LABEL:?}"
k=$SLURM_ARRAY_TASK_ID; n=eval_${LABEL}_s$k; o=$E20/eval/$LABEL/scores/$n
if [ -f $o/scsc_${n}_${n}.json ]; then echo "$n done-before"; exit 0; fi
rm -rf $o
t0=$(date +%s); bash $E20/code/score_e20.sh $E20/eval/$LABEL/jobs/$n $B/run/validation_pack $o; rc=$?
echo "$n rc=$rc $(( $(date +%s)-t0 ))s host=$(hostname -s)"; exit $rc
