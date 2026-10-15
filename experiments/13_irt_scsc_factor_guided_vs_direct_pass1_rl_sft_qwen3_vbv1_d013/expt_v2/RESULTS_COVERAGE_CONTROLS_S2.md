# Experiment 13 v2-S2 hosted coverage-judge controls: PASS

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_COVERAGE_CONTROLS_S2.md>

**TLDR:** The hosted validated judge route passes its frozen train-only controls: 50/50 ratings measured, complete request receipts, and both members meet every control threshold. This resolves the historical model-query access failure for this route; train mutation/coverage audits, Phase 1 and the learning gates remain required. No experiment optimizer update or test evaluation has run.

Measured 10-14-2026. The [original freeze](locks/COVERAGE_CONTROLS_S2.json) was published at `f59b423`; [registration successor](locks/COVERAGE_CONTROLS_S2_REGISTRATION1.json) at `1151dd6` preceded both judge admissions. The successor changes only the registration name's case after HTTP 422 occurred before any judge run. The original manifest, scientific settings and thresholds remain unchanged. [Provisioning evidence](phase2/COVERAGE_SERVICE_REGISTRATION_S2.md), [admissions](phase2/coverage_admission.json), [machine-readable result](phase2/coverage_controls_result.json).

Five train tasks each supplied five controls. GPT-6 Sol at high reasoning effort and Claude Opus 5.5 at maximum compute effort each rated every control once. The table gives the number satisfying the frozen rule out of five measured cases, separately for each member.

| Control | Frozen raw-score rule, scale 0–5 | Required count | GPT-6 Sol high | Opus 5.5 max |
|---|---|---:|---:|---:|
| Oracle | At least 4 | 5/5 (at least 90%) | 5/5 | 5/5 |
| Vacuous | At most 1 | 5/5 (at least 90%) | 5/5 | 5/5 |
| Blank | Exactly 0 | 5/5 (at least 90%) | 5/5 | 5/5 |
| Shuffled | At most 1 | 5/5 (at least 90%) | 5/5 | 5/5 |
| Half-deleted | Inclusive 1–4 | 4/5 (at least 80%) | 4/5 | 4/5 |

Each member gave one half-deleted case 5/5, outside its control range; that miss is retained and the precommitted 4/5 requirement is met exactly. The other extreme controls received oracle 5/5 and blank, vacuous and shuffled 0/5 throughout. No case, prompt or threshold was replaced after observing scores.

All 50 declared receipts were present exactly once, all 50 were measured, and all 50 verified their frozen request envelope, prompt hashes and no-fallback receipt. The actual hosted agent archives matched the frozen executable, setup and contract bytes. There were exactly 50 model-query attempts: one per rating, zero transient query retries. Provider-returned model/effort identity fields are not available in this validated bundle; this check verifies the pinned selectors and request/receipt contract, not an unavailable response identity field.

The reported model charges are $0.5906425 for GPT-6 Sol and $2.3933504 for Opus, total **$2.9839929**, with charges present for 50/50 ratings. Sandbox charges are unreported and are not assumed zero. The pre-disclosed conservative model estimate was $38.88518, or $77.77036 including the permitted transient retry. The existing Vals-managed route and task preapproval covered these runs; no personal provider credential or new funding route was used.

These are fixed technical-control counts on five selected train tasks, not population efficacy estimates; confidence intervals and p-values are not applicable (`p-val=n/a`). One rating per member/control gives no within-member repeat-variability estimate. Actual formal specification coverage retains the validated three repeats per member, median within member, then mean of the two medians divided by five. This route check does not replace that aggregation or establish absence of reward gaming.

Both runs reached terminal completion before the single control evaluation. The owned service and tunnel then exited under their registered process identities, port 9878 was released, and only this service's unique remote registration and authentication secret were removed. [Cleanup receipt](phase2/coverage_cleanup.json).

Phase 1 continues under v2-S2. The historical HTTP 403 remains recorded, while these successful model-query controls establish current route availability. The train-only mutation audit, fixed coverage-monitor manifest and independent hidden-gold-test adapter checks still precede learning. Selected-checkpoint test coverage remains unrun until the main-run and test-selection gates admit it.

Publication verification: the required Lean integration suite passed **708 tests, 3 skipped, zero failures in 305.54 seconds**, direct exit 0 ([receipt](phase2/resource_audit_publication_test.json)). This also checks the prospective resource-accounting and pilot stop-rule helpers; it is not a Phase 2 device admission.
