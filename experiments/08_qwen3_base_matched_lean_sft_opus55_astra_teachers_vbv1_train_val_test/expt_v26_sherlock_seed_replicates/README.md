# V26: Sherlock seed replicates (third v4 1.7B seed; v4 recipe at Qwen3-4B-Base, 2 seeds)

**TLDR:** One Slurm chain on Sherlock trains three checkpoints with the exact [expt_v4](../expt_v4/PROTOCOL.md) recipe and data (1.7B seed 20260832; 4B seeds 20260830 and 20260831), generates 135 validation tasks x 8 for each with the frozen v12 settings, and Lean-scores them. Result (all metrics no DT: Lean kernel check plus non-vacuity gate, no differential testing): 1.7B seed SD 0.30 pts pass@1 (range 0.56) over three seeds; 4B 8.98% and 8.70% pass@1, within noise of SNAP's `sft_4B_f1p0` (9.26%), pooled +3.81 pts over 1.7B. This is the fallback because the V20/V23/V25 training data is on SNAP only. Frozen design: [PROTOCOL.md](PROTOCOL.md). Status: done (results in [results.md](results.md)).

## Files

| File | What it does |
|---|---|
| `PROTOCOL.md` | Locked design, arms, metrics, predictions (committed alone, before this package) |
| `train_v26.py` | `prepare`: corpus copy + hash, both model downloads + per-file hashes (shards vs Hub LFS), v4 token gate with each tokenizer, chain-input checks. `train --arm --seed`: expt_v4's loop; 4B uses `HostAdamW` (same AdamW on float32 host copies) |
| `run_job.sh` | Slurm wrapper for prepare/train (expt_v4's, Sherlock modules only) |
| `gen_v26.sbatch` | AT-476's vLLM Apptainer generation command (v12 settings) for one checkpoint, then the Lean job dirs; fails unless 1,080 cells |
| `score_one.sh` | AT-477's claim-based scorer for one sample job, unchanged |
| `score_v26.sbatch` | Array 0-7 on `normal`, `-c 1 --mem 16G`, one sample each |
| `collect_v26.sh` | `afterany` collector: receipts, step tables, raw generations, scores, logs, sacct table -> `$SCRATCH/rl4cv_sherlock/expt_v26_results.tgz` (+ `.sha256`) |
| `submit.sh` | Submits everything once with `--dependency` (afterok; collector afterany), mail BEGIN/END/FAIL to both of Brando's addresses, ids in `jobs_v26.tsv` |
| `analyze_v26.py` | pass@1, pass@8, 95% task-bootstrap CIs, seed spread, paired differences; run locally on the fetched tarball |
| `tests/test_offload_equivalence.py` | HostAdamW gives bit-identical parameters to in-place AdamW over 60 updates (passes, torch 2.6.0 CPU) |
| `tests/standin_v16_tables.md` | analyze_v26.py on the expt_v16 scores reproduces expt_v16's committed numbers |

`token_manifest.jsonl` is expt_v4's file, copied into the package (not duplicated in Git); `prepare` checks its hash.

## Chain

| Step | Partition / resources | Wall | Depends on |
|---|---|---|---|
| prepare | `normal`, 4 CPU, 32 GB | 2 h | — |
| train 1p7b_s20260832 | `gpu`, 1 GPU `GPU_MEM:80GB` (H100), 4 CPU, 64 GB (= expt_v4) | 4 h | afterok prepare |
| train 4b_s20260830, 4b_s20260831 | `gpu`, 1 GPU `GPU_MEM:80GB` (H100), 16 CPU, 128 GB | 12 h | afterok prepare |
| gen x3 | `gpu`, 1 GPU `GPU_SKU:L40S\|GPU_SKU:H100_SXM5`, 8 CPU, 48 GB | 6 h (1.7B), 10 h (4B) | afterok its train |
| score x3 (array 0-7) | `normal`, 1 CPU, 16 GB | 3 h | afterok its gen |
| collect | `normal`, 1 CPU, 4 GB | 1 h | afterany all |

Training needs an 80 GB GPU (1.7B peaked at 47.85 GiB in expt_v4, above an L40S's 48 GB less overhead; 4B keeps ~32 GB of float32 parameters + gradients on the GPU). The three trainings run in parallel, one GPU each.

## Remote layout

Package and outputs live in `$SCRATCH/rl4cv_sherlock/expt_v26`: `data/` (corpus, tokens), `cache/huggingface` (both models), `runs/<arm>_s<seed>/` (steps.csv, identity/result/weights_manifest, `hf/` export, training_state.pt), `gen/<label>/raw.jsonl`, `score/<label>/{jobs,scores}`, `logs/`, `jobs_v26.tsv`. It reads, never writes, the AT-476 generation tree (`$SCRATCH/rl4cv_sherlock/v4_validation/{rl4cv_gen,run/validation_pack}`), the vLLM image and the AT-475 grading directory. Weights stay on `$SCRATCH` (90-day purge applies).

## Analysis after the collector

```
tar xzf expt_v26_results.tgz -C <dir>
python analyze_v26.py --v26-root <dir> --v16-data <expt_v16 data: v16_v4_2026083x/{raw.jsonl,scores}> --out results
```

The test split is never loaded.
