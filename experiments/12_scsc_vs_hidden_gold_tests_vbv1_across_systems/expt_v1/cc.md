# Run and land experiment 12 phase A (SCSC versus hidden gold-reference tests on VeriBench V1) on skampere1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/cc.md>

**TLDR:** You test whether VeriBench's SCSC agrees with hidden gold-reference tests, with zero model calls. Extract each gold reference's ground `example` tests. Build and validate a mechanical adapter that re-points those tests at a candidate's own Lean function, then lock the protocol. Evaluate every saved candidate file of the 11 primary systems (plus experiments 01 and 08 as secondary panels). Then run the frozen analyses P1–P3 and publish `results.md` with every denominator.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Context and rules

- **Read first:** `~/agents-config/INDEX_RULES.md`; the repository `CLAUDE.md` (D-004 frozen forecasts, D-012 push small and often); then `EXP=experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems` → `README.md`, `PROTOCOL.md`, `expt_v1/forecasts/e12_phase_a_forecast.json` (frozen; never edit), `expt_v1/CKPT_e12.md`. Background: experiment 04's `METRICS.md` and `expt_v3/results.md` (why its generic adapter failed), experiment 07 (the analysis template), and VeriBench experiment 75's `prover_diagnostics/results/01_adapter_synthesis` (an older adapter attempt: learn from its failure classes, do not trust or reuse its outcomes).
- **Owner:** Emily Xia (@emxia18), with Ethan Li (@lethan3) advising; tracking issue in the checkpoint. Master: Claude Code on Brando's laptop.
- **Work root:** `WORK=/lfs/skampere1/0/brando9/rl4cv_e12`, with your own clone `$WORK/rl-4-code-verification` on `main`. Pull before every push, stage explicit paths, push each landed step. Raw candidate files, bridges and per-test logs stay under `$WORK` (they contain model output on VeriBench tasks); commit manifests, hashes, controls and summaries.
- **Zero model calls, zero judge calls, zero GPUs.** CPU-only Lean compilation in the frozen grading project used by experiments 01, 05 and 08: find it from experiment 08's `expt_v1/results/scorer_adapter_check.json` and 01's `run_model.sh` (Lean v4.22.0, Mathlib at the recorded commit). Keep Lean parallelism polite: the host is shared, so watch the load average and other users' jobs.
- **Never read sealed data:** experiment 107's human-round packets or key, or experiment 109's sealed FSC/SCSC.
- **Never edit** a candidate file, gold file, recorded factor or the frozen forecast. Never re-sample, drop or reorder cells by outcome.
- **Checkpoint:** keep `$EXP/expt_v1/CKPT_e12.md` live (Created / Last updated from `date "+%m-%d-%Y %H:%M %Z"`; step, commits, exact next command, blockers). `results.md` is the live result record. The status file `$WORK/STATUS_e12` holds `RUNNING`, `BLOCKED: <reason>` or `DONE`.

## 1. Inputs and joins (zero outcomes)

1. Locate and hash the inputs of PROTOCOL § 1:
   - VeriBench experiment 103's `summary.json` rows plus its collected candidate files on this host (search `/lfs/skampere1/0/brando9/veribench_vb103/…/private/`);
   - experiment 102's `validated_per_candidate.csv` plus its candidate files through `input_inventory_tier1.json` / `tier2.json`;
   - rl4cv experiment 01's scored JSONL and job files (`/lfs/skampere1/0/brando9/rl4cv_e01/out/`);
   - experiment 08's validation ladder cells (`/lfs/skampere1/0/brando9/rl4cv_e08/`);
   - the 896 gold files at the pin.
2. Join every factor row to exactly one candidate file (SHA-256 where recorded). Write `$EXP/expt_v1/results/input_manifest.json` with per-system counts and `file_missing` lists. Apply the stop rules of PROTOCOL § 6: file missing above 5%, the system SCSC recompute, and the 100-file compile reproduction.
3. Commit and push.

## 2. Hidden tests and adapter (zero real-candidate outcomes)

1. `$EXP/expt_v1/scripts/extract_hidden_tests.py` (one-sentence TLDR docstring): PROTOCOL § 2. Write `hidden_tests_manifest.json` with per-task test counts and `no_tests` tasks.
2. `$EXP/expt_v1/scripts/adapter_e12.py`: PROTOCOL § 3's mapping, allowed transformations and bridge, with unit tests under `tests/`. Run `make test`.
3. Run controls C1–C4 (gold, renamed gold, mutated gold, wrong task). Write `controls_e12.json`. If an expectation misses, fix the extraction or adapter and rerun all controls; never relax an expectation.
4. Lock: fill PROTOCOL's lock line with the adapter and extraction hashes recorded. Commit and push **before** any real candidate is evaluated.

## 3. Evaluate (after the lock)

- Evaluate every compiling candidate in the primary panel, then the secondary panels, producing the per-cell outcomes of PROTOCOL § 4 in `$WORK/cells_e12.jsonl` (no file contents).
- Retry only infrastructure failures (a process killed, the host out of memory), as the identical cell; a timeout is `unknown`.
- Commit summaries at milestones.

## 4. Analyze and publish

1. `$EXP/expt_v1/scripts/analyze_e12.py`: PROTOCOL § 5 (P1, P2, P3, G-A, descriptive tables, bounds, and the experiment 08 secondary rows). Seed 20261009.
2. Verify the forecast hash with `rl4cv.forecast.verify_forecast` before reading any analysis output.
3. Fill `results.md`:
   - a one-sentence setup and verdict;
   - each prediction with its value, interval and holds/fails;
   - the per-system table, coverage and bounds;
   - the inspected disagreements;
   - the secondary panels;
   - deviations.
   Report failed predictions exactly like successful ones (D-004).
4. Update `experiments/README.md` row 12 and the README status table. Run `make test`, commit and push.
5. Write `DONE` and give the checkpoint its final state (verdicts with numbers, coverage, next version: hidden proofs and the agent-spec v8 panel).

**TL;DR:** Extract the gold references' ground tests, validate a mechanical adapter on controls, lock, run every saved candidate through it with zero model calls, and publish whether SCSC tracks hidden-test success (P1), beyond compiling (P2), with frozen predictions and full denominators.
