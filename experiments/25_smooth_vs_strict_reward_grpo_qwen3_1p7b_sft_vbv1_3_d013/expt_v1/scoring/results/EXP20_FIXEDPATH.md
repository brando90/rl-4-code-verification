# Exp 25 smooth scorer with a fixed job-dir path (AT-2442, 2026-11-01)

Problem (from AT-1799, `EXP20_RESCORE.md`): the frozen scorer (pin 59059a20, bytes hash-checked by `partial_credit_e20.py`) keeps 4000 chars of the Lean log (`COMPILE_LOG_CAP`) and every diagnostic line carries the absolute source path, so smooth d depended on the job-dir path length (4 of 48 saved Exp 20 rollouts differed, 0.0003 to 0.0006).

Fix: `code/partial_credit_fixedpath.py` (new, same CLI as `partial_credit_e20.py`, now what `train_e25.py` and `verify_local_scoring.py` call). It copies the job dir to a real path of one fixed length (default 66 characters = Sherlock's Exp 20 phase-0 job dir; `E25_FIXEDPATH_LEN`, base `E25_FIXEDPATH_BASE`, default `/tmp/e25_fixedpath`), runs `partial_credit_e20.py` there, deletes the copy, and records `scored_job_dir` and `fixed_job_dir_len` in the output JSON (`job_dir` stays the original). A symlink does not work: `declaration_adapter.inspect_source` resolves the source path. The frozen scorer and Exp 20 files are untouched; `COMPILE_LOG_CAP` is not raised because that would change pinned bytes.

What ran: `verify_fixedpath.py` on skampere1, all 48 saved Exp 20 phase-0 rollouts of the AT-1799 sample (25 job dirs, 25 at once, Lean 4.22.0 + Mathlib 79e94a09), smooth only, compared with `phase0_cells_e20.csv` factored_reward (`results/verify_exp20_fixedpath_skampere1.json`). Every scored path was 66 characters.

Result (smooth, factored_reward):
- 36 rollouts measured: 35 identical to the saved Exp 20 value (diff 0.0), 1 differs.
- The 4 path-length cases now reproduce the saved values exactly, from any original job-dir path.
- 12 rollouts unresolved (Lean parser recovered from malformed source): same as before; saved 0.0 or empty, train_e25 scores them 0.0.
- Not re-run: strict (does not read the log; 48/48 agreed in AT-1799).

Borderline-timeout case (`easy_set__1_myadd`, e20_p0_c0_s5): still differs, 0.2039 vs saved 0.2154 (d 39/46 vs 46/46). Sherlock's compile hit the scorer's 600 s limit (state TIMEOUT), so no errors were read and d = 1.0; here the same file compiled before the limit, so errors were read. The limit is the default argument of the frozen `compile_lean_file`, so it cannot change without changing pinned bytes. Effect: a smooth d term can jump by about 0.01 on a rollout whose compile time sits near 600 s (here 483 s on an unloaded node, over 600 s on a loaded one). Treat smooth values of rollouts with compile time above about 500 s as load dependent; strict is unaffected.
