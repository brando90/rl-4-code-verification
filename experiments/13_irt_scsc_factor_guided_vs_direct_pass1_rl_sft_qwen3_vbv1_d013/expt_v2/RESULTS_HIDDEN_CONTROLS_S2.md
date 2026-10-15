# Experiment 13 v2-S2 train hidden-test controls: PASS

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_HIDDEN_CONTROLS_S2.md>

**TLDR:** The single frozen train-only hidden-test control run passes all four admission criteria on 64 tasks from distinct train groups. All misses and incomplete applicability remain recorded. This admits the independent hidden-test route for the required train audit; it does not constitute that audit, an efficacy result or permission to skip the remaining Phase 1 and learning gates.

Measured 10-14-2026 after [the control freeze](phase2/HIDDEN_CONTROLS_S2.md) was published at `4b8efd4`. The [lock](locks/HIDDEN_CONTROLS_S2.json), SHA-256 `12181b9dd3b2001dca75f5d93f71cffbb0b19ff1ad5d858dce1fa141d7ce5553`, binds the private cohort, 708 tests, 585 prebuilt mutant candidates and unchanged corrected experiment-12 adapter. [Machine-readable result](phase2/hidden_controls_result.json).

| Control | Observed criterion satisfaction | Frozen requirement | Verdict |
|---|---:|---:|---|
| Gold against its own hidden tests | 697/708 tests, 98.45% | At least 98% applicable and passing | PASS |
| Consistently renamed gold | 60/63 eligible C1 all-passing tasks, 95.24% | At least 95% recovered with every test passing | PASS |
| First compiling implementation mutant | 54/61 compiling mutants killed, 88.52% | At least 50 compiling mutants and 60% killed | PASS |
| Cyclic wrong-task gold | 63/64 rejected or demonstrably failing, 98.44% | At least 95% | PASS |

All 64 task receipts completed. C1 has 697 evaluated tests, all passing, and **11 unevaluable tests on one task**; those 11 remain in the 708-test admission denominator. C2 has 62 fully applicable cells, one incomplete cell and one deterministic compile failure. Its measured tests include ten false results; recovery is assessed only within the 63 tasks that passed every C1 test, as frozen. No renamed source was repaired after observation.

C3 retains the three tasks with no frozen mutant candidate. Of 61 compiling mutants, 60 are fully applicable and one has 11 unevaluable tests. There are 54 demonstrated kills; the other seven are not counted as kills, including that incomplete case. The known-kill fraction is 54/61; allowing the one incomplete case either outcome gives [54/61, 55/61]. A passing hidden test never caused selection of another mutant. C4 has seven fully applicable and 57 incomplete mapping cells; unmapped wrong-task symbols are intended rejections, while type/bridge uncertainty alone cannot pass the control. One wrong-task control was not rejected or demonstrably failing and remains a miss.

No criterion, cohort, source, mapping rule or threshold changed during the run. These are fixed technical-control counts, with exact declared denominators, not population efficacy estimates; confidence intervals and p-values are not applicable (`p-val=n/a`). A route-control PASS does not establish immunity to gaming, semantic completeness of the gold tests, or hidden-test applicability for every later candidate. Later partially applicable candidates remain missing for all-tests-pass and are separately bounded.

The owned controller ran for 417.948 seconds through cleanup, with 585 bounded Lean invocations, zero model calls and zero graphics-device hours. Private artifacts occupy 36,977,993 bytes. This is controller wall time, not measured processor utilization. Cleanup verified that no marked child remained; no signal was needed. The watchdog's registered controller exited. The unchanged 16-line cron schedule still equals its recorded additive installation.

The [hosted formal-specification judge controls](RESULTS_COVERAGE_CONTROLS_S2.md) separately passed. Both routes still need the frozen train mutation audit and pilot-monitor inputs before learning. The anchor panel continues under v2-S2; no anchor score, actual-data fit, independent full batch 2 or experiment optimizer update has run at this report.

Publication verification: required Lean integration suite **731 passed, 3 skipped, zero failures in 446.40 seconds**, direct exit 0 ([receipt](phase2/mutation_ledger_publication_test.json)).
