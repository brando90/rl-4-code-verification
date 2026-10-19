# V18: Finish explicit proof cleanup of the original Python-to-Lean pool

**Doc link:** [Results](results.md)

**TLDR:** Preserve V13's immutable 818 accepted replacements and recheck its 227 unchanged original files. Attempt all 1,540 remaining answers with focused four-file Terra/high batches. The final fully cleaned original pool contains verified accepted files only; unresolved automation is explicitly excluded, never inserted as an automated fallback.

## Prospective setup — 10-19-2026

The user explicitly requested completion of the cleanup, the second training run, continued monitoring and another conditional $300 if necessary. This new phase leaves V13's completed data, receipts and V12's already frozen partial comparison untouched. The shared campaign maximum is now $900, with cleanup at most $780 and adaptation at most $120; prior charges count toward these caps.

Frozen original pool: 2,585 rows, SHA-256 `7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b`. V13 supplied 818 accepted replacements (exact receipt/source hashes reused), 227 unchanged answers without targeted proof automation, and 1,540 unresolved/unattempted rows. Recheck the 227 actual current full-file/kernel results with CPUs, without model calls. Every old partial proof map remains archived and seeds its corresponding new case.

## Model, batching and bounds

Use only `gpt-5.6-terra`, high reasoning, Codex CLI 0.114.0 with the authorized private lab-key environment route. Up to 32 micro-worktree identities share 16 compiler slots. Group four files per CLI turn; inline only focused current source context and exact target IDs, rather than rereading large metadata and repeated task boilerplate. The first real four-file batch calibrates cost and throughput and is part of the declared batch.

New V18 bounds are at most two CLI attempts per batch, four distinct final candidate source hashes per case, 900 seconds per CLI attempt and 120 seconds per compiler operation. These new user-authorized attempts are separately recorded and do not rewrite V13's bounds or outcomes. Bounded failure means an explicit proof was not established in this attempt; it does not imply the statement is false or mathematically impossible.

Before a model call, one CPU-only candidate tries plain commented `rfl` in every targeted proof, with a truthful definitional-reflexivity sketch. Admit it only if the complete unchanged file and every named proof pass the frozen kernel check. A failed reflexivity candidate leaves all prior partial proof seeds intact. It counts against the same four-source-hash limit, leaving three distinct model-produced candidates; mechanical successes are separately reported and require no model call.

If a CLI is interrupted or changes a draft after an earlier successful check, retain the shortest exact passing explicit source snapshot from that case's bounded checks. Require the unchanged inspector pin, source hash and valid kernel report; final format/overlap gates still apply. This preserves actual evaluated proof bytes instead of losing a valid result because a later draft was unfinished.

Use the same complete automation inventory as V13. Plain named-lemma reasoning, `exact`, `apply`, `rw`, `rfl`, `calc`, induction, constructors/cases and explicit `linear_combination` are allowed. Original anonymous concrete executable `native_decide` tests stay byte-identical. Implementations, theorem/specification statements, domains, hypotheses, APIs, namespaces and test inputs stay fixed by reconstruction from the original Lean parser's proof-term ranges. No hidden automation wrappers, new axioms, sorry/admit, unsafe/elaborator escapes, weakened statements or enormous unreadable generated terms are accepted.

Add a brief mathematical sketch and meaningful English comments every few proof lines. Keep proofs concise without obfuscation. The original full FILE answer and unchanged prompt must fit the pinned Qwen template and 16,384 total tokens. All accepted source bytes require the unchanged frozen kernel inspector and allowed axiom cones. Full-pool protected-reference screening remains against the 764 validation/test/fresh diagnostic references; protected material is never sent to teacher workers.

## Cost and liveness

V13 consumed ordinary-rate estimate $237.391247 and conservative ledger charge $469.991219. The prior individual-turn conservative average would not fit the new remaining cleanup allowance. Focused four-file batches target an additional $154–$308 conservative estimate for 1,540 files; this forecast is uncertain, particularly for longer proofs, and will be updated from the first actual batch.

Import the shared `expt_v15/campaign_budget.py` helper. Reserve $10 per Terra CLI attempt and stop at $1.20 observed conservative usage; retain the native single-response exposure margin. Ordinary-rate estimates are $2/$0.20/$12 per million uncached input/cached input/output tokens; conservative ledger charges are $5/$0.40/$18. These are configured-price estimates, not invoices. The shared helper activates the preapproved third tranche when bounded dispatch exposure exceeds the earlier allocation; the watcher activates it early when remaining earlier headroom cannot support four lanes. No rates or caps are silently raised. Unknown billing is charged at the full reservation; repeat settlement is idempotent.

An ordinary remote supervisor polls every 15 seconds, observing completion, death, idle/missing deliverables, errors and funding holds. It adopts healthy children or fences dead writers, recovers only within the fixed attempts, and publishes all outcomes. A budget/provider hold remains a truthful unresolved state and triggers coordinator attention; it never becomes a claim that an unattempted proof is irreparable. The fully cleaned comparison must not wait silently on one-worker reservation churn.

Preparation may resume after an interrupted transport only before `dispatch.json` exists: existing private micro worktrees and profiles are reused, and no model calls begin until the complete input manifest and deterministic controls exist. Once dispatch exists, source input preparation refuses to overwrite it.

## Final contract

Remote run root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v18`. Preserve original records, attempted proof artifacts, source snapshots, compile/kernel receipts, per-batch prompts/decisions and usage. Publish a 2,585-row outcome table, accepted-only `final/fully_cleaned_existing_training.jsonl`, changed-source replacement records, protected-screen receipt and immutable completion hashes. Excluded rows stay in the declared denominator with precise reasons. V19 owns the subsequent full-cleaned training launch; this phase does not alter V12's earlier frozen pool or watches.
