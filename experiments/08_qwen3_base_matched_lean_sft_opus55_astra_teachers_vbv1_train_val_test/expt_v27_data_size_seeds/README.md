# V27: SFT data-size ablation with seeds (Qwen3-1.7B-Base, v4 recipe, 12.5 / 25 / 50% x 2 seeds)

**TLDR:** One Slurm chain on Sherlock trains six Qwen3-1.7B-Base checkpoints with the exact [expt_v4](../expt_v4/PROTOCOL.md) recipe on the first 12.5%, 25% and 50% of S (the same nested examples experiment 08's ladder rungs had seen), two data-order seeds each, then generates 135 validation tasks x 8 per checkpoint with the frozen v12 settings and Lean-scores them like expt_v16. The 100% rung is the two existing v4 seeds. Readout: each data doubling's pass@1 / pass@8 gain vs seed noise (0.56 / 4.4 pts) and vs experiment 17's curve. Frozen design: [PROTOCOL.md](PROTOCOL.md). Status: package built, not yet submitted.

## Files

| File | What it does |
|---|---|
| `PROTOCOL.md` | Locked design, subsets, runs, metrics, pre-registered readout and predictions (committed alone, before this package) |
| `runs.tsv` | The six runs (index = Slurm array task id): fraction, seed, run name, label |
| `train_v27.py` | `prepare`: corpus copy + hash, Qwen3-1.7B-Base download + per-file hashes (shard vs Hub LFS), v4 token gate, ladder subsets checked against the rung token counts (`data/subsets.json`), chain-input checks. `train --index i`: expt_v4's loop on runs.tsv row i (subset, seed, ceil(n/2) updates, warmup 20 + cosine to 0) |
| `run_job.sh` | Slurm wrapper for prepare/train (expt_v4's, Sherlock modules only) |
| `gen_v27.sbatch` | Array task i: AT-476's vLLM Apptainer generation (v12 settings) for run i, then the Lean job dirs; fails unless 1,080 cells |
| `score_one.sh` | AT-477's claim-based scorer for one sample job, unchanged |
| `score_v27.sbatch` | Array 0-7%4 on `normal`, `-c 1 --mem 16G`, one sample each |
| `collect_v27.sh` | `afterany` collector -> `$SCRATCH/rl4cv_sherlock/expt_v27_results.tgz` (+ `.sha256`), no weights |
| `submit.sh` | prep -> train array 0-5%3 (afterok) -> gen array 0-5%3 (aftercorr) -> 6 score arrays (afterok on gen task i) -> collect (afterany); mail BEGIN/END/FAIL to both of Brando's addresses; ids appended to `jobs_v27.tsv` |
| `analyze_v27.py` | Per run and per rung pass@1 / pass@8 with 95% task-bootstrap CIs, rung-to-rung gains vs the seed-spread bars, E17 curve comparison, complete runs vs SNAP ladder rungs |
| `tests/test_v27.py` | CPU tests: subsets = ladder rungs (tokens, steps, nesting, manifest order), run table + orders, schedule shape at 82/164/334/658 steps, the training loop on a tiny Qwen3, E17 constants = refit (all pass, torch 2.14 CPU) |
| `tests/standin_tables.md` | analyze_v27.py on stand-ins built from the expt_v16 scores (pipeline check, not results) |

## Run on Sherlock

```bash
# upload rl4cv_v27_pkg.tgz to $SCRATCH/rl4cv_sherlock/, then:
cd $SCRATCH/rl4cv_sherlock && mkdir expt_v27 && tar xzf rl4cv_v27_pkg.tgz -C expt_v27 && cd expt_v27 \
  && sha256sum -c --quiet PACKAGE_SHA256SUMS && echo PKG_OK && bash submit.sh
```

Inputs it expects on Sherlock (all built by AT-475/476/477): `$SCRATCH/rl4cv_sherlock/expt_v4/data/s_v1.jsonl`, `v4_validation/` (vLLM pack, generation code), `containers/vllm-openai_v0.30.0.sif`, `grading/` (Lean 4.22 + Mathlib). Prep fails in minutes if one is missing.

## Analysis (local, after the collector)

```bash
tar xzf expt_v27_results.tgz -C v27_root
PYTHONPATH=src python analyze_v27.py --v27-root v27_root --v16-data <expt_v16 data: v16_v4_2026083{0,1}/raw.jsonl + scores/> --out results
```

Needs the repo's `external/veribench_scorer` importable, as for expt_v16.

**TLDR-end:** [rl4cv: SFT data-size ablation] `08_.../expt_v27_data_size_seeds` is a ready Sherlock package for six 1.7B runs (12.5/25/50% x 2 seeds) scored like expt_v16; not yet submitted.
