# Experiment 25 stage 0: local strict + smooth Lean scoring (no Sherlock)

**TLDR:** `train_e25.py` scores rollouts with `$E20_ROOT/code/score_e20.sh` (strict) and `$E20_ROOT/code/partial_credit_e20.py` (smooth). Both now run on a local grading tree (Lean v4.22.0 + Mathlib + the frozen scorer, pin 59059a20) instead of Sherlock's `score_sherlock.sh`. Verified on 64 saved Exp 8 rollouts (skampere1) and 48 (mercury1, mercury2): strict agrees on 160/160. Exp 20's own saved rollouts are Sherlock-only; see the last section.

## Installed trees (set `E20_ROOT=<ROOT>`, `E20_GRADING=<ROOT>/grading`, `RL4CV_SRC=<ROOT>/grading/rl4cv/src`)

| Host | ROOT | Python to use |
|---|---|---|
| skampere1 | `/lfs/skampere1/0/brando9/rl4cv_e25` (128 cores) | any 3.12 (the scorer is stdlib-only) |
| mercury1 | `/lfs/mercury1/0/brando9/rl4cv_e25` (96 cores) | `/lfs/mercury1/0/brando9/.local/share/uv/python/cpython-3.12.11-linux-x86_64-gnu/bin/python3.12` (system python is 3.8: do not use) |
| mercury2 | `/tmp/rl4cv_e25_brando9` (`/lfs/mercury2/0/` has 16 GB free; `/tmp` is on the root disk and is lost on reboot: rebuild with the command below) | `/lfs/mercury2/0/brando9/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/bin/python3.12` |

Layout: `ROOT/code` = Exp 20's `partial_credit_e20.py`, `declaration_adapter.py`, `DeclarationProbe.lean`, `durable_capture.py`, `logged_scorer_e20.py` byte-for-byte, plus this folder's `score_e20.sh`, `score_local.sh`, `scorer_python_e20.sh`. `ROOT/grading` = `bin/{lake,lean}` (wrappers to the v4.22.0 toolchain; this is what fixes `lake: No such file or directory`), `elan/toolchains/leanprover--lean4---v4.22.0`, `lean_src` (Exp 8's Mathlib project, rev 79e94a09), `veribench_scorer` (pin 59059a20, checked by `setup_local_grading.sh`), `rl4cv/src` (copy of `src/` at install time: rerun the setup after pulling `src/`).

## What changed against Sherlock

- `score_e20.sh` keeps Exp 20's CLI (`<job-dir> <pack> <out>`) and D-109 durable compiler capture (`compiler_diagnostics/` under `<out>`); it calls `score_local.sh` where Exp 20 called `$SCRATCH/rl4cv_sherlock/grading/score_sherlock.sh`.
- `score_local.sh` runs exactly Exp 8's `run_validation.sh` call: `score_scsc.py --job-dir J --pack P --name basename(J) --gold-dir <gold> --lake-dir <lean_src> --skip-tc --out-dir O`, with `bin/` first on `PATH`.
- `scorer_python_e20.sh` is Exp 20's hook with `$E20_GRADING` in place of `$SCRATCH/...`.
- `partial_credit_e20.py` is untouched: it already reads `E20_GRADING` and `RL4CV_SRC`.
- `score_sherlock.sh` itself is not in any repo or on any host I can read. `score_local.sh` is rebuilt from its call sites (Exp 8 `score_one.sh`, Exp 20 `score_e20.sh`, the Exp 8 `scorer.log`), not copied from it.

## Use

```
ROOT=/lfs/skampere1/0/brando9/rl4cv_e25
export E20_ROOT=$ROOT E20_GRADING=$ROOT/grading RL4CV_SRC=$ROOT/grading/rl4cv/src
bash $ROOT/code/score_e20.sh <job-dir> <pack> <out>          # strict -> <out>/*_per_task.csv
python3.12 $ROOT/code/partial_credit_e20.py --job-dir <job-dir> --out <out>/partial_<name>.json --evidence-root <out>/compiler_diagnostics   # smooth
```
`train_e25.py` already passes `PATH=$GRADING/bin:$PATH`, `PYTHONPATH`, `RL4CV_SRC`, `E20_GRADING`, `PYTHON` to both. Run one job dir per sample index, as `materialize_jobs` makes them, several at once (the verification used 8 to 24 concurrent jobs).

## Install on a new host or rebuild

```
# on skampere1 (once): Exp 8 grading dir + Lean toolchain -> ROOT
bash experiments/25_*/expt_v1/scoring/setup_local_grading.sh /lfs/skampere1/0/brando9/rl4cv_e25
tar cf /dfs/scratch0/brando9/grading_tree.tar -C /lfs/skampere1/0/brando9/rl4cv_e25 grading     # 7.5 GB; /dfs/scratch0 is ~100% full, delete after
# on the target host, from a checkout (or the extracted min tree of experiments/20 sherlock, experiments/25 scoring and src/)
bash experiments/25_*/expt_v1/scoring/setup_local_grading.sh <ROOT> --from-tar /dfs/scratch0/brando9/grading_tree.tar   # ~70 s
```
The setup rewrites `bin/lake` and `bin/lean` for the host's path, so a tree is not relocatable by plain `cp`: always run the setup.

## Verify

```
python3.12 verify_local_scoring.py --root <ROOT> --saved-job <e08 jobs/opus55_s1_s0> --saved-scores <its *_per_task.csv> --pack <pack_views/teachers/opus55_s1> --n 48 --workers 24 --out <dir>
```
It writes the trial sources through the trainer's own `materialize_jobs`, runs strict and smooth as `train_e25.py` calls them, and compares with the saved rows.

## Evidence (saved Exp 8 Opus 5.5 rollouts, `results/verify_*.json`)

| Host | Rollouts (pass / fail saved) | Strict agree | Per-task fields identical | Smooth measured | Parse-failure zero credit | Adapter strict agrees | Concurrency | Wall |
|---|---|---|---|---|---|---|---|---|
| skampere1 | 64 (31 / 33) | 64 | 64 | 52 | 12 | 64 | 32 | 96 s |
| mercury1 | 48 (23 / 25) | 48 | 48 | 38 | 10 | 48 | 24 | 96 s |
| mercury2 | 48 (23 / 25) | 48 | 48 | 38 | 10 | 48 | 24 | 108 s |

- Strict: the local result equals the saved Exp 8 per-task row in `scoring_status`, `agent_compiles`, `IC_ap`, `IC_pp`, `kernel_n_theorems`, `kernel_n_honest`, `kernel_probe_ok`, `submission_status`, and the trainer's binary reward `reward_kernel_binary(scored_response(row))`, on every rollout. No disagreements.
- Smooth: the adapter's own strict equals the frozen strict on every measured rollout. The 12 / 10 not-measured ones are the "Lean parser recovered from malformed source" case, which `train_e25.py` scores as parse failure with zero smooth (the same case as Exp 20's `parse_failure_zero_credit`); all have saved strict 0.
- Smooth values are identical on all 48 rollouts shared by skampere1, mercury1 and mercury2.
- Timing per rollout (Opus files, ~8k tokens, concurrent): strict about 13 s (skampere1, 8 at once in an earlier run), 18 s (skampere1, 32 at once), 18 s (mercury1) and 25 s (mercury2) with 24 at once; smooth about 28 to 33 s for a measured rollout, 7 s for a parse failure, 0 s for an empty file. A batch of 64 rollouts is about 1 to 2 minutes on a mercury host with 24 to 32 at once.

## Not verified here (read this)

The saved **Exp 20** rollouts' Lean sources (phase 0, 4,312 cells) exist only on Sherlock (`/scratch/users/brando9/rl4cv_sherlock/e20/phase0/`); the repo keeps their scores and SHA-256s, not the files, and this task did not sign in to Sherlock. So Exp 20's saved scores could not be re-scored directly. What stands in for them:
1. The strict path is the same frozen scorer, same pin, same call as Exp 8, and it reproduces Exp 8's saved scores on 160 rollouts.
2. The smooth formula in `src/rl4cv/e13.py` reproduces Exp 20's saved `factored_reward` from its saved components on 3,203 of 3,203 measured cells (maximum difference 0).
3. Cross-host: smooth values match to the digit on three hosts.
A direct Exp 20 re-score needs the phase-0 job directories copied off Sherlock (a Sherlock sign-in, which Brando has to allow); `verify_local_scoring.py` takes any saved job dir plus per-task csv, so it reruns on them unchanged for strict.
