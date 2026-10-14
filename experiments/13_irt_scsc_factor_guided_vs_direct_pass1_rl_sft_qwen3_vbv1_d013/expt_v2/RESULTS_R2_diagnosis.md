# Experiment 13 version 2: read-only R2 diagnosis under adopted A3

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_R2_diagnosis.md>

**TLDR:** All 49 ordinary exceptions are classified under Amendment A3: 2/49 timing/resource dependent (a), 0/49 pipeline defects (b), 4/49 historical-record irreproducibility (c), and 43/49 unknown (d). All four unequal cells are class (c); none is class (d). The supplemental A2 retry that became a typed timeout is class (a), outside those 49. Opaque unresolved reasons are `RuntimeError` for 2/2 cells, with no sealed detail inspected. No cell was re-measured. A3 rule 3(i) is satisfied; the master must enforce exclusions and full-manifest worst-case bounds before G0. G0 was not run.

Created: 10-14-2026 13:08 PDT

## Scope, chronology and disposition

The original [R2 FAIL under A2](RESULTS_R2.md) remains unchanged. This report applies the [adopted A3 rules](AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md), whose [adoption record](AMENDMENT_A3_ADOPTION_10-14-2026.md) discloses their post-observation chronology. The owner began read-only evidence collection around 12:57 PDT on 10-14-2026, learned of the 13:00 addendum at 13:04 PDT, then pulled `57c3bb6` and applied its ordered rules. Initial descriptive failure signatures were not an admission decision. No new A3 proposal file is created.

The addendum supersedes the earlier request for a public 50-cell table and competing proposals: the public report contains aggregate causes and the identities/classes of the four unequal ordinary cells. The complete private diagnosis covers 50/50 requested ordinary cells: the 49 A3 exceptions plus one previously typed A2 retry. It includes split, historical status, attempt history, discrepancy type, per-attempt memory, available contemporaneous host records, cause assessment and retry assessment. No component values are published here.

All statistics below are deterministic ledger counts, not sample estimates: p-val=n/a; confidence intervals are not applicable. Denominators are 4 unequal ordinary cells, 45 unresolved ordinary cells, one supplemental typed ordinary retry, and two unresolved opaque cells. The two ordinary exception groups together comprise A3's 49. The full manifest remains 38,784 cells: 33,456 ordinary and 5,328 opaque.

## Ordered A3 classification

| A3 rule 2 class | Unequal ordinary / 4 | Unresolved ordinary / 45 | A3 set / 49 | Supplemental typed retry / 1 |
|---|---:|---:|---:|---:|
| (a) Timing or resource dependent | 0/4 | 2/45 | 2/49 | 1/1 |
| (b) Deterministic oracle-pipeline defect | 0/4 | 0/45 | 0/49 | 0/1 |
| (c) Historical-record irreproducibility | 4/4 | 0/45 | 4/49 | 0/1 |
| (d) Unknown under the rule | 0/4 | 43/45 | 43/49 | 0/1 |

Rules were evaluated in order. A class (a) assignment here requires an explicit recorded timeout. A3 also allows elapsed time within 10% of a frozen limit or an out-of-memory kill, but the retained evidence does not establish either additional trigger for the other cells. In particular, whole-cell elapsed time sums several subprocesses; it cannot be compared with a single 600-second oracle or 900-second frontend deadline. Per-subprocess elapsed times were not retained. An `INTERNAL PANIC: out of memory` with exit 1 is not evidence of an out-of-memory **kill**. This literal distinction leaves eight such cells in (d), despite their plausible resource-cap mechanism. No existing receipt is rewritten or retyped.

Class (b) requires a reproducible difference in the **oracle** path (extraction, vacuity, status mapping or source handling). The retained failures do not establish one. Repeated frontend crashes alone do not meet that rule. The frozen adapter maps nonzero frontend exits to `RuntimeError`; that explains missing complete measurements but is not evidence that the historical strict oracle path changed.

## Four unequal cells: historical-record irreproducibility

All four are validation cells. Each has one R2 attempt, value inequality only, and historical/current status `scored`/`scored`. The historical strict value is 0 and the reproduction is 1. Their historical cache records `compiles=false`; the R2 run of the pinned historical scorer records successful compilation. Source hashes and the compile-environment fingerprint match. The historical cache has no kernel report; the reproduction's oracle subprocesses all exit 0. No class (a) trigger or class (b) difference is established before assigning (c).

| Ordinary cell ID (policy / task / sample) | Split | A3 class | Attempts | Discrepancy; historical status |
|---|---|---|---:|---|
| `sft_4B_f0p5/security_set__security_6858__vulnerabilities__137_unsafehmaclength/4` | validation | (c) | 1 | value only; `scored` |
| `sft_8B_f0p125/security_set__security_6858__vulnerabilities__95_unsafecerttransparency/1` | validation | (c) | 1 | value only; `scored` |
| `sft_8B_f1p0/security_set__security_6858__vulnerabilities__137_unsafehmaclength/3` | validation | (c) | 1 | value only; `scored` |
| `sft_8B_f1p0/security_set__security_6858__vulnerabilities__144_unsafeintegeroverflowalloc/2` | validation | (c) | 1 | value only; `scored` |

The pinned historical function `_compute_agent_compile_scores` was invoked by the frozen `historical_oracle_v2.py`; the original ladder reader supplies its source-family value/status. The cache shortcut requires `compiles is True`, so the historical `false` cache entries would not bypass a fresh compile even if supplied. The wrapper's bookkeeping split does not alter compilation: the scorer stores it as metadata. There is no demonstrated parse/extraction, vacuity or source-selection discrepancy. This is an observed failure to reproduce the old record with historical code, not a proof that every possible future scheduling condition must return the same result.

The common historical/current compile-environment fingerprint is `5a9560145df56c7cba359866bb6188c495eee258d7fc8e59ed87427cda40e7dd`. Eleven relevant frozen code/environment bindings match L1v2. The pinned scorer is revision `59059a20d40adf3289869e58302169ad78102877`; Lean is v4.22.0. Historical per-task score rows and caches retain the failed-compile outcome but not the compiler return code, elapsed time or raw failure message. The retained scorer logs contain no task-specific failure explanation. Therefore **the original failure mechanism remains unresolved**: timeout under shared-host load and elaborator nondeterminism are possibilities, not findings. These cells are not the separately recorded kernel-probe-rejection consistency cases.

An identical new attempt might repeat or change the observed value, but there is no evidence that it would restore the historical value. Selecting attempts until the value matches would not establish fidelity. No such attempt ran or is selected by class (b).

## Forty-five unresolved ordinary cells and one typed retry

| Retained diagnostic signature | Count / 45 | Ordered A3 assignment | Evidence and likely mechanism |
|---|---:|---|---|
| Interpreter deep-recursion termination | 16/45 | (d) | Explicit stderr; exit 134 in both attempts. Runtime recursion/stack failure; no literal (a) trigger or oracle-path defect established. |
| Frontend out-of-memory panic | 10/45 | 2 (a), 8 (d) | Two also have explicit oracle timeouts in both attempts. All ten have frontend memory panic; allocation cap is plausible, but panic exit 1 is not a logged kill. |
| Exit 139 without diagnostic | 10/45 | (d) | Both attempts exit 139 with empty component stderr. Consistent with a segmentation-fault exit convention; underlying cause unknown. |
| `Nat.pow` exponent panic | 6/45 | (d) | Explicit arithmetic/runtime panic in both attempts; no demonstrated oracle-path difference. |
| Stack overflow | 2/45 | (d) | Explicit stack-overflow abort in both attempts; exit 134. Not a recorded deadline or out-of-memory kill. |
| GNU Multiple Precision library overflow | 1/45 | (d) | Explicit `gmp: overflow in mpz type` in both attempts; exit 134. Arithmetic/runtime failure. |
| **Total** | **45/45** | **2 (a), 43 (d)** | All 45 repeat the same frontend signature across attempts 1 and 2. |

The supplemental typed retry (1/1, outside the 49) changed from a frontend out-of-memory panic to a `TimeoutExpired` at the frozen 900-second frontend deadline. It remains a typed deterministic resource limit and is class (a). Complete-cell time on that retry is 915.8 seconds; its partial oracle had already run. A2's 46 ordinary retries thus produced 0/46 new complete measurements, 45/46 unresolved outcomes and 1/46 typed limit. These observed frequencies are not estimated probabilities for a hypothetical third attempt.

For all 92/92 attempts across these 46 cells, the saved partial oracle value/status matches the primary historical expectation; every historical status is `scored`. The failure occurs before a complete component measurement returns, so neither a complete-cell value mismatch nor a complete-cell status equality is asserted for these nonmeasured cells. They remain in declared denominators. Repeated arithmetic, recursion and stack signatures give no evidence that an identical third attempt would help; exit 139 remains unpredictable from the logs. Memory/timeout modes may vary with shared load, as the typed retry illustrates, but no successful recovery is demonstrated. No third attempt is proposed under A3's class (b) rule.

## Memory and shared-host evidence

Each of the 96/96 selected ordinary attempts (four singleton mismatches plus 46 pairs) retains whole-cell elapsed time and sampled process-tree peak resident-set size. The private diagnosis records their exact values and timestamps. Resident-set size sums the worker tree and is not identical to the 64 gibibyte (GiB) per-process virtual-address-space cap.

The four unequal attempts last 974.4–1,333.6 seconds and have sampled tree peaks 6.447–6.450 GiB. No historical per-cell load/memory measurement was retained. No contemporary host load average is logged inside any of these four R2 attempt windows. A scope snapshot overlaps two of their windows; its scope memory and cumulative processor time are not host load average. Other original-run snapshots do contain host load averages, but extrapolating those to a different attempt would not establish a timeout cause.

The ten recurring frontend memory-panic cells have second-attempt peaks 55.721–62.805 GiB. This supports a possible address-space-cap explanation, without proving an operating-system kill. The one supplemental timeout retry peaks at 15.344 GiB after a 62.883 GiB first attempt. No contemporaneous A2 host snapshot was retained in the inspected resource log. Missing load observations are explicitly marked in the private per-cell records; current host measurements were not substituted.

## Opaque route: count and reason only

A separate read-only opaque process verified the private status-ledger hash against its public receipt, selected unresolved statuses internally and returned only aggregate reason codes. It opened no test source, per-cell log or measurement receipt. The underlying two causes remain unclassified beyond the code below; no attempt to infer them from ordinary cells is made.

| Opaque unresolved reason | Count / unresolved |
|---|---:|
| `RuntimeError` | 2/2 |

The retained public receipt reports 2/5,328 unresolved, within A2's maximum five, and equality among measured cells PASS. Each already received its single identical A2 retry. The opaque PASS stands under A3 rule 3(iv). No test identifier, strict value, component or source is disclosed.

## Admission implications and recommendation

All four unequal cells are (c), satisfying A3 rule 3(i); there is no class (b) defect to fix and the rule-selected repair/re-measurement set is **empty**. Recommend that the master proceed to an exclusion-and-bounds admission audit, without a new oracle attempt or an R0/R1 rerun. This round does not run G0 or certify that its bounds implementation is ready.

A3 requires exclusion of all 49 diagnosed ordinary exceptions. Together with the 168 already typed ordinary limits, this gives 217/33,456 ordinary exclusions and 33,239/33,456 retained measured/equal cells. The private exclusion manifest lists every ordinary identifier and its original status/class; original records and values are unchanged. The full ordinary denominator is still 33,456, not 33,239. Test exclusions remain sealed and test cells do not enter G0/G1.

Before G0 or G1, the master must ensure the data loader uses the complete exclusion set and reports valid full-manifest worst-case bounds for each statistic, including missing cells' effects on eligibility and conditioning. Renormalizing to complete cases or substituting point imputations is insufficient. A verdict that flips within those bounds is INCONCLUSIVE under A3 rule 4. G0's frozen thresholds remain at least 21/135 dense-only tasks and area under the receiver operating characteristic curve (AUC) at least 0.65; undefined one-class AUC fails. No threshold, forecast or later no-retry gate changed here. The original A2 failure remains published; satisfying A3's classification condition does not rewrite it.

The validated Valkyrie judge route is reported unavailable by the master brief; it was not probed. No model calls, graphics processing unit launches, training or historical-cell measurements occurred during diagnosis. The required software suite exercises fixtures only.

## Evidence paths and SHA-256 hashes

`WR` below is `/lfs/skampere1/0/brando9/rl4cv_e13v2`; `D` is `WR/R2_diagnosis_10-14-2026`. Private artifacts are audit material, not published component data. SHA-256 denotes the Secure Hash Algorithm with a 256-bit digest. Each private diagnosis line embeds its source receipt/log paths and their hashes, timestamps and matched host-log line numbers; `ordinary_diagnosis_line_hashes.json` binds each line including its terminating newline. Historical extracts bind both source-file hashes and selected line hashes. All 1,057 inspected ordinary evidence files and 42 version-1 files were hash-checked unchanged.

| File | SHA-256 |
|---|---|
| `WR/R2/ordinary_manifest.jsonl` | `2b6b764f481c4a1cd87d47a67a1746e5bbbd78f79571131fa1ca2383cd163eba` |
| `WR/R2/ordinary/results.jsonl` | `d0574c96b2b90f9882aacffae5cfb1db75f9bc3d1cefcca060f66d134c9ae5ca` |
| `WR/R2_A2/ordinary/results.jsonl` | `3611d101695b5ad427bdadf6f9136c28f6fc44348abff9ad33e9d1168c112811` |
| `WR/R2/resource_snapshots.jsonl` | `12033a42ea81f958307924f8e6ebe486e985c5f0cca32cba8e68692a24594790` |
| `D/ordinary_diagnosis_private.jsonl` | `c0bc72064a32e45dbdb4601639438a08b6c5303f8b55fddd9f11a08026e09b2b` |
| `D/ordinary_diagnosis_line_hashes.json` | `9a32625b58f6c1c0ad65ef7e9aa67eae95cad9addf87d2b382f241fe472c604e` |
| `D/a3_49_classification_private.json` | `69c01bc09e6df4a63bb2c4f3053217136f5d2ee933932296e42fd0e0608a80fa` |
| `D/a3_ordinary_exclusions_private.json` | `c00b35abaecda874820d4b1b29015655e248c19f319fa574fefa3d0804124128` |
| `D/mismatch_historical_records.json` | `2e255b4399b35cf7f20d274729614dfbe9574655a32ff9069a6ea58f698e62f8` |
| `D/mismatch_score_details.json` | `46c990e3cb950a3cbf999f5c5ed68ac3a6dbb5478d3efd72947c7a1a5ba5a718` |
| `D/mismatch_historical_logs.json` | `134fa19d5422d50dec39dc3b5672016a1670790747e793c4fe36ea1266dc6b32` |
| `D/opaque_reason_counts.json` | `714e842e9c078eac7b4bd0469d1ff62147d8ac42e10b2ea8ca5dc043dc3535c9` |
| `D/diagnosis_summary.json` | `f7ed75f5d7bc6b02392a9fb148a91badfacbd16f6089296304e8f224637ebe71` |
| `D/preserved_evidence_hashes.json` | `038093a490d6a3541e8eed74b62513b4dfb43adcf89979869bf4e370dba60bc6` |
| `WR/state/diagnose_R2_readonly_10-14-2026.py` | `a7161d36de54a3a2ffb8b3310dd03fb206e6226df12924878f9c94b00d2ed871` |
| `WR/state/opaque_reason_counts_readonly_10-14-2026.py` | `f04d3d292332f5a6077172aec9f11c4d03be837ad01d5b6291f906a3d84aeb81` |
| `WR/state/finalize_R2_diagnosis_readonly.py` | `51ced9789ecf3904535394843afb436c5a4a0ae6d34cbd47e2ea40b08e382f91` |

The opaque process reported status-ledger hash `15f20571c42d8bea39fc6d957cfcf3ac9e20bd6a09705dfe34ffbff45a8c40f6` for `WR/R2_A2/opaque/private_nonmeasured_cells.json`, matched to public-receipt hash `a7d295aefa88fce0f4fc6edc7775c9582f2ae7755e14776b1960ef809dfaa636`. The owner consumed only its aggregate output.

The four unequal cells' private diagnosis line bindings are:

| Ordinary ordinal | Line in `D/ordinary_diagnosis_private.jsonl` | SHA-256 including newline |
|---|---:|---|
| 25668 | 31 | `b286f762ede3d6241fd733c5f8af9fcb7d5a80690465390ae3d0a9614191bba9` |
| 29113 | 36 | `0ecfb99cbf9df156ec0b694dd9136a77cc2f980194a5d4bb2566cc8ae7f18618` |
| 33227 | 48 | `fdcc1533311eaac57260346dc55c6d1b0bf47cc15c84cd760ffda2bdfff1c3a9` |
| 33242 | 49 | `1dd47144ef6dc32218baa5b68fd70b38b6ba569267cc2448eb0401eeb623dee7` |

## Publication verification

`E13_REQUIRE_LEAN_INTEGRATION=1 make test` passed: **333 passed, 23 skipped, 0 failed**, 170.80 seconds. Existing Lean integration tests executed. Log: `D/make_test.log`, SHA-256 `daad38b1c1872fb2aea86fddaf3a377309c434e726429fc0cfea47534aea250e`. No historical-cell re-measurement was part of that suite. Deterministic verification: p-val=n/a.

After synchronizing concurrent experiment-12 code/tests from main `d3c2777`, the same required suite passed again: **382 passed, 23 skipped, 0 failed**, 164.19 seconds. Log: `D/make_test_after_sync.log`, SHA-256 `74fda0b37d8f974e2df127012b4b8907a06c419b97cd45e1edb43c7c825b532e`. The four documentation changes rebased cleanly; no experiment-13 code or measurement changed.

A second clean synchronization to main `69ae5be` added independent experiment-15 code/tests and experiment-10 documentation, with no shared-code or experiment-13 changes. The newly added test module was checked separately: `python -m pytest -q tests/test_e15_irt.py`, **14 passed**, 47.06 seconds; `E13_REQUIRE_LEAN_INTEGRATION=1` remained set. Log: `D/test_e15_after_sync.log`, SHA-256 `ed9fb949bcc200349b2a9d44c2ed48dc7cfe8bc8f3008b7318e221be3c2a43da`. This complements the preceding full-suite run rather than claiming another full-suite run.
