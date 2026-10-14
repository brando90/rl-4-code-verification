# Experiment 13 version 2: R2 reproduction under Amendment A2

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_R2.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 fails R2's amended measurement-admission gate. All 38,784 cells are accounted for, but 4 of 33,243 measured ordinary cells disagree with the historical oracle. The opaque route passes its amended checks. G0 and both later phases are not admitted; the reinforcement-learning hypothesis remains untested.

Published result prepared: 10-13-2026 21:21 PDT. This is the full R2 result under [Amendment A2](AMENDMENT_A2_R2_untyped_cells_and_admission_10-13-2026.md), replacing the original incomplete-only admission decision. The original coordinator finished naturally and was never stopped or modified.

## Counts and admission

| Route | Declared | Accounted | Measured | Typed deterministic limits | Untyped cells retried once | Unresolved / allowed maximum | Oracle equality among measured | Route verdict |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Ordinary | 33,456 | 33,456 | 33,243 | 168 | 46 | 45 / 33 | FAIL | FAIL |
| Opaque | 5,328 | 5,328 | 5,319 | 7 | 2 | 2 / 5 | PASS | PASS |

A2 requires equality on **every** measured cell, zero integrity defects, private lists of typed limits with reason codes, and unresolved ceilings 33/33,456 ordinary and 5/5,328 opaque. The final result has 0 integrity defects. Component-consistency checks pass on both routes; PLAN § 2c remains satisfied. The ordinary equality requirement fails independently of missingness; its unresolved ceiling also fails. Overall **FAIL**, as computed by the frozen A2 admission function and [public receipt](R2_A2/public_result.json).

- Ordinary retry outcomes: `{"deterministic_resource_limit": 1, "unresolved_measurement": 45}`.
- Opaque retry outcomes: `{"unresolved_measurement": 2}`.
- Every selected untyped cell received exactly attempt 2; no attempt 3 or measured-cell retry occurred. Original attempt-1 results and evidence remain unchanged.
- The original result contained 33,243 ordinary measured cells, 167 typed limits and 46 untyped cells; opaque counts were 5,319, 7 and 2 respectively. All original counts and hashes are retained in the [original public result](R2_A2/original_public_result.json).

Ordinary measured equality is 33,239/33,243 unique cells and 36,477/36,481 source-family readbacks. Value equality is 36,477/36,481; status equality is 36,481/36,481. The 4 unequal measured cells are retained privately and were not retried. Among 733 ordinary strict-success readbacks, 0 have component deficits. There are 2 typed kernel-probe-rejection consistency branches. These are deterministic full-cohort reproduction checks, so confidence intervals and p-values are not applicable (p-val=n/a).

The historical unique-cell denominator is 38,784 = 21,504 base + 20,520 ladder − 3,240 overlaps, representing 42,024 declared source-family readbacks. Ordinary accounting covers 12,936 train cells and 20,520 validation cells; 5,328 historical test cells stay opaque. The parent ladder's unavailable 5,400 cells remain separately declared and are not relabelled as measurements.

## Chronology and frozen evidence

R0 attempt 2 passed 30/30 authored fixtures; R1 attempt 1 passed 400/400 allowlisted train cells. [L1v2](RESULTS_L1v2.md) was published at `a7991af` before any validation/test factors. Its carried forecasts F0v2=0.50 and F1v2=0.85 retain their version-1 history. Original reproduction started at 10-13-2026 13:53:52 PDT and finished before the 20:43:24 prelaunch check.

A2's 0.1% unresolved tolerance was chosen **after** the original opaque public observation (5,319 measured, seven typed limits, two untyped / 5,328). This is a disclosed post-observation technical tolerance, not a prospective scientific threshold. Original A2 code and lock were published at `d72cd10` before retries. No test cell, value, factor, source or discrepancy detail was inspected or exposed.

The first A2 launch failed in resource preflight before reading route results or reserving a retry: systemd's requested cap of 1,044,624,427,008 bytes becomes exactly 1,044,624,424,960 bytes in Linux's 4,096-byte pages. A zero-cell control confirmed the 2,048-byte representation difference. The [written justification](reproduction/README_A2_resource_preflight.md) was committed at `c44a1c9`; the separate launcher, tests and [supplemental lock](locks/A2_resource_preflight.json) were committed and published at `90089e2` before corrected launch at 10-13-2026 20:57:06 PDT. All original A2 and measurement code, sources, environment, limits and retry rules remained unchanged. Initial failure logs remain private and preserved. This preflight restart performed no extra measurement attempt.

Opaque retries and reconciliation ran in their separate process; only counts, hashes and statuses left it. Its equality field is PASS for all measured cells. Ordinary per-cell diagnostics remain private; test per-cell diagnostics remain sealed. Typed-limit and unresolved-cell identifiers/reason codes are retained in private per-route ledgers, whose hashes are in the public receipts.

Preservation checks confirm 42/42 version-1 files and 47/47 frozen attempt-1 files unchanged, the original L1v2 JSON unchanged, and 50 unchanged L1v2 bindings plus the master's explicitly authorized PLAN supersession. PLAN and `cc.md` instruction amendments and the separately owned live master checkpoint are not misrepresented as frozen measurement bytes. Original A2 lock digest: `a18efcdb64d1d0f5bc315c15f8315eae91d559f5e03b43e2bf868ece1309d552`.

## Resources, verification and disposition

The run retained the measured 48-worker global ceiling, 64 GiB per-process address-space limit, original memory headroom admission and aggregate cap. No graphics processor, model call or optimizer update was used. Ordinary effective peak tree-resident memory was 67,436,621,824 bytes (99th percentile 6,940,449,587.20); these resource observations do not justify a gate retry. Frozen timeouts remain typed missing measurements. Fenced cleanup stopped 336 registered descendants from 178 terminal workers, with 0 forced kills and zero measurement retries. Each action verified process/start/boot and receipt identities; it changed no result or attempt. The [final process and attempt audit](R2_A2/closeout_verification.json) confirms no live measurement child and exactly 38,784 first attempts plus 48 second attempts. After measurements ended, watchdog retirement used `crontab -` instead of `crontab -l` for a read and briefly cleared the account schedule. Seven unrelated entries were restored byte-for-byte from preserved snapshots and independently matched against the later experiment-08 teardown backup, excluding its documented retired entries and our two owned entries. Both helper reads were corrected. The 21:20 PDT periodic monitor checks may have been missed; no active job was killed and no measurement changed. The two owned entries remain retired; no terminal marker or email was created ([incident and restoration receipt](R2_A2/watchdog_retirement.json)).

Before corrected launch, 22 synthetic A2/resource controls passed, followed by `E13_REQUIRE_LEAN_INTEGRATION=1 make test`: **333 passed, 23 unrelated skips, 172.52 seconds**. The final publication suite also passed **333 tests with 23 unrelated skips in 174.31 seconds**, recorded in the [verification receipt](R2_A2/publication_test_receipt.json). R2 used only A2's authorized one-time retries of untyped cells.

Under [PLAN § 4](PLAN.md#4-phases-gates-and-transitions) and A2 rule 3, stop downstream measurement and publish this failure. No G0 statistic, anchor generation, fitted item-response model, reinforcement-learning comparison or Phase 2 test evaluation is claimed. A2 does not authorize repairs or reruns of unequal measured cells. Per the master's latest direct instruction, no terminal notification is sent and no obsolete INCOMPLETE-only stop is published.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 completed full accounting and A2's authorized retries, but ordinary oracle inequality fails R2. The matched reinforcement-learning hypothesis remains untested.
**Snapshot:** R0 attempt 2 PASS 30/30; R1 PASS 400/400; R2 accounted 38,784/38,784; ordinary unequal 4/33243; opaque equality PASS; R2 FAIL; zero downstream training updates.
