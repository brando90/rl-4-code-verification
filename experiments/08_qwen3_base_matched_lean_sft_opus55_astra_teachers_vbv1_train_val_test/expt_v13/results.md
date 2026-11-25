# V13 results: Explicit proof replacements for 2,585 original answers

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Cleanup phase frozen: 818 replacements passed kernel, format and overlap checks; all 2,585 rows are accounted for. Original fallbacks preserve the remaining cases, and the immutable completion receipt releases the matched second training run.

## Latest measured snapshot

| Measure | Observed |
|---|---:|
| Declared answers | 2585 |
| Original files parsed successfully | 2585 / 2585 |
| Parsed proof terms | 100234 |
| Answers with targeted automation | 2358 |
| No replacement needed | 227 |
| Current kernel-verified replacements | 818 |
| Running | 0 |
| Pending | 0 |
| Temporary budget holds | 0 |
| Original fallback outcomes (status=FALLBACK only; 1767 rows keep the original in total, see `original_fallbacks`) | 1481 |
| Calibration final FILE/template passes | 4 |
| Calibration protected exact / near | 0 / 0 |
| Settled ordinary-rate estimate USD | 237.3912 |
| Settled conservative ledger charge USD | 469.9912 |
| In-flight reserved USD | 0 |
| Second preapproved budget tranche active | True |

Remote observation Unix time: `1792430822.8889015`. API charges are configured-price estimates, not invoices.

## Comparison phase freeze

Freeze partial proof-cleanup cohort now for the authorized matched training comparison: budget reservation headroom reduced concurrency to one lane and delayed the second training run. Preserve the healthy active case within its native budget; retain untouched originals for every unresolved/unattempted row. Recorded at 10-19-2026 10:25:25 PDT. See [prospective amendment](AMENDMENT_freeze_comparison.md).

## Frozen result

```json
{
  "state": "DONE_PARTIAL",
  "declared": 2585,
  "accounted": 2585,
  "replacements": 818,
  "original_fallbacks": 1767,
  "replacements_sha256": "ad84f18d0273a243190f5e213702224a8a979299d61b43aa40b4196c716e1982",
  "training_sha256": "0ada06ed829d2012c77374af3ad3e1eec02555d2a8ca901d8d218a6a084bd974",
  "source_sha256": "7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b",
  "protected_references": 764,
  "protected_exact": 0,
  "protected_near": 0,
  "observed_unix": 1792430868.9535768,
  "unchanged_no_targeted_automation": 227,
  "flagged_original_fallbacks": 1540,
  "comparison_phase_frozen": true,
  "freeze_receipt_sha256": "30c25c7a647a1c3af53c23035914ad5e562144ee9df5a59aa97c3372b5aa6299",
  "freeze_reason": "Freeze partial proof-cleanup cohort now for the authorized matched training comparison: budget reservation headroom reduced concurrency to one lane and delayed the second training run. Preserve the healthy active case within its native budget; retain untouched originals for every unresolved/unattempted row."
}
```

## What was checked

- All 2,585 original files parsed with the pinned Lean parser; exact proof-term ranges protect every unchanged implementation, statement, namespace and test input.
- First four real replacements passed the unmodified frozen kernel inspector, FILE extraction, Qwen chat template, 16,384-token cap and 764 protected-reference screens (zero exact/near hits).
- Positive/unsolved-negative kernel controls, automation rejection, implementation/native-test preservation, actual harmless-child usage termination and dead-driver recovery passed.
- The saved-proof search compared entire non-proof file contexts across all 2,585 originals; no interchangeable explicit saved proof was found.
- The initial parser attempt lacked imported environment extensions. Loading those extensions fixed it; no paid work used the failed extraction.

Full model/compiler logs and immutable candidate bytes remain on skampere1 under `lean_corpus_v13`. Compact progress, 2,585-row outcome tables and source/runtime manifests are mirrored in `results/`. Model-training comparisons are owned by V12; no training score is inferred from these teacher proof checks.
