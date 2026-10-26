# Dispatch 4: experiment 13 v4, single-run pause mode and re-admission (CPU only; no pause, no GPU)

**TLDR:** Implement [the operational change to V4-A3](OPERATIONAL_V4-A3_single_pause_10-21-2026.md): pause exactly one designated v3 run, A_1302, instead of five, and release v4's gates once that one pause is recorded. Test and dry-run it, and publish a new admission. Do not pause anything and do not use a GPU; the master runs the pause and starts the gates.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, **ultra** effort (Brando: "when in doubt ask codex ultra max thinking"), on skampere1. The dispatcher is the experiment 13 master, on 10-21-2026. All binding limits from dispatches 1–3 still apply.

## Read first

- `expt_v4/OPERATIONAL_V4-A3_single_pause_10-21-2026.md`: the decision, the rule and the designated run.
- `AMENDMENT_V4-A3_…`, `CKPT_v4_implementation.md`, `README.md`.
- `phase2/pause_v3.py`, `phase2/admission.py` (`launch_timing`), `phase2/runner.py`, `phase2/launch_control.py`, `phase2/install_watchdog.py`, `phase2/build_plans.py`, `phase2/dry_run.py`, and their tests.
- The v3 watchdog's pause-list feature.

## What to build

1. **Designated single pause.** `pause_v3.py` pauses only the designated run, A_1302. It reads the run from a small machine-readable operational record bound in the admission, for example `phase2/operational_pause.json`, with `{"mode": "single", "trajectories": ["A_1302"], "record": "OPERATIONAL_V4-A3_single_pause_10-21-2026.md"}`.
   - Keep every safety check: clean lease-wait boundary only, `SIGSTOP` then a recheck, PID-reuse checks, the shared lock with the v3 watchdog, an atomic pause list, and never `B_1301`.
   - Refuse any trajectory that is not designated.
2. **Gate release.** `launch_timing` and the runner release `gates` when the veto condition holds and the designated pause is recorded. The pilot keeps its existing conditions: B_1301's `T5_30.json` exists with its lease released, and all gates passed.
   - v4 stages compete fairly for idle authorized devices through the same per-device locks. Add no standing reservation.
   - The pilot still needs 3 GPUs and still respects every v3 lock.
3. **Veto condition.** Keep the `E13V4_A3_NO_VETO=1` / `--veto-not-issued` gate, and keep 12:00 PDT 10-21 as the earliest time. Brando's choice of a single pause was made at about 11:2x, so the window has passed whenever the master runs this.
4. **Tests.**
   - Unit tests for single-pause selection, refusal of a non-designated run, refusal of `B_1301`, and gate release with one pause but not with none.
   - The pilot must still wait for B_1301.
   - Rerun the full v4 suite, the v3 watchdog test, and the root suite.
5. **Dry run.** A GPU-free stub dry run of the single-pause path: the pause tool returns WAIT while a stage runs and PAUSED at a fake boundary, and the gates are released only afterwards.
6. **Admission.** A new admission binding the operational record and the changed code. `launch-check` must pass, with runtime conditions listed: the designated pause recorded, an idle authorized lease, and the pilot conditions.
7. **Commands for the master.** Record exact commands in `CKPT_v4_implementation.md`:
   - a read-only boundary probe for A_1302;
   - a pause loop that calls the pause tool every 20 s until A_1302 is PAUSED, then installs the v4 watchdog once;
   - the gate start;
   - a progress check.

## Binding limits

- Do not run the pause tool with `--execute` and do not create the real pause list.
- Do not install the cron line.
- No GPU allocation, model generation or optimizer step.
- Do not touch the six running v3 trajectories, their tmux sessions, or v3's cron line.
- The shared venv is read-only.
- $0.
- Kill only processes you started.
- No edits to the frozen protocol, the amendments, or the operational record. If something cannot be done as written, record the smallest fix in the checkpoint.
- Commits use explicit pathspecs; rebase, then push to `main`.

## Deliverables

- Code and tests, with v4, watchdog and root-suite counts.
- An updated `CKPT_v4_implementation.md`: status, the new admission SHA-256, the exact master commands, a fresh GPU census, and one copy-ready sentence.
