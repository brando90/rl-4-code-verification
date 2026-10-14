# Experiment 13 v2 amendment A3 (PROPOSED): rule-based R2 diagnosis and admission with bounded exceptions

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md>

**TLDR:** R2 failed under Amendment A2 ([RESULTS_R2.md](RESULTS_R2.md)). On the ordinary route, 4 of 33,243 measured cells disagree with the historical oracle value (36,477/36,481 readbacks equal), and 45 cells stay unresolved against a ceiling of 33. The opaque route passed.

A3 proposes how the 49 ordinary cells are diagnosed and when G0 may be admitted. Its classification rules are committed here **before any per-cell diagnosis is read**, so that admission follows rules, not outcomes.

**Status:** PROPOSED. Not in force until the experiment's current coordinator adopts it. On 10-14-2026 that is the ultracode master, `CKPT_MASTER_oct14-cc-rl4cv-master-ultracode-progress.md`.

**Disclosure:** written after the R2 FAIL was published, and before the diagnosis of its 49 ordinary cells.

Created: 10-14-2026 12:58 PDT by the version 2 master (Claude Code `claude-opus-5-5`, session "Oct 9: IRT for eval metric decomposition").

## Why

Revision 2 and A2 made R2 the measurement-fidelity admission check. It is not a test of the hypothesis. Three facts bear on it:

- **Fidelity is near-complete:** value equality on 36,477 of 36,481 readbacks, status equality on all of them, and opaque equality PASS.
- **Downstream does not use these cells:** Phase 2's strict reward and its test evaluation score **new** outputs with the frozen official scorer.
- **The forecasts are untouched:** F0v2 and F1v2 were frozen at L1v2, before any validation factor was computed, and G0 has not been run.

A permanent stop over 49 of 38,784 cells (0.13%) leaves the hypothesis untested. An admission with diagnosed causes and worst-case bounds is the standard an ML venue would accept, provided it is disclosed.

## Rules (fixed before the diagnosis is read)

1. **Diagnose all 49 ordinary cells** (4 unequal, 45 unresolved) privately: train and validation only, no test cell. Use the retained evidence:
   - phase reached;
   - exit codes and signals;
   - elapsed time against each frozen limit;
   - complete Lean messages;
   - extraction and vacuity paths;
   - the historical record.

   Publish a cause table with counts only. Historical strict values are already public; component values of these cells are not published.
2. **Classify each cell by these rules, in order:**

   | Class | Rule | Treatment |
   |---|---|---|
   | (a) Timing or resource dependent | Elapsed time within 10% of a frozen limit, a timeout signal, or an out-of-memory kill, in either the historical or the version 2 run | Becomes a typed resource limit (listed). Allowed, as under A2 |
   | (b) Deterministic pipeline defect | The version 2 oracle path differs from the historical code path for a reproducible reason: extraction selection, vacuity, status mapping, source handling | Fix the code. Verify that the fix reproduces the historical value on every cell of that defect class and still passes all 30 R0 fixtures and all 400 R1 cells. Re-measure only cells selected by the defect-class rule, never by outcome. The fix applies to all later measurement |
   | (c) Historical-record irreproducibility | The historical record cannot be reproduced by the historical code itself in the pinned environment | Listed exception |
   | (d) Unknown | None of the above | Stays unresolved; see rule 3 |
3. **Admission to G0.** All of these must hold:
   - (i) each of the 4 unequal cells is in class (a), (b) after a verified fix, or (c);
   - (ii) every class (a) and (c) cell, and every class (d) unresolved cell, is excluded from the G0 and G1 data;
   - (iii) the excluded cells are listed by ID, and each G0 and G1 statistic is reported with its full-manifest worst-case bounds over them;
   - (iv) the opaque PASS stands.

   **If any of the 4 unequal cells is class (d), R2 FAIL stands and version 2 stops.** This replaces A2's 0.1% unresolved ceiling with exclusion plus worst-case bounds, as rl4cv's missing-cell rule already requires.
4. **G0 and later gates are unchanged.** They are never retried, and a statistic whose verdict flips within its worst-case bounds is reported as INCONCLUSIVE.

## Notes for the coordinator

- **Crontab incident (10-13 21:20 PDT).** The current skampere1 crontab equals `state/crontab_before_e13v2.txt` line for line (verified 10-14 12:55 PDT). Experiment 13's own watchdog lines are retired, so re-arm them **additively** if work resumes. Never replace the whole crontab.
- **Phase 2 is blocked on Valkyrie.** Its FSC test evaluation needs the validated Valkyrie judge, and that route has returned HTTP 403 since 10-13 03:27 PDT (issue #68).
