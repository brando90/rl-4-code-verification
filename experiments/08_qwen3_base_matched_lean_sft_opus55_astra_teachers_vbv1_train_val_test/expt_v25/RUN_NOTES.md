# V25 matched proof-version run

## Frozen intervention and actual launch

The dataset contains the exact **3,568 V20 example IDs, prompts, row order, pools
and batch indices**. The trainer verifies every prompt-token prefix and all 1,784
batch indices against the frozen V20 files, and uses the exact recorded V20
learning rate for each optimizer update. Original pretrained
`Qwen/Qwen3-1.7B-Base` revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`
is reloaded with a fresh optimizer after the disposable control.

**2,094 rows (58.69%) restore admissible original automation-containing proofs;
1,474 rows retain the exact V20 JSONL bytes.** The response proof version changes;
there are no newly generated teachers, new tasks, dropped IDs, new tiny examples,
or late Workbook additions.

| Pool | Total | Restored | Exact V20 retained |
|---|---:|---:|---:|
| Python | 684 | 683 | 1 |
| Workbook | 2,145 | 1,411 | 734 |
| Prior explicit repairs | 61 | 0 | 61 |
| Public Mathlib/DeepSeek | 678 | 0 | 678 |
| Total | 3,568 | 2,094 | 1,474 |

Of the unchanged rows, 1,328 already had the same original non-comment proof or
never had an automation-cleanup predecessor. The remaining 146 are explicit
pairing gaps: 69 parser failures, 13 cases with no admissible different original
automation-containing proof span, and 64 composed candidates that failed the
full-source check. Nine unsafe original named-proof slots retain their V20 proof
even where other proof slots in the row are restored. No named `native_decide`,
holes, declared axioms or failed proofs were admitted to force pairing coverage.

V20 code outside parser-owned proof terms is preserved. Proof-dependent sketches
and comments are adapted mechanically to describe the actual restored tactics;
the comment adaptation asserts identical non-comment tokens. Unchanged rows keep
their original comments exactly. Current source/response hashes and all per-row
restoration choices are recorded in the frozen data and row table.

The resulting assistant-loss budget is **2,793,297 tokens**, versus V20's
2,948,296, with the same 1,784 optimizer updates and learning-rate sequence.
The longest sequence is 8,723 tokens. Loss-token lengths and the corresponding
within-batch token weighting naturally differ with the proof versions; this is
not a matched-token-budget comparison.

Frozen training SHA256:
`6dad28a97f534c765275397727f6072ae535dfb8813bf1dfb40a9b76bad6ad97`.

The discarded original-base longest/shortest control passed on GPU 3, with
27.97 GiB peak allocated memory. Production **PID 3335074** made its first actual
optimizer update on **A100 GPU 3** at Unix **1792454240.9934413**, after reloading
the original base model and a fresh AdamW optimizer. First learning rate:
`1.0000000000000002e-06`, exactly as recorded for V20.

## Provenance fields in changed rows

Changed rows intentionally retain their V20 lineage metadata, including fields
such as `remaining_automation`, `selection_policy`, `verification_basis`,
`automation_cleanup_v18`, and historical annotation/token-count fields. These
describe earlier source stages and are **not the current V25 proof-version
authority**. The current authority is:

- `automation_restoration_v25` in each changed row;
- the frozen `base/data/row_results.csv`;
- actual assistant content plus its updated `response_sha256`/`lean_sha256`;
- `base/data/tokens.pt`, `token_manifest.json` and `prepare_receipt.json` for
  actual token lengths and loss masks;
- the referenced V25 full-source or comment-equivalence verification receipt.

No post-freeze metadata edit was made to the dataset.

## Verification and planned evaluation

All 2,158 composed candidates were accounted for in 315.6 seconds using at most
96 single-thread Lean checks. There were 2,094 passes and 64 actual compile
failures. Of the passes, 134 reuse source-bound frozen kernel evidence after
checking full-source comment equivalence and excluding source-position
metaprogramming; 1,960 pass new full-source checks. All 2,024 new checks retain
durable compiler stdout/stderr, command/source/compiler identities, exit/timeout
status and kernel evidence. Failed candidates retain their exact V20 rows.

The frozen 764-reference protection screen retains zero exact or near matches.
The original prompts were audited for tactical restrictions; no instruction
contradicting restored automation was found.

The persistent pipeline trains once, generates the full fixed 135 × 8 validation
manifest and invokes the mandatory durable-logging 32-worker scoring entry from
`expt_v24/future_logging/`. Compile/kernel time limits and theorem acceptance are
unchanged. It does not open the test split. Scores are pending; no improvement or
25% target claim is made from training loss.

## Remote artifacts

Root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v25`.

- `counterpart_audit/`: all original source mappings and cached evidence audit.
- `counterpart_sources/`: exact baseline/original sources, native parser ranges,
  composed counterparts, and parser command logs.
- `restoration_candidates/`: admissible proof-slot choices and explicit gaps.
- `restoration_verification/`: every completed pass/failure, evidence and final
  accounting receipt.
- `base/data/`: immutable matched training data, schedule, token masks and freeze.
- `base/{smoke,run}/`: discarded control and actual fresh-base training trajectory.
- `validation/v25_base/`: future complete generations and evaluated agent files.
- `scoring_parallel_v1/`: future full 1,080-cell ownership/results and durable logs.
- `analysis/v25_base_{summary.json,cells.csv,tasks.csv}`: authoritative final score
  when evaluation completes.
