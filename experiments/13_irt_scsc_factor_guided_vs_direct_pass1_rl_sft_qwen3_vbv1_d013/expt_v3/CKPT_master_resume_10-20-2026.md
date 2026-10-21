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

## 18:55 PDT: v3 still healthy; v4 CPU code done; launch blocker fixed by Amendment V4-A1; dispatch 2 running

**v3-A7.** Completed updates at 18:48 PDT:

| Trajectory | Completed updates |
|---|---|
| A_1301 | 12 |
| A_1302 | 1 |
| B_1301 | 17 |
| B_1302 | 8 |
| P_1301 | 17 |
| P_1302 | 5 |

- No `T5_*.json` or `result_30.json` exists yet.
- The watchdog's last tick was OK at 18:40, with all six skipped because they are live.

**v4 dispatch 1** finished at 15:57 PDT, pushed as `7aec74f7` and `57482ca2` ([checkpoint](../expt_v4/CKPT_v4_implementation.md)).

- **Tests:** the v4 suite passes 89/89; the root suite passes 1,388, skips 15 and fails 0.
- **Reducer:** the A6 reducer reproduces the protocol's design counts exactly.
- **Context:** 20,041 tokens.
- **Blocker:** the owner correctly refused launch. A raw top-20 receipt cannot determine the generator's support when logits tie at the 20th place or at the top-p boundary, because vLLM 0.10.0 keeps every tied token and sorts unstably. The engine's `processed_logprobs` mode is taken before temperature and filtering, so it does not help.

**Amendment V4-A1** (`7877faac`), adopted by the master before any v4 data, fixes this:

- the generator records top-64 raw log-probabilities, with a strict completeness certificate (v_64 < v_20) and a top-p tie and margin certificate;
- uncertified positions count against V4-T1's 99% support allowance, which makes the gate harder to pass;
- the trainer keeps whole tie groups;
- nothing else changes.

**v4 dispatch 2** runs in tmux `codex-rl4cv-e13v4-impl2` on skampere1 since 18:51 PDT ([prompt](../expt_v4/PROMPT_dispatch_e13_v4_runner_after_A1.md), `75fa35ee`; log `/lfs/skampere1/0/brando9/rl4cv_e13v4/impl2_codex.log`). It implements V4-A1, the end-to-end stage runner, the launch and watchdog plans, a new admission and a GPU-free dry run. CPU only.

**GPUs.** The owner's census at 15:40 PDT found all 24 devices on skampere1–3 busy. skampere1 devices 0, 5 and 7 hold v3 workers, so v4 starts only when GPUs free up. Experiment 120's folder and processes could not be identified in either repository. The device guard's idle check at launch is binding regardless.

## 19:10 PDT: experiment 19 proposal received; scoring accepted, A-sel pending Brando

Experiment 19, the IRT lane in session local_268be283, sent two things: a frozen proposal ([PROPOSAL_e13_prompt_selection_arm_10-21-2026.md](../../19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/PROPOSAL_e13_prompt_selection_arm_10-21-2026.md)) and forecasts of V4-G0.

- **Forecast scoring: accepted.** It is descriptive and affects no v4 gate.
  - After G0, the v4 runner joins the frozen forecast file to G0's private per-task counts on SNAP and verifies the hash.
  - It publishes only aggregates: Spearman and AUC for each of the three forecasts, G0's mean mixed probability and the chosen G.
  - **Hash mismatch:** on main (`46c955aa`) the forecast file hashes to sha256 `f5ef9be0…`, but its ledger and sidecar record `abb0cb31…`. Experiment 19 was asked to re-freeze it before G0. The mismatch is disclosed either way.
- **Arm A-sel (strict reward on a top-quarter train pool ranked by panel pass rate): not adopted, pending Brando.**
  - As a fourth v4 arm: graded 6/10. It adds about a third to a pilot already near a week of GPU time, and it tests prompt selection, not reward shaping. Experiment 19 also found its evidence is not IRT-specific.
  - As a pre-declared contingent condition, run only if V4-T5 fails on A: graded 7/10.
  - If adopted, it is written as a numbered amendment before G0.

## 19:20 PDT: coordinator light QA (Fable 5.1 max): V4-A1 correct; V4-A2 and V4-A3 recorded

- **Verdict:** CORRECT, graded 9/10. V4-A1 precedes dispatch 2. `PROTOCOL.md` is byte-identical to the `d4778e25` lock, and the reconstruction matches the native vLLM sampler.
- **[V4-A2](../expt_v4/AMENDMENT_V4-A2_receipt_invariance_and_sampler_backend_10-20-2026.md)** (`41c2b8b6`):
  - adds a pass criterion for receipt invariance: an exact unit check on the installed `Sampler`, plus an R0/R1 engine check on the T1 probe, with an R2 tolerance if the engine is not deterministic;
  - pins `VLLM_USE_FLASHINFER_SAMPLER=0` and the native path, and logs the selected forward in each receipt.

  `flashinfer` is absent from the pinned venv, and the A6 attempt-2 generation log shows the native fallback, so v4 samples exactly as A6 did.
- **[V4-A3](../expt_v4/AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md)** (`41c2b8b6`), the coordinator's option (c), **subject to Brando's veto until 10-21-2026 12:00 PDT**:
  - Once v4 is admitted, A_1301, A_1302, B_1302, P_1301 and P_1302 pause at clean lease-wait boundaries and are final, with their counts kept in the full denominator.
  - B_1301 alone continues to its T5_30 verdict, and v3-A7 then ends, with no extension and no main study.
  - v4's gates use freed GPUs. Its pilot starts after B_1301's verdict.
- **Pace correction (coordinator):** an update costs **2.6–3.2 GPU-hours** once the roughly 35-minute generation lease is counted, not 2–2.6. B_1301 generated u18 from 15:42 to 16:17 and was scored by 16:21, so it was queued for an optimizer lease, not stalled. A_1302 u2's long optimizer step has since finished.
- **Next:** dispatch 2 finishes, then dispatch 3 implements V4-A2, the V4-A3 pause tooling (a pause list read by the v3 watchdog, and lease-wait boundary detection) and the experiment 19 forecast scorer. Those are bound into the admission.
