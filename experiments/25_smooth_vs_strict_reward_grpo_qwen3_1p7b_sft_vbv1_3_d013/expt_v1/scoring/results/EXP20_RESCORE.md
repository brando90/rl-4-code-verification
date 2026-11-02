# Exp 25 scoring check on Exp 20's own phase-0 rollouts (AT-1799, 2026-11-01)

What ran: `verify_exp20_rescore.py` on skampere1 re-scored 48 saved Exp 20 phase-0 rollouts (Lean sources copied from Sherlock `e20/phase0/jobs`, source SHA-256 equal to the saved one on all 48) with the Exp 25 local scorer: strict via `code/score_e20.sh` (frozen scorer pin 59059a20), smooth via `code/partial_credit_e20.py`, local Lean v4.22.0 + Mathlib 79e94a09. Saved values are the rows of Sherlock `phase0_cells_e20.csv`. Sample (seed 1799): 16 strict passes, 20 strict-fail rollouts with measured smooth, 6 parse-failure, 6 unresolved (`exp20_rescore_sample.csv`).

Result (`verify_exp20_skampere1.json`):
- strict: 48/48 agree (binary reward), compiles: 48/48 agree.
- smooth (factored_reward): 37/48 identical, plus the 6 parse-failure rollouts where Exp 20 saved 0.0 and the local scorer reports "unresolved measurement: Lean parser recovered from malformed source", which train_e25.py scores as 0.0 -> 43/48 agree after that mapping; 5 differ by 0.0003 to 0.0115 (all strict 0).

The 5 smooth differences, both explained:
1. 4 rollouts (differences 0.0003 to 0.0006): the declarations term d is one declaration lower locally. Cause: the frozen scorer keeps only 4000 characters of the Lean log (head 2000 + tail 2000, `COMPILE_LOG_CAP`), and every diagnostic line carries the absolute file path, so the number of error lines that survive depends on the job-dir path length (Sherlock path 12 characters longer than the local one). Check: re-run with a job dir path of the same length as Sherlock's -> all 4 reproduce the saved factored_reward exactly (`verify_exp20_pathmatched_rerun_skampere1.json`, differences 0.0).
2. `easy_set__1_myadd` (difference 0.0115, d 39/46 locally vs 46/46 saved): the saved Sherlock run hit the scorer's 600 s compile timeout (execution.json state TIMEOUT), so no errors were read and d = 1.0; locally the same file compiled in 483 s, inside the limit. Not a code difference; it is a compile that sits near the 600 s limit. The path-matched rerun still differs here, as expected.

Implication for the Exp 25 trainer: smooth reward's d term depends on job-dir path length (and on borderline compile time), by up to about 0.01 on measured rollouts. Keep one fixed job-dir path for every scoring call, or raise `COMPILE_LOG_CAP`, before comparing smooth values across runs. Strict is unaffected.
Wall: 1,063 s for 48 rollouts x (strict + smooth), 24 workers, loaded node.
