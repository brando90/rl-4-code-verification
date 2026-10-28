# Experiment 25 (checkpoint reuse), expt_v1: Stage 0 analyses and 0e audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/25_checkpoint_reuse_for_rho_h_law/expt_v1/cc.md>

**TLDR:** Run `python experiments/25_checkpoint_reuse_for_rho_h_law/expt_v1/stage0.py all` (CPU, about 1 minute, PYTHONPATH=src:.) to regenerate `results/0b_prefix_night{4,5}.json`, `results/0b_cross_start_night4_to_night5.json` and `results/0c_real_rho_h.json` from committed data. The 0e audit outputs are in `audit_0e/` (scripts that query the Hugging Face API, plus the parsed answers).

Prompt for a future agent: read `../PROTOCOL.md` first; do not change a frozen criterion after seeing an outcome; log deviations in `../results.md`.

TL;DR: Stage 0 code and data live here; tests are `tests/test_e25_stage0.py`.
