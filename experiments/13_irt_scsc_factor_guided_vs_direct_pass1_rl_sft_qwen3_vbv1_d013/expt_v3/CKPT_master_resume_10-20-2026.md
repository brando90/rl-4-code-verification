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

## 19:35 PDT: correction, the experiment 19 forecast hash is consistent

The 19:10 "hash mismatch" was a false alarm. The `rl4cv.forecast` convention hashes the canonical JSON text without its final newline.

- The master verified that the committed file (one commit, `46c955aa`) ends with exactly one newline.
- Its newline-stripped SHA-256 is `abb0cb3115b86fd3107a565fdfacd53343f285b7d27b34fd30d4dcb682436286`, which matches the sidecar and ledger. Hashing the file's raw bytes gives `f5ef9be0…` instead.
- No re-freeze is needed. The v4 forecast scorer must check the file with `rl4cv.forecast.verify_forecast` (`src/rl4cv/forecast.py`), or with the stripped hash, and record `abb0cb31…`.

## 22:00 PDT: v3 healthy; v4 dispatch 2 done; V4-A4 adopted; dispatch 3 running

**v3-A7.** Completed updates at 21:53 PDT:

| Trajectory | Completed updates |
|---|---|
| A_1301 | 12 |
| A_1302 | 2 |
| B_1301 | 17 |
| B_1302 | 8 |
| P_1301 | 18 |
| P_1302 | 6 |

- No `T5_*.json` or `result_30.json` exists yet.
- The watchdog was OK at 21:50, with zero preserved deaths.
- B_1301 is still queued behind the other trajectories for optimizer leases, which is what V4-A3's pause addresses.

**v4 dispatch 2** (`000ac82b`, `8b46cf8f`):

- **Done:** the V4-A1 certificates and an ordered CPU stage runner.
- **Tests:** v4 117/0/0 (passed/skipped/failed); root suite 1,405 passed, 15 skipped, 0 failed.
- **Dry run:** all 12 stages, 6 × 60 symbolic updates, plus the order, crash and no-signal controls.
- **Blocked on two things.** First, at uncertified positions NeMo's truncated importance correction exp(old − gen), capped at 2, has no generator probability ([blocker](../expt_v4/BLOCKER_V4_A1_importance_correction.md)). Second, the real adapters are unfinished.

**[V4-A4](../expt_v4/AMENDMENT_V4-A4_importance_correction_at_uncertified_positions_10-20-2026.md)** (`b3c25eef`) is adopted. A Codex ultra consult graded it ADOPT WITH CHANGES, 8/10, and all three fixes are incorporated ([record](../expt_v4/CONSULT_V4-A4_codex_10-20-2026.md), `750e7a65`).

- At uncertified positions the correction weight is 1, through a detached imputation used only inside that term.
- The KL term stays inactive (coefficient 0), and every diagnostic that uses the generator's log π̃ covers certified positions only.
- The guard stops a trajectory before the optimizer step if more than 1% of tokens are uncertified, on generated positions and on actor-loss tokens across ranks and microbatches.
- The bound B on the loss perturbation is reported every update. The gradient bias remains unmeasured and is disclosed.

**Dispatch 3** runs in tmux `codex-rl4cv-e13v4-impl3` since 21:57 PDT ([prompt](../expt_v4/PROMPT_dispatch_e13_v4_dispatch3_adapters_A2_A3_A4.md); log `/lfs/skampere1/0/brando9/rl4cv_e13v4/impl3_codex.log`). CPU only, it builds:

- V4-A4 and V4-A2;
- the V4-A3 pause list in the v3 watchdog, plus a boundary-checked pause tool that it does not run;
- the experiment 19 forecast scorer;
- the real adapters with leased subprocesses;
- a launch plan reconciled with V4-A3, a new admission, and a dry run.

**GPU census (dispatch 2, 19:05 PDT):** 20 of 24 devices busy. skampere1 devices 0, 2, 4 and 6 were idle, but of the eligible devices only 0 was free, and 5 and 7 held v3 workers.

## 10-21-2026 00:55 PDT: v4 dispatch 3 done; admission statically ADMITTED; waiting for the V4-A3 window

**v3-A7.** Completed updates at 00:53 PDT:

| Trajectory | Completed updates |
|---|---|
| A_1301 | 13 |
| A_1302 | 3 |
| B_1301 | 18 |
| B_1302 | 9 |
| P_1301 | 18 |
| P_1302 | 6 |

- No `T5_*.json` or `result_30.json` exists yet.
- The watchdog was OK at 00:50, with zero deaths.
- The pause list `autoresume_paused.json` does not exist yet.

**Dispatch 3** (`1e667077`, `13a5fd7a`; [checkpoint](../expt_v4/CKPT_v4_implementation.md)) delivered:

- the real leased adapters for generation, scoring, training, checkpointing, export, refit, replay and audits;
- V4-A2, V4-A3 and V4-A4;
- the experiment 19 scorer, with `verify_forecast` True and hash `abb0cb31…`.

Verification:

- **Tests:** v4 142 passed; v3 watchdog 16 passed; root suite 1,405 passed, 15 skipped, 0 failed.
- **Sampler check:** the installed `Sampler` receipt shows 10,000 positions with 0 mismatches.
- **Dry run:** a GPU-free run through the real adapters with stub engines covered 360 symbolic updates and the A4 stop at 1.17% uncertified. The pause tool returned WAIT while stages were running.

**Admission:** `phase2/admission_dispatch3.json`, SHA-256 `29276968a2e93abcea5dede2f763703ed207b2f4f0e6c94f542268f8b11c758c`. It is statically ADMITTED.

The remaining conditions are runtime-only and owned by the master:

1. the window closes at 10-21 12:00 PDT with no veto, and the five clean pauses are recorded;
2. an idle authorized device lease;
3. for the pilot only, B_1301's `T5_30.json` and every gate PASS.

The exact commands are in the checkpoint's "Exact master commands" block.

**Implementation correction:** dispatch 3 restored the inherited v3 standard-deviation scaling of advantages, tested against the installed function. No protocol change.

**Open:** experiment 120's identity is still unresolved for its required GPU-use check. The coordinator has been asked. At 22:48 PDT, 21 of 24 devices were busy, and skampere1 devices 0, 5 and 7 were occupied by v3.

## 10-21-2026 01:10 PDT: experiment 120 GPU check resolved; veto line confirmed

- **Veto line confirmed.** The coordinator confirmed that Brando's 07:35 report carries "VETO WINDOW on the experiment 13 V4-A3 reallocation until 10-21-2026 12:00 PDT". The coordinator relays any veto. If none arrives by 12:00, there was no veto.
- **Experiment 120 GPU check (protocol § 5), resolved.** Experiment 120 is `experiments/120_v1like_private_tasks_open_weight_agent_proxy_filter_sherlock/` in the private repository vb-priv-bmg; its owner session is local_52dcc83e. The coordinator observed it at about 00:55 PDT with `nvidia-smi` and `ps`:

  | Host | Experiment 120 use |
  |---|---|
  | mercury1 | GPUs 0–7: two Qwen3.8-27B-FP8 vLLM servers, tensor parallel 4, since about 15:08 PDT 10-20 |
  | mercury2 | GPUs 0–7: calibration/pilot vLLM servers, since about 20:58 PDT |
  | Sherlock | 5 pending jobs |
  | skampere1–3 | none |

  At the current pace experiment 120 runs until about 10-28.
- **Rule adopted:** v4 never uses mercury1 or mercury2 GPUs 0–7. v4's device guard admits only skampere1 devices 0, 5 and 7 and idle skampere2/3 devices, so experiment 120 does not conflict. The guard's idle check stays binding everywhere.

## 10-21-2026 11:15 PDT: Brando back ("go do it"), so no V4-A3 veto; pause loop armed for 12:00:30

- **Decision:** Brando wrote at about 11:00 PDT: "I'm back to work. What should we do next? Go do it and test it." The master read this as no veto of V4-A3.
- **Pause tool timing:** the admitted pause tool refuses to act before 12:00 PDT. The master did not edit admitted code to start sooner.
- **Pre-flight tests (CPU), on the deployed tree:**
  - `launch-check`: ADMITTED, 0 blockers, admission `29276968…`; it takes 13 s.
  - v4 suite: 142 passed in 48.8 s.
  - v3 watchdog suite: 16 passed.
- **Infrastructure fix.** Two finished v3 retry tmux sessions had dead panes (exit status 0) since 10-20, because remain-on-exit is on: `rl4cv-e13v3-retry-A-1301-u12` (retry finished 15:42) and `rl4cv-e13v3-retry-P-1302-u6` (finished 19:59). They made the pause tool's one-pane identity check fail for A_1301 and P_1302, which would have aborted every pause call. Their pane text was saved to `$WR/phase2/autoresume_deaths/*_finished_status0_saved_10-21-2026.txt`, and only those two dead sessions were closed. No live process was touched.
- **Boundary probe (read-only, 11:08 PDT):**

  | Trajectory | Completed updates | State |
  |---|---|---|
  | A_1301 | 14 | stage running |
  | A_1302 | 5 | between stages, not yet waiting |
  | B_1302 | 11 | stage running |
  | P_1301 | 19 | stage running |
  | P_1302 | 8 | between stages, not yet waiting |

- **Pause loop.** tmux `e13v4-a3-pauser` runs `/lfs/skampere1/0/brando9/rl4cv_e13v4/a3_pause_loop.sh` (log `a3_pause_loop.log`).
  - From 12:00:30 PDT it runs the admitted `pause_v3.py --veto-not-issued --execute` every 20 s, so each trajectory pauses only at its own lease-wait boundary.
  - Once all five are PAUSED or ALREADY_PAUSED, it runs `install_watchdog.py --install` once. The v4 controller then runs T1, G0, T2, T3, T4 and the B audits on idle authorized GPUs.
  - It stops after 12 hours.
  - Its success count was tested on four sample outputs.
- **Checks:** a one-shot check runs at 12:20 PDT (cron job `b008d77a`).

## 10-21-2026 11:20 PDT: HOLD — no v3 pause until Brando confirms

- **Why.** The coordinator relayed Brando's 11:13 PDT message: "ps: don't pause things unless it's necessary...or I say it?". It was read as a possible veto of the V4-A3 pause.
- **Done.** The master stopped tmux `e13v4-a3-pauser` at 11:14:48 PDT, before it acted. It had only been sleeping until 12:00:30: no pause list exists and no trajectory was signalled. The HOLD line is in `a3_pause_loop.log`. The 12:20 check (`b008d77a`) was deleted. All six v3 trajectories run unchanged.
- **GPU census (11:15 PDT, `nvidia-smi`).** **0 of 24** skampere1–3 GPUs are idle; every device has compute processes. skampere1 devices 0, 5 and 7 hold v3. mercury1 and mercury2 GPUs 0–7 are excluded for experiment 120. So the v4 gates cannot start without a pause.
- **B_1301's pace.** 20 of 30 updates are complete. Its last four updates took 7.3, 9.3, 8.0 and 5.0 hours, because it queues behind the other five trajectories.

  | Option | B_1301's T5_30 | v4 |
  |---|---|---|
  | No pause | about 10-24 midday | starts after T5_30 |
  | Pause all five | about 10-22 evening (about 3 GPU-hours per update) | gates run meanwhile on a freed GPU |
  | Pause one run | — | needs a runner change and re-admission (the admitted runner requires all five pauses) |

- **Waiting on Brando:** pause all five, pause one, or no pause. The coordinator is asking him, and so is the master in its own chat.

## 10-21-2026 11:22 PDT: Brando chose "pause one run only"; A_1302 designated; dispatch 4 running

- **Decision.** Brando answered the coordinator at about 11:2x PDT, his own choice: "Pause one run only." He is away rating for about 5 hours.
- **Record.** The [operational change to V4-A3](../expt_v4/OPERATIONAL_V4-A3_single_pause_10-21-2026.md) (`94c20d07`) states the pause rule before any pause. The rule puts arm A first (strict reward, almost no signal), then the replication seed 1302, then the fewest completed updates, and never B_1301. It selects **A_1302** (5 of 30).
  - **Timestamp correction:** the record's status line says "recorded … 11:35 PDT". The commit time of `94c20d07`, about 11:19 PDT, is authoritative. The file is left unchanged because dispatch 4 binds its hash.
- **Effect.** The other five v3 runs continue. v4's gates compete fairly for idle authorized devices, with no standing reservation, so B_1301's T5_30 stays around 10-24. The 3-GPU pilot waits for B_1301's T5_30 or for free GPUs. Any later stop of a running v3 run is confirmed with Brando first.
- **Dispatch 4** runs in tmux `codex-rl4cv-e13v4-impl4` since 11:20 PDT, Codex `gpt-6-astra` at ultra effort ([prompt](../expt_v4/PROMPT_dispatch_e13_v4_dispatch4_single_pause.md); log `/lfs/skampere1/0/brando9/rl4cv_e13v4/impl4_codex.log`). It builds the designated single-pause mode and the gate release on one pause, then tests, dry-runs and re-admits. It does not pause anything and uses no GPU.
- **After dispatch 4,** the master pauses A_1302 at a lease-wait boundary and starts the gates. The master messages the coordinator at each step.

## 10-21-2026 12:55 PDT: dispatch 4 done (admission `a8a1b8f2…`); A_1302 pause blocked by a dead boundary signal; dispatch 5 running

- **Dispatch 4** (`3b2df5c3`, `63a0d3d0`) delivered:
  - the single designated-pause mode, read from an admission-bound `phase2/operational_pause.json`;
  - a three-device availability check before the pilot (it holds candidate locks only while checking, so it is not a standing reservation).

  **Tests:** v4 168 passed, v3 watchdog 16 passed, root suite 1,405 passed with 15 skipped and 0 failed. The dry run showed WAIT then PAUSED, with the gates released only afterwards. **Admission:** ADMITTED, SHA-256 `a8a1b8f28497e51ba3d898dceb07902c9dc18f83bdac9164b49e462a9a79e390`; `launch-check` passes. **Census at 11:24:** 24 of 24 devices busy.
- **Master pre-flight at 12:47.** `launch-check` passes. The read-only probe returned `WAIT_STAGE_RUNNING` for A_1302, which was correct because it was optimizing. Its `pane_text` was blank lines only.
- **Blocker found.** No `rl4cv-e13v3-pilot-*` pane has any output. `pilot_run.py` waits for GPUs silently, through `allocation()` and `time.sleep(30)`. The admitted rule needs "waiting for an idle GPU" in the pane, so it could never mark A_1302 READY. The dry runs used fake panes and missed this.
- **Replacement signal, verified on live runs.**
  - Waiting runners show: the python runner in `hrtimer_nanosleep`, 0 children, no lease without an `_end`, and an update directory in a pre-allocation state. B_1302 and P_1301 matched this, stable over 31 s.
  - Scoring shows `futex_wait_queue` with Lean children (P_1302).
  - Optimizing shows an active `update_lease.json` and one child (A_1302).
- **Pause not run yet.** The master did not run the pause; a loop on the admitted rule would wait forever, and spoofing pane text was rejected as dishonest.
- **[Dispatch 5](../expt_v4/PROMPT_dispatch_e13_v4_dispatch5_pause_boundary_signal.md)** (`2c7d7fc3`) runs in tmux `codex-rl4cv-e13v4-impl5` since 12:51 PDT, Codex `gpt-6-astra` at ultra effort, CPU only. It implements the process and disk-state boundary rule (SIGSTOP and recheck kept), tests it on the observed states, runs a live read-only probe, and re-admits.
- **Then** the master pauses A_1302 and starts the gates. All six v3 runs keep running meanwhile.
