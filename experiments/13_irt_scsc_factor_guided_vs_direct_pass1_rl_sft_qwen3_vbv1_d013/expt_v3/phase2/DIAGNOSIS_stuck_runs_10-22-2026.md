**TLDR:** Experiment 13 is blocked by missing Lean tooling and incorrect checkpoint-completion detection in v3, repeated foreign-process device refusals, low disk headroom, and a deterministic vLLM serialization error that exhausted v4’s three-attempt cap; a tested v3 resume fix is staged, not activated.

Copy-ready status: Experiment 13’s v3 pilot and v4 T1 probe remain blocked; diagnosis identifies independent scoring, resume, device-sharing and serialization failures, with 1,168.41 GB of ranked disk candidates and an isolated resume fix awaiting deployment decisions.

# Experiment 13 stuck-run diagnosis — 10-22-2026

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e13v3-resume-missing-receipt-fix-10-22-2026/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/phase2/DIAGNOSIS_stuck_runs_10-22-2026.md>

Canonical experiment: `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/` (factor-guided versus direct pass-at-one reinforcement learning from a supervised-fine-tuned Qwen3 policy). A, B and P below are its existing trajectory labels; seed suffixes distinguish paired runs. T1 is the v4 generator/receipt technical probe. A4 here is the protocol’s infrastructure-attempt cap, distinct from the separate V4-A4 importance-correction amendment.

Prepared for Brando and the VeriBench/rl4cv general coordinator. Observations use skampere1’s local PDT clock on 10-22-2026; no inference or training was launched. `GB` = 10^9 bytes; `GiB` = 2^30 bytes. Operational counts are censuses, not sampled scientific estimates; confidence intervals and p-values do not apply.

## Decision needed

1. **[p 10/10] Address independent v3 causes together before deploying the staged fix.** Restore `lake` discoverability in the actual cron-to-runner environment; recover scoring on the *same retained generations*, preserving failed measurements, rather than generating replacements. Free disk and use genuinely available devices. The staged receipt fix handles incomplete optimizer attempts but cannot turn cached missing scores into measured rewards. No such recovery was activated here.
2. **[p 10/10] Choose a disk-loss budget.** The lowest-impact identified payload is the rejected layout probe (126.45 GB). For the requested 500+ GB target, retiring only the 14B native policies at steps 82, 164 and 497 releases 531.75 GB, subject to the experiment-08 owner accepting loss of those exact-resume states. Keep halfway step 334, final step 658, every exported model and the protected live paths below. No live data deletion or move occurred.
3. **[p 10/10] Keep v4 stopped pending Brando’s protocol decision.** Fix the function-serialization incompatibility prospectively and validate it without consuming another admitted attempt; then Brando decides whether a new admission/amendment permits another probe. Raising or resetting the cap alone will repeat the same failure.
4. **[p 9/10] Review the periodic counter reset.** It clears exhausted v3 counters every two hours, including B_1301. Thus the nominal limit of three bounds each reset interval, not the lifetime of an update. Changing this schedule is a separate owner action; this diagnosis changed neither cron nor counters.

Collaborator message in Brando’s voice: “I have a staged fix and a disk recovery menu, but disk alone will not restart these runs successfully. The missing Lean tool and vLLM serialization failure need separate fixes, and I need to decide whether to re-admit the capped v4 probe.”

## 1. Verified v3 failure chain

Live data root `V3=/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2`; live code root is the canonical experiment’s `expt_v3/phase2/` in `/lfs/skampere1/0/brando9/rl4cv_e13v3/rl-4-code-verification`. Paths below are evidence references, not commands to execute.

### B_1301 — update 23: not an optimizer-loading crash

- The original pilot stopped at **03:58:33** with `RuntimeError: all rewards missing; opportunity retained, no fabricated optimizer update`. Saved pane: `V3/autoresume_deaths/rl4cv-e13v3-pilot-B-1301_10-22-2026_040002.log`.
- `V3/pilot/B_1301/update_00023/score/cells/result.json` records **0/256 measured**, with all **256/256** errors exactly `[Errno 2] No such file or directory: 'lake'`. All 256 retained group rewards are `null`.
- The supervisor launched an optimizer retry at **04:40:02** because it tested only whether 256 generation files and `score/groups.json` existed. It did not require usable measured rewards.
- The retry’s `update/execution.json` records **exit_code 0**, **288.564 seconds**. Its `update/output/result.json` says **`UNMEASURED`, `optimizer_updates: 0`, `usable_groups: 0`**, reason `no complete measured reward group; no optimizer call`. The trainer’s normal all-missing branch (`expt_v2/phase2/trainer_core.py:112`) writes this result without an `after/` checkpoint.
- The enclosing resume helper then failed at **04:45:26** in `account()` → `export()` → read `after/receipt.json`; the saved pane is `V3/autoresume_deaths/rl4cv-e13v3-retry-B-1301-u23_10-22-2026_045002.log`. The last buffered run-log messages happen to be model/optimizer loading. They do **not** show an out-of-memory failure, signal termination or disk-write failure. The successful stage exit and explicit zero-update result identify the actual failure.
- Subsequent ticks classify any `result.json` as `account_then_launch`, reserve an attempt, and hit the same missing receipt. At **10:40:06, 10:50:06 and 11:00:06**, all three reservations fail this way. These are bookkeeping failures, not three new training runs. At 11:10 and later the counter is exhausted.

**Freeing disk alone: no.** It removes a later startup gate but does not repair `lake`, cached unresolved scores, checkpoint classification or the exhausted counter.

### A_1301, B_1302 and P_1301 — latest three reserved attempts

The following is the last completed three-reservation cycle at the diagnostic snapshot; “restart” is separated from an actual launched process.

| Trajectory / update | Reservation 1 | Reservation 2 | Reservation 3 | Disk alone sufficient? |
|---|---|---|---|---|
| A_1301 / 18 | **10:40:02 launch**; pilot dies **11:13:50**, all rewards missing | **11:20:02 optimizer retry**; stage exits 0 in **241.007 s**, produces `UNMEASURED`, then helper dies **11:24:37** on missing receipt | **11:30:07 accounting error** on the same missing receipt; no new training stage | **No:** 256/256 missing-`lake` scores, stale unresolved scoring, receipt bug, counter cap |
| B_1302 / 13 | **10:40:07 accounting error** on missing receipt | **10:50:06 same** | **11:00:07 same** | **No:** same 256/256 missing-`lake` scores and receipt bug; counter cap |
| P_1301 / 23 | **10:40:07 launch**, death **10:43:35**: guard cannot read `/proc/2087485/environ` | **10:50:07 archive-empty-and-launch**, death **10:51:09**: `/proc/2401274/environ` | **11:00:07 archive-empty-and-launch**, death **11:04:06**: `/proc/3701664/environ` | **No:** all three fail device ownership checks before generating anything; need an uncontested device and a retry slot as well as headroom |

For the **last three actual process starts**, A_1301’s sequence was 09:00:03 (disk gate at 09:00:04), 10:40:02 (missing scores), 11:20:02 (zero-update result → missing receipt). Its 09:00 dead pane is `...pilot-A-1301_10-22-2026_091002.log`.

B_1302’s last three actual starts were **02:50:03** (pilot dies 04:33:14, all rewards missing), **04:40:02** (optimizer aborts 04:42:27 on `PermissionError: /proc/2010017/environ`), and **06:40:07** (stage exits 0 in **297.812 s**, `UNMEASURED`, then helper dies 06:45:41 on missing receipt). Evidence: `V3/pilot/B_1302/update_00013/update_failed_permission_10-19-2026/run.log`, `update/execution.json`, `update/output/result.json`, and the 04:40, 04:50 and 06:50 saved panes.

P_1301’s three generation logs are respectively:

- `V3/pilot/P_1301/update_00023_infrastructure_10-19-2026_5/generate/run.log`
- `V3/pilot/P_1301/update_00023_infrastructure_10-19-2026_6/generate/run.log`
- `V3/pilot/P_1301/update_00023/generate/run.log`

All report `PermissionError` at `device_guard.py:31`, before engine work. The historical foreign process owners cannot be reconstructed from the dead PIDs alone; their names are **unresolved**. Current process inventory independently confirms eth127, truongvo and alexspan activity, including eth127’s use of Brando’s shared Python environment. No foreign process was accessed beyond read-only public process metadata or altered.

### Why `lake` disappeared; why disk is an additional blocker

The live cron sets `PATH=/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/bin:/usr/local/bin:/usr/bin:/bin`. It also sets `BASH_ENV`, but that variable is not evidence that a Python process or a `/bin/sh` cron command sourced it. The resume helper’s launch commands prepend the wrapper directory to inherited `$PATH`; the scoring subprocess inherits this environment.

`/lfs/skampere1/0/brando9/.elan/bin/lake` **exists**, while `/usr/local/bin/lake` does not. The selected `PATH` read from live P_1302 process **3962183** also lacks `.elan/bin`; no other environment values were printed. This supports an environment propagation failure, not a missing installation. P_1302 is at risk of the same scoring failure, but it was left untouched and is not claimed to have failed.

At **12:10:15**, `df -B1 /lfs/skampere1/0` measured **172,667,674,624 available bytes = 160.81 GiB**. `pilot_run.py:145–146` requires **200 GiB** before creating a fresh update directory: a **39.19 GiB** shortfall then. This checks new opportunities; the optimizer-retry helper does not repeat that disk gate. Hence “every v3 update refuses” is too broad: retries can run below the threshold, and availability fluctuated during the morning. Ray’s “over 95% full” notices are warnings, not proof of the specific crashes.

`/lfs/skampere1/0/brando9/rl4cv_e13v4/e13v3_periodic_reset.py` plus `37 */2 * * *` cron verifies the two-hour reset. It skips paused A_1302 but resets every other exhausted trajectory. The 12:10 snapshot had counters 3 at A_1301/18, B_1301/23, B_1302/13 and P_1301/23.

### Protected trajectories

- **P_1302:** process **3962183**, started 07:24:02, verified alive; 13 complete updates at inspection, latest complete state `update_00013/update/output/after/`. “Alive” is not a claim that optimizer computation was happening at the instant sampled. No action taken.
- **A_1302:** explicitly listed in `autoresume_paused.json` under V4-A3; six complete updates, latest `update_00006/update/output/after/`. It remains paused.

## 2. v4 T1 probe and its A4 cap

Live root `V4=/lfs/skampere1/0/brando9/rl4cv_e13v4`; deployed admission digest starts **9209a408**. `watchdog.log` still reports `STOP_A4_CAP`, `attempts: 3`, `status: DIAGNOSE`, ending at `run/T1/probe/attempt_04`.

| Attempt | Start → failure recorded (10-21-2026 PDT) | Device refusals before engine start | Consuming failure |
|---|---|---:|---|
| 02 | 20:19:20 → 21:04:34 | 2 | trial_0003: `TypeError`, function not serializable |
| 03 | 21:10:40 → 21:23:34 | 0 | trial_0001: identical `TypeError` |
| 04 | 21:30:42 → 23:41:58 | 8 | trial_0009: identical `TypeError` |

All three have `engine_started.json`, **zero generated responses**, `optimizer_started: false`, `statistics_started: false`, and `consumed_a4_attempt: true` in their zero-effect evidence. Their terminal `worker_failed.json` and `run.log` point to `expt_v4/phase2/generation_runtime.py:36`:

```python
backend = engine.collective_rpc(worker_backend)
```

vLLM **0.10.0** routes that Python function through its message encoder, which rejects it with:

```text
TypeError: Object of type <class 'function'> is not serializableSet VLLM_ALLOW_INSECURE_SERIALIZATION=1 to allow fallback to pickle-based serialization.
```

This is a deterministic remote-procedure-call serialization incompatibility, after engine creation and before generation, not disk exhaustion or the token-certification threshold. The installed source confirms the guard in `.../vllm/v1/serial_utils.py:125–128`. The three consumed attempts are genuine engine-started failures; pre-engine lease refusals merely delayed them.

Attempt 01 is a retained **pre-engine lease refusal**, explicitly exempted by dispatch 8, and does not consume the cap. I rehashed all **108** files bound by the four `zero_effect_evidence.json` records (5 + 25 + 11 + 67): **0 mismatches**. No generation or optimizer result was inferred from worker chat. The last lease end records `RELEASED` at **23:41:58**, with **0.017434 device-hours**; a surviving lease file’s original `ACTIVE` field does not override its end receipt. `impl8_codex.log` was last modified at **19:33** and its final completion output precedes these failures.

**Options and recommendation:**

- **Recommended:** keep the stop, stage a v4-owned worker extension exposing the sampler check as a **named worker method**, and pass that method’s string name to `collective_rpc`. Installed `worker/worker_base.py` supports `worker_extension_cls`; the public method accepts string names. A prospective implementation must preserve the same sampler verification and pinned version and test actual serialization, not only a stubbed engine. This is an implementation recommendation, not an executed or validated v4 fix.
- **Smaller alternative:** explicitly enable the reported pickle-serialization option only in the trusted local worker execution environment, verify the same sampler check and rebind the admission. This changes the transport configuration; it is not silently enabled here.
- **After either technical fix:** Brando decides whether to authorize a new admission/amendment and attempt allowance. `PROTOCOL.md:84` and `phase2/recovery.py:35–36` cap consuming attempts at three. Preserve all three failed attempts and zero-effect receipts. Re-admission must not erase the history or disguise the exhausted cap.
- **Leave stopped:** scientifically valid if Brando chooses not to spend another attempt. Raising the cap or freeing disk without the serialization fix has no evidence of benefit.

## 3. Ranked disk-recovery menu — nothing deleted or moved

Survey at approximately **12:12–12:17 PDT**, with leaf-policy sizes measured before report creation. Exact byte counts and timestamped protected-state inspection are in [the evidence record](DIAGNOSIS_evidence_10-22-2026.json); command outputs remain in `/lfs/skampere1/0/brando9/rl4cv_e13v3/diag_10-22-2026/evidence/`.

The ranking balances reclaimable bytes against preserved outputs. Entries are **disjoint policy payload directories**, not entire experiment folders; retain surrounding `training_info.json`, `config.yaml`, data-loader state, reports and logs. Native policy directories contain weights, optimizer and associated recovery state. `step_{82,164,497}` below means those three exact directories, excluding **334 and 658**. All paths are beneath `/lfs/skampere1/0/brando9`.

| Rank | Exact candidate path(s) | GB | GiB | What deletion loses; disposition |
|---:|---|---:|---:|---|
| 1 | `rl4cv_e08/ckpt/14B/checkpoints/step_{82,164,497}/policy` | **531.75** | **495.23** | Exact native resume at three earlier 14-billion-parameter checkpoints and binary replay provenance. Corresponding Hugging Face exports remain for inference/evaluation; halfway and final native states remain. **Owner decision required.** |
| 2 | `rl4cv_e08/ckpt/8B/checkpoints/step_{82,164,497}/policy` | **294.94** | **274.68** | Same loss for 8-billion-parameter checkpoints. Preserve all exports plus steps 334 and 658. **Owner decision required.** |
| 3 | `rl4cv_e08/ckpt/4B/checkpoints/step_{82,164,497}/policy` | **149.54** | **139.27** | Same loss for 4-billion-parameter checkpoints; does not touch the protected exported `hf/step_658` start policy. **Owner decision required.** |
| 4 | `rl4cv_e08/layout_probe_10-09-2026/checkpoints/tmp_step_2/policy` | **126.45** | **117.77** | Incomplete state of a rejected layout probe; loses binary forensic reproduction of that failed probe, not a successful production resume. `semantic_stop.json` explicitly records scientific rejection and the retained partial checkpoint. **Lowest-impact, operationally safe-now candidate under the observed inventory**, retaining the surrounding diagnostic evidence. |
| 5 | `rl4cv_e08/ckpt/1.7B/checkpoints/step_{82,164,497}/policy` | **65.73** | **61.22** | Same earlier exact-resume loss for 1.7-billion-parameter models. Keep exports and halfway/final native states. **Owner decision required.** |
| | **Top-five total** | **1,168.41** | **1,088.16** | **1,168,405,454,848 allocated bytes**, before concurrent disk growth. |

These policy payloads belong to `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/`. No readable process command, working directory, mapped file, open descriptor or current cron entry identified a consumer of the candidate payloads. The earlier native policies have **zero hardlinked regular files**, so the listed size is not a duplicate-hardlink saving. The corresponding exported checkpoint directories exist; exported tensors were not reloaded or comprehensively rehashed. Evaluation can still require original native states for exact continuation studies, which is why the large production candidates require an owner decision.

**Minimum/goal choices:** two 14B policies, `step_82/policy` and `step_164/policy`, total **354.50 GB (330.15 GiB)** and exceed the 300 GB request. Adding `step_497/policy` makes **531.75 GB**, exceeding 500 GB. Adding the rejected probe instead to the two-policy option yields **480.95 GB**, below the 500 GB goal. The rejected probe plus all three 14B policies yields **658.20 GB**. No 300 GB “unconditionally safe now” set is certified without accepting some owner-specific loss.

**Safety limit of the inventory:** 1,950 processes were enumerated; 5,861 `/proc` probes were unavailable, predominantly permission restrictions and process races across working-directory, executable, descriptor and mapping probes. Other users’ private process state was not bypassed. No observed reference is therefore not proof that a remote or private consumer cannot exist. Recheck consumers immediately before any later deletion. Here “safe-now candidate” means rejected, inactive diagnostic state with no observed live dependency, not authorization or a guarantee against concurrent changes.

### Large areas deliberately not offered for blanket deletion

| Area | Measured size | Why retain / whose decision |
|---|---:|---|
| `rl4cv_e08/sft_v3` | **915.82 GB** | **Keep.** Live `resume_e14_after_oom.py` process 2991617 reads configurations and controls continuation; this entire workflow is excluded from the recovery menu. |
| `rl4cv_e08/nemo_rl` (including `.venv`) | **23.65 GB** | **Keep.** v3, v4 and eth127’s processes use the environment. Observed eth127 process 59531 and evaluator 557584 reference its interpreter. |
| `rl4cv_e08/ckpt/4B/hf/step_658` | **17.66 GB** | **Keep.** Explicitly protected supervised-fine-tuned start policy; v3 logs load it. |
| `.cache/huggingface` | **1,790.58 GB** | Owner/use audit needed per model/dataset; offline jobs can reopen cached files between stages. Re-downloadability does not make it safe for a running job. No blanket deletion. |
| `data` | **1,402.74 GB** | Training/evaluation inputs; manifest and consumer audit unresolved. No blanket deletion. |
| `unified-training-pilot-10-04-2026` | **229.16 GB** | Separate experiment provenance and recovery ownership not established; owner decision required. Not included in savings. |
| `valkyrie_legacy_bucket_mirror_10-14-2026` | **139.37 GB** | Legacy raw-result/provenance mirror; remote recoverability not verified. Owner decision required. |
| `rl4cv_e13v2` | **182.28 GB** | v3 imports and cron’s `PYTHONPATH` reference this tree; preserve bound technical inputs and runtime dependencies. |
| `rl4cv_e13v3/phase2/technical` | **117.58 GB** | Frozen gate evidence and checkpoint provenance; do not remove on an “old checkpoint” heuristic. |

The broad top-level scan reported approximately **9.15 TB** under Brando’s tree, but exited 1 with **4,554 unreadable-path errors**. Treat that broad inventory as incomplete, not a precise filesystem reconciliation. Focused experiment-08, v3 and candidate-policy scans completed successfully. Counts use allocated blocks; directory totals can differ between scans because of live writes and hardlink accounting. These are not file-system snapshots.

### Each newest complete v3 `after/` state stays

Under `V3/pilot/`, preserve at least these states **and every file referenced by a live stage**, including the associated current exports:

| Trajectory | Latest complete update | Required retained relative path |
|---|---:|---|
| A_1301 | 17 | `A_1301/update_00017/update/output/after/` |
| A_1302 | 6 | `A_1302/update_00006/update/output/after/` |
| B_1301 | 22 | `B_1301/update_00022/update/output/after/` |
| B_1302 | 12 | `B_1302/update_00012/update/output/after/` |
| P_1301 | 22 | `P_1301/update_00022/update/output/after/` |
| P_1302 | 13 | `P_1302/update_00013/update/output/after/` |

All six receipts parsed; **78/78 bound files** existed with the recorded byte sizes, **0 missing/size-mismatched**. Receipt digests were recorded. Full tensor content hashes were not reread; this establishes presence/size, not a new cryptographic validation of roughly 300 GB of states. P_1302 may advance, so a later deletion must recompute its newest complete state. No v3 pilot payload is included in the top-five menu.

## 4. Staged resume fix — not activated

Branch: `e13v3-resume-missing-receipt-fix-10-22-2026`.
Worktree: `/lfs/skampere1/0/brando9/rl4cv_e13v3/diag_10-22-2026/wt`.
Base: `8f3f6e30` from `origin/main`; live checkout stayed on `94215e67` with its existing dirty/untracked files untouched. The three relevant runner/helper source hashes matched between live files and the branch before editing.

- `autoresume_watchdog.py`: only route to accounting when **both** result and `after/receipt.json` exist. A dead partial with retained generations/scores but no after receipt routes to the existing optimizer retry instead of repeatedly attempting export.
- `resume_pilot_after_foreign_gpu.py`: use the same completion condition in direct accounting, optimizer retry and partial discovery. Read the predecessor summary and require its checkpoint receipt before parking any failed output. Retry from that predecessor’s exported model and native checkpoint, preserving all existing generations and scores. Park a stale export as well so it cannot be attached to a newly retried optimizer result.
- The supervisor’s existing durable `reserve_attempt()` remains the only retry-slot reservation in the watchdog path. Each scheduled retry consumes **one** slot; three failures stop without accounting a fictitious update. Already exhausted live counters are **not** reset by this patch. The external two-hour reset still exists and is not changed.
- A receipt’s presence is the routing prerequisite, not a replacement for the existing export/restore integrity verification. A malformed receipt does not become a fabricated success. If the immediately preceding completed state is missing, the helper diagnoses rather than silently skipping back farther and changing the update lineage.
- `pilot_run.py`, admitted scientific settings, bound training code, the v4 code, cron, pause records, leases and counter files were not edited. The worktree is deliberately retained because the user requested staged review and prohibited deletion/moves.

**Material deployment limitation:** the three live `UNMEASURED` cases have cached all-missing scores. Applying only this patch would schedule bounded retries of those same unusable scores, not repair the run. Correct the environment and separately recover identical-cell scoring under its provenance rules before expecting training progress; never delete scored/generation history or fabricate zero rewards. Activation also needs the owner to reconcile the existing exhausted retry budget, rather than this patch granting more attempts.

### Verification and publication

- Focused existing v3 suite plus new regression tests: **97 passed**, 0 failures, 0 skips, CPU only. The regression cases cover both `MEASURED`-looking and `UNMEASURED` result files without a receipt, exactly three persisted reservations across five ticks, previous-complete-state replay, retained generations/failed evidence, stale-export isolation, missing predecessor refusal, and normal completed-state accounting. Existing tests cover live/paused trajectory and probe-error refusals.
- Repository `make test`: **1,405 passed, 15 skipped, 6 existing warnings, 0 failures, 382.95 seconds**.
- Tests use a private temporary directory under `/lfs`, empty `CUDA_VISIBLE_DEVICES`, offline model loading and disabled Python bytecode writes to shared packages. External dependencies are read through new symlinks in the isolated worktree; the shared environments were not installed into or modified.
- Diff/secret inspection and `git diff --check`: **passed**.
- Publication: **Push succeeded** to `e13v3-resume-missing-receipt-fix-10-22-2026`; implementation commit `9d9b97eaa581a7cf017b563d71d7e06bfffde4a9` matched the remote branch. The final documentation head is recorded in `diag_10-22-2026/publication_receipt.json`. No merge and no live activation.

Raw verification logs: `diag_10-22-2026/evidence/tests_v3.log` and `evidence/make_test.log`. The code diff, regression test, this report and the compact evidence record are committed together. The report has a byte-identical copy at `diag_10-22-2026/DIAGNOSIS_stuck_runs_10-22-2026.md` after finalization.

## Scope and unresolved items

No GPU computation, training, extra model call, live-file edit, live data deletion/move, cron edit, counter/lease edit, restart, stop or kill was performed by this diagnosis. Existing tests exercise mocked orchestration and their own temporary fixtures; none invokes the live watchdog entry point. Final read-only verification at **12:26:28 PDT** confirmed unchanged live runner/helper hashes and crontab, unchanged A_1302 pause record, and live P_1302 PID 3962183. Available disk was **171,903,381,504 bytes (160.10 GiB)**. The shared repository’s Git metadata was used only to fetch and create/publish the requested worktree/branch. Existing unrelated modifications were preserved.

Unresolved: owner approval to sacrifice earlier exact-resume checkpoints; foreign/remote private consumers beyond the readable inventory; actual recovery of cached scoring failures; v4 prospective transport implementation and Brando’s re-admission decision; full tensor-content rehashes. No scientific result or successful continuation is claimed. The requested Markdown files are the deliverables; no live Google document or external notification was changed.

Report assembled: **10-22-2026 12:23:32 PDT**. Verification finalized at **10-22-2026 12:24:52 PDT**.
