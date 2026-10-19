# V13: Explicit proof replacements for the original 2,585 Python-to-Lean answers

**Doc link:** [Experiment home](README.md)

**TLDR:** Process all 2,585 frozen original answers. Use Terra with high reasoning to rewrite broad automation in parsed proof terms, keeping every implementation, specification and existing concrete native test unchanged. Admit only exact-byte Lean/kernel and training-format passes; retain each unresolved original as a flagged fallback for the matched second training run.

## Frozen scope — 10-19-2026, before paid dispatch

- Input: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/onep7/data/existing.jsonl`, SHA-256 `7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b`; 2,585 rows.
- Actual Lean 4.22 parser extraction: 2,585/2,585 successful, 100,234 proof terms; 2,358 answers contain targeted proof automation and 227 require no proof replacement.
- Use `gpt-5.6-terra`, high reasoning, Codex CLI 0.114.0, isolated profiles and micro Git worktrees on skampere1. Initial four real training cases calibrate cost and throughput; then up to 32 lanes with 16 compiler slots and shared exposure reservations.
- At most two CLI attempts and four distinct source hashes per answer; 900 seconds per attempt, 120 seconds per compiler operation. Infrastructure/provider holds retain the original answer and all receipts. No silent model/key substitutions.
- User authorized the existing lab OpenAI key through Codex CLI. It is read only into the CLI environment from the private LFS key file; no key enters Git, worker prompts or model logs.

## Allowed change and acceptance

The compiler's syntax tree supplies exact proof-term byte ranges. The coordinator reconstructs the file from the untouched original bytes and replacement terms; every implementation, declaration statement, domain, hypothesis, namespace, API, test input and property definition is thereby preserved. A short English proof sketch is inserted immediately after imports. Helpers are proved local `have`/`let` constructions inside an existing proof term. Existing anonymous proofs using `native_decide` remain byte-identical executable tests, as required by the benchmark format.

Use the complete `expt_v9/prefer_explicit.py` automation inventory, including `simp`, `simpa`, `omega`, `exact?`, `aesop`, `linarith`, `nlinarith`, `ring`, `norm_num`, `decide` and related search/normalization tactics. Plain `exact`, `apply`, `rw`, `rfl`, `change`, `calc`, constructors, cases, induction and explicit `linear_combination` are permitted. Definitions that compute with `decide`, attributes such as `@[simp]`, and lemma identifiers are preserved as non-proof source. Do not conceal excluded tactics in macros or change theorem names/statements to evade the inventory.

Every replacement's full source passes the existing frozen kernel inspector, with all named theorem/lemma axiom cones restricted to `propext`, `Classical.choice`, `Quot.sound`; no verifier changes. `sorry`, `admit`, new axioms, native reduction in named proofs and elaborator escape hatches fail acceptance. Actual positive, unsolved negative, automation negative and proof-only preservation controls pass before dispatch.

The assistant answer keeps its original FILE envelope and unchanged system/user messages. The frozen FILE extractor and pinned Qwen tokenizer/chat template must agree exactly and remain within 16,384 total conversation tokens. The original tiny-example 1,000-token target does not apply to these older complete Python-to-Lean files. Comments explain the finished proof every few meaningful lines, with more detail at tricky steps.

## Money and compute

The user authorized an initial $300 total additional model spend and a further $300 if the first is insufficient. Initial cleanup allocation is $240 with $60 reserved for adaptation; the preapproved second tranche allows cleanup up to $480 and adaptation up to $120, total at most $600. All purposes share `adaptive_1p7b_campaign/budget.json` with a lock and append-only reservation/settlement events.

Verified official Terra pricing is input $2/M, cached input $0.20/M and output $12/M for ordinary contexts. Cache writes and long contexts may cost more; the ledger conservatively charges uncached input $5/M, cached input $0.40/M and output $18/M. It also retains the ordinary-rate estimate separately. These are configured-price estimates, not invoices. Sources: [model limits](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [pricing](https://developers.openai.com/api/docs/pricing).

The documented native limits are 1,050,000 context tokens and 128,000 output tokens. Before any CLI attempt reserve $10: one worst-case in-flight request is $7.554 at the conservative rates, plus a $1.20 observed-usage stopping threshold. Read actual cumulative `token_count` events every 0.2 seconds and terminate at the threshold; on missing usage charge the full reservation. Configure local context 128,000 and automatic compaction 100,000 to reduce actual exposure, while retaining the native-limit reservation. A synthetic session-log control verifies the same usage parser/threshold before paid work. Dispatches denied by the ledger wait for reservations to settle or become recorded budget fallbacks; no global daily guard is changed.

Compilation uses CPUs, no GPUs. The two training runs use separately assigned GPUs under V12. No validation/test content or model validation outputs are supplied to teacher workers. Final coordinator-only screens include 764 protected validation/test/fresh diagnostic references; replacements with exact or near overlap fall back to their original row.

## Outputs and matched-run contract

Remote run root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v13`.

- `final/replacements.jsonl`: successful replacement rows with original example index, original response hash, unchanged prompts, new source/response hashes and absolute frozen-kernel receipt path/hash.
- `final/cleaned_existing_training.jsonl`: all 2,585 answers in original order; failures/unattempted rows remain flagged original fallbacks.
- `final/row_results.csv`, `final/summary.json`: full denominator and each exclusion/fallback.
- Root `completion.json`: `DONE` or `DONE_PARTIAL`, all 2,585 accounted, exact `replacements_sha256` and training hash.
- Per-case original input/source, candidate source snapshots, actual compiler evidence, worker decisions, usage and model logs remain remote. Compact receipts and tables are mirrored to this experiment.

V12 preserves its frozen admitted original IDs and order and substitutes only rows matching the original response hash and passing its independent deterministic source/format checks. Training can proceed with partial cleaned coverage; coverage is reported rather than dropping difficult examples.
