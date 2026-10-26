# Dispatch 7: experiment 13 v4, count only relevant vanished processes (CPU only; no pause, no GPU)

**TLDR:** With the dispatch 6 admission (`71d9be74…`), the live A_1302 pause loop returned `WAIT_OBSERVATION` 17 times and `WAIT_RACE` once in 18 calls between 16:47 and 16:58 PDT on 10-21. Throughout, A_1302 sat at a clean boundary: runner `S`/`hrtimer_nanosleep`, 0 children. Any same-user process vanishing anywhere in the `/proc` census blocks READY, and other lanes on skampere1 spawn short-lived brando9 processes constantly. Restrict observation errors to processes relevant to the trajectory, test, and re-admit. Do not pause anything and do not use a GPU.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, **ultra** effort, on skampere1. The dispatcher is the experiment 13 master, on 10-21-2026 at about 17:00 PDT. All earlier binding limits still apply. The decision is unchanged: pause only A_1302.

## Rule to implement

A process that vanishes or is unreadable during the census blocks READY only if it is **relevant**:

- the runner;
- a member of the runner's process group;
- a child of the runner, or of any of its threads;
- a process whose argv, cwd or open file descriptors reference the trajectory's pilot directory, when that can be determined before it vanished.

Every other vanished or unreadable process is recorded in a count only (an `ignored_vanished` integer) and does not block.

Keep every positive check unchanged:

- runner identity;
- zero children, read from the runner's own `/proc/PID/task/*/children` at each observation, so a vanished child of the runner is still caught;
- runner wait channel;
- no other live process referencing the pilot directory;
- no active lease, the pre-allocation disk state, and no `summary.json`;
- two observations, the runner-only SIGSTOP plus stopped recheck, and the shell staying `S`;
- the lock, the atomic pause list, and the SIGTERM after the durable record.

A relevant process that is unreadable for a reason other than vanishing still returns WAIT.

## Tests and evidence

- Unit tests: unrelated vanished processes are ignored; a vanished runner child, group member or pilot-referencing process blocks; the runner's own children list catches a child that vanishes mid-scan; the stopped recheck applies the same rule.
- Rerun the v4 suite, the watchdog test and the root suite.
- Repeat the dummy tmux pane test (runner-only stop holds) on a session you own, then kill it.
- Run a read-only `--probe` of A_1302 for about 10 minutes (no `--execute`). Report the status counts, and show READY appears whenever A_1302 is waiting.
- New admission; `launch-check` must pass. Point the master wrapper `/lfs/skampere1/0/brando9/rl4cv_e13v4/a1302_pause_then_gates.sh` at the new admission, changing only that line, and record the diff.
- Update `CKPT_v4_implementation.md` with the counts, the SHA-256 and one copy-ready sentence.

## Binding limits

- No `--execute` against any v3 run, no real pause list, no cron install.
- No GPU use.
- Do not touch the six v3 runs beyond read-only inspection.
- The shared venv is read-only.
- $0.
- Kill only processes you started.
- No edits to the protocol, the amendments or the operational records.
- Commits use explicit pathspecs; rebase, then push to `main`.
