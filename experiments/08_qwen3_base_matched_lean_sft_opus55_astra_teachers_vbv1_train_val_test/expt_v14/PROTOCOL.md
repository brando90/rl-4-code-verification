# Failure-guided curriculum preparation protocol

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/PROTOCOL.md

**TLDR:** Diagnose format, elaboration, proof, semantic and length failures separately. Add public or training-only examples that teach the missing operation, retaining Python-to-Lean examples in every training mixture. New candidates require the existing kernel and contamination gates.

## Starting evidence

The version 6 matched comparison evaluated every one of 135 validation tasks with eight attempts per system (1,080 cells). Control produced 99 successes (9.17%); adding the original tiny curriculum produced 74 (6.85%). The paired difference was −2.31 percentage points, task-bootstrap 95% interval [−3.89, −0.83], 10,000 draws, seed 0, p-value not computed. There was one training seed. Starting-checkpoint historical results were 55/1,080 and used a historical runtime, so their comparison is descriptive. These are binary test-and-proof success numbers, not formal specification coverage or SCSC.

Version 7 had 29/50 seen tiny tasks and 9/50 fresh tiny tasks pass strict checks. All 100 extracted correctly; 40 compiled and were kernel honest; 60 failed compilation. Two fresh files compiled but failed Python differential behavior. Fresh data and outputs are protected, not curriculum inputs. The fixed format was already attainable on short diagnostic tasks; longer validation generations were much less reliable. In version 6, control extracted 979/1,080 and hit the length cap on 101/1,080; mixed extracted 976/1,080 and capped on 104/1,080. Mean generated lengths were 4,753 and 4,840 tokens, respectively.

## Adaptive decisions

Use aggregate categories and generic names of Lean syntax/type errors. Never supply protected task text, model solutions, gold references, concrete failing expressions, or task-specific repairs to data authors. A category may prioritize independently selected public-source or train-split examples; it does not authorize generating a solution to that validation task.

| Observed gap | Training intervention | Evidence to record |
| --- | --- | --- |
| Missing FILE boundary, code fence, missing final close or truncation | More short complete files in the identical wrapper; one concise proof sketch, focused inline comments; track response length percentiles; train stopping/EOS | Extracted / declared, capped / declared, generated token distribution |
| Natural/integer/real/Boolean type mismatches, coercions, unknown names | Small pinned-toolchain public examples of the same generic construct, explicit type annotations, explicit named lemmas and coercion steps | Compiler-category counts, source family, token exposure |
| Unsolved proof goals or inappropriate automation | Existing explicit alternatives first; otherwise bounded Terra rewrites that preserve statements and implementations, using explicit terms, induction, rewriting and named lemmas | Before/after automation inventory, exact target/implementation audit, kernel receipts |
| Python behavior mismatch despite compilation | Public/train-only translation exercises covering integer division/modulo, negative values, list indexing, empty inputs and return types; differential tests | Differential success / compiled and case manifests |
| Retention loss on Python translation while theorem-only training improves | Increase Python-to-Lean assistant-loss token share or use theorem pretraining then a short translation replay phase; keep comparisons at a declared token budget | Per-source assistant-loss tokens, optimizer schedule, paired validation differences |
| Broad improvement but unstable proof completion | Smaller learning rate and checkpoint selection on validation; repeat a promising frozen recipe with a second training seed | Checkpoint identity, seed, complete common validation manifest |

Adding data is a hypothesis, not a promotion criterion. Keep the first all-current-data run intact. The cleaned-data comparison starts from the same initialization and uses a declared assistant-loss-token budget; record differences in source composition and actual exposure. Do not hide a regressed run or cherry-pick its individual completions. A 25% target means the predeclared binary success metric on the complete fixed validation cohort, not pass@8 or a filtered easier subset.

## Public source candidates

### Mathlib

Pin `leanprover-community/mathlib4` at `79e94a093aff4a60fb1b1f92d9681e407124c2ca`, Lean 4.22.0, Apache-2.0. The preparer selects complete short modules whose last named theorem is identifiable without modifying its context, retains all original imports and the full original file, and constructs a completion prompt with the final theorem body omitted. It never replaces original imports with `import Mathlib`; the latter can import the target itself. This conservative text selection is candidate discovery, not a parser or verification certificate. Kernel verification of the exact complete file and target is mandatory. Full import/context preservation and source hashes are retained. Prefer explicit target proof bodies and reject placeholder/new-axiom/native-decide files. Retain upstream source and copyright/license notices outside the model response as provenance, and original file comments within it.

### DeepSeek-Prover-V1

Pin revision `1ee889f608fb12ba3596757ee91a60acd663ea81`, source JSONL SHA256 `a2cdac64d011eee00836ce1a2c5511dfa5567346afabe897c3309ac17771b92b`, 27,503 upstream train rows. Preserve header, statement and proof exactly. This source uses Lean 4.7.0-rc2 historically; successful current Lean 4.22 compilation cannot be assumed. The dataset license remains unresolved; the user explicitly authorized provisional use while obtaining mentor confirmation. Record `license_unresolved_user_authorized` in manifests rather than falsely describing it as cleared. Start with short explicit proofs and the relevant gap tags, not a blanket 27,503-proof rewrite.

## Candidate gates

1. Hash and immutable revision agreement; retain upstream row/module identity and license status.
2. Current pinned Lean compile and frozen kernel inspector, allowed axioms only, no `sorry`, `admit`, new axioms or `native_decide`.
3. Exact theorem statement and implementation preservation for any repair; separate source meaning review where there is an English statement.
4. Existing broad automation inventory; explicit named terms, `rw`, `rfl`, constructors, cases, induction, and explicit `linear_combination` remain permitted.
5. Actual frozen FILE extraction plus Qwen template/token checks, answer sketch/comments, no invented Python wrapper for theorem-only data.
6. Global exact/near protected screens and exact statement/prompt deduplication against all admitted pools.
7. Freeze JSONL hash, source counts and assistant-loss-token exposure before each run. Raw model traces remain remote and are excluded from training.

## Unattended hosts

SNAP is primary. Existing detached sessions survive SSH loss but not a reboot automatically. Current eth127 Kerberos tickets expire at 10-20-2026 00:53:33 UTC; new AFS key reads after that require renewed tickets unless a private local copy has been staged by the coordinator. Do not assume brando9's documented keytab renewal is installed for eth127. An SSH master also expires eventually; server-side workers, models, corpus, tools and an approved local private credential must remain usable without the Mac.

GX10 fallback uses a dedicated user-owned venv and official CUDA 13 ARM wheels. Docker currently requires a password/group change, which the venv route avoids. It is training-capable only after a real GB10 tensor/matrix backward control and an actual tiny Qwen optimizer step pass. This experiment runs only the bounded tensor control; it does not launch a model or allocate new paid compute.
