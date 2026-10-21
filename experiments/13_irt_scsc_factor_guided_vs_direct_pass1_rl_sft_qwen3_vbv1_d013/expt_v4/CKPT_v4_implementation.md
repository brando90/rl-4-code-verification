**TLDR:** Dispatch 2 implements V4-A1 certificates and an ordered CPU stub runner; measured launch is BLOCKED on unspecified importance correction and unfinished measured adapters.

# Experiment 13 v4 implementation checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/CKPT_v4_implementation.md>
**Companion:** <https://docs.google.com/document/d/1KqUi39sz532dIGg8EYCy6w62Q0KzO2XWhpM2MMSWvHE/edit>
**Created:** 10-20-2026 15:27 PDT. **Last updated:** 10-20-2026 19:19 PDT.

## State

- Scope: `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4`; Dispatch 2, CPU only.
- Owner: Codex gpt-6-astra; requested high effort; skampere1; full filesystem access, approval policy never.
- Status: **BLOCKED, not launch-ready**. Certificates and the full synthetic stage sequence pass; real backend is unfinished.
- Frozen protocol d4778e25 and amendment V4-A1 7877faac are unchanged; their full hashes are in the new admission.
- Done: top-64 constructor/request, strict top-k certificate, 1e-5 nucleus margin, trainer boundary tie inclusion, full/reduced receipts.
- Done: ordered single-attempt stages, predecessor/admission hashes, placebo precomputation, all-six extension, bounded recovery.
- Done: launch/watchdog plans at the requested work-directory paths, plus admission-bound repository mirrors.
- Tests: v4 **117 passed, 0 skipped, 0 failed** in 31.35 s; root suite **1,405 passed, 15 skipped, 0 failed**, 6 warnings in 396.62 s.
- Dry run: all 12 stage entries complete; six trajectories × 60 symbolic updates = 360; zero real optimizer steps.
- Controls: order rejection; zero-response crash recovered on attempt 2; no-signal T2 stops without update/refit/resampling.
- Admission: `phase2/admission_runner.json`; 44 local bindings and six external bindings (four runtime files, two plan mirrors).
- Admission SHA-256: `58e1b31df8e87e0e797f4043a9e03a9a7e774cf6982b302914c59490ab10f433`.
- CPU admission check passes; launch-check rejects the explicit scientific and implementation blockers below.
- Scientific blocker: uncertified positions have no generator log probability, required by NeMo's separate capped actor correction.
- Implementation gap: real scorer/trainer/checkpoint/replay/audit adapter and leased subprocess orchestration are not integrated.
- Smallest prospective fix: record actual filtered sampled-token probability at every position, or explicitly amend the correction rule.
- GPU census 10-20-2026 19:05 PDT: 20/24 devices occupied; skampere1 0/2/4/6 idle, only 0 eligible here; 5/7 remain v3-owned.
- Experiment 120 attribution remains unresolved; no process was attributed without evidence.
- No GPU allocation, model generation, optimizer step, provider call, cron installation, tmux session or v2/v3 edit; $0.
- Next [p 8/10]: master resolves the actor-correction rule; then finish measured adapters and incorporate newly arrived A2/A3 before a new admission.
- Master decision [p 8/10]: specify the missing actor-correction semantics prospectively; no launch go can substitute for that fix.
- Publication: implementation `000ac82b8744c1ed379818fe0d283d4349d35e89` rebased on `686aa9ca`, pushed to main and verified remotely; companion updated/read back.

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
