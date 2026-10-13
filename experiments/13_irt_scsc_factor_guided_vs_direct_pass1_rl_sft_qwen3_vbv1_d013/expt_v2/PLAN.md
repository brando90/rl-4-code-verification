# Experiment 13 v2 plan (revision 2): measure every output, keep the historical strict oracle, protect chronology, then run the reviewed gates through RL

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/PLAN.md>

**TLDR:** Version 1's historical audit ended BLOCKED: 6,739 of 21,504 cells measured, 14,764 rejected by its exception handling, causes not retained. Version 2 is the separately authorized prospective condition that version 1's closeout requires (Brando, 10-13-2026: "Try again", continuing his 10-09 request: plan, one light review, run to completion).

Revision 2 applies the single requested review (Codex GPT-6 Astra, ultra, 10-13-2026; `REVIEW_v2.md`: FAIL, 3 critical and 9 major findings, all fixed here). It makes six changes:

1. Strict comes only from the historical oracle, value and status, never from the new components.
2. Development diagnostics use train-split cells only.
3. The version 2 measurement lock and forecasts are frozen before any validation or test factor is computed.
4. Partial credit comes from an elaborator-backed probe that keeps complete diagnostics.
5. Arm-specific failures disable only that arm.
6. Memory, devices and recovery have enforceable limits.

Created: 10-13-2026 by Claude Code (`claude-opus-5-5`, master session "Oct 9: IRT for eval metric decomposition"). Revision 2: 10-13-2026. Status: PLANNED; nothing launched.

## 1. What version 1 established, and its verified rejection paths

| Fact | Evidence |
|---|---|
| Design reviewed once (GPT-6 Astra, ultra), 11 findings reconciled; protocol and the Phase 1 and Phase 2 plans are reusable | `../expt_v1/REVIEW.md`, `../PROTOCOL.md`, `../expt_v1/PHASE1_IRT_PLAN.md`, `../expt_v1/PHASE2_MATCHED_RL_PLAN.md` |
| Source hashes: 20,520 ladder and 21,504 base-model sources match; 15 authored strict controls reconciled; 30 adapter fixtures passed on skampere1 | `../expt_v1/results.md`, `../expt_v1/PHASE0_CONTROLS_RESULT.json` |
| Historical audit: 21,504 accounted, **6,739 measured, 14,765 unmeasured** (14,764 `source_or_pinned_probe_rejected`, 1 reboot interruption) | `../expt_v1/RESULTS_opaque_audit_terminal.md` |
| Forecasts F0 and F1 were frozen on 10-10-2026, before any factor outcome was published | `../expt_v1/locks/forecast_ledger.jsonl` |

**Code paths that end in the generic rejection class.** These are a verified inventory, not per-cell causes; cause frequencies are unknown until the instrumented diagnostic in § 4.

1. **Vacuity screen.** `opaque_base_audit.py` raises `AuditError("unparseable theorem type")` before the adapter runs.
2. **Parser.** `declaration_adapter._probe` raises on a nonzero parser exit, non-JSON output, or a terminal `parse_error`.
3. **Identity checks.** Invalid command spans, duplicate fully qualified names, and kernel/parser theorem-identity disagreement each raise.
4. **Count overflow** (found by the review and reproduced without Lean). `theorem t : True := by trivial` yields two historical vacuity pattern hits for one theorem. `PartialCredit` then raises `ValueError("theorem counts inconsistent")`.
5. **Loading and environment.** Module loading, pinned-module errors, source, hash and encoding errors also raise. A rejection is therefore not necessarily a malformed submission.
6. **One catch-all.** A single `except` maps all of these to one class and discards phase, message, return codes and logs.

## 2. Measurement contract

### 2a. Strict is the historical oracle, value and status

Version 2 never derives strict from components. For each source family it calls the frozen historical code path, returning the historical **value** and **status**:

| Family | Historical oracle | Status semantics kept |
|---|---|---|
| Experiment 08 ladder | `analyze_ladder.py` | `known=False` → `None`. An unparseable theorem type turns 1 into 0. Example presence, vacuity, frozen kernel probe and the pinned extractor apply |
| Experiment 05 base cells | Experiment 05's recorded scorer path, as bound in version 1's sealed manifest | As recorded |

Teacher files (`score_teacher_files.py`) are not in the manifest. If any are ever added, their `served`/`None` semantics are kept.

The oracle's own rules carry over unchanged:

- **Extraction:** pinned `single_call.py` selection. Labelled blocks first; otherwise the longest eligible block for one target.
- **Cap:** a capped but valid file may score 1, because the cap flag is not part of `reward_kernel_binary`.
- **Exceptions:** `native_decide` in an `example` and an unused declared axiom do not fail a file. A `sorry`, `admit`, `native_decide` or declared axiom in a stated theorem's dependency cone does.
- **Probe rejection:** a kernel-probe rejection after a successful compile is 0, as in the reviewed printed-`error:` fixture.

### 2b. Components are experimental measurements

Components come from a new **elaborator-backed probe**, `expt_v2/DeclarationProbe_v2.lean` with `declaration_adapter_v2.py`. It runs Lean's frontend command by command on the unchanged source, with these properties:

- **Complete messages.** It records the full message list per command: no 4,000-character cap, with stdout and stderr both captured.
- **Recovery.** It continues past parse and elaboration errors.
- **Axioms after failure.** It reads each stated theorem's axioms from the final environment, including after earlier failures.
- **Denominators.** Unresolved stated obligations stay in the denominators.
- **Raw evidence.** Full raw evidence is stored privately per cell.

The components are those of `../PROTOCOL.md` § 3:

| Component | Definition |
|---|---|
| `e` | Extraction present |
| `d` | Fraction of top-level commands that elaborate without error; a parse-error region counts as one failed command |
| `t` | Implementation and examples elaborate; **at least one `example` present** |
| `p` | Proved-theorem fraction over stated theorems |

Guards keep **raw vacuity screen hits separate from distinct vacuous theorems** (fixing path 4), plus the stated-theorem count. Cap status is a recorded covariate. It is not a component factor, so it never forces a zero.

### 2c. Consistency is a diagnostic, not a definition

For every measured cell, record these, and report each with its count and full denominator:

- whether `strict = 1` implies every component is at its maximum;
- whether all components at maximum with `strict = 0` falls in a typed branch:
  - kernel-probe rejection;
  - a top-level non-declaration failure;
  - vacuity;
  - no example;
  - extraction-selection difference.

An untyped inconsistency fails R1 or R2.

### 2d. Status classes

| Class | Meaning | Retry |
|---|---|---|
| Measured | Oracle value and status reproduced, components recorded | — |
| Transient infrastructure | Reboot, killed tool, lost node | One identical retry (a bounded policy stated here, not a `CLAUDE.md` number); still missing afterwards → INCOMPLETE |
| Deterministic resource limit | Reproducible timeout or memory ceiling at the frozen limits | No retry; reported per cell |
| Integrity defect | Missing, replaced or re-encoded source | Blocks the gate |

## 3. Chronology and data isolation

1. **Development set.** Train-split cells only: experiment 05's base-model cells on the 539 train tasks, 3 models × 8 samples, about 12,936 cells. The allowlist is frozen by cell ID from D-013's split manifest. All adapter development, fixtures from real data, and the § 4 diagnostic sample come from it. No validation or test cell is executed during development.
2. **L1v2 measurement lock**, appended to `expt_v2/locks/` before any validation or test factor is computed. It freezes:
   - the measurement contract (§ 2);
   - adapter, probe and oracle implementation hashes;
   - complete manifests and grouped folds;
   - the model and fit configuration for Phase 1;
   - **F0v2 and F1v2**.

   F0v2 and F1v2 carry the numeric predictions of version 1's F0 and F1, with that history recorded, bound to the version 2 hashes. Version 1's timestamps are not claimed as prospective registration of the changed procedure.
3. **Information already observed.**
   - Version 1 computed private equality results for 6,739 base cells. No per-cell value, factor or comparison was published, and the master has read none.
   - The design evidence used published experiment 08 validation aggregates, before version 1's F0 lock.
   - Both facts are recorded in L1v2.
4. **Validation reproduction and G0** run in the ordinary harness, after L1v2.
5. **Test cells** (base cells on the 222 test tasks) run only in a separate opaque process. It exposes completeness, hashes and the equality status, nothing else.
   - A test discrepancy blocks admission.
   - Inspecting it needs a numbered chronology amendment that gives up the untouched-test claim.

## 4. Phases, gates and transitions

### R0 — fixtures (skampere1, pinned Lean; integration tests required, never skipped)

The fixtures are version 1's 30 plus these:

- a valid file at the token cap (oracle 1);
- a printed-`error:` kernel rejection after a successful compile (0);
- no `example` (0);
- `native_decide` in an `example` only (unchanged);
- multiple Lean blocks (pinned selection);
- the `True := by trivial` vacuity overflow;
- an error beyond 4,000 characters of log;
- a failed proof followed by a valid theorem (asserts the actual partial `p` and `d`);
- a top-level non-declaration failure;
- `known=False` and `None` status;
- an unparseable theorem type in a compiling file and in a non-compiling one.

Each fixture has an independently written expected oracle value and status, components and reason code.

**Gate R0:** every fixture matches; the full suite passes with `E13_REQUIRE_LEAN_INTEGRATION=1`, so the adapter integration cases run.

### R1 — instrumented diagnostic on the train-split allowlist

- **Sample.** A seeded sample of 300 cells from version 1's rejected train-split cells, and 100 from its measured train-split cells, drawn by cell ID only. If fewer exist, take all.
- **Version 1 wrapped.** The **complete** version 1 per-cell path (vacuity, adapter and `PartialCredit`) runs inside a wrapper that records phase and exception and changes nothing else.
- **Version 2.** The version 2 pipeline runs on the same cells.
- **Report.** The cause table uses Wilson 95% intervals on the **300 rejected** cells as denominator. Version 2's measured share and its consistency diagnostics are reported alongside.
- **Gate R1:**
  - every cell measured, except typed classes;
  - oracle value and status reproduced on every measured cell;
  - no untyped inconsistency;
  - every cause branch above 1% covered by a fixture.

  Fixes go in before L1v2. After L1v2, a fix requires a numbered amendment.

### L1v2 lock (§ 3)

### R2 — full reproduction

- **Manifest:** experiment 05's 21,504 base cells ∪ experiment 08's 20,520 available ladder cells = **38,784 unique cells**. The parent ladder's 5,400 unavailable cells stay listed separately.
- **Routing:** train and validation cells run in the ordinary harness; test cells run in the opaque process.
- **Gate R2:** a **complete** reproduction of oracle value and status on all 38,784, except typed deterministic-limit cells listed with reasons.
  - **INCOMPLETE does not advance to G0.** It is an unresolved technical measurement, not evidence about the hypothesis.

### G0 — on validation outputs, after R2

Per `../PROTOCOL.md` § 3:

- dense-only tasks for the 4B full-schedule checkpoint ≥ 0.15 × 135, i.e. **at least 21 of 135**;
- predictive validity on the zero-success subset of the 50% rung: AUC ≥ 0.65. If the subset contains only one class, the AUC is undefined and G0 fails admission.

### Transition table

| Event | Effect |
|---|---|
| R0, R1 or R2 fails or is INCOMPLETE; integrity defect | Stop downstream measurement; publish the failure with evidence |
| G0 fails | Stop arms B and C (README rule); Phase 2 is not run, since A against P alone does not test the hypothesis |
| G1 fails, H2 fails, or arm C's variance check fails | Disable **arm C only**; A, B and P continue to Phase 2 |
| T1–T4 fail | Stop Phase 2 at that gate; publish |
| T5 fails | One preregistered horizon extension, per the reviewed plan; then stop |
| A test discrepancy in the opaque process | Block test-based admission; chronology amendment required to inspect |

## 5. Phase 1 — interpretable model, G1 and H2

Phase 1 follows `../expt_v1/PHASE1_IRT_PLAN.md` and `../PROTOCOL.md` § 4. The ordering is fixed:

1. **LP-1:** a bounded resource and probability admission for **generation only**. It covers device route (§ 7), sampler, probability agreement on a probe batch and token caps.
2. **Anchor panel for arm C**, three connected policies on the 539 train tasks with the Phase 2 sampler:
   - **Base:** reuse experiment 05's Qwen3-4B-Base train receipts only if their sampler and extraction match the Phase 2 sampler exactly; otherwise generate a new Base batch.
   - **50%:** generate a batch for `sft_4B_f0p5`.
   - **100%:** generate batch 1 for `sft_4B_f1p0`.
3. **Freeze** the calibration, item parameters and **F2** in the locks folder.
4. **Batch 2**, independent, for `sft_4B_f1p0`: the H2 test.

Each batch is 539 × 8 samples, about 21.6 million generated tokens, roughly 1–1.5 device-hours on one A100, H200 or B200 with vLLM (D-101). Up to four batches total about 4–6 device-hours, and the master records each one's device plan in the checkpoint.

G1 is reported with bias, absolute error and intervals on grouped folds, as reviewed.

### Phase 1b — SWE-bench promotion gate (optional, not on the critical path)

This is a separate protocol, `expt_v2/PHASE1B_PROTOCOL.md`, frozen before any execution. It specifies:

- the promotion statistic;
- information used;
- task and system partitions;
- missingness and uncertainty.

Item parameters come only from systems in other folds, as in experiment `14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems`. Candidate and incumbent outcomes never fit their own forecasts.

Experiment 14 supports the premise; its result (`../../14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/results.md`):

- **Setup:** 164 systems × 424 tasks, 2,000 splits, n_A = 50 observed tasks per split, fixed-fit conditioning.
- **Level:** the 2PL forecast has mean absolute error 0.0344 vs 0.0554, a difference of +0.0210 [+0.0195, +0.0224] (system-cluster bootstrap), p-val=0.001.
- **Rank:** small, and gone by n_A = 250.
- **Scope:** a historical SWE-bench forecasting result, not established transfer to Lean or to a promotion model.

Experiment 10's locked revision 3 stays unchanged.

## 6. Phase 2 — matched RL comparison

Phase 2 follows `../expt_v1/PHASE2_MATCHED_RL_PLAN.md` and `../PROTOCOL.md` §§ 5–8 as reviewed:

- sequence: LP → T1 → T2, T3 → T4 → T5 → L2;
- four arms (A, B, C and P, with C subject to the transition table) × 3 paired seeds;
- matched cumulative-token thresholds;
- validation selection, then one test evaluation;
- formal specification coverage (FSC) through the validated Valkyrie judge (D-102, D-108).

The 260–350 A100-hour figure stays an estimate until T4 measures it. On SNAP the plan is recorded in the checkpoint (Trigger Rule 51).

## 7. Execution safety

### Memory and concurrency

- **Measure first.** During R1, measure peak resident memory per complete cell, including the child processes of the frontend, compile and kernel probe.
- **Concurrency:** `floor(0.5 × available memory headroom / p99 peak)`, capped at 48, and lowered if other owners' load rises.
- **Enforce:** each cell runs in its own process group under `prlimit --as` with a per-worker cap. An aggregate `systemd-run --user --scope -p MemoryMax=` cap is used where the node supports it; otherwise a semaphore admits workers only while measured headroom stays above 25%.
- **Kill rule:** kill a process group only if it belongs to this run's receipts.
- **Runtime:** re-estimate from the repaired pipeline's measured complete-cell cost. Version 1's rate included early rejections.

### Device route

- **Own registry.** Version 2 uses an experiment-13-owned lease registry under `/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/`, with its own ownership and accounting. Experiment 08's `gpu_lease_e08.py` accepts only owner `e09`, so it is never used.
- **Before claiming a device**, check:
  - all compute processes, including Brando's own other experiments;
  - every other experiment's lease files: 08, 09, 12, 14;
  - reservations recorded by the rl4cv master (Codex thread `01a11d6a`).
- **Etiquette:** claim only idle, unreserved devices, and release them on exit.
- **Paths:** caches, temporary outputs and installs live under version 2's own work root. Borrowed environments are read-only.

### Supervision and one writer

The watchdog `expt_v2/watchdog_e13v2.sh` runs from cron every 15 minutes, plus `@reboot`. It:

- uses a shared recovery `flock` with the owner and the master;
- binds processes to their run by PID, start time and boot ID;
- adopts surviving children instead of relaunching over them;
- keeps a persistent per-cell attempt ledger across reboots and account changes, so the one-retry policy cannot reset;
- emails `brando.science@gmail.com` only on completion or on an event that needs Brando, deduplicated.

Its self-tests:

- a fake mailer;
- an owned unique test session for kill tests, never another experiment's;
- concurrent-recovery and orphaned-child cases.

## 8. Owners, accounts, completion, timeline

### Owners and accounts

- **Master:** this Claude Code session on the Mac (Rule 55).
- **Owner:** one SNAP worker on skampere1 in tmux `codex-rl4cv-e13v2-owner`, the single writer.
  - Codex `gpt-6-astra`, effort `high`, full access, with the verbatim SNAP pre-approval line.
  - Fallbacks under Rule 48: Claude Code `claude-fable-5-1` `high` (`clauded`), then the Vals profile.
  - On 10-12, Codex-Vals was at its limit and Stanford Codex was read-only (experiment 14's record).
- **Pre-dispatch check:** no live version 1 writer on skampere1 (CKPT § Coordination).

### Completion

Phase 2's test analysis is published:

- primary contrasts B − A and C − A, with C absent if disabled;
- placebo contrasts;
- guards and full denominators.

The README and the experiments index are updated, and one completion email is sent. Stopping at a gate under § 4's transition table is a valid, reported outcome.

### Timeline and risks

| Phase | Estimate | Main risk |
|---|---|---|
| R0, R1 | 1–2 days | Building the elaborator-backed probe; cause branches |
| L1v2, R2, G0 | About 1 day | Memory-bounded throughput; opaque test process |
| Phase 1 | 2–3 days | Anchor generation devices; identification |
| Phase 2 | Pilot about 1 day; main 3–6 days | Free devices; trainer T1 (experiment 09 failed it); Lean scoring throughput |

The master needs the Stanford VPN off campus. The SNAP owner and watchdog do not.
