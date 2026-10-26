# Dispatch 3: experiment 13 v4, real adapters plus amendments V4-A2, V4-A3 and V4-A4 (CPU only, no launch)

**TLDR:** Finish v4 to a launch-ready admission. Implement V4-A2, V4-A4, the V4-A3 pause tooling and the experiment 19 forecast scorer. Integrate the real generator, scorer, trainer, checkpoint, export, replay and audit adapters with leased stage subprocesses. Reconcile the launch plan with V4-A3, and bind everything into a new admission. Use no GPU, generation or optimizer step, and record the result in `expt_v4/CKPT_v4_implementation.md`.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, high effort, on skampere1. The dispatcher is the experiment 13 master, on 10-20-2026. This continues dispatches 1 and 2, and all their binding limits still apply.

## Read first

- `expt_v4/PROTOCOL.md` (frozen).
- The amendments: `AMENDMENT_V4-A1_…`, `AMENDMENT_V4-A2_…`, `AMENDMENT_V4-A3_…`, `AMENDMENT_V4-A4_…`.
- `BLOCKER_V4_A1_importance_correction.md`, `CKPT_v4_implementation.md`, `README.md`, and your own `phase2/` and `tests/`.
- From `expt_v3/phase2/`: the real stage scripts behind `pilot_run.py` (generation, scoring, update, account and export), `resume_pilot_after_foreign_gpu.py`, `autoresume_watchdog.py` and `device_guard.py`.
- `src/rl4cv/forecast.py` (`verify_forecast`), and experiment 19's `expt_v1/forecasts/e19_g3_forecast_v4_g0.json`.

## What to build

1. **V4-A4** (importance correction at uncertified positions), exactly as written. Test it on the installed NeMo loss on CPU. The test must cover four things: a unit weight at uncertified positions, unchanged certified positions, a stop when an update's uncertified fraction is above the threshold, and the reported fields.
2. **V4-A2.**
   - The installed-`Sampler` unit check: at least 10,000 positions, including ties, with sampled tokens identical with and without 64 log-probabilities. It runs now on CPU and its receipt is bound in the admission.
   - The R0/R1/R2 engine-check code for V4-T1.
   - `VLLM_USE_FLASHINFER_SAMPLER=0` in every generator environment.
   - The `flashinfer`-absent import check in the admission.
   - Worker-side logging of the selected `TopKTopPSampler.forward` in each generation receipt.
3. **V4-A3 tooling.**
   - Add a pause list to the v3 auto-resume watchdog (`expt_v3/phase2/autoresume_watchdog.py`). The watchdog file is not bound by the v3 admission, so this is the only v3 file you may change.
     - Listed trajectories are skipped with the detail `paused (V4-A3)`.
     - The list file is `/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/autoresume_paused.json`.
     - Extend `expt_v3/tests/test_autoresume_watchdog.py`.
   - Write a pause tool for the master, which runs it. It runs nothing until the master invokes it.
     - For each listed trajectory, it confirms a clean boundary: the runner's pane shows "waiting for an idle GPU", the trajectory holds no lease, and no stage process is running.
     - It then stops only that runner's process group, recording process ID, start time and pane.
     - Otherwise it waits and retries on a later call.
   - Do **not** create the pause list or run the tool. Both wait for the veto window (10-21-2026 12:00 PDT) and for the master.
4. **Real adapters.**
   - Wire the v4 stage runner to the real components:
     - vLLM generation with the A1 and A2 receipts and the 12,288-token contract;
     - the official strict scorer and B's reward;
     - the NeMo trainer with the filtered objective;
     - checkpoint export, refit, T3 replay and the B audits.
   - Each stage runs as a leased subprocess through the v4 device guard, using the v3 pattern.
   - Test everything possible on CPU. Prove the GPU paths' argument vectors and environments with dry checks, without allocating a device.
5. **Forecast scorer.**
   - After V4-G0 scoring, check experiment 19's forecast file with `verify_forecast`, which must return True, and record `abb0cb31…`.
   - Join the file with G0's per-task counts privately on SNAP.
   - Publish aggregates only, with no task IDs:
     - Spearman and AUC for 1 ≤ s ≤ 31, for each of the three forecasts;
     - G0's mean q̂_8;
     - the chosen G.
   - It is descriptive and is never an input to any v4 gate.
6. **Launch plan and admission.**
   - Reconcile the launch plan with V4-A3. The technical gates may run on GPUs freed by the pause after the veto window; the learning pilot runs after B_1301's `T5_30.json` and only if every gate passed.
   - Write a new admission binding the protocol, all four amendments, the code, the tests, the plans and the receipts.
   - `launch-check` must pass, except for runtime conditions that only the master can satisfy: the veto window, a device lease, and B_1301's verdict for the pilot. Name those conditions explicitly.
7. **Dry run.** Redo the full GPU-free dry run against the real adapters with stub engines. Add V4-A4's stop path and the pause tool, which must refuse while a stage is running.

## Binding limits

- No GPU allocation, model generation or optimizer step.
- No v3 change beyond the watchdog pause-list feature and its test.
- Do not pause anything, do not create the pause list, and do not install the cron line.
- The shared venv is read-only.
- $0.
- Kill only processes you started.
- No edits to the frozen protocol or the amendments. If one cannot be implemented as written, record the smallest fix in the checkpoint.
- Commits use explicit pathspecs; rebase, then push to `main`.

## Deliverables

- Code and tests, with v4, v3-watchdog and root-suite counts.
- An updated `README.md`.
- An updated `CKPT_v4_implementation.md`: status, admission SHA-256, the remaining runtime-only conditions, the exact master commands (pause, gates, pilot, watchdog install and progress check), a fresh GPU census, and one copy-ready sentence.
