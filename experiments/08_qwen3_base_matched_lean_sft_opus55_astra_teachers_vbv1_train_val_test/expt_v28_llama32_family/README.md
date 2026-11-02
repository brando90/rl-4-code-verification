# V28: model-family replicate (Llama-3.2-1B and 3B; Gemma-3 prepared)

**TLDR:** Package for the second model family: the expt_v4 Lean SFT recipe at Llama-3.2-1B and 3B, three seeds each, validation pass@1 and pass@8 (no DT), same columns as the Qwen3 tables of [V26](../expt_v26_sherlock_seed_replicates/README.md). Design: [PROTOCOL.md](PROTOCOL.md). Status: full chain finished 2026-11-02 (60 of 60 jobs COMPLETED); results in [results.md](results.md): Llama-3.2-1B 2.96% and 3B 7.35% validation pass@1 (no DT), 3B beats 1B by +4.38 pts, both below Qwen3 at matched size; one locked prediction missed (3B just above 7%). Gemma-3 smoke package prepared, not submitted.

## Files

| File | What it does |
|---|---|
| `PROTOCOL.md` | Design, models, deviations, predictions, Gemma addendum |
| `train_v28.py` | `prepare` (corpus hash, model download + hashes, per-family token gate and manifest), `train` (expt_v4 loop, `HostAdamW` for 3B), `smoke` (4 updates on the longest examples, peak memory, export) |
| `run_job.sh` | Slurm wrapper for prepare, train and smoke (Sherlock modules only) |
| `gen_v28.sbatch` | vLLM generation for one checkpoint with the family's stop tokens; `SMOKE=1` for 3 tasks x 2 samples |
| `score_one.sh`, `score_v28.sbatch` | Lean scoring, one sample per array task (V26's, renamed) |
| `collect_v28.sh` | Terminal collector -> `$SCRATCH/rl4cv_sherlock/expt_v28_results.tgz` |
| `submit.sh` | `smoke`, `full` or `gemma-smoke`; ids in `jobs_v28_smoke.tsv` / `jobs_v28.tsv` / `jobs_v28_gemma_smoke.tsv` |
| `analyze_v28.py` | pass@1, pass@8, CIs, seed spread, paired differences, Qwen3 reference rows |
| `tests/test_formats.py` | Prompt and stop-token checks for Llama-3 and Gemma-3 formats against the real tokenizers (pass) |
| `tests/test_offload_equivalence.py` | `HostAdamW` equals in-place AdamW (V26's) |

## Run

On Sherlock: copy this folder to `$SCRATCH/rl4cv_sherlock/expt_v28`, `bash submit.sh smoke`, read `logs/` and `runs_smoke/*/steps.csv`, then `bash submit.sh full`. `prepare_receipt.json` pins `train_v28.py`'s hash: editing the script after prepare makes training refuse to start.

## Gemma-3 smoke (prepared 2026-11-02, not submitted)

Copy this folder to `$SCRATCH/rl4cv_sherlock/expt_v28_gemma_smoke` on Sherlock and run `bash submit.sh gemma-smoke` there (own `prepare_receipt.json`, data and cache; the Llama receipt is untouched). `train_v28.py` gained two environment switches that default to the Llama behaviour: `V28_ARMS=gemma1b,gemma4b` (set by `submit.sh gemma-smoke`) enables exactly those models, and `V28_ATTN=sdpa|eager` picks the attention backend. Details and pass rule: Gemma-3 smoke addendum in [PROTOCOL.md](PROTOCOL.md).
