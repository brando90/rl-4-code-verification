# Dispatch 5: experiment 13 v4, a pause-boundary signal that works for silent v3 runners (CPU only; no pause, no GPU)

**TLDR:** The admitted pause tool treats a v3 run as at a clean boundary only when its tmux pane shows "waiting for an idle GPU". The live v3 runner (`expt_v3/phase2/pilot_run.py`) prints nothing: it polls `nvidia-smi` and sleeps 30 s. All six pilot panes are blank, so A_1302 can never be paused. Replace the pane-text check with a process and disk-state signal, test it on real observations, and re-admit. Do not pause anything and do not use a GPU.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, **ultra** effort, on skampere1. The dispatcher is the experiment 13 master, on 10-21-2026 at about 13:00 PDT. All earlier binding limits still apply. The decision is unchanged: pause only A_1302 ([operational record](OPERATIONAL_V4-A3_single_pause_10-21-2026.md)).

## Evidence (master, 10-21-2026 12:47–12:55 PDT, read-only)

- **Admitted probe:** `pause_v3.py --trajectory A_1302 --probe` returns `WAIT_STAGE_RUNNING`, with `pane_text` consisting only of blank lines. Every `rl4cv-e13v3-pilot-*` pane has 0 nonblank lines.
- **Runner output:** the runner's stdout and stderr are the pane's terminal (`/dev/pts/45` for A_1302), but `pilot_run.py` never prints while waiting. Its `allocation()` loops over GPUs 0, 5 and 7, then `time.sleep(30)`. Only the retired retry helper printed "waiting for an idle GPU".
- **Process tree:** each pane shell (`sh -c …`) is the runner group's leader. The python runner is its child. Stage work runs as children of the python runner.
- **Observed states** (python runner PID, `/proc/PID/wchan`, child count, active lease):

  | Run | Runner PID | wchan | Children | Active lease | What it is doing |
  |---|---|---|---|---|---|
  | B_1302 | 1291595 | `hrtimer_nanosleep` | 0 | none | `update_00012` scored, waiting for an update allocation |
  | P_1301 | 1246693 | `hrtimer_nanosleep` | 0 | none | `update_00021` has only `plans.json` and `cells.json`, waiting for a generate allocation |
  | P_1302 | 3171723 | `futex_wait_queue` | 21–32 | none | scoring (Lean children) |
  | A_1302 | 692011 | `hrtimer_nanosleep` | 1 | `update_lease.json` without `_end` | optimizing |

  Both waiting runs held the same state 31 s later.

## What to build

1. **New boundary rule** for `pause_v3.py`, applied to v3 `pilot_run.py` runners. READY only if **all** of these hold:
   - exactly one python runner for the trajectory (its argv contains `pilot_run.py --arm X --seed Y`), with PID and start-tick checks;
   - the runner has **zero child processes**, and no other process references the trajectory's pilot directory;
   - the runner's `/proc/PID/wchan` is `hrtimer_nanosleep`, on two observations about 1 s apart;
   - no active lease for the trajectory: every `*_lease.json` under its latest update directory has a matching `*_end.json`;
   - the latest `update_000NN` directory is in a pre-allocation state:
     - `plans.json` and `cells.json` exist and `generate_lease.json` does not (waiting to generate); **or**
     - `score/groups.json` exists and `update_lease.json` does not (waiting to optimize);
   - `summary.json` is absent from that directory.

   Keep the SIGSTOP-then-recheck, applied to the **whole** rule. Keep the shared watchdog lock, the atomic pause-list write and the SIGTERM to the runner's group. The group is the pane shell plus the python runner, so verify that it contains only those two. Never touch B_1301 or any non-designated run.
2. **Pane text** is recorded in the receipt as context only. It no longer decides anything.
3. **Tests.**
   - Fixtures built from the four observed states above, plus edge cases: a child present, a lease without `_end`, `summary.json` present, wchan changing between observations, two runners, PID reuse, and the SIGSTOP recheck failing.
   - A test showing that the old pane-text-only rule could never pass on a blank pane, as a regression record.
   - Rerun the v4 suite, the v3 watchdog test and the root suite.
4. **Live read-only probe.** Run the new probe (no `--execute`) against the real A_1302. Then, if any v3 run is waiting at that moment, run it against that run read-only to show READY can be reached. Record both outputs. Probing a non-designated run is allowed only in read-only probe mode.
5. **Re-admission and handoff.** Publish a new admission; `launch-check` must pass. Update the master commands in `CKPT_v4_implementation.md`, with the same pause loop and gate start, now using the new rule.

## Binding limits

- No `--execute`, no real pause list, no cron install.
- No GPU allocation, generation or optimizer step.
- Do not touch the six v3 runs or their sessions beyond read-only `/proc` and file inspection.
- The shared venv is read-only.
- $0.
- Kill only processes you started.
- No edits to the frozen protocol, the amendments, or the operational records.
- Commits use explicit pathspecs; rebase, then push to `main`.

## Deliverables

- Code and tests, with counts.
- The live probe outputs.
- The new admission SHA-256.
- The updated master commands.
- One copy-ready sentence in `CKPT_v4_implementation.md`.
