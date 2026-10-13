# Experiment 13 version 2 owner checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/CKPT_e13_v2_owner.md>

**TLDR:** Amendment A1 resumed experiment 13 version 2; R0 attempt 2 passed all 30 fixtures and its required repository suite.

Created: 10-13-2026 11:44 PDT
Last updated: 10-13-2026 12:57 PDT

## Goal
- Complete amended development acceptance, then the unchanged scientific gates and matched reinforcement-learning comparison.
## What ran
- R0_attempt_2 completed as process 280828; 30 authored fixtures, serial 64 GiB address-space ceiling.
- Required full suite: 283 passed, 23 skips, 168.61 seconds; all seven required Lean integration cases executed.
- Fix/justification commits before rerun: `3fbcb96`, `7ed9e85`, `76d85b4`.
## Results
- Attempt 2 PASS, 30/30; lock `67f005f9b146704ec5007be748d6a30bc01239d0f0af826d3aec489799872759`. Attempt 1 retained at 26/29 matches.
- Owner process 887384, full access/no approvals; fenced watchdog re-armed as `e13v2_a1`, two owned cron entries restored.
## Stuck / blocked
- None. No historical train, validation or test cell has run for version 2.
## Next steps
- [p 10/10] Publish accepted R0; freeze and execute R1 train-only diagnostic.
## Brando to-do
- None.

## Log
- 10-13-2026 12:57 PDT -- R0 attempt 2 completed PASS: 30/30 fixtures, oracle values/statuses, and components. R1 admitted after publication.
- 10-13-2026 12:52 PDT -- Resumed under A1 at `cb5e175`, committed three justified fixes, froze and launched attempt 2; required full suite passed.

## Prior owner record (before A1; stop superseded)

- Owner: skampere1, tmux `codex-rl4cv-e13v2-owner`; Codex `gpt-6-astra`, effort `high` (runbook worker pin), command-line interface 0.154.0; observed full access `danger-full-access`, approvals `never`.
- Owner native process: 887384; boot `839e7dd6-64e1-4a80-9498-31d30b3cc2df`. Launch evidence: `/lfs/skampere1/0/brando9/rl4cv_e13v2/owner_launch.json`. First useful actions: read binding plans, inspect clean checkout and process inventory.
- Work root: `/lfs/skampere1/0/brando9/rl4cv_e13v2`; owned clone `rl-4-code-verification`, branch `main`, starting revision `1e0c8f85a5943997ee2124180f7e492db3ca92b8`.
- Coordination: no live version 1 session or executable found. Pattern matches in the current owner's arguments are the pasted runbook, not a version 1 writer. Master checkpoint remains separately owned.
- Version 1 preservation: complete file digest inventory at `$WR/state/v1_baseline_hashes.json`; version 1 files stay byte-identical.
- Environment: pinned Lean and scorer under `/lfs/skampere1/0/brando9/rl4cv_e08/` read-only. New virtual environment, caches and temporary files under this work root.
- Resources: no accelerator allocation or model calls; setup and fixtures use central processors. Preflight available memory 1,939 GiB; filesystem free 5.4 TiB. Cell concurrency is not chosen until train diagnostics measure memory.
- Denominators: train/validation/test tasks 539/135/222; full reproduction 38,784 unique cells; base 21,504 plus ladder 20,520 minus overlap 3,240. Parent unavailable ladder 5,400 stays separate. Diagnostic target 300 rejected plus 100 measured train cells, selected by identifier only.
- Chronology: no validation or test factors computed in version 2; lock precedes those measurements. Historical test content remains opaque.
- Authorization: verbatim Stanford Network Analysis Project pre-approval in `cc.md`; no new charges or provider-key route used.
- Published initial records: `c49d4ba` (includes own `63ccdfc` and the master's concurrent checkpoint update). Setup `make test`: 277 passed, 23 skipped. SciPy was installed in the private environment after an initial collection failure.
- Watchdog: six tests passed (fake mailer, unique tmux kill, concurrent recovery, orphan child, persistent attempts, deterministic no-retry). Full `make test`: 283 passed, 23 skipped. Shared lock `$WR/watchdog/recovery.lock`; SQLite attempt/process ledger persists across boots. Owner PID/start/boot checked. Two additive cron entries installed (15 minutes, reboot). Existing mail credential authenticated without sending; only terminal/human-needed events email.
- Recovery configuration currently monitors the registered owner and adopts registered children; automatic executor replacement is not yet configured. Do not claim unattended executor recovery until the verified handoff route is installed.
- Node health: shared filesystem percentage-free warning (3,212 GiB free) does not constrain the bounded local fixture work; local work root has 5,483 GiB free. No shared cleanup performed.
- Authored development evidence only: valid source oracle 1, components at maximum; failed proof followed by valid theorem retains proof fraction 1/2 and command fraction 2/3. These are development checks, not the frozen R0 gate. Raw evidence under `$WR/state/`.
- Formal R0 freeze: `locks/R0.json`, digest `e2041b3ca1f4fca5a226c8cc28b1d544698ea5ea5968d27d8a09ea5f5a092a49`; serial execution under 64 GiB address-space ceiling and durable per-fixture attempts. Results digest `6d87f6a616fdac0c229b63df5ec36b474d87086d452a0c08565899a0a26991d0`.
- Required integration suite: 283 passed / 23 unrelated conditional skips / 0 failed, 164.72 seconds; all 30 inherited experiment-13 tests executed. Initial isolated Pytest startup lacked pygments, failed before collection, and was repaired without retrying scientific fixtures.
- Failures: unavailable `String.ofList` in authored long-log fixture (d=2/5, expected 4/5); stderr assertion (text retained as information message); unresolved theorem causes frontend exit 1 on `Mathlib.pp.mathlib.binderPredicates` initialization. Strict oracle remains independently reproduced for all 29 cases.
- Frozen scientific implementation and all authored sources are retained. Raw evidence: `$WR/r0/`; source copies and complete hash inventory are published under `expt_v2/`. The 42 original version 1 files are byte-identical.
- R1 preparation was never executed; three draft scripts are preserved privately at `$WR/state/unexecuted_r1_preparation/`. No train allowlist, L1v2 lock, historical factors, fitted model or training exists.
- Terminal closeout: gate result pushed as `6e9c7c2bc1c2435f1455ec7667b1933e8e16174b` and verified on remote `main`. The watchdog recorded exactly one `stopped` notification as `sent` to `brando.science@gmail.com` without carbon copy. Both owned cron entries were retired; all unrelated entries were preserved. No registered experiment child remains alive. Durable receipt: `$WR/state/completion.json`. No downstream run is admitted.
- Binding stop: R0 failed. This condition is terminal, not an infrastructure retry or an account handoff. The parent retains the unresolved measurement dependency for its planned reinforcement-learning comparison.
