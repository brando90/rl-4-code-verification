# Experiment 13 v2: the single requested light review and its resolution

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/REVIEW_v2.md>

**TLDR:** Brando requested one light review ("codexd ultra astra gpt6 light qa"). Codex GPT-6 Astra (effort ultra) reviewed the version 2 plan at `3ae1d0b` and returned FAIL: 3 critical, 9 major and 1 minor finding. All 13 are fixed in the binding plan (revision 2), the owner runbook and one test file. The implementation-level fixes are verified at gates R0 and R1. There is no automatic re-review.

## Review identity

| Field | Value |
|---|---|
| Builder | Claude Code `claude-opus-5-5` (master session "Oct 9: IRT for eval metric decomposition") |
| Reviewer | Codex CLI 0.162.1, model `gpt-6-astra`, reasoning effort `ultra`, sandbox `danger-full-access`, approval `never`, session `01a13675-179a-7410-a356-3b5bba3e4f7a` |
| Role and classification | Acceptance; **critical** (evaluation/scoring integrity), so the strongest opposite-company model was required and used |
| Reviewed commit | `3ae1d0b9a7c83d5a7489a6ef992393a9fb7aad5b` (draft plan, runbook, checkpoint); read-only brief; no reviewed file changed |
| Run | 10-13-2026 11:10:05 → 11:21:46 PDT, exit 0, on Brando's Mac |
| Reviewer's own checks | 23/23 pure contract tests passed; in-memory reproduction of the cap, unparseable-type, served-status and vacuity-overflow branches; pinned Lean integration suite not executed |

## Verbatim review

Everything between the markers is the reviewer's final message exactly as written to `--output-last-message`. It was copied by script, not retyped (sha256 `65f04bacfa80acfad11a97e7bc0ffb07bbec5ffa95c92e70246429758cd3d442`).

<!-- BEGIN VERBATIM CODEX REVIEW -->
**FAIL.** The version 2 plan reintroduces strict-scoring defects fixed in version 1 and does not preserve the required measurement chronology and test-data isolation.

Reviewed commit `3ae1d0b9a7c83d5a7489a6ef992393a9fb7aad5b`, experiment `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`. Below, experiment-local paths are relative to that folder; historical scorer filenames refer to experiment 08’s `expt_v1/scripts/`.

1. **CRITICAL — The scoring contract cannot reproduce the historical oracle.**  
   Evidence: [PLAN.md:35–49](/Users/brandomiranda/vb_worktrees/rl4cv-e13v2-plan-10-13-2026/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/PLAN.md:35), `src/rl4cv/rewards.py:37–55`, `analyze_ladder.py:81–95`, and `score_teacher_files.py:257–294`.

   The proposed product of extraction, declaration cleanliness, implementation/example cleanliness, proof fraction, vacuity and theorem presence is **not** the historical strict predicate:

   | Edge case | Historical behavior | Contract discrepancy |
   |---|---|---|
   | Valid extracted file reaching the token cap | Can score **1**; `truncated` is not used by `reward_kernel_binary` | PLAN forces zero and defines extraction to exclude capped outputs |
   | Actually truncated, non-compiling file | **0** when historically scored | Correct zero, but because compilation fails—not because the cap flag is set |
   | Unparseable theorem type; otherwise passing file | Ladder: **0**. Teacher readback: **None** | PLAN promises zero everywhere; these historical branches differ |
   | Unparseable theorem type; compilation or another strict requirement already fails | **0** in both readbacks | Correct zero; version 1’s unconditional exception was unnecessarily broad |
   | Valid implementation and theorem, **no example** | **0** | Product lacks an explicit example-presence guard; implementation cleanliness can still be true |
   | Top-level command fails outside declaration spans | **0** | Clean declaration fractions do not establish whole-file compilation |
   | Whole-file compilation succeeds but frozen kernel probe rejects | **0**, including the reviewed printed-`error:` fixture | Successful component checks cannot replace official post-probe status |
   | Empty extraction | Known ladder cell: **0**. Teacher without a scorer row: **0** only for a served empty response; otherwise **None** | A universal extraction-zero rule loses measurement status |
   | No theorem | **0** | The theorem-presence guard correctly covers this case |
   | Vacuity | **0** if either historical theorem-type or file-pattern screen hits | `v` must preserve both screens exactly; see finding 2 for count overflow |
   | `sorry`, `admit`, `native_decide`, or declared axiom in a named theorem’s dependency cone | **0** | Correct only with complete kernel dependency evidence and all stated theorems retained |
   | `native_decide` in an example, or an unused declared axiom | Does not automatically fail an otherwise valid file | A file-wide forbidden-token rule would change the oracle |
   | Ladder `known=False` | `kernel_binary=None`, even with source present | Existing source does not imply a measured historical label |
   | Teacher `served=False` | Without a row: **None**. With a row: numeric scoring still runs, while `failure_class` remains `unmeasured` | Scalar value and measurement status must remain distinct |
   | Multiple Lean blocks | Score the source selected by the pinned extractor | The component formula does not specify selection; concatenating blocks or choosing a passing block changes the result |

   Multiple-block selection is specified in pinned `single_call.py:132–162`: labelled blocks take precedence; otherwise one target uses the longest eligible block. `src/rl4cv/veribench/exp103.py:93–100` applies that extraction and path resolution.

   **Fix:** Preserve a source-specific legacy oracle returning its original value **and status**, separately from experimental components. Remove the asserted product identity and automatic cap zero. Make R0 compare against the actual frozen readbacks, including their `None` branches.

2. **MAJOR — The root-cause inventory and diagnostic sample miss an executable rejection path.**  
   Evidence: `PLAN.md:5,24–31,85–87`; `opaque_base_audit.py:229–241`; `declaration_adapter.py:144–150`; `src/rl4cv/e13.py:47–50`; `score_teacher_files.py:217–227`.

   One theorem, `theorem t : True := by trivial`, produces **two** historical pattern hits. The adapter passes `vacuous_count=2`, `theorem_count=1` into `PartialCredit`, which raises `ValueError("theorem counts inconsistent")`. The audit catches that as `source_or_pinned_probe_rejected`. I reproduced this without Lean execution.

   Moreover, rerunning only the declaration adapter misses the audit’s preceding vacuity check—the very unparseable-type exception named as root cause. Missing/malformed parser output, module-loading errors and source errors also cannot all be called malformed submissions. Their historical frequencies remain unknown.

   **Fix:** Wrap the complete per-cell audit path, including vacuity and `PartialCredit` construction. Preserve raw screen-hit counts separately from distinct-theorem counts. Replace the blanket causal claim with the verified exception inventory; assign frequencies only after the correctly instrumented diagnostic.

3. **CRITICAL — The diagnostic procedure can unseal test outcomes.**  
   Evidence: `PLAN.md:85–97,101`; `cc.md:39`; `PROTOCOL.md:24–28`.

   The 21,504-cell base population includes train, validation **and test** tasks. Sampling from its entire rejection/measured ledger therefore permits test cells into a diagnostic process that examines exceptions, per-declaration status and mismatches, then changes the adapter. Avoiding *stored* factor values does not prevent newly computed outcomes or diagnostics from exposing test information.

   **Fix:** Restrict development diagnostics to a frozen train/validation allowlist. Run test equality in the separate opaque process required by the protocol, exposing only permitted completeness/hash/equality receipts. A test discrepancy blocks admission; inspecting it requires the prescribed chronology amendment and loss of the original untouched-test claim.

4. **CRITICAL — F0v2 is frozen after its outcomes have already been computed.**  
   Evidence: `PLAN.md:85–113`; `cc.md:34–40`; `PROTOCOL.md:13–20`; `CLAUDE.md:40–43`.

   The diagnostic sample and full reproduction compute the new factors before Phase 0v2-d appends F0v2. The reproduction includes the validation outputs used by G0. There is also no explicit new L1 measurement lock or F1 successor binding the changed adapter, model implementation, folds and configuration.

   Reusing the **numerical predictions** from version 1 is legitimate if their history is retained and the new binding precedes relevant outcome exposure. Reusing their old timestamps as prospective registration of a changed measurement procedure is not.

   **Fix:** Freeze the version 2 measurement contract, complete implementation hashes, manifests, folds, F0 and F1 before historical factor execution. Record information already observed. Post-diagnostic amendments must disclose exposure and cannot retroactively restore an untouched prospective gate.

5. **MAJOR — The proposed reuse does not provide the promised partial-credit evidence.**  
   Evidence: `PLAN.md:37–58,68–80`; `declaration_adapter.py:126–149`; pinned `run_real_eval.py:179–219`; pinned `kernel_axioms.py:316–328,487–518`.

   The adapter attributes declaration errors using a compiler log capped at 4,000 characters. Errors omitted from its middle can leave failed declarations marked clean. The pinned kernel probe runs its inspector only after successful compilation; failed files receive unresolved theorem classifications, not the surviving proofs shown by the separate inline `#print axioms` demonstration.

   Consequently, strict equality can pass while the experimental fractions are wrong. Retaining only the last 4 KB of **stderr** is particularly inadequate because Lean diagnostics appear on **stdout**.

   **Fix:** Require an elaborator-backed diagnostic channel that observes the unchanged source, preserves complete command diagnostics and dependency evidence after failures, and retains unresolved stated obligations in denominators. Store full raw evidence privately. Add fixtures asserting actual partial fractions, including errors beyond the log cap and a failed proof followed by a valid theorem.

6. **MAJOR — Phase 1’s rollout schedule omits required anchors and restores an admission-order conflict.**  
   Evidence: `PLAN.md:130–134,145–152`; `cc.md:47–58`; `PROTOCOL.md:18,68–72,103`.

   Two batches from the full-schedule checkpoint do not supply the required three-policy train anchor panel: Base, 50%-supervised-fine-tuning and 100%-supervised-fine-tuning. The plan also places these batches before the pilot resource/probability admission later listed in Phase 2, and does not place F2 between calibration batch 1 and independent batch 2.

   **Fix:** Explicitly inventory reusable compatible Base receipts, supply the missing 50% train anchor, and budget every required generation. Put the bounded resource/probability admission before rollout generation; freeze F2 and calibration before batch 2. The stated 539-task train scope itself respects decision D-013.

7. **MAJOR — “Stop the chain” conflicts with the reviewed arm-specific decisions.**  
   Evidence: `PLAN.md:64,120–153,188`; `cc.md:12`; `PROTOCOL.md:119`; `expt_v1/PHASE1_IRT_PLAN.md:17`.

   A failed G1, independent-batch gate H2, or arm-C variance check should disable **C**, while eligible A/B/P reinforcement-learning comparisons continue. The binding plan instead requires every preceding phase to pass and describes the first failed gate as a terminal outcome.

   **Fix:** Add an explicit transition table distinguishing global technical failures from arm-specific exclusions. Preserve eligible A/B/P execution after C fails.

8. **MAJOR — Phase 1b has no protected fitting/evaluation boundary.**  
   Evidence: `PLAN.md:136–141`; `cc.md:52`; experiment 10 `PROTOCOL.md:48,94–99`.

   Fitting on experiment 07’s component matrix and evaluating on experiment 10’s pairs can reuse the same systems and task outcomes. Calling the analysis secondary and leaving experiment 10’s protocol unchanged does not prevent this leakage.

   **Fix:** Freeze a separate Phase 1b protocol specifying the promotion statistic, calibration information, task/system partitions, missingness and uncertainty. Candidate/incumbent evaluation outcomes must not fit their own forecasts. Any use of held-out-task outcomes from reference systems must be explicitly defined and kept disjoint from the evaluated systems, as in the relevant experiment 14 design. D-013 is VeriBench-specific; this analysis needs its own separation contract.

9. **MAJOR — Forty-eight Lean workers have no enforceable memory budget.**  
   Evidence: `PLAN.md:102–103`; `cc.md:41`; `declaration_adapter.py:56–58`; pinned `run_real_eval.py:205–210` and `kernel_axioms.py:298–302`.

   The plan gives node capacity and wall-clock limits, but no measured peak memory per worker, aggregate memory allocation or process-tree limits. A load snapshot cannot prevent a later node-wide out-of-memory event affecting other owners. The old processing rate also includes rejected cells that skipped later work, so it is not a sound throughput baseline for repaired scoring.

   **Fix:** Measure peak resident memory and complete-cell costs under bounded admission, derive concurrency from available headroom, and enforce an aggregate allocation covering child processes. Re-estimate runtime from the repaired pipeline.

10. **MAJOR — The proposed device-admission route is not executable for experiment 13.**  
    Evidence: `PLAN.md:162`; `cc.md:47–50,59`; experiment 08 `gpu_lease_e08.py:26–30,207,346–357`.

    The referenced lease interface accepts only owner `e09`, applies experiment 09’s limits and writes inside experiment 08’s work root. Using its default would misattribute ownership and budget. Separately, “no other user’s process” plus low utilization does not exclude another experiment running under Brando’s account or an idle reserved device.

    **Fix:** Specify a valid experiment-13 allocation route with distinct ownership/accounting and coordinated reservations. Check all processes and leases, including same-user owners. Preserve the borrowed environment read-only; use owned installation, cache, temporary-output and diagnostic paths.

11. **MAJOR — Watchdog recovery lacks the ownership and retry fencing needed for one writer.**  
    Evidence: `PLAN.md:168–178`; `cc.md:30,66`; experiment 08 `watchdog_e08.sh:23–39,48–63`.

    A missing terminal session does not prove its scientific children have exited. Concurrent cron/master recovery can also race unless they share a lock. “Once per incident” is not the same as the scientific one-retry allowance: the reference watchdog resets recovery markers after reboot.

    **Fix:** Require a shared recovery lock, run-bound process identity checks, adoption of surviving children, and persistent per-cell attempt/budget accounting across reboots and account changes. Test concurrent recovery and orphaned children, not only a dead pane. If adapting the reference self-test, replace its hard-coded `wd-selftest-e08` kill target with an owned unique session; no version 2 kill implementation exists yet to verify.

12. **MAJOR — The seven environment-dependent tests need conditional admission.**  
    Evidence: `PLAN.md:81`; `tests/test_e13_declaration_adapter.py:20–27,30–60`.

    These seven parametrized cases hard-code cluster fixture, scorer and Lean-project paths and have no skip guard. All three paths are absent on this Mac.

    **Fix:** Resolve explicit configurable paths, following the project’s `VERIBENCH_ROOT` convention where applicable, and skip with a precise prerequisite explanation when the integration environment is absent. Do not skip merely because the host is macOS. The pinned Stanford Network Analysis Project run must require those prerequisites and execute the integration cases; local skips cannot count as passing R0’s Lean acceptance.

13. **MINOR — The imported experiment 14 statistic loses its uncertainty scope.**  
    Evidence: `PLAN.md:138`; `CKPT_e13_v2.md:23`; experiment 14 `results.md:45–47,62`.

    The numbers match the source, but `n_A=50` is the observed-task count per split, not the study denominator. The summary omits 164 systems × 424 tasks, 2,000 splits, the system-bootstrap method, fixed-fit conditioning and reported p-value.

    **Fix:** Link the result and retain those qualifications. It supports a historical forecasting result, not established transfer to Lean or the new promotion model.

The gate interpretation should also be explicit:

- **R0/R1 are not currently achievable under all stated requirements**, because the proposed contract contradicts retained historical fixtures and readback semantics.
- **R2 requires complete equality, not merely 100% equality among whichever cells measured.** Under `PLAN.md:64`, **INCOMPLETE cannot advance to G0**. It is an unresolved technical measurement result, not evidence against the scientific hypothesis.
- An identical-cell retry is appropriate; **exactly one** is a new bounded policy, not a number mandated by `CLAUDE.md`. Missing/replaced sources are integrity defects, and deterministic resource-limit failures need distinct classification from transient infrastructure failures.
- The union arithmetic is correct: **38,784 unique available cells**, with the parent ladder’s **5,400 unavailable cells** retained separately.
- G0’s inherited definition is usable once scoring and chronology are repaired: at least **21/135** dense-only tasks, and the specified area-under-the-receiver-operating-curve threshold on the zero-success earlier-rung subset. Undefined one-class discrimination fails admission.
- For the diagnostic cause table, rejected-population shares use the **300 rejected samples**, not the combined 400. G0/G1 retain grouped-task intervals; Phase 2 retains paired-seed/task-group uncertainty and full-manifest bounds. Formal specification coverage remains on the validated Valkyrie route.

Verification: **23/23** existing pure contract tests passed; in-memory checks reproduced the cap, unparseable-type, served-status and vacuity-overflow branches. The pinned Lean integration suite was not executed. No reviewed files changed.

VERDICT: FAIL
CRITICAL_ISSUES: 3
MAJOR_ISSUES: 9
FIXES_APPLIED: 0
STRUCTURAL: SKIP
SUMMARY: Version 2 is not ready for dispatch: its strict contract is inconsistent with historical scoring, and its diagnostic sequence risks test leakage and retrospective forecasts. Repair those contracts and the identified execution prerequisites before measurement.

<!-- END VERBATIM CODEX REVIEW -->

## Resolution

| # | Severity | Finding | Fix | Where |
|---|---|---|---|---|
| 1 | CRITICAL | The component product is not the historical strict predicate (cap, unparseable types, no example, top-level failures, kernel-probe rejection, empty extraction, `known`/`served`, multiple blocks) | Strict now comes **only** from the frozen historical oracle per source family (value and status), with pinned extraction and cap semantics. Components are separate experimental measurements. Consistency is a typed diagnostic, not a definition. Each listed edge case is an R0 fixture | PLAN §§ 2a–2c, 4 (R0) |
| 2 | MAJOR | Missed rejection path (vacuity overflow → `PartialCredit` `ValueError`); the diagnostic wrapped only the adapter | Verified rejection inventory, with frequencies unknown until diagnosed. The R1 wrapper covers the complete version 1 path. Raw screen hits are kept separate from distinct vacuous theorems; overflow is a fixture | PLAN §§ 1, 2b, 4 |
| 3 | CRITICAL | The diagnostic sample could include test cells | Development and R1 use a frozen **train-split allowlist** only. Test cells run only in the opaque process. A test discrepancy blocks admission and needs a chronology amendment | PLAN §§ 3, 4 |
| 4 | CRITICAL | F0v2 was frozen after factor outcomes were computed | **L1v2** freezes the contract, hashes, manifests, folds, F0v2 and F1v2 **before** any validation or test factor execution. Version 1's numeric predictions are carried with their history, without claiming their old timestamps. Information already observed is recorded | PLAN § 3 |
| 5 | MAJOR | Reused evidence channel: 4,000-character log cap, stderr-only, no kernel inspection after failed compiles | New elaborator-backed probe: complete per-command messages (stdout and stderr), axioms after failures, unresolved obligations in denominators, private raw evidence. Fixtures for an error beyond the cap and for a failed proof followed by a valid theorem | PLAN § 2b, R0 |
| 6 | MAJOR | Phase 1 lacked the three-policy anchor panel; admission order; F2 placement | LP-1 generation admission first. Anchors: Base (reused only if exactly compatible), 50% and 100% SFT. Calibration and F2 frozen before independent batch 2 | PLAN § 5 |
| 7 | MAJOR | "Stop the chain" contradicted arm-specific rules | Transition table: G1, H2 or arm-C failures disable C only; A, B and P continue | PLAN § 4 |
| 8 | MAJOR | Phase 1b had no fitting/evaluation boundary | Separate `PHASE1B_PROTOCOL.md` frozen before execution. Item parameters only from other folds' systems, as in experiment 14. Off the critical path | PLAN § 5 |
| 9 | MAJOR | No memory budget for 48 Lean workers | Peak memory measured during R1. Concurrency from headroom (cap 48), `prlimit` per worker, an aggregate scope cap or headroom semaphore, owned process-group kills only. Runtime re-estimated | PLAN § 7 |
| 10 | MAJOR | Experiment 08's lease route is unusable (owner `e09` only) | Experiment-13-owned lease registry. Checks all processes, including same-user ones, and the leases of experiments 08, 09, 12 and 14. Owned caches and paths | PLAN § 7 |
| 11 | MAJOR | Watchdog lacked one-writer fencing | Shared `flock`, run-bound identities (PID, start time, boot ID), adoption of children, persistent per-cell attempt ledger, owned kill-test session, concurrent and orphan tests | PLAN § 7, runbook § 0 |
| 12 | MAJOR | Seven environment-dependent tests had no skip guard | `tests/test_e13_declaration_adapter.py`: `E13_*` path variables; a skip with a precise reason when prerequisites are absent; `E13_REQUIRE_LEAN_INTEGRATION=1` makes absence an error. Mac: 269 passed, 35 skipped, 0 failed; with the flag, absence raises | test file; PLAN R0 |
| 13 | MINOR | Experiment 14's statistic lost its scope | Full scope stated: 164 × 424, 2,000 splits, n_A = 50, system-cluster bootstrap, p-val 0.001, fixed-fit conditioning; not evidence of transfer to Lean | PLAN § 5 |

The reviewer's gate interpretations are adopted:

- INCOMPLETE cannot advance to G0.
- One identical retry is a stated bounded policy.
- Integrity defects and deterministic limits are distinct from transient faults.
- The G0 threshold is at least 21 of 135, and a one-class AUC fails.
- Cause-table shares use the 300 rejected cells.

```
VERDICT: FIXED
CRITICAL_ISSUES: 0
MAJOR_ISSUES: 0
FIXES_APPLIED: 13
STRUCTURAL: IMPROVED
SUMMARY: All 3 critical and 9 major findings are fixed in plan revision 2, the runbook and the adapter test guard; implementation-level fixes are verified at R0/R1 before any measurement, and no automatic re-review was run.
```
