# Experiment 13 v2 plan: a scorer that measures every output, then the original gates, through RL to completion

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/PLAN.md>

**TLDR:** Version 1's historical audit ended BLOCKED: it measured only 6,739 of 21,504 cells. The other 14,764 were rejected by its own design: any Lean parse error or unparseable theorem statement raised an exception, which was caught without a diagnosis, while the original strict score simply counts such files as failures.

Version 2 is the separately authorized prospective condition that version 1's closeout requires (Brando, 10-13-2026: "Try again", continuing his 10-09 request to plan, take one light review and run to completion). It has three parts:

1. A scorer that measures every output, scoring malformed, cut-off and non-compiling files as failures with partial credit.
2. Full diagnostics for every cell.
3. The original reviewed gates and phases, from G0 through the Phase 2 RL comparison.

Created: 10-13-2026 by Claude Code (`claude-opus-5-5`, master session "Oct 9: IRT for eval metric decomposition") for Brando. Status: PLANNED; nothing launched.

## 1. What version 1 established and why it stopped

| Fact | Evidence |
|---|---|
| Design reviewed once (GPT-6 Astra, ultra), 11 findings reconciled; protocol, Phase 1 and Phase 2 plans are reusable | `../expt_v1/REVIEW.md`, `../PROTOCOL.md`, `../expt_v1/PHASE1_IRT_PLAN.md`, `../expt_v1/PHASE2_MATCHED_RL_PLAN.md` |
| 20,520 ladder and 21,504 base-model source hashes match; 15 authored strict controls reconciled; 30 adapter fixtures passed | `../expt_v1/results.md`, `../expt_v1/PHASE0_CONTROLS_RESULT.json` |
| Historical audit: 21,504 accounted, **6,739 measured, 14,765 unmeasured** (14,764 `source_or_pinned_probe_rejected`, 1 reboot interruption); exited BLOCKED 10-11-2026 23:15 PDT | `../expt_v1/RESULTS_opaque_audit_terminal.md` |
| Forecasts F0 and F1 were frozen before any factor outcome was read; no factor value was disclosed | `../expt_v1/locks/forecast_ledger.jsonl` |

**Root cause, from the code** (`../expt_v1/opaque_base_audit.py`, `../expt_v1/declaration_adapter.py`):

1. **Unparseable theorem statement.** The audit raises `AuditError("unparseable theorem type")` whenever the frozen vacuity screen cannot parse a theorem type. The original strict score did not reject these files: experiment 08's `analyze_ladder.py` (lines 91–92) sets `kernel_binary` to 0 when it would otherwise be 1, "conservative for a policy gate".
2. **Parse errors.** `_probe` raises `AdapterError` when the Lean parser helper exits nonzero, or when its terminal event reports `parse_error` ("parser errors are terminal, not guessed around"). Malformed and truncated files are exactly the failures a partial-credit scorer must measure.
3. **Identity disagreements.** An invalid command span, a duplicate declaration name, or a mismatch between kernel and parser theorem identities raises `AdapterError`. Non-compiling files, which elaborate with errors, plausibly reach these branches.
4. **Diagnostics discarded.** One `except (AdapterError, AuditError, OSError, UnicodeError, ValueError)` writes the single class `source_or_pinned_probe_rejected` and drops the phase, message, return code and logs. This is why the cause per cell cannot now be assigned.

Items 1–3 are code paths, not per-cell findings. Section 3's diagnostic sample assigns causes with evidence before any full rerun.

## 2. Scoring contract for version 2

- **Measured means a recorded outcome, never a skip.** Every cell whose source exists gets a measured strict value and measured component values. A file that does not parse, truncates, fails to compile, has an unparseable theorem statement, or has no theorem is a measured failure:
  - strict is 0;
  - components carry whatever partial credit Lean's per-command results support;
  - a component with no evidence is 0, with a reason code.
- **Only infrastructure faults are unmeasured.** A probe timeout, out-of-memory kill, missing or replaced source, tool crash or reboot leaves a cell unmeasured. It keeps a typed reason code and full receipts, and gets exactly one identical retry, as rl4cv's rules require. Unmeasured cells stay in the denominator.
- **Strict is the historical definition, byte for byte.** It reuses the pinned scorer and vacuity screen behind the historical `kernel_binary`, including the rule that an unparseable theorem type cannot count as a pass. The new per-declaration components must imply that same strict value: `e · 1[d = 1] · t · 1[p = 1] · v · 1[n_thm ≥ 1]`.
- **Components** keep the definitions in `../PROTOCOL.md` § 3:
  - `e`: Lean extracted and not cut off.
  - `d`: fraction of top-level declarations that elaborate without an error message. A parse-error region counts as one failed declaration; commands after the parser recovers are still counted.
  - `t`: implementation and `example`s elaborate.
  - `p`: fraction of stated theorems whose axioms are within {`propext`, `Classical.choice`, `Quot.sound`}. Lean v4.22.0 reports per-theorem axioms after a failed proof (`../design_evidence/lean_partial_credit_probe_output.txt`).
- **Identity disagreements are logged, not fatal.**
  - `p` uses kernel theorem identities; `d` uses parser command spans.
  - Disagreements are recorded per cell.
  - The strict-consistency check below decides whether one matters.
- **Full diagnostics per cell**, in a private receipt:
  - phase reached;
  - exception class and message;
  - return codes;
  - the last 4 KB of standard error;
  - parser terminal event;
  - per-declaration status;
  - timings;
  - source hash.

  Public files carry counts, reason-code tallies and hashes only, as in version 1.

## 3. Phases, gates and decision rules

Each phase starts only when the previous one passes. A gate failure stops the chain and is reported with its evidence, never retried until it passes.

### Phase 0v2-a — scorer fix and fixtures (CPU, no model calls)

1. **Implement** `expt_v2/declaration_adapter_v2.py` and, if needed, `expt_v2/DeclarationProbe_v2.lean`, from the version 1 code, with the contract in § 2. Keep version 1's files byte-identical.
2. **Fixtures.** Keep version 1's 30 fixtures, plus at least these:
   - a parse error mid-file, with later declarations;
   - a file truncated mid-proof;
   - an unparseable theorem statement in a file that compiles, and one in a file that does not;
   - a duplicate declaration name;
   - a theorem inside a namespace with a failing earlier declaration;
   - an empty extraction;
   - a file with no theorem;
   - `sorry` and `native_decide` in a theorem;
   - a 15-minute timeout simulation.

   Each fixture has an independently written expected strict value, component values and reason code.
3. **Gate R0:** every fixture matches; `make test` passes; version 1's tests still pass.

### Phase 0v2-b — diagnostic sample (CPU)

1. From version 1's private result ledger, draw a seeded uniform sample of 300 cells among the 14,764 rejected ones and 100 among the 6,739 measured ones, without reading any stored strict or factor value.
2. Run the version 1 adapter with diagnostics switched on, using a wrapper that records the exception and changes nothing else.
3. Run the version 2 adapter on the same 400 cells.
4. Publish:
   - a cause table (counts per root-cause branch), with 95% Wilson intervals for each branch's share among the rejected population;
   - version 2's measured share;
   - its strict-consistency share on the 400.
5. **Gate R1:**
   - version 2 measures all 400, apart from infrastructure faults that pass on their one retry;
   - its strict value equals the historical `kernel_binary` on every measured cell;
   - any cause branch above 1% of the sample is explained by a fixture.

   If a mismatch appears, fix the definition through a numbered amendment before the full run. The full run never tunes on outcomes.

### Phase 0v2-c — full strict reproduction (CPU)

1. **Manifest:** the union of experiment 05's 21,504 base cells and experiment 08's 20,520 available ladder cells. The overlap is 3,240, giving **38,784 unique cells**; the parent ladder's 5,400 missing cells stay listed as missing.
2. **Parallelism:** 48 worker processes on skampere1 (128 cores, about 2 TiB of memory), checked against current load before launch. The pinned Lean v4.22.0, Mathlib copy and limits are 900 s parse, 600 s compile and 900 s kernel.
3. **Expected wall clock:** about 2 hours. Version 1 ran one process at about 7.5 cells per minute. The real rate is recorded after the first 500 cells.
4. **Gate R2:**
   - every cell is measured, or unmeasured only for infrastructure after one identical retry;
   - unmeasured cells number 0, or the gate reports INCOMPLETE with their list;
   - the version 2 strict value equals the historical `kernel_binary` on **100%** of measured cells.

   Any mismatch fails R2 and is diagnosed before G0.

### Phase 0v2-d — gate G0 (CPU)

Before measuring, append F0v2 to the forecast ledger with the same value as version 1's F0 (0.50), bound to the version 2 adapter hash. Then measure G0 exactly as `../PROTOCOL.md` § 3 defines it, on validation outputs:

- dense-only share for the 4B full-schedule checkpoint, threshold ≥ 0.15;
- predictive validity from the 50% rung to the 100% rung, AUC ≥ 0.65 for 4B.

If G0 fails, arms B and C stop (README decision rules).

### Phase 1 — interpretable model and gate G1

Follow `../expt_v1/PHASE1_IRT_PLAN.md` and `../PROTOCOL.md` § 4 as reviewed:

- grouped folds;
- conditional hurdle likelihood;
- M0, M1, M2, M3 and M3e on identical outer-held-out cells;
- convergence, sensitivity and simulation recovery;
- G1 report with bias, absolute error and intervals.

**Train-split rollout batches** (H2 and arm C anchors):

- two independent batches from `sft_4B_f1p0`, 539 tasks × 8 samples each, with the Phase 2 sampler;
- self-hosted vLLM on one device (D-101);
- about 43 million generated tokens in total, roughly 2–3 device-hours on an A100, H200 or B200.

**Phase 1b, SWE-bench model for AlphaHebe:**

- Experiment `14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems` already shows a 2PL ability forecast beats half-A pass@1 on level: mean absolute error (MAE) 0.0344 vs 0.0554 at n_A = 50, a difference of +0.0210 [+0.0195, +0.0224].
- Phase 1b fits the conjunctive model to experiment 07's components (gate, T_fix, T_keep → resolved).
- It scores an IRT promotion gate on experiment 10's incumbent → candidate pairs as a secondary analysis.
- Experiment 10's protocol locked on 10-09-2026 (revision 3), so this does not change it.

### Phase 2 — matched RL comparison

Follow `../expt_v1/PHASE2_MATCHED_RL_PLAN.md` and `../PROTOCOL.md` §§ 5–8 as reviewed:

- LP pilot manifest and resource lock;
- T1 probability check;
- T2–T3 update, refit and resume;
- T4 measured cost;
- T5 learning pilot;
- L2 main lock;
- four arms (A strict, B SCSC-style, C IRT-guided, P placebo) × 3 paired seeds, at matched cumulative generated-token thresholds;
- validation selection, then one test evaluation;
- FSC on test outputs through the validated Valkyrie judge (D-102, D-108).

**Device budget:**

- The 260–350 A100-hour figure is an estimate.
- T4 replaces it with measured cost before L2.
- On SNAP the plan is recorded in the checkpoint rather than asked (Trigger Rule 51 pre-approval).
- Devices come only from idle GPUs, checked with `nvidia-smi` and kept clear of other users, or through experiment 08's lease interface. No device held by another owner is used.

## 4. Owners, accounts and supervision

- **Master:** this Claude Code session on the Mac (Rule 55). It writes plans, dispatches, verifies, publishes and reports; it never runs the experiment.
- **Phase owner:**
  - One SNAP worker on skampere1, the single writer for version 2, in tmux `codex-rl4cv-e13v2-owner`.
  - Codex `gpt-6-astra`, effort `high`, full access (`codex --sandbox danger-full-access --ask-for-approval never`), with the verbatim SNAP pre-approval line.
  - Fallback under Rule 48 if that account is limited: Claude Code `claude-fable-5-1` `high` (`clauded`), then Claude Code on the Vals profile (`clauded-vals`).
  - On 10-12-2026, Codex-Vals was at its usage limit and the Stanford Codex account was read-only (experiment 14's record); the personal Codex account ran experiment 14's review.
- **Watchdog (no model calls):**
  - `expt_v2/watchdog_e13v2.sh` in the skampere1 crontab every 15 minutes, plus `@reboot`.
  - It checks the owner's tmux pane and processes, progress freshness, disk headroom, and done or blocked markers.
  - It relaunches a dead loop at most once per incident.
  - It emails `brando.science@gmail.com` only on completion or on an event that needs Brando, deduplicated.
  - It removes its own cron line when every phase is done or blocked. This is modeled on experiment 08's `watchdog_e08.sh`.
- **Master check-in:** hourly from this session while it is open. Each check-in reads the receipts, confirms the watchdog and dispatches the next phase. The watchdog does not depend on it.

## 5. Completion, publication and reporting

- **Results.** `expt_v2/results.md` is live from launch. Each phase publishes its report and sanitized receipts; private receipts stay under `/lfs/skampere1/0/brando9/rl4cv_e13v2/`.
- **Publishing.** Commits go to `main` after `make test`, with explicit pathspecs.
- **Done means all of these:**
  - Phase 2's test analysis is published, with the primary contrasts B − A and C − A, the placebo contrasts, guards and full denominators;
  - experiment 13's README and the experiments index are updated;
  - one completion email has been sent.
- **Stopping early.** A failed gate earlier in the chain is a valid stopping point. It is reported as that gate's result, with what it means for the hypothesis.

## 6. Timeline and risks

| Phase | Estimate | Main risk |
|---|---|---|
| 0v2-a, b | about 1 day | A cause branch with no fixture → amendment |
| 0v2-c, d | about 3 hours of compute | Strict mismatch on a definition edge case |
| 1 | 1–2 days | Identification with few policies; device time for the two rollout batches |
| 2 | Pilot about 1 day; main 3–6 days | Free devices; trainer passing T1 (experiment 09 failed it); Lean scoring throughput inside the RL loop |

The master cannot reach SNAP from an off-campus network without the Stanford virtual private network (VPN). Brando connects it, or works from campus, for the master's check-ins and dispatch. The SNAP-side owner and watchdog do not depend on the Mac.
