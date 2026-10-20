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
2. **Targeted driver** `$WR/phase2/e13v3_targeted_resume_10-20-2026.py`, log `$WR/phase2/targeted_resume_10-20-2026.log`, using the owner's own `launch`, `spawn_retry` and `account` functions:
   - launched `rl4cv-e13v3-pilot-A-1302`;
   - started `rl4cv-e13v3-retry-A-1301-u12` and `rl4cv-e13v3-retry-P-1302-u6`, both waiting for an idle eligible GPU;
   - moved B_1301 update 17's partial export, written when step 1 was stopped, aside to `export_partial_killed_10-20-2026`, then re-accounted update 17 and relaunched `rl4cv-e13v3-pilot-B-1301`;
   - set `remain-on-exit on` for every new session, so the next silent death leaves its error on screen.

## For the next coordinator

- **If a trajectory dies:** read its retained pane (`tmux capture-pane -p -t <session>`). Restart it with the targeted functions, not the full script, while other trajectories are live.
- **Recurring cause:** foreign-GPU `/proc/<pid>/environ` permission errors on a shared node. A permanent fix belongs in the allocation guard: treat an unreadable foreign process as "device busy" instead of raising.
- **T5:** B/1301 compares updates 1–10 with 21–30 for a +0.02 rise in its own train reward. At update 13 it was 0.01035 against 0.00845, not met. One preregistered extension to 60 updates follows if it fails.
