# V22: Sol review of terminal tiny-proof repair failures

**TLDR:** The user authorized Sol to review the cases where V21 Terra exhausted its proof-repair bounds. Preserve the V21 failures and review exact separate copies with `gpt-6.1-sol`, high reasoning. V18's 800-row snapshot and live V20 training remain unchanged.

## Cohort and immutable evidence

Admit a case only after its V21 four-case batch is DONE and its case state is EXCLUDED_BOUNDED_REPAIR. Copy the original curriculum row, parser-owned proof ranges, original Lean and FILE envelope, prior verification, latest partial proof map and actual compiler diagnostics into V22. V21 files are read-only. The dynamic review cohort closes when V21's final completion exists; its source indices, manifest hash and parent completion hash are then immutable. All reviewed outcomes are reported, including unresolved cases.

The original 500-row source SHA256 remains `2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119`. No validation or evaluation material is sent to workers.

## Exact model, budgets and bounds

- Exact model `gpt-6.1-sol`, reasoning `high`, existing lab-key Codex CLI route, full access and no approval prompts. No Terra substitution.
- Six parallel case workers. At most two CLI turns and four NEW source-hash checks per case in this separate phase. Original V21 attempt counts and all receipts remain unchanged.
- 900 seconds per CLI turn, 120 seconds per compiler operation; share V21's 16 compiler lockfiles so aggregate compiler concurrency stays at 16.
- Use the existing shared `campaign_budget.py` ledger: $900 total campaign ceiling, $780 cleanup ceiling, including all earlier charges and in-flight reservations. Reserve $10 per request and stop at $1.20 observed conservative usage. No automatic ceiling increase.
- Official model/pricing pages fetched on 2026-10-19 confirm the exact identifier, high reasoning, 1,050,000 context and 128,000 maximum output. Ordinary estimates per million tokens: input $2, cached input $0.10, output $10. Conservative ledger rates cover long-context/cache-write exposure: input $5, cached input $0.20, output $15. These estimates are not invoices. Worst single-response exposure plus the observed stop fits the $10 reservation.
- Estimated additional conservative charge $10–$70 for the expected small failure cohort, uncertain. Existing 128,000-context/100,000-auto-compaction settings reduce ordinary request size but do not replace conservative exposure reservations.

Sources: [official model](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [official pricing](https://developers.openai.com/api/docs/pricing).

## Proof and admission requirements

Preserve original implementations, domains, hypotheses, APIs, namespaces, specifications and every test statement. Only original parsed proof terms may change. No deletion or renaming of named numeric-test theorems, hidden automation wrappers, new axioms or proof escapes. Use the same complete 40-tactic exclusion policy as V21, allowing its byte-identical original anonymous concrete `native_decide` test exception. Plain named lemmas and explicit structural reasoning are permitted.

Use concise mathematical proof sketches and meaningful English inline comments. Every changed final proof needs the exact unchanged frozen Lean/kernel inspection and allowed axiom cones; assistant FILE answer must remain below 1,000 Qwen tokens and the full conversation at most 16,384. Final admission reuses V21's approved exact-token comment-only adapter if needed, preserving raw checked source, original receipt and explicit annotated-source provenance. It performs protected-reference and duplicate checks with no new model or compiler calls.

The final output is a repaired delta, plus a complete review outcome table and portable proof receipts. It supplements V21 after joining by the original task identifier/source index; it never overwrites the first-pass corpus or its failures.
