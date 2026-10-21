# Experiment 13 v4 implementation checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/CKPT_v4_implementation.md>
**Companion:** <https://docs.google.com/document/d/1KqUi39sz532dIGg8EYCy6w62Q0KzO2XWhpM2MMSWvHE/edit>
**Created:** 10-20-2026 15:27 PDT. **Last updated:** 10-21-2026 13:13 PDT.

**TLDR:** Dispatch 5's process/disk boundary works on silent v3 pilots: A_1302 is refused while optimizing, and P_1301 reaches READY on a blank pane. All requested CPU suites pass; the new admission passes launch-check. Implementation and admission are published to main at 9ec6640d; real pausing and gate execution remain master-owned.

## State

- Goal: silent-runner pause-boundary admission for experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4, CPU only, $0.
- Owner: Codex gpt-6-astra, ultra effort, skampere1; full access / approval never; this pre-existing dispatch checkout.
- What ran: process/disk implementation, 52 observed-state tests, full suites, synthetic stop/recheck, admitted read-only probes admission seal and verified main publication at 9ec6640d.
- Results: v4 233 passed; watchdog 16 passed; root 1,405 passed / 15 skipped / 6 warnings; final focused tests 91 passed; zero final failures.
- Admission SHA-256: ffbeb4e6b2b64408d4a151a24bf0034400bef9c7d6d09d0da0a10f71efeb72b7 (73 local / 319 runtime bindings); launch-check PASS.
- Live probes: A_1302 WAIT_STAGE_RUNNING; B_1302 WAIT_STAGE_RUNNING during a polling child; P_1301 READY; all panes blank.
- Stuck / blocked: nothing; Dispatch 5 complete.
- Next steps: [p 9/10, master-owned] use the bound Dispatch 5 commands below for the designated A_1302 pause when ready, then the unchanged watchdog/gate start; no execution by this worker.
- Brando to-do: none.
- Limits honored: no v3 signals or real pause-list writes, cron install, GPU allocation, generation, optimizer step or shared-venv edit; $0.
- Publication: 9ec6640d9ab8cf982f1b9af6c19e0d1f431c4395 on main, remote hash verified; rebase patch and all 18 owned files unchanged; backup removed.
- Helper: admission_lookup, inherited gpt-6-astra/ultra; full access/never and useful reads verified; completed only tests/test_pause_boundary.py.
- Companion: five Dispatch 5 paragraphs updated in the existing Google document and read back exactly.

## Dispatch 5 evidence and exact master commands

The silent v3 pilot never emits the retired helper's wait message. Readiness now requires two observations at least one second apart with one stable Python pilot runner, zero children, no other readable trajectory references, an isolated two-member pane-shell/runner group, and hrtimer_nanosleep. The latest numbered update must have no summary and no active lease, with either plans/cells before generation or score/groups before optimization. Pane text is retained only as context. Every non-designated execution request is refused before probing or locking; read-only probes may inspect all six v3 trajectories.

Linux changes a stopped sleeper's wait channel to do_signal_stop. The whole-rule recheck therefore retains and binds the two pre-stop sleeping observations, then requires two observations of the same stopped shell/runner identities, zero children/references, and the same valid disk/lease state. A failed recheck resumes the original group without a pause-list write or termination. This kernel behavior was observed using a temporary worker-owned CPU sleeper, which was then cleaned up; no v3 process was signalled.

The process-group census includes all users. Trajectory references are checked in same-user argv and readable current-directory/open-file links. Six protected same-user system-daemon descriptor inspections were unavailable on this host and are recorded in the probe context; readable argv is still checked. Runner/child/group inspection failures refuse readiness. No fixed wait time or pane wording can override stage activity.

[Verification](phase2/verification_dispatch5.json) and [synthetic stop/recheck evidence](phase2/dry_run_dispatch5.json) accompany the new [admission](phase2/admission_dispatch5.json). **233/233 v4 tests, 16/16 watchdog tests and 1,405 root tests passed**, with 15 root skips, six existing warnings and zero final failures. The 91 focused tests also pass on the final source; 65 v4 tests were added overall, including 52 observed-state cases. The first root attempt used the wrong NeMo source path and returned four e09_seeds KeyErrors; the documented experiment-09 source prefix resolved all four in a complete make test rerun, with no root code edits. These are deterministic counts, not statistical estimates (confidence intervals and p-values do not apply). Tests use observed-state fixtures, temporary disk files and simulated v3 signals. The frozen protocol, amendments, operational records and deployed v3 code are unchanged.

The final admission SHA-256 is **ffbeb4e6b2b64408d4a151a24bf0034400bef9c7d6d09d0da0a10f71efeb72b7**, with **73 local and 319 runtime/evidence bindings**; static launch-check passes. Its local source/test/plan bindings exactly equal those of the [preseal admission](phase2/admission_dispatch5_preseal.json), SHA-256 20a4e7fd79b22e8b247700b989100a062c25a88c41431007d13c5fdddeff9e4b, used by the live probes. The final admission additionally binds their exact stdout files and command provenance. The checkpoint is outside the closure to avoid self-reference.

Live read-only outputs (10-21-2026, PDT), with blank panes throughout:

| Trajectory | Observation times | Result | Evidence |
|---|---|---|---|
| A_1302 | 13:02:59 and 13:03:01 | WAIT_STAGE_RUNNING | PID 692011, one child and active update lease, update_00006; [full output](phase2/live_probe_dispatch5_A_1302.json) |
| B_1302 | 13:03:18 and 13:03:20 | WAIT_STAGE_RUNNING | PID 1291595 changed from zero children/nanosleep to one polling child/pipe_read; no active lease, update_00012; [full output](phase2/live_probe_dispatch5_B_1302.json) |
| P_1301 | 13:04:21 and 13:04:23 | READY | PID 1246693, stable start tick 68953605, zero children, no active lease, plans/cells before generate allocation at update_00021; [full output](phase2/live_probe_dispatch5_P_1301.json) |

The real pause list was absent before and after probing. The synthetic pause fixture returned WAIT_STAGE_RUNNING then PAUSED, gate release false → false → true and pilot release false; its three signals are simulated. The 360-update full stub run remains historical Dispatch 4 evidence, not a newly measured result.

**Copy-ready sentence for the master:** I fixed the silent-runner pause boundary in experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4, with 233 v4, 16 watchdog and 1,405 root tests passing, A_1302 correctly refused while optimizing, P_1301 reaching READY on a blank pane, and a new admission passing launch-check; no v3 run was paused and no GPU was used.


Publication: [9ec6640d](https://github.com/brando90/rl-4-code-verification/commit/9ec6640d9ab8cf982f1b9af6c19e0d1f431c4395) is on main, confirmed by remote hash readback. Rebase from old base 2c7d7fc3 onto 2614a895 (a master-checkpoint-only change) preserved the owned patch exactly in range-diff and all 18 owned file hashes. The temporary backup branch, pointing to 78f87f93, was removed after verification. Post-rebase launch-check passes with final admission ffbeb4e6b2b64408d4a151a24bf0034400bef9c7d6d09d0da0a10f71efeb72b7. The Google companion's five updated paragraphs and corrected admission digest were read back exactly. No temporary checkout was created; this pre-existing dispatch checkout remains because the admitted plans use its absolute paths. This publication receipt changes only the unbound checkpoint.

The master runs the following commands from this checkout. They are prepared instructions, not actions taken by Dispatch 5. The real clock and no-veto flag remain authoritative even if this handoff arrives before noon.

```bash
cd /lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
V4_WORK=/lfs/skampere1/0/brando9/rl4cv_e13v4
V4_ADMISSION=$V4_ROOT/phase2/admission_dispatch5.json
export HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 VLLM_USE_FLASHINFER_SAMPLER=0
export PYTHONPATH=$PWD/src

# Read-only boundary probe: two process/disk observations; pane text is context only.
"$V4_PY" "$V4_ROOT/phase2/pause_v3.py" --admission "$V4_ADMISSION" --trajectory A_1302 --probe

# Set only when the master has established absence of a veto.
export E13V4_A3_NO_VETO=1
"$V4_PY" "$V4_ROOT/phase2/admission.py" launch-check --record "$V4_ADMISSION"

# Run after 10-21-2026 12:00 PDT. WAIT includes watchdog-lock contention.
# One installer call after the loop; a tool error stops this block.
(
  set -euo pipefail
  while true; do
    V4_PAUSE_REPORT=$("$V4_PY" "$V4_ROOT/phase2/pause_v3.py" --admission "$V4_ADMISSION" --trajectory A_1302 --veto-not-issued --execute)
    printf '%s\n' "$V4_PAUSE_REPORT"
    V4_PAUSE_STATUS=$(printf '%s\n' "$V4_PAUSE_REPORT" | "$V4_PY" -c 'import json,sys; r=json.load(sys.stdin); assert set(r)=={"A_1302"}; print(r["A_1302"])')
    case "$V4_PAUSE_STATUS" in
      PAUSED|ALREADY_PAUSED) break ;;
      WAIT_*) sleep 20 ;;
      *) exit 1 ;;
    esac
  done
  "$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan "$V4_WORK/watchdog_plan.json" --log "$V4_WORK/watchdog.log" --admission "$V4_ADMISSION" --install
)

# Gate start: the same single tmux controller used by the watchdog.
# It runs gates in order and cannot enter the pilot until its separate conditions hold.
"$V4_PY" "$V4_ROOT/phase2/launch_control.py" --plan "$V4_WORK/launch_plan.json"

# Read-only progress:
"$V4_PY" "$V4_ROOT/phase2/runner.py" progress --work "$V4_WORK/run" --admission "$V4_ADMISSION" --engine local
```

The pause-loop subshell must exit successfully before gate start. On a repeated invocation, `ALREADY_PAUSED` is accepted; the installer replaces only its own tagged v4 cron entry and leaves v3's entry intact. While waiting for pilot resources, the controller may exit and be retried by the watchdog; an unsuccessful capacity check creates no training receipt or standing reservation.

## Historical Dispatch 4 evidence (superseded by Dispatch 5)

The [operational decision](OPERATIONAL_V4-A3_single_pause_10-21-2026.md) and [machine-readable selection](phase2/operational_pause.json) designate only A_1302. The pause tool, runner, controller and watchdog installer read the admission-bound selection. No frozen protocol, amendment or operational decision was edited. v3's deployed watchdog already accepts a dictionary containing only A_1302 and remains unchanged.

The smallest implementation correction outside pause selection is the previously missing three-device pilot availability check: it holds all candidate locks only while checking idle state and v3 leases, then releases them. The existing serial pilot's subprocesses still acquire individual stage leases. There is no standing reservation or change to the scientific schedule. Tests cover insufficient devices, a busy device, a held v3 lock, an unreleased v3 lease and lock release after the check.

[Verification](phase2/verification_dispatch4.json): **168/168 v4 tests, 16/16 v3-watchdog tests and 1,405 root tests pass**, with **15 root skips, six existing warnings and zero failures**. Test logs and their hashes are bound. Counts are deterministic checks, not statistical estimates; confidence intervals and p-values do not apply.

[The new admission](phase2/admission_dispatch4.json) is **ADMITTED**, SHA-256 **`a8a1b8f28497e51ba3d898dceb07902c9dc18f83bdac9164b49e462a9a79e390`**. It has **72 local bindings and 304 runtime/evidence bindings**, including both operational records, changed code/tests, prepared/deployed plans, unchanged deployed v3 watchdog/tests, current test logs and dry-run evidence. Static `launch-check` passes. Every measured stage remains `PENDING`.

[Dry-run evidence](phase2/dry_run_dispatch4.json): **WAIT_STAGE_RUNNING → PAUSED**, gate release **false → false → true**, pilot release **false** without B_1301. Only A_1302 is probed; all three signals are simulated, with **zero real signals**. The full CPU stub chain completes **12 stages and 360 symbolic updates**, including extension, order refusal, crash recovery on attempt 2 and no-signal stop. These are synthetic controls, not live gate outcomes. Source/test bindings are identical between the [preseal admission](phase2/admission_dispatch4_preseal.json), SHA-256 `fdc4cf9dc47479ba7493ce07d18cb2ebe7a784394500c51c12db694b0918639b`, and the final admission; the final record adds the resulting evidence. Private traces: `/lfs/skampere1/0/brando9/rl4cv_e13v4/dry_run_dispatch4`.

[Fresh GPU census](phase2/gpu_inventory_dispatch4.json), **10-21-2026 11:24:28 PDT**: **24/24 devices occupied**, **0/19 authorized devices idle** across skampere1 (only 0, 5, 7 authorized), skampere2 and skampere3. All three read-only probes succeeded. Mercury1/2 remain outside the guard's allowed hosts; the operational record identifies those devices as reserved for experiment 120. No device was acquired, and the census makes no reservation; refresh it at launch.

**Remaining runtime conditions:** the unchanged noon deadline and no-veto flag, a recorded clean A_1302 pause, then a freshly acquired idle authorized stage lease. The pilot additionally waits for B_1301's T5_30 verdict and lease release, all gates passed, and three idle authorized devices under shared locks. No standing reservation is added. `launch_control.py` explicitly propagates the verified no-veto flag into the tmux session so an existing server cannot lose it.

**Copy-ready sentence for the master:** I implemented single-run pausing for experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4, with 168 v4, 16 watchdog and 1,405 root tests passing plus a GPU-free WAIT-to-PAUSED dry run; the new admission passes launch-check, and the master can pause A_1302 after noon/no veto, then start gates when an authorized device is idle.

Publication: implementation and admission **[`3b2df5c3`](https://github.com/brando90/rl-4-code-verification/commit/3b2df5c3da5a597af4d5081062734479e4d28456)** are pushed to `main`; remote readback matched exactly. The first push met a concurrent checkpoint update, so the worker rebased again over `9d555e67`. Range comparison against the owned pre-rebase backup (`84ec0457`, old base `94c20d07`) showed an identical patch, and the entire owned v4 subtree was byte-identical. The backup branch is removed after that verification. `launch-check` passes with the unchanged admission digest. The Google companion's six updated paragraphs were read back exactly. No temporary checkout was created; this pre-existing dispatch checkout is retained because the bound master plans and admission use its paths. This publication-note edit changes only the unbound checkpoint.

## Historical Dispatch 3 evidence (superseded by Dispatch 4)

The [README](README.md) explains the integrated adapters and [verification receipt](phase2/verification_dispatch3.json) records final suite counts and log hashes. The stage subprocess environment explicitly includes the installed Lean toolchain directory, so the cron controller does not depend on an interactive shell PATH. CPU installed-loss tests prove unit correction at uncertified positions, unchanged certified correction, both >1% stop paths and the required diagnostics. The installed-vLLM [Sampler receipt](phase2/sampler_cpu_receipt.json) records **10,000 positions / 0 token mismatches**, including ties, unchanged per-request RNG states and absent FlashInfer. The actual worker backend and engine R0/R1/R2 still require live T1 measurements.

Adapter integration also restored the inherited v3 standard-deviation scaling that was missing from the earlier CPU implementation; an installed-function parity test covers it. This is an implementation correction, with no protocol or amendment edit.

The experiment 19 [verification receipt](phase2/forecast_verification.json) records `verify_forecast=True` and canonical SHA-256 `abb0cb3115b86fd3107a565fdfacd53343f285b7d27b34fd30d4dcb682436286`. No G0 outcome exists. Its future private join stays under the run directory; only `forecast_aggregates.json` may be published. Spearman uses q̂_8, AUC targets 1 ≤ s ≤ 31, and all three forecasts are reported. Complete-task counts, missingness bounds and 10,000 whole-task bootstrap intervals accompany aggregates; no forecast statistic controls a gate.

A [real CPU scoring smoke check](phase2/cpu_scoring_smoke_dispatch3.json) passed through a leased stage subprocess: one explicitly synthetic empty completion, strict 0, factored reward 0, one retained compiler command, no model call. This verifies the local scorer interface only and is not a G0 outcome or gate statistic.

The new [admission](phase2/admission_dispatch3.json) is **ADMITTED**, SHA-256 **`29276968a2e93abcea5dede2f763703ed207b2f4f0e6c94f542268f8b11c758c`**, with **68 local bindings and 305 runtime/evidence bindings**. It binds the protocol, four unchanged amendments, implementation, tests, plans, installed/reused sources, model/tokenizer inputs, forecast, deployed v3 watchdog/test, test logs, README, census and CPU receipts. `launch-check` passes its static checks. The checkpoint itself carries the admission digest and is outside the hash closure to avoid a self-reference.

The [full dry-run receipt](phase2/dry_run_dispatch3.json) reports **12 stages, six trajectories × 60 symbolic updates = 360**, extension of all six after T5_30, then `MAIN_RESOURCE_CHECK` at T5_60 without launching main. It also records order rejection, zero-response crash recovery on attempt 2, `STOP_NO_SIGNAL`, **`STOP_V4_A4` at 3/256 = 1.171875% uncertified positions**, and `WAIT_STAGE_RUNNING` for all five fake pause targets with no signal or pause-list write. The [trace validation](phase2/dry_trace_validation_dispatch3.json) checks **1,694 full-sequence subprocesses plus one A4 stop subprocess**: explicit stub flags, empty CUDA device environment, native sampler setting, zero device seconds, successful exits and every CPU lease released. Real optimizer steps/model generations/GPU allocations/provider spend are all **0**.

The dry run used the identical final code/tests/plans under [the preseal admission](phase2/admission_dispatch3_preseal.json), digest `022d11308eb950b58aeebce742e9d955b52b77ca2a79dc2c33d3081d41243105`. The final admission adds the resulting receipts and deployment evidence without changing that code. Full private trace: `/lfs/skampere1/0/brando9/rl4cv_e13v4/dry_run_dispatch3_release`; summary SHA-256 `bbeaf547d34ec740f9e3a18555cb8a6ce3d8c4b7c6ba56f97005247adc041b67`. Reproduce with the README command on a fresh output directory.

**Remaining runtime-only conditions (master-owned):**

1. V4-A3's veto window closes without a veto at **10-21-2026 12:00 PDT**, and the master records the five clean pauses using the tool. A veto requires restoring the frozen timing in a new prospective plan/admission; this A3 plan refuses early execution.
2. A stage obtains a freshly verified **idle authorized device lease**, respecting v3 reservations and the experiment 120 occupancy check. No eligible device was idle in the final census.
3. **Pilot only:** B_1301's frozen `T5_30.json` verdict exists, its lease is released, and all v4 technical prerequisite stages passed. A live gate failure stops; the CPU dry run is not gate evidence.

Development dry runs were stopped by admission checks when owned source changed; their partial directories are retained and are not passing evidence. Deterministic test counts are checks, not scientific estimates; intervals/p-values are not applicable. Six root warnings are existing deprecation/fork warnings.

### Exact master commands — prepared, not executed

Only the master runs this block after confirming no veto and the window ending **10-21-2026 12:00 PDT**. A waiting pause status means retry on a later call; it never authorizes interrupting a stage. Read-only process inspection confirmed that the actual tmux pane shell and runner share a process group; the tool recognizes precisely that owned pair, excludes shell command strings from runner identity, and refuses any additional group member. Five added CPU cases cover this deployment detail. The five recorded pauses release the gates; B_1301 continues to its frozen `T5_30.json`. Its `EXTEND_TO_60` spelling is the v3 failure verdict and does not authorize a v3 extension under A3.

```bash
cd /lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
V4_WORK=/lfs/skampere1/0/brando9/rl4cv_e13v4
V4_ADMISSION=$V4_ROOT/phase2/admission_dispatch3.json
export HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 VLLM_USE_FLASHINFER_SAMPLER=0
export PYTHONPATH=$PWD/src
# Set only after the master has established absence of a veto.
export E13V4_A3_NO_VETO=1
"$V4_PY" "$V4_ROOT/phase2/admission.py" launch-check --record "$V4_ADMISSION"
# Pause: writes only clean pauses; invoke again later for WAIT_* trajectories.
"$V4_PY" "$V4_ROOT/phase2/pause_v3.py" --admission "$V4_ADMISSION" --veto-not-issued --execute
# Watchdog: install from day one after A3 conditions; the controller uses the same stage lock.
"$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan "$V4_WORK/watchdog_plan.json" --log "$V4_WORK/watchdog.log" --admission "$V4_ADMISSION" --install
# Gates: begins only after all five clean pauses are recorded.
"$V4_PY" "$V4_ROOT/phase2/runner.py" gates --work "$V4_WORK/run" --admission "$V4_ADMISSION" --engine local
# Pilot: only after B_1301 T5_30, released lease, and all eight prerequisite stages PASS.
"$V4_PY" "$V4_ROOT/phase2/runner.py" pilot --work "$V4_WORK/run" --admission "$V4_ADMISSION" --engine local
# Read-only progress and recovery inspection:
"$V4_PY" "$V4_ROOT/phase2/runner.py" progress --work "$V4_WORK/run" --admission "$V4_ADMISSION" --engine local
"$V4_PY" "$V4_ROOT/phase2/recovery.py" --work "$V4_WORK/run"
```

The commands above list each requested action. Install the watchdog immediately after the clean pauses, before gates, so it is present from day one. Its controller executes the same ordered sequence, waits for pilot timing and never launches main. Do not run a second manual controller alongside its active tmux controller. The master can use the [launch plan](phase2/launch_plan.json) `gates_argv`/`pilot_argv` or the watchdog-controlled sequence. The cron line has not been installed.

The tested v3 watchdog and its test were also deployed atomically into the active v3 checkout after verifying that both existing files exactly matched their original tracked bytes. The [deployment receipt](phase2/watchdog_deployment_dispatch3.json) binds old/new hashes. No other v3 file, existing cron entry or process was changed, and the real pause list is absent. Thus all six v3 trajectories retain the existing behavior until the master invokes the pause.

The runtime guard observes devices at each lease and respects v3's per-device locks/reservations. Read-only [GPU census](phase2/gpu_inventory_dispatch3.json), **10-20-2026 22:48:49 PDT**: **21/24 devices occupied**. skampere1 idle devices are 3, 4 and 6, which are outside the v4-authorized subset; 0, 5 and 7 are occupied. skampere2 and skampere3 have no idle device. All three host probes succeeded; this census acquired no lease. Occupancy attribution is reported only when process evidence supports it; experiment 120 ownership is unresolved unless its process path identifies it. The master must refresh and resolve that check before launch as required by the protocol.

**Copy-ready message for the master:** I finished v4’s real leased adapters, A2–A4 and the experiment 19 forecast scorer, with 142 passing v4 tests, 16 passing watchdog tests, 1,405 passing root tests and a 360-update GPU-free stub run; admission `29276968a2e93abcea5dede2f763703ed207b2f4f0e6c94f542268f8b11c758c` passes static launch-check, leaving the master’s A3 timing/pauses, idle lease and B_1301 pilot conditions.

Publication: implementation commit **[`1e667077`](https://github.com/brando90/rl-4-code-verification/commit/1e667077c7b075c7158e255883eb5fa2ba77e157)** was committed with explicit pathspecs, rebased over the master’s `b193341c` checkpoint and pushed to `main`; the remote SHA matched on readback. The Google companion’s owned v4 section was updated and read back exactly, preserving all other content. This publication-note update changes only this checkpoint; the admission digest and bound artifacts stay unchanged. Read-only measured progress reports every live v4 stage `PENDING`. No live launch follows publication.

## Historical dispatches — superseded admissions and commands

The following preserved sections describe their original state. Dispatch 3 above supersedes their blocker claims, admission paths and launch instructions.

## Dispatch 2 evidence and exact continuation

**Concurrent amendments discovered at final rebase:** master added [V4-A2](AMENDMENT_V4-A2_receipt_invariance_and_sampler_backend_10-20-2026.md) and [V4-A3](AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md) while this A1 dispatch was in progress. Neither changes the actor-correction blocker. A2's 10,000-position installed-sampler test, R0/R1/R2 engine criterion, explicit FlashInfer-disable setting, import-absence check and worker-side backend receipts are **not implemented or bound by this scoped admission**. A3 is subject to veto until 10-21-2026 12:00 PDT; this dispatch makes no v3 pause or schedule change. The prepared launch plan still uses the earlier release condition and must be reconciled with the effective A3 outcome before use. No launch-ready claim applies to these new requirements.

[Verification receipt](phase2/verification_dispatch2.json) records **117 passed / 0 skipped / 0 failed** for v4 and **1,405 passed / 15 skipped / 0 failed** for the root suite. Logs are `/lfs/skampere1/0/brando9/rl4cv_e13v4/v4_dispatch2_tests_final.log` and `root_dispatch2_tests.log`. The v4 suite uses the read-only NeMo venv plus separate `test_deps`; root uses the historical experiment-09 source override as documented in the preserved reproduction section. Six root warnings are existing deprecation/fork warnings. Initial development test failures were corrected; these are the final rerun counts. Counts are deterministic checks, not scientific estimates (confidence intervals/p-values not applicable).

**Copy-ready message for the master:** I implemented V4-A1 certificates and verified the ordered CPU runner with 117 passing v4 tests, a passing root suite, and all six synthetic trajectories through extension; measured launch is blocked by unspecified importance corrections at uncertified positions, and the real scorer/trainer/checkpoint adapter remains unfinished.

[Blocker report](BLOCKER_V4_A1_importance_correction.md) separates the scientific contract gap from the unfinished measured backend. The top-20 support-information blocker from Dispatch 1 is superseded by A1; it is not reused as the present reason to stop. The installed NeMo CPU loss test proves that generator probability affects the loss even with an unchanged trainer ratio. Unknown values are never filled from trainer values or masked silently. The master must own any change to the frozen objective.

[Dry-run receipt](phase2/dry_run_dispatch2.json) binds every command and each stage receipt to the new admission. Full logs/receipts remain under `/lfs/skampere1/0/brando9/rl4cv_e13v4/dry_run_dispatch2` (20 MiB). All results there are synthetic: no gate, actual audit, maximum-length memory measurement, model generation or optimizer step occurred. The one-token fixture preserves the declared 1,024 G0 slots and 256 pilot slots. It freezes 30,720 placebo draws before P, fails the 30-update feasibility gate, extends all six trajectories, and reaches a resource-check decision at 60 without launching main. Completed-stage status PASS means the stage finished; the nested T5 scientific verdict is separately FAIL/PASS.

```text
T1 PASS -> G0_GENERATE PASS -> G0_SCORE PASS -> G0_SELECT PASS
T2 PASS -> T3 PASS -> T4 PASS -> B_AUDITS PASS
PILOT30 PASS -> T5_30 EXTEND_ALL_SIX -> PILOT60 PASS -> T5_60 MAIN_RESOURCE_CHECK
Out-of-order G0_GENERATE: rejected (exit 1)
Injected pre-generation T1 crash: exit 1; explicit recovery: PASS on attempt 2
No-signal sequence: T2 STOP_NO_SIGNAL; T3 rejected (exit 1); no T2 update/refit exists
```

To reproduce on a **new** output directory (receipts are deliberately exclusive):

```bash
cd /lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
"$V4_PY" "$V4_ROOT/phase2/dry_run.py" --root /lfs/skampere1/0/brando9/rl4cv_e13v4/dry_run_dispatch2_reproduction --admission "$V4_ROOT/phase2/admission_runner.json"
"$V4_PY" "$V4_ROOT/phase2/admission.py" check --record "$V4_ROOT/phase2/admission_runner.json"
```

The following are the exact prepared **master commands**, not presently executable launch authorization. The installer with `--install` and every measured stage are rejected by the new admission. After a prospective fix and a completed measured adapter, regenerate/rebind the plans and admission; do not flip their status fields. Refresh the GPU census and verify v3's release condition at actual launch.

```bash
# Install watchdog: NOT RUN; blocked by admission now.
"$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json --log /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog.log --admission "$V4_ROOT/phase2/admission_runner.json" --install
# First measured stage: NOT RUN; blocked by admission now.
"$V4_PY" "$V4_ROOT/phase2/runner.py" T1 --work /lfs/skampere1/0/brando9/rl4cv_e13v4/run --admission "$V4_ROOT/phase2/admission_runner.json" --engine local
# Planned tmux controller, prefix rl4cv-e13v4-: NOT RUN; checks admission and v3 release.
"$V4_PY" "$V4_ROOT/phase2/launch_control.py" --plan /lfs/skampere1/0/brando9/rl4cv_e13v4/launch_plan.json
# Read-only progress for measured work (currently all pending):
"$V4_PY" "$V4_ROOT/phase2/runner.py" progress --work /lfs/skampere1/0/brando9/rl4cv_e13v4/run --admission "$V4_ROOT/phase2/admission_runner.json" --engine local
# Inspect recovery without executing it:
"$V4_PY" "$V4_ROOT/phase2/recovery.py" --work /lfs/skampere1/0/brando9/rl4cv_e13v4/run
```

[Launch plan](phase2/launch_plan.json) includes concrete argument vectors for every stage and the leased-device interface. [Watchdog plan](phase2/watchdog_plan.json) points to the v4-only controller; no cron or session was created. Plans describe the blocked implementation honestly. `device_lease.allocation` and its idle/ownership guard are tested with mock devices, but the measured stage adapter is still required to invoke them.

The fresh [GPU census](phase2/gpu_inventory_dispatch2.json) records skampere1 devices 5/7 as Brando-owned PIDs 1486934/1125764, with working directories and ancestry identifying v3. Skampere2/3 have no idle devices. It establishes no process-to-experiment-120 attribution. Availability is a dated observation, not a reservation.

## Historical Dispatch 1 record (superseded)

The sections below are preserved history, including the old top-20 blocker and old admission digest. Use the Dispatch 2 state and commands above for current status.

## Implemented contracts and decisive checks

See [README.md](README.md) for the component map. Installed-source comparison tests cover native tie handling and the retained top-p boundary token; a 40-way equal-logit control leaves 38 tokens in the true support while a top-20 receipt carries at most 21. Positive reconstruction tests require a complete vocabulary or an external completeness certificate; the pinned engine supplies neither for ordinary top-20 requests. This is an information limitation, not a tolerance failure. Source evidence is bound in [admission_cpu.json](phase2/admission_cpu.json).

The actual NeMo loss executes forward/backward on synthetic CPU logits with sparse fixed old support. NeMo scales logits before calling the loss: v4 hooks use float32 division once, and the loss wrapper does not divide twice. The synthetic full-length probe is written but has not run on the real model; its target builder has a tiny CPU backward control preventing mutation of embedding indices saved by autograd. No CPU test is counted as a real T1–T4 gate.

G0 uses seeds 1304001/1304002, 10,000 paired whole-task bootstrap draws, both missing-slot completions and exact known-value controls. Gate tests cover fallback to B rewards or stop without resampling, five T2 criteria including pre-clipping gradient norm, T3 replay identity, T4 required records, gate single-attempt reservations and the three-attempt infrastructure-only cap. Placebo tests bind the sorted 17-significant-digit reference digest, the ≥90% rule, counter draws before P and density/variance denominators. Pilot controls cover conservative T5, all-six 30→60 extension and T from both A seeds' updates 1–30 only.

[context_values.json](phase2/context_values.json) covers 539 train, 135 validation and 222 test prompts for each engine. It rejects 8,192 and 15,945 context lengths. Only held-out instruction text was read to compute lengths. [A6_counts.json](phase2/A6_counts.json) contains no task identities: histogram `{0:51,1:2,2:3,3:3,4:0,5:2,6:1,7:1,8:1}`, 54 complete groups, eight mixed strict groups and 49 varying B groups, with 512 input receipt hashes and source manifest/aggregate hashes. The frozen protocol's counts agree exactly. These are exhaustive descriptive counts, not new outcome estimates.

## Test reproduction and environment recovery

The v4 suite uses only the original pinned NeMo runtime. Pytest 8.4.2 and its dependencies reside in the separate work-directory `test_deps`; nothing was installed into the shared venv. Logs remain at `/lfs/skampere1/0/brando9/rl4cv_e13v4/v4_tests_final.log` and `make_test_configured.log`.

The first repository-wide run had seven environment failures (1,355 passed, 41 skipped): missing external scoring repositories/legacy utility path and the historical experiment-09 test's `e09_seeds` dependency. Restored local untracked symlinks to existing pinned `external/veribench` and `external/veribench_scorer` (c11b99… / 59059…), plus `/lfs/skampere1/0/ultimate-utils` pointing to Brando's existing utility checkout. Added the existing experiment-09 NeMo source to PYTHONPATH **only for the root historical suite**; no source was changed. All seven failed tests then passed, followed by the full 1,388-pass suite. Six warnings concern existing deprecations/fork behavior. The v4 suite ran separately without this alternate source path.

Exact CPU commands (run from the indicated checkout):

```bash
cd /lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e13v4/test_deps:$PWD/src
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
"$V4_PY" -m pytest -q "$V4_ROOT/tests"
"$V4_PY" "$V4_ROOT/phase2/admission.py" check --record "$V4_ROOT/phase2/admission_cpu.json"
# Expected nonzero exit with the documented frozen-contract blocker:
"$V4_PY" "$V4_ROOT/phase2/admission.py" launch-check --record "$V4_ROOT/phase2/admission_cpu.json"
# Historical root suite only (keep this source override out of the v4 suite):
PATH=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin:$PATH PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e09/nemo_rl:$PYTHONPATH make test
```

## Remaining launch work and exact command boundary

There is **no valid model-launch command under this frozen protocol**. The implemented admission guard deliberately blocks launch even if someone changes its JSON status. This dispatch supplies tested components and a bound rejection receipt, not a runnable end-to-end pilot or evidence that the technical gates passed.

1. [p 8/10] Resolve the source-proven receipt insufficiency: the smallest amendment exposes actual filtered token IDs and normalized probabilities at sampling time, or a complete tie-expanded top-k set with original order and a completeness certificate. Keep the objective/sampler unchanged; the master owns any amendment to the frozen protocol.
2. [p 8/10] After that amendment, integrate concrete generator/scorer/update/recovery commands with these components and bind new admission. Actual NeMo worker integration, sampler backend, raw receipt extraction and full-length memory behavior still need launch measurement. Do not restore the old v3 runner's retired lengths/objective.
3. [p 7/10] After the master's v3 release condition and an idle-device lease, execute T1/G0/T2/T3/T4 and B audits in frozen order, bind measured cost/reserve, freeze all placebo draws before P, then run the six trajectories and conditional extension. No gate may be silently repeated; partial samples must be diagnosed and retained.
4. [p 5/10] Resolve the canonical identity/location of experiment 120 before attributing any GPU process to it; the census below is verified, its experiment label is not.

The future watchdog requires an existing admission-bound plan at `/lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json` with concrete argument-vector commands. This path is reserved for the future plan; no such launch plan or cron entry was created. Once all preceding requirements have been met, these are the exact watchdog commands (the install command is currently rejected by admission):

```bash
# With V4_PY and V4_ROOT set as above, preview only:
"$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json --log /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog.log --admission "$V4_ROOT/phase2/admission_cpu.json"
# Launch-time only, after the plan and a new valid admission exist:
"$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json --log /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog.log --admission "$V4_ROOT/phase2/admission_cpu.json" --install
```

## Experiment 120 GPU report

At 10-20-2026 15:40 PDT, all 24 devices across skampere1/2/3 had compute processes; zero were idle. [gpu_inventory.json](phase2/gpu_inventory.json) preserves device IDs, owners, process IDs/names and Brando-owned ancestry. The three eligible skampere1 devices are attributed to `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3` by their process working directories and pilot ancestry, not to experiment 120:

| Host/device | Owner | PID | Process |
|---|---|---|---|
| skampere1/0 | brando9 | 1258391 | ray::DTensorPolicyWorker.__ray_call__ |
| skampere1/5 | brando9 | 875936 | ray::DTensorPolicyWorker.train |
| skampere1/7 | brando9 | 904183 | ray::DTensorPolicyWorker.__ray_call__ |

The other skampere1 devices belong to eth127 (1/3/6) and srivatsavad (2/4). Skampere2 devices 0–7 are held by vmadan/alexspan/srivatsavad; skampere3 devices 0–7 by vmadan/alexspan/ruhana. Full per-device process rows are in the linked receipt. No process was killed or modified. Local relevant repository searches, current remote VeriBench main trees, owned tmux/process names and this census did not establish a canonical experiment-120 folder or matching owner/process. Its GPU use is **unresolved**, not zero. Refresh the census at launch; this is a dated observation, not a reservation.

## Copy-ready message

I have the experiment 13 v4 CPU implementation passing 89 tests, with the historical repository suite also passing. Launch remains blocked because the frozen top-20 generator receipt cannot recover the exact sampling support when cutoff logits tie; the protocol is unchanged and no training or generation has run.

## Event log
- 10-20-2026: Loaded frozen protocol and installed sampler sources; identified top-20 information loss at the k-th tie before any model execution.

- 10-20-2026 15:44 PDT: CPU implementation reaches 80 passing tests; complete prompt-length and A6 count receipts written. Read-only three-host inventory found all devices occupied; no v4 launch.

- 10-20-2026 15:56 PDT: Final v4 suite 89/89 passes; configured root suite 1,388 passes/15 skips/0 failures. Bound 29 local artifacts plus four runtime sources, preserving the code-level launch blocker. Corrected once-only worker temperature scaling and verified synthetic probe targets do not mutate saved embedding indices. No launch or cron installation.

- 10-20-2026 15:57 PDT: Inspected exact staged changes, credential-pattern scan and whitespace check; all 32 authored files are confined to v4 and begin with TLDR. Rebased on origin/main 7bbe1f79, pushed 7aec74f7, and verified the remote hash. Admission recheck unchanged; Google companion update verified by readback. This documentation-only receipt closes publication.

- 10-20-2026 19:11 PDT: Dispatch 2 certificates and 115-test CPU suite pass; all 12 stub stages and 360 symbolic updates verified, including crash recovery and no-resampling stop. New admission explicitly blocks unresolved importance correction and unfinished measured adapter; root verification/publication pending.

- 10-20-2026 19:13 PDT: Final v4 suite 115 passed/0 skipped/0 failed; root make test 1,405 passed/15 skipped/0 failed. CPU admission verifies; measured progress is all PENDING; launch-check deliberately rejects. Dry-run summary and log hashes committed with the blocked implementation.

- 10-20-2026 19:17 PDT: Final diff fixes watchdog spawn/fence race and binds T1 denominator to saved response lengths; 117 v4 tests pass. Regenerated admission `58e1b31df8e87e0e797f4043a9e03a9a7e774cf6982b302914c59490ab10f433` and all command-line dry-run receipts; root tested code is unchanged.

- 10-20-2026 19:19 PDT: Rebased on origin/main 686aa9ca and pushed implementation 000ac82b; remote hash verified. Rebase added master A2/A3 (read, unchanged, not implemented by this A1 admission); recorded their pending requirements and veto window. Shared runtime/frozen A1/protocol still hash-verify; no launch.

- 10-20-2026 22:13 PDT: Dispatch 3 implementation entered integration verification; installed 10,000-position sampler check PASS, preliminary v4 131/131 and watchdog 16/16 pass; root and subprocess dry run in progress. No launch.

- 10-21-2026 11:23 PDT: Dispatch 4 implementation started: operational A_1302 selection, shared timing, read-only probe and CPU fixture controls; deployed v3 watchdog already supports the subset and remains unchanged.

- 10-21-2026 11:31 PDT: Dispatch 4 verification complete: 168 v4 / 16 watchdog / 1,405 root passed (15 skipped); single-pause dry run and 360 symbolic updates passed; sealed admission a8a1b8f28497e51ba3d898dceb07902c9dc18f83bdac9164b49e462a9a79e390. Publication pending; no live actions.

- 10-21-2026 11:34 PDT: Published 3b2df5c3 to main and verified the remote hash after two clean rebases over concurrent checkpoint-only changes; owned patch unchanged, admission still valid, Google companion synchronized. No real pause, cron install or GPU work.

- 10-21-2026 12:57 PDT: Dispatch 5 implemented process/disk observations and stop-aware whole-rule rechecks; B_1302 read-only observation reaches READY, A_1302 remains active; tests and new admission in progress.

- 10-21-2026 13:08 PDT: Dispatch 5 verified: 233 v4 / 16 watchdog / 1,405 root passed (15 skipped), 91 final focused checks; admitted live A_1302 refusal and P_1301 READY; sealed 9b5089a141bb877b96f55f58ef91748badfd9fb980d139c13ef15339ccd92c23, launch-check PASS; rebase/publication next.

- 10-21-2026 13:11 PDT: Corrected two literal newline escapes in the README table before publication and resealed only its runtime binding; final admission ffbeb4e6b2b64408d4a151a24bf0034400bef9c7d6d09d0da0a10f71efeb72b7. Source/test/plan bindings and all evidence unchanged; prior unpublished seal retained privately.

- 10-21-2026 13:13 PDT: LANDED 9ec6640d9ab8cf982f1b9af6c19e0d1f431c4395 on main; remote SHA verified, range-diff identical and 18 owned files unchanged after rebase; final launch-check PASS, Google readback verified, backup removed; no v3 pause, cron or GPU action.
