# Current-toolchain verification of remaining Workbook candidates

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v10/PROTOCOL.md

**TLDR:** Compile all 10,995 retained but unchecked Workbook candidates with the existing pinned Lean 4.22 and frozen kernel inspector. Preserve all failures and the earlier curation record; no model calls or new training.

Frozen 10-19-2026 05:17 , before bulk checks. Input is version9’s complete retained, formatted Workbook cohort lacking current kernel verification. Check the exact selected unannotated source against its saved source hash. The 500 unchanged tiny examples and 672 checked Workbook proofs retain their existing evidence and are not recompiled.

Run 48 concurrent single-threaded Lean checks on skampere1, with 15 seconds per compiler operation and one native check per cell. Compiler/kernel gates remain unchanged: a valid complete inspector report, at least one named theorem, every theorem honest, and no axioms outside propext, Classical.choice and Quot.sound. Preflight positive, sorry and declared-axiom controls. This new full-cohort check does not consume or rewrite the earlier review’s bounded alternative-selection attempts. Infrastructure recovery resumes saved successful/failed cells without resampling or silently changing budgets.

All 10,995 cells receive source-hash receipts and an outcome. Failed proofs remain excluded; timeouts and compatibility failures do not establish mathematical invalidity. Record exact inspector, source, manifest and output hashes. Raw compiler files stay on the cluster; compact per-row results and summaries go to Git. A persistent named tmux process owns the queue and records live progress. No GPU is allocated.

The prior 74 unresolved cases receive a diagnostic audit from existing compiler receipts, without new model calls or proof edits. Categories may overlap. Compatibility repair or increased resource budgets are separate prospective amendments preserving original source and outcomes. The 1,082 semantic rejections remain preserved and quarantined as single-model judgments; bulk compilation cannot validate informal/formal alignment.

The GX10 is reachable (20 ARM CPU cores) but currently has no Lean toolchain/cache. Start the cluster queue immediately. Add GX10 execution only if a matching frozen environment passes controls and can reduce the remaining wall time; reserve disjoint cells or use verified atomic ownership. Existing training jobs are preserved.

## Unresolved recovery amendment, 10-19-2026 05:19 PDT

Before recovery checks, declare all74prior unresolved cases. For parser cases, add legacy single-binder summation/product macros expanding directly to `Finset.sum`/`Finset.prod`; retain the exact original theorem statement and supplied proof body. Test the notation on a known finite sum first. For actual recorded recursion/heartbeat/timeout failures, allow60seconds per compiler operation. Check at most two existing indices per eligible case: the prior selected index and original0, without replacement sampling or new proof generation. Use four additional CPU workers. Other library/proof failures remain explicitly excluded; no automatic theorem edits. Every recovery is a separate condition with original outcomes retained. Recovered proofs require comment reassembly/format checks and protected screens before training admission. No paid model calls.

## GX10 acceleration amendment, 10-19-2026 05:25 PDT

Freeze the last1,600cells of the original10,995-cell manifest as a native ARM accelerator shard. Use the exact same selected source bytes, Lean4.22.0, Mathlib79e94a0, inspector bytes and15-second/compiler-operation gate, with16single-threaded CPU workers. Native import and positive/sorry/declared-axiom controls must pass first. This extends execution to a second architecture, without generating new proofs or changing statements. Both hosts retain their own complete raw evidence.

The laptop relays completed GX10 successes only after validating the actual inspector report and exact frozen source hash. It publishes a reusable receipt only if the cluster cell has no existing owner directory, using an atomic directory rename. The cluster dispatcher reuses these verified receipts when it reaches the shard. Existing cluster results are never overwritten; independent overlaps remain recorded by host, and a possible concurrent start leaves original cluster execution authoritative. At most one native attempt per source per host, with no retries of failed proofs. Failed ARM checks do not replace the original cluster attempt. If the relay is unavailable, both host jobs continue and the cluster still finishes the full declared cohort. Source/manifest/inspector hashes and host attribution remain explicit. This relay performs orchestration only; no experiment runs on the laptop.
