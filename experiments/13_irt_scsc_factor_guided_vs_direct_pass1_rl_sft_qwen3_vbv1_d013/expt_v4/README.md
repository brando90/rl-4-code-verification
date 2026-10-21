# Experiment 13 v4: silent-runner boundary and prospective admission

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/README.md>

**TLDR:** Dispatch 5 admits a process/disk boundary for silent v3 runners while preserving the decision to pause only A_1302. Gates require that one recorded clean pause and the unchanged veto condition; the pilot still requires B_1301's verdict/released lease, all gates passed and three idle authorized devices. Live actions remain master-owned; this dispatch uses only CPU tests and synthetic dry runs.

`experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4` compares strict reward (A), factored reward (B), and a start-density placebo (P). [The checkpoint](CKPT_v4_implementation.md) records the admission digest, final dry-run outcome, test counts, remaining runtime conditions, live read-only probes and exact master commands.

## Frozen contracts

The [protocol](PROTOCOL.md) and all four amendments are unchanged and hash-bound:

- [V4-A1](AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md): top-64 raw receipts, support certificates and trainer tie handling.
- [V4-A2](AMENDMENT_V4-A2_receipt_invariance_and_sampler_backend_10-20-2026.md): installed-Sampler CPU invariance, R0/R1/R2 engine checks and native sampler evidence.
- [V4-A3](AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md): veto window, gates first, pilot after B_1301; pause scope is superseded by the operational decision below.
- [V4-A4](AMENDMENT_V4-A4_importance_correction_at_uncertified_positions_10-20-2026.md): unit actor correction at uncertified positions, isolated loss-only imputation, 1% update guards and perturbation bound.

[The unchanged operational decision](OPERATIONAL_V4-A3_single_pause_10-21-2026.md) is also hash-bound, with [operational_pause.json](phase2/operational_pause.json) selecting exactly A_1302. Execution refuses every other trajectory, including B_1301; read-only probes may inspect all six declared trajectories. The veto deadline remains 10-21-2026 12:00 PDT; neither a synthetic fixture clock nor admission bypasses it.

A4 resolves the contract gap in the preserved [Dispatch 2 blocker](BLOCKER_V4_A1_importance_correction.md). That report and the old admissions are historical; use `phase2/admission_dispatch5.json` for this implementation.

## What is implemented

Generation uses vLLM 0.10.0, temperature 0.6, top-k 20, top-p 0.95, context 20,041 and response cap 12,288. Every generator environment forces `VLLM_USE_FLASHINFER_SAMPLER=0`; admission checks that `flashinfer` is absent. Each generation receipt records the selected `TopKTopPSampler.forward` from the actual worker. The installed `Sampler.forward` CPU check covers 10,000 positions, including ties, and produces zero token mismatches with receipt collection off/on. The eight-response R0/R1/R2 engine comparison remains a live T1 gate.

The NeMo RL 0.4.0 loss uses fixed old trainer supports, temperature scaling once and the inherited leave-one-out, standard-deviation-scaled advantages. A4 changes only the capped actor correction at uncertified positions: its weight is one. Certified positions retain their correction. Unknown generator probabilities remain null in receipts and NaN in the stored training batch; only the parent loss's private payload receives the detached old probability. The complete update checks both generated-token and valid-actor-token uncertified fractions before constructing a policy. Fractions above 1% stop without an optimizer step. Each update reports both denominators, certified fraction, log-weight quantiles/cap rate, certified-only probability/entropy diagnostics and the loss-perturbation bound. Unit correction is an approximation: empirical bias remains unmeasured, and this bound concerns loss, not gradient change.

`local_engine.py` composes generation, official strict scoring and B's reward, filtered training, native checkpoint save/restore, CPU export, generator refit, saved-batch T3 replay, the maximum-length probe and fixed-cohort B audits. Every component runs as a subprocess with its own recorded argument vector, environment, lease, PID/start time and exit evidence. Device stages acquire an idle authorized GPU through the v4 guard and respect v3 reservations; scoring/export have CPU leases. Raw compiler stdout/stderr survive timeouts. A real CPU smoke check scored one explicitly synthetic empty completion through this leased adapter and retained its compiler output. B runs padding/deletion/substitution and hidden-gold checks; missing audit coverage stops B. No paid judge is called.

Pilot storage retains the latest native checkpoint and export per trajectory, metadata and hashes for completed updates, and all T2/T3 replay evidence. Superseded pilot tensor payloads are retired only after a newer durable continuation exists; each retired payload has a hash receipt. A 100 GiB pre-update free-space check stops before model construction if a checkpoint transition cannot be stored.

After G0 selection, `forecast_score.py` verifies the frozen experiment 19 forecast (`abb0cb3115b86fd3107a565fdfacd53343f285b7d27b34fd30d4dcb682436286`), joins counts privately on SNAP and writes anonymous aggregate Spearman, mixed-task AUC, mean q̂_8 and chosen G. It includes whole-task bootstrap intervals, denominators and missingness bounds. Forecasts are descriptive and never gate inputs. No live forecast outcome has been computed.

## Stage order and recovery

```text
T1 -> G0_GENERATE -> G0_SCORE -> G0_SELECT -> T2 -> T3 -> T4 -> B_AUDITS
   -> PILOT30 -> T5_30 -> [PILOT60 -> T5_60, only on extension]
```

Stages bind predecessor receipts, immutable operation inputs and completed outputs to the admission. Statistics are reserved once. Recovery permits at most three infrastructure starts only when there is explicit evidence of zero generation, zero optimizer effects and no statistic. Ambiguous partial work stops. A completed T5 stage and its scientific verdict are separate fields. Main training never launches automatically.

`--engine local-stub` runs this same subprocess composition with JSON stub primitives and `CUDA_VISIBLE_DEVICES=''`. The preserved Dispatch 3 local-stub run covers six trajectories through the 60-update extension, order refusal, pre-generation crash recovery, no-signal stop and A4 stop. Dispatch 4 adds the single-pause WAIT-to-PAUSED path and gate-release checks, and reruns the ordered sequence with the in-process CPU stub. Synthetic results establish control flow only; they do not establish live gate success, GPU memory fit, scoring accuracy on new model output or learning.

The master-only `pause_v3.py` offers `--probe --trajectory A_1302` for read-only boundary inspection and requires explicit execution after the veto window for a pause. It requires the same single pilot_run.py runner and isolated pane-shell group on two observations at least one second apart: zero runner children or other readable trajectory references, hrtimer_nanosleep, no active latest-update lease, pre-generation inputs or scored groups awaiting optimization, and no summary. Pane text is receipt context only. Execution retains the shared watchdog lock and repeats the whole rule after stopping the group; Linux reports do_signal_stop while stopped, so the receipt binds the two pre-stop sleep observations to the same stopped identities and unchanged disk state. A running stage is refused; the master retries later. The real pause list has not been created, no runner has been signalled, and no cron entry has been installed. The deployed v3 watchdog already supports a single-item pause dictionary; Dispatch 5 changes no v3 files or processes. Read-only --probe can inspect any of the six declared v3 trajectories, including B_1301; execution still refuses every trajectory except A_1302.

The pilot's three-device availability preflight acquires and releases the same per-device locks used by v3 before admitting a pilot stage. It holds no standing reservation: generation and optimizer subprocesses still acquire their own idle-device leases, compete with v3, and release on completion. This fills an existing missing resource check; it does not change the frozen scientific protocol or convert the serial pilot runner to a new parallel schedule.

## CPU verification

```bash
cd /lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2
export PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e13v4/test_deps:$PWD/src
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
"$V4_PY" -m pytest -q "$V4_ROOT/tests"
"$V4_PY" "$V4_ROOT/phase2/admission.py" launch-check --record "$V4_ROOT/phase2/admission_dispatch5.json"
# Use a fresh output directory; immutable receipts are never overwritten.
"$V4_PY" "$V4_ROOT/phase2/dry_run.py" --root /lfs/skampere1/0/brando9/rl4cv_e13v4/dry_run_dispatch5_reproduction --admission "$V4_ROOT/phase2/admission_dispatch5.json"
```

Verification: **233 v4 passed; 16 v3-watchdog passed; 1,405 root passed, 15 skipped, 0 failed**. The shared virtual environment remains read-only. The root reproduction additionally prepends `/lfs/skampere1/0/brando9/rl4cv_e09/nemo_rl` to `PYTHONPATH`, sets the pinned venv's `bin` first on `PATH`, and runs `make test`.

## Entry points and evidence

| Artifact | Purpose |
|---|---|
| [Admission](phase2/admission_dispatch5.json) | Frozen contracts, source, tests, plans, installed/reused components and CPU receipts |
| [Verification](phase2/verification_dispatch5.json) | Final counts and immutable log hashes |
| [Sampler receipt](phase2/sampler_cpu_receipt.json) | Installed CPU off/on-64 invariance and backend |
| [Silent-boundary probes](phase2/live_probes_dispatch5.json) | A_1302 active-stage refusal; P_1301 READY on a blank pane; B_1302 polling-child refusal |
| [Pause control](phase2/dry_run_dispatch5.json) | Synthetic stop/recheck, atomic temporary receipt and gate release |
| [Historical full stub dry run](phase2/dry_run_dispatch4.json) | Single-pause WAIT/PAUSED path, gate release, symbolic pilot extension and diagnosed stops |
| [Subprocess preview](phase2/adapter_dry_contracts.json) | Prospective real-stage argv/environment, not executed |
| [Launch plan](phase2/launch_plan.json), [watchdog plan](phase2/watchdog_plan.json) | A3-aware master commands and controller |
| [Checkpoint](CKPT_v4_implementation.md) | Dry-run evidence, remaining runtime conditions, commands and handoff |
