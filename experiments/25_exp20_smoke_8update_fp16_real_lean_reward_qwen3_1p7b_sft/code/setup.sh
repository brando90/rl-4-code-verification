#!/bin/bash
# Exp 25 setup on Sherlock: code dir, fp16 copy of the start checkpoint (symlinked weights, config torch_dtype float16)
E20=$SCRATCH/rl4cv_sherlock/e20; E25=$E20/e25; M=$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf
mkdir -p $E25/code $E25/logs $E25/ckpt_fp16
cp train_e25.py $E25/code/; cp e25.sbatch $E25/
for f in $M/*; do b=$(basename $f); [ $b = config.json ] || ln -sfn $f $E25/ckpt_fp16/$b; done
sed -E 's/"((torch_)?dtype)": *"bfloat16"/"\1": "float16"/' $M/config.json > $E25/ckpt_fp16/config.json
grep -n dtype $E25/ckpt_fp16/config.json; ls $E25 $E25/ckpt_fp16 | head -30; sha256sum $E25/code/train_e25.py
