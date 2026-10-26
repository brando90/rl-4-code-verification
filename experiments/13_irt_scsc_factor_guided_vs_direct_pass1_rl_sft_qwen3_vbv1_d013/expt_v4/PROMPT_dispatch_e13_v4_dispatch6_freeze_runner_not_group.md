# Dispatch 6: experiment 13 v4, freeze the runner instead of the tmux pane group (CPU only; no pause, no GPU)

**TLDR:** The live pause tool reaches READY for A_1302, but its SIGSTOP never sticks. The tool stops the whole pane process group. Because the pane shell is a direct child of the tmux server, tmux receives `SIGCHLD` (stopped) and immediately sends `SIGCONT` to the pane's group. The stopped recheck therefore always fails (`WAIT_NOT_STOPPED`, reported as `WAIT_RACE`). Freeze only the python runner PID, require that state, and fix the `/proc` race. Re-admit. Do not pause anything and do not use a GPU; the master runs the pause.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, **ultra** effort, on skampere1. The dispatcher is the experiment 13 master, on 10-21-2026. All earlier binding limits still apply. The decision is unchanged: pause only A_1302 ([operational record](OPERATIONAL_V4-A3_single_pause_10-21-2026.md)).

## Evidence (master, 10-21-2026, live)

1. **The live loop** with the dispatch 5 admission (`ffbeb4e6…`) ran from 14:34 to 15:31 PDT and returned `WAIT_RACE` on every call (more than 14 calls). A_1302 was never left stopped; every check found state `S`.
2. **A master replica of `pause()`'s steps** (`/lfs/skampere1/0/brando9/rl4cv_e13v4/a1302_race_diag.py`, output `a1302_race_diag_out.txt`) ran three times at 15:31–15:32. Each time:
   - the pre-stop `boundary()` was `READY`;
   - the group members were `[(691994 sh, S, do_wait), (692011 python, S, hrtimer_nanosleep)]`;
   - after `os.killpg(691994, SIGSTOP)`, a 0.05 s sleep and `observe()`, **both members were still `S`**, with the same wait channels;
   - `observation_status(stopped=True)` returned `WAIT_NOT_STOPPED`;
   - identity, `latest_update`, `files`, `leases` and `lease_files` were all equal.
3. **Control outside tmux.** The same group stop on a `setsid sh -c python…` group gives `T`/`do_signal_stop` for both members, and it persists for at least 1 s.
4. **Cause.** tmux's server, in `server_child_stopped()`, sends `killpg(pane_pid, SIGCONT)` whenever a pane's direct child stops for any reason other than `SIGTTIN`/`SIGTTOU`. Confirm this against the installed tmux version on skampere1.
5. **Separate bug.** At 14:19 a call crashed with `FileNotFoundError: /proc/42087/stat`. Some `proc()` call outside the guarded census loop reads a process that exited mid-scan. It is likely in the per-runner `fresh`, the `process_group_members` or a `references` path.

## What to build

1. **Freeze the runner only.**
   - Send `SIGSTOP` to the python runner PID with `os.kill`, after the identity check, not to the group.
   - The stopped check requires the runner to be `T`/`do_signal_stop`, with zero children, and the pane shell (the group's other member) to stay `S`/`do_wait` with unchanged identity.
   - Keep every other rule: two observations, an unchanged disk state, the shared watchdog lock, the atomic pause list and the PID checks.
   - After the pause list is durable, send `SIGTERM` to the runner's group, as before.
   - In `finally`, send `SIGCONT` to the runner PID, after an identity check.
   - Bound the time stopped, and never leave the runner stopped on any exception path.
2. **The `/proc` race.** Treat a process that vanishes during any read as "changed". Return a WAIT status instead of raising, and keep the existing safety meaning.
3. **Tests.**
   - A fake-tmux test where a group stop is auto-continued, as it is under tmux, and the runner-only stop holds.
   - Vanishing-process tests at each `proc()` call site.
   - Every exception path sends SIGCONT.
   - Rerun the v4 suite, the watchdog test and the root suite.
4. **A live stop test on a dummy tmux pane you own** (not a v3 run). Create a tmux session whose pane runs `sh -c '<venv python> -c "sleep loop"'`, with a name outside the `rl4cv-e13v3-*` and `rl4cv-e13v4-*` prefixes. Show:
   - a group SIGSTOP is auto-continued by tmux;
   - a runner-only SIGSTOP holds (state `T`) while the shell stays `S`;
   - SIGCONT restores it.

   Kill the dummy afterwards.
5. **Read-only live probe of A_1302** (no `--execute`), then **re-admission**: a new admission, and `launch-check` must pass. Update the master commands in `CKPT_v4_implementation.md`. Reuse the existing pause loop (the master's wrapper is `/lfs/skampere1/0/brando9/rl4cv_e13v4/a1302_pause_then_gates.sh`, which retries only `/proc` races) and the existing gate start. If the admission filename changes, say so.

## Binding limits

- No `--execute` against any v3 run, no real pause list, no cron install.
- No GPU allocation, generation or optimizer step.
- Do not touch the six v3 runs or their sessions beyond read-only `/proc` and file inspection.
- The shared venv is read-only.
- $0.
- Kill only processes you started, including the dummy tmux session.
- No edits to the frozen protocol, the amendments, or the operational records.
- Commits use explicit pathspecs; rebase, then push to `main`.

## Deliverables

- Code and tests, with counts.
- The dummy-pane stop evidence.
- The A_1302 read-only probe output.
- The new admission SHA-256.
- The updated master commands.
- One copy-ready sentence in `CKPT_v4_implementation.md`.
