# Experiment 13 v3: master intervention record, 10-20-2026 (dead pilot arms restarted)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/CKPT_master_resume_10-20-2026.md>

**TLDR:** At 12:45 PDT on 10-20-2026, four of the six paired-pilot trajectories had no live process. The experiment 13 master (Claude Code `claude-opus-5-5`, session "Oct 9: IRT for eval metric decomposition"), asked by Brando to make sure nothing stays stuck, restarted only those four with the owner's own resume functions. The two live trajectories were not touched, provider spend is unchanged at $0, and no scientific setting changed.

## State found (skampere1, 12:45 PDT)

| Trajectory | Latest live update | Process | Diagnosis |
|---|---|---|---|
| A_1301 | 12: 256 generations, scored, no optimizer result | none since 10-19 13:22 | the 10-19 retry session died |
| A_1302 | 2: zero generations | none since 10-19 about 14:37 | infrastructure failure |
| B_1301 | 17: optimizer result present, no summary | none since 09:07 | died before accounting |
| P_1302 | 6: scored, no optimizer result | none since 11:16 | died during or before the update |
| B_1302 | live | `rl4cv-e13v3-pilot-B-1302` | healthy, untouched |
| P_1301 | live (update 17 scoring) | `rl4cv-e13v3-pilot-P-1301` | healthy, untouched |

The sessions left no logs: their tmux panes closed on exit. There is no experiment 13 v3 cron watchdog. Eligible devices are 0, 5 and 7.

## What the master did

1. **Started, then stopped, a full run of `resume_pilot_after_foreign_gpu.py`.** At 12:48 it archived A_1302's empty update 2 as `update_00002_infrastructure_10-19-2026_2`. The master then stopped it (12:51) before it reached any live trajectory.
   - **Why stopped:** `resume_partials()` scans every trajectory. For a live update it would either raise "partial generation", aborting all relaunches, or spawn a duplicate optimizer retry and rename the live update directory.
   - **Rule:** run the full script only when **every** pilot session is dead.
2. **Targeted driver** `$WR/phase2/e13v3_targeted_resume_10-20.py`, log `$WR/phase2/targeted_resume_10-20-2026.log`, using the owner's own `launch`, `spawn_retry` and `account` functions:
   - launched `rl4cv-e13v3-pilot-A-1302`;
   - started `rl4cv-e13v3-retry-A-1301-u12` and `rl4cv-e13v3-retry-P-1302-u6`, both waiting for an idle eligible GPU;
   - moved B_1301 update 17's partial export, written when step 1 was stopped, aside to `export_partial_killed_10-20-2026`, then re-accounted update 17 and relaunched `rl4cv-e13v3-pilot-B-1301`;
   - set `remain-on-exit on` for every new session, so the next silent death leaves its error on screen.

## For the next coordinator

- **If a trajectory dies:** read its retained pane (`tmux capture-pane -p -t <session>`). Restart it with the targeted functions, not the full script, while other trajectories are live.
- **Recurring cause:** foreign-GPU `/proc/<pid>/environ` permission errors on a shared node. A permanent fix belongs in the allocation guard: treat an unreadable foreign process as "device busy" instead of raising.
- **T5:** B/1301 compares updates 1–10 with 21–30 for a +0.02 rise in its own train reward. At update 13 it was 0.01035 against 0.00845, not met. One preregistered extension to 60 updates follows if it fails.

## Fix for the foreign `/proc` crash, 10-20-2026 13:30–13:35 PDT (auto-resume watchdog)

**Root cause.** `device_guard.check` runs at every model-stage start. It reads `/proc/<pid>/environ` for each process on the leased GPU. When another user's job lands on that GPU, the read raises `PermissionError`, and only `FileNotFoundError` is caught, so the runner dies. Sharing a GPU with another user is correctly forbidden, so the stage would abort in any case.

**Why the frozen code was not edited.**
- `pilot_run.py` and `device_guard.py` are among `pilot_admission.json`'s 17 hash bindings, so editing them makes `check_admission` refuse.
- Every completed update records the admission digest, which `run()` checks on resume, so re-pinning the admission would refuse every trajectory.

**Fix: [`phase2/autoresume_watchdog.py`](phase2/autoresume_watchdog.py).** It is a new file outside the bindings, so no scientific setting changes. A cron job runs it every 10 minutes (`# e13v3-autoresume`). For each trajectory with no live tmux session and no live process, it applies the owner's own step:

| State of the latest update | Action |
|---|---|
| Optimizer result present | account, then launch |
| Zero generations | archive, then launch |
| Complete and scored | retry the optimizer step |
| Nothing partial | launch |
| Partial generation, an update-1 retry, or 3 attempts already used on this update | diagnose only |

It also keeps each dead pane's last 200 lines in `$WR/phase2/autoresume_deaths/`.

**Light QA.** Codex `gpt-6-astra`, effort ultra, one round: **FIXES_NEEDED, 1 critical**. All five findings were fixed with no re-review.
1. Probes now fail closed. Liveness counts any session, any process naming the trajectory (runner, owner retry or surviving stage process) and the runner's controller lock during repairs, and it is rechecked just before acting.
2. The owner's `nvidia-smi` wrapper is replaced atomically and only when it differs. This is applied in the watchdog and in the owner's unbound `install_gpu_filter`.
3. Restart attempts are reserved durably before each action, and each trajectory's failure is isolated.
4. Panes are retained from creation by a name-filtered tmux hook, `session-created[13]`, which matches only `rl4cv-e13v3-*`. It also covers pilots launched by retries.
5. An update-1 optimizer retry, which the owner helper cannot do, is reported for diagnosis.

**Verification.**
- Watchdog tests: 14/14 pass. On skampere1, `expt_v3/tests` passes 89/89; on macOS, only the Linux-only device-guard test fails, because macOS has no `/proc`.
- A dry run and one real tick at 13:30 both returned `skip` for all six trajectories, which were live.
- Crontab: 13 lines plus 1, with the others verified unchanged; backup `$WR/state_crontab_before_autoresume_*.txt`.

**Removing it.** Delete the `# e13v3-autoresume` cron line and run `tmux set-hook -gu 'session-created[13]'`.

## 15:30 PDT: v3 progress normal; v4 protocol frozen; v4 implementation owner dispatched

**v3-A7 is progressing, not stuck.** At 15:22 PDT the completed updates were:

| Trajectory | Completed updates |
|---|---|
| A_1301 | 11 |
| A_1302 | 1 |
| B_1301 | 17 |
| B_1302 | 7 |
| P_1301 | 16 |
| P_1302 | 5 |

- Each optimizer step takes **122–156 minutes** on one GPU, measured over the last three updates of A_1301, P_1301 and B_1301.
- GPUs 0, 5 and 7 are optimizing A_1301 u12, B_1302 u8 and P_1301 u17. B_1301 u18 (generation) and P_1302 u6 (optimizer) wait for an idle GPU.
- The watchdog skips all six, because all six are live.

At this rate, B_1301's T5_30 verdict is about 2–3 days away.

**v4 protocol frozen** at `d4778e25` ([PROTOCOL.md](../expt_v4/PROTOCOL.md)). One Codex `gpt-6-astra` ultra light QA round returned FIXES_NEEDED with 3 critical findings. All 8 findings are fixed ([record](../expt_v4/LIGHT_QA_10-20-2026.md)). The main changes:

- the objective is the filtered policy that is actually sampled;
- V4-T2 requires a nonzero gradient on a usable group;
- the length contracts move to 12,288 tokens;
- the group size is chosen by V4-G0;
- the placebo's claim is narrowed to the start policy's reward density;
- inference follows parent § 7.

**v4 implementation owner.** It is Codex `gpt-6-astra` at high effort, on CPU only, running in tmux `codex-rl4cv-e13v4-impl` on skampere1 since 15:25 PDT. Its brief is [the dispatch prompt](../expt_v4/PROMPT_dispatch_e13_v4_implementation.md) (`c5c12306`).

- Clone: `/lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification`.
- Log: `/lfs/skampere1/0/brando9/rl4cv_e13v4/impl_codex.log`.
- Checkpoint: `expt_v4/CKPT_v4_implementation.md`.
- It uses no GPU until the launch trigger: B_1301 `T5_30.json` FAIL, or all six `result_30.json`.

**Expected v4 resource pressure.** At about 2.5 GPU-hours per optimizer step, before the longer 12,288-token outputs, the 6 × 30-update v4 pilot needs on the order of 450–550 GPU-hours. On GPUs 0, 5 and 7 alone that is about a week, so skampere2 and skampere3 idle GPUs (through the v4 device guard) matter.

**Monitoring.** A session cron runs every 3 hours, at :23 plus an offset. It checks v3, the v4 owner and the launch trigger.
