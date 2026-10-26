# First 1.7B continuation finished at11.1%; final cleanup and second run pending

**Doc link:** [experiment home](README.md)

**TLDR:** The10,940-example continuation completed training and all1,080validation cells:120successes (11.11%). Proofcleanup froze818verified replacements plus originalfallbacks, releasing the second training preparation. The follow-up controller and result publisher had infrastructure failures; those were repaired and their evidence retained.

**Last updated:** 10-19-2026 10:49 PDT.

| Phase | State | Result |
|---|---|---|
| First1.7B continuation | COMPLETE | 5,470updates,13,168,888assistantlosstokens;120/1,080validationbinarysuccesses |
| First-run uncertainty | MEASURED | Task-bootstrap95%interval6.94–15.83%;135tasks, eightattempts each; p-value not computed |
| Original2,585proofcleanup | DONE_PARTIAL | 818verified replacements,227unchanged originals,1,540flagged originalfallbacks; all2,585accounted |
| Final cleaned comparison | PREPARING | Partial dataset had zero optimizer updates; final version18 cohort will train under version19 on GX10 |
| Extra public-source verification | COMPLETE | 688/729formalpasses;41failures retained |
| Extra public-source admission | AVAILABLE | 678examples passed currentkernel/FILE/template/token/overlap/dedup checks; finalcomment-version pointer recorded separately |
| Adaptive controller | RECOVERED | Actual first-result recomputation passed; independent ordinary-code death watcher is running |

## What worked and what did not

The first run's120/1,080successes compare descriptively with99/1,080for the previous replay condition and74/1,080for the previous tiny-augmented condition. Different data, budgets and continuation histories prevent attributing the change to a single component. The25%goal remains unmet.

There were971extractedoutputs and120compilingoutputs. All109unextractedoutputs were length-capped;108of those began with the correctFILEmarker and Lean fence. Among all1,080cells,851extractedoutputs failed compilation and110were capped. Thus failing to finish and failing Lean are distinct problems. A full CPU-only diagnostic pass preserves original scores and will report generic compiler categories; protected task content is not used as teacher data.

The cleanup's conservative accounting reduced concurrency to one worker near its$480phaseallocation while1,445cases remained pending. The phase was explicitly frozen rather than continuing that slow queue; unfinished or unsuccessful replacements retain the originalanswers, visiblyflagged. Actual ordinary-rate estimate forcleanup is$237.39; conservative accounting charge$469.99, not an invoice.

The follow-up controller lacked `TINY_RUN_ROOT` for evaluatorimport, then crashed when its model prematurelysettled theparentreservation and thewrapper settled it again. The model did produce a valid independent120/1,080recomputation but no new training regime before the crash. Repairs set the environment, reconcile settlement idempotently from actualCLIusage, prohibitmanualparentsettlement, and add an independent deathwatcher. Gitpublication also stalled onCSVCRLFrecordterminators; thepublisher now normalizes only serialization and verifies identical parsed fields. No scores, evaluationprompts, splits or proofacceptance were changed.

[First-run results](../expt_v12/results.md) · [Cleanup evidence](../expt_v13/results.md) · [Public-source admission](../expt_v14/results.md) · [Recovery amendment](AMENDMENT_recover_followup.md).

## Current execution boundary

The later user instruction requires finishing the remaining proof cleanup before the final second training condition. [The new prospective amendment](AMENDMENT_finish_cleanup_gx10.md) records the $900 maximum, Terra teacher pin and single Astra code-port exception. Version18 deployment and the single version19 checkpoint relay await the dropped cluster connection's human reauthentication. GX10 is reachable; its installed CUDA environment passed small GPU controls, but the full1.7B hardware control and production training have not started. This is an access blocker, not a completed result.

## Latest automatic snapshot

10-19-2026 12:01 PDT.

- current validation: 120/1,080 binary successes; 11.11%, complete manifest.
- Current training: 5,470/5,470 updates; 13,168,888 assistant loss tokens.
- Historical partial-cleanup SNAP training: 0 updates; dispatcher unknown. Final second-run ownership is version19.
- Version13 cleanup snapshot: {'FALLBACK': 1481, 'DONE': 877, 'UNCHANGED': 227}; declared 2,585. Final admission counts are in its immutable completion receipt.
- Version18 remaining cleanup: {'declared': 2585, 'states': {'PENDING': 1528, 'ACCEPTED_INHERITED': 818, 'ACCEPTED_UNCHANGED': 227, 'EXCLUDED_BOUNDED_REPAIR': 4, 'ACCEPTED_MECHANICAL_RFL': 4, 'REPAIR_RUNNING': 3, 'ACCEPTED_REPAIRED': 1}, 'batches': {'PENDING': 383, 'USER_STOPPED_PAID': 1, 'DONE': 1}, 'verified': 1050, 'observed_unix': 1792436379.3890038, 'v18_conservative_charge_usd': 3.3370452, 'v18_base_estimate_usd': 1.6899186000000002, 'cleanup_total_conservative_usd': 473.3282642, 'cleanup_reserved_usd': 0, 'tranche3activated': True}.
- Additional public sources: 729/729 checked; {'FORMAL_CHECK_FAILED': 1, 'FORMAL_PASS': 688, 'LIBRARY_IDENTIFIER': 1, 'SYNTAX_COMPATIBILITY': 39}.
- Paid work: $243.10 base-rate usage estimate; $481.11 conservatively charged; $0.00 reserved for in-flight work. Estimates are not invoices.
- Authorized maximum: $900.00; second $300 tranche active: True; third $300 tranche active: True. Goal receipt: False.
