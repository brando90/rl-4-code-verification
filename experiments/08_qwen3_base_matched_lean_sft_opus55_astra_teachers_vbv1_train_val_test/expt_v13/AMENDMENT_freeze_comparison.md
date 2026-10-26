# V13 amendment: Freeze partial cleanup for the matched comparison

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Freeze the available checked proof replacements now and release the second authorized training run. The remaining original answers stay as explicit fallbacks.

Recorded before finalization: 10-19-2026 10:25:25 PDT.

Freeze partial proof-cleanup cohort now for the authorized matched training comparison: budget reservation headroom reduced concurrency to one lane and delayed the second training run. Preserve the healthy active case within its native budget; retain untouched originals for every unresolved/unattempted row.

Measured pre-freeze counts: {"DONE": 876, "FALLBACK": 36, "PENDING": 1445, "RUNNING": 1, "UNCHANGED": 227}; kernel-verified replacements: 817 / 2585. Active cases: existing_1803. No budget rates, ceilings, checker rules or receipts change. No provider failure is asserted. The admission flag and pending-to-original fallback transition are protected by the existing queue lock. The current healthy CLI is allowed to finish within its original900-second limit, then the existing format/protected-screen finalizer binds replacements to completion.json.
