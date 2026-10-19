# Prospective amendment: validate all prepared public-source candidates

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/AMENDMENT_bulk_validation.md

**TLDR:** Compile the frozen 217 Mathlib and 512 DeepSeek candidate files on SNAP with eight CPU workers and the unchanged Lean 4.22/kernel inspector. Record all 729 outcomes; a formal pass remains outside training until the other admission gates pass.

## Prospective scope, 10-19-2026

The coordinator authorized this CPU-only pass before its first compilation. The existing version 12 training pool and both training conditions are unchanged. There are no model calls, proof changes, automatic repairs, paid compute allocations or new source selections in this pass.

- Cohort: exactly 217 existing `mathlib_candidates.jsonl` rows and 512 existing `deepseek_candidates.jsonl` rows.
- Mathlib candidate SHA256: `51c8991b689a5b27ee071dc787d33c086687f49fde6a748d0374f96c5b878e61`.
- DeepSeek candidate SHA256: `9538fcd310754eb54122d09a6c689403823fa78f79dce7cac7b2611b7c7f3d4d`.
- Mathlib pin: `79e94a093aff4a60fb1b1f92d9681e407124c2ca` (Lean 4.22.0).
- DeepSeek pin: `1ee889f608fb12ba3596757ee91a60acd663ea81`; raw artifact SHA256 `a2cdac64d011eee00836ce1a2c5511dfa5567346afabe897c3309ac17771b92b`.
- Frozen kernel-inspector SHA256: `5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287`.
- Eight single-threaded Lean workers, 60 seconds per compiler operation, one measured attempt per candidate. Successful receipt reuse on coordinator resume must validate the exact source and existing compiled-module bytes; an interrupted unreceipted operation can be restarted once, retaining its prior evidence.

## Freeze and controls

Before compilation, validate cohort hashes, source revisions, source records and all assistant-source hashes. For Mathlib, compare each complete candidate file with the actual immutable Git blob at the pinned revision and matching shared source file. Preserve every original import, helper, namespace, typeclass/variable context and theorem. For DeepSeek, reconstruct the exact candidate from its pinned raw row (`header + newline + formal_statement + newline + formal_proof + newline`) and require its original train label. Reconstruct the original prefix prompt and require message equality. Freeze a per-row manifest, source copies, toolchain identity, inspector hash and driver hash.

Run a proved positive theorem plus `sorry` and declared-axiom negative controls before the cohort. Compilation is insufficient: every named source theorem and helper must be inspected, honest, source-position resolved, and restricted to `propext`, `Classical.choice`, `Quot.sound`. Require exact source-hash agreement and the frozen inspector's report validation. Do not enable `native_decide`.

The first positive-control gate compiled and passed kernel inspection, then exposed a driver receipt-path bug: the inspector's `compiled_module` field is a Lean module identifier, not a filesystem path. The driver now hashes `evidence_dir/original.olean`. That failed preflight and its original freeze are retained under `preflight_failures/compiled_module_identifier_path/`. No cohort candidate had been compiled before this correction; the identical 729-source manifest is re-frozen with the corrected driver hash.

## Outcomes and later admission

Keep every declared row in the CSV, including unstarted, failed, timed-out and executor-error cells. Retain exact per-row source and kernel receipts remotely. A `FORMAL_PASS` means the supplied formal declarations compile and have honest kernel proofs. It does not establish that an English statement was faithfully formalized, nor does it certify a benchmark score. Flag possible untyped fractional-exponent expressions for semantic review without claiming they are necessarily wrong.

All rows retain `training_admitted=false`. A formal pass still needs the sketch/comment policy, exact frozen FILE/template/token checks, protected exact/near screens, global deduplication and semantic/context checks required by the original protocol. DeepSeek retains `license_unresolved_user_authorized`. Failures remain preserved and excluded from training pending a separate bounded repair decision.

## Persistence

Run from `public_gap_sources_v14/` in a named detached `rl4cv-public-source-verify-v14` tmux session. An ordinary parent watcher records driver exit, final completion or failure, and a heartbeat. It performs at most one resume after an interrupted driver; no model is involved. The batch uses local scratch and existing readable Lean binaries/dependencies, so it does not need the laptop or an AFS credential read. Root publication collects compact JSON/CSV receipts; full sources and compiler artifacts stay on SNAP.
