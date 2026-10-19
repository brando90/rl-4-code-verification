# Public source audit: Mathlib4 and MiniF2F/ProofNet validation

Observed 10-19-2026. This audit inspected public source repositories and local data-policy text. It did not inspect protected local benchmark contents, generate proofs, or compile source files. Counts below come from reading the pinned public source archives or JSONL records; they are not kernel-verification results.

## Mathlib4: complete proofs available at our existing toolchain

- Official source: <https://github.com/leanprover-community/mathlib4>.
- Target revision: **`79e94a093aff4a60fb1b1f92d9681e407124c2ca`**, the official **`v4.22.0`** tag, exactly matching the existing experiment's Mathlib pin.
- Immutable toolchain evidence: [lean-toolchain](https://github.com/leanprover-community/mathlib4/blob/79e94a093aff4a60fb1b1f92d9681e407124c2ca/lean-toolchain), specifying Lean `v4.22.0`.
- License: **Apache-2.0**, [pinned LICENSE](https://github.com/leanprover-community/mathlib4/blob/79e94a093aff4a60fb1b1f92d9681e407124c2ca/LICENSE). Retain applicable source copyright and attribution notices with extracted or modified material.
- Real complete proof evidence: [Mathlib/Data/List/Basic.lean](https://github.com/leanprover-community/mathlib4/blob/79e94a093aff4a60fb1b1f92d9681e407124c2ca/Mathlib/Data/List/Basic.lean) contains complete theorem bodies together with original imports, namespace, variables and prerequisite declarations.
- Do not use current master automatically: the observed master toolchain was `v4.36.0-rc1`, incompatible with assuming our existing `v4.22.0` environment.

### Recommended normalization

Use **full-module proof completion preserving the original imports and context**. A prompt may supply the original module prefix and a theorem with an explicitly missing proof; its assistant answer should be a complete source file in our existing file-marker and Lean-code-block envelope. Preserve namespaces, scoped notation, universe/variable declarations, local instances, helper declarations, declaration order and relevant options. Select short modules or bounded prefixes first and record source byte ranges, hashes and declaration names.

Do not replace original imports with `import Mathlib` indiscriminately. That aggregate imports the original target theorem as well, which can hide missing dependencies and enable answers that invoke the target by its original name. Do not split source solely with a theorem regex and presume the result retains its elaboration context. Parsed declaration boundaries and pinned-environment verification are preferable.

This audit did not enumerate all admissible proofs or establish an admitted count. Admission still requires contamination screening, complete-proof checks, toolchain compatibility and actual verification receipts. Preserve proof-only task semantics; do not manufacture Python inputs.

## MiniF2F: public validation statements, no complete targets in inspected Lean4 port

- Canonical benchmark: <https://github.com/openai/miniF2F>.
- Observed canonical source revision: **`4e433ff5cadff23f9911a2bb5bbab2d351ce5554`**. Its [pinned README](https://github.com/openai/miniF2F/blob/4e433ff5cadff23f9911a2bb5bbab2d351ce5554/README.md) documents optional example proofs, validation allowed for development, and test reserved for final evaluation. The canonical Lean license is [Apache-2.0](https://github.com/openai/miniF2F/blob/4e433ff5cadff23f9911a2bb5bbab2d351ce5554/lean/LICENSE). Artifact counts below use the Lean4 port pin rather than the original Lean3 source.
- Public Lean4 port: <https://github.com/yangky11/miniF2F-lean4>.
- Inspected immutable revision: **`5746b7d6c47855ce1294bed87329618ff7f1bc31`**.
- Port repository license: **MIT**, [pinned LICENSE](https://github.com/yangky11/miniF2F-lean4/blob/5746b7d6c47855ce1294bed87329618ff7f1bc31/LICENSE). The canonical project's Lean material is described as Apache licensed; preserve upstream attribution and relevant notices rather than treating the port license as erasing upstream terms.
- Toolchain: **Lean/Mathlib `v4.24.0`**, [lean-toolchain](https://github.com/yangky11/miniF2F-lean4/blob/5746b7d6c47855ce1294bed87329618ff7f1bc31/lean-toolchain), [lakefile.lean](https://github.com/yangky11/miniF2F-lean4/blob/5746b7d6c47855ce1294bed87329618ff7f1bc31/lakefile.lean).
- Archive count: **244 validation task files; all 244 contain a `sorry` token; zero without `sorry`**. The 244 test task files also all contain `sorry`; these test files are not candidates for the requested validation-only ingestion.
- Concrete placeholder: [MiniF2F/Valid/amc12_2000_p5.lean](https://github.com/yangky11/miniF2F-lean4/blob/5746b7d6c47855ce1294bed87329618ff7f1bc31/MiniF2F/Valid/amc12_2000_p5.lean) ends with `:= by sorry`.

**Blocker:** this Lean4 port supplies prompts, not complete supervised proof answers. Acquire separately licensed complete solutions, or generate and verify solutions as a separately recorded stage, before placing these problems into supervised training. A successful compilation with `sorry` is not a proof receipt. Migration from its `v4.24.0` source environment to our `v4.22.0` target also needs checking.

## ProofNet: public validation statements and English proofs, no formal proof answers

- Canonical source: <https://github.com/zhangir-azerbayev/ProofNet>.
- Inspected canonical revision: **`509ad79710ed4f46ff5c282ed5640c1aa9ac3f30`**.
- Canonical license: **MIT**, [pinned LICENSE](https://github.com/zhangir-azerbayev/ProofNet/blob/509ad79710ed4f46ff5c282ed5640c1aa9ac3f30/LICENSE).
- Canonical validation source: [benchmark/valid.jsonl](https://github.com/zhangir-azerbayev/ProofNet/blob/509ad79710ed4f46ff5c282ed5640c1aa9ac3f30/benchmark/valid.jsonl), **185 records**, fields `id`, `formal_statement`, `src_header`, `nl_statement`, `nl_proof`. The formalizations are Lean3 and the statements do not supply complete Lean4 proof targets.
- Canonical test has **186 records**, reserved from this requested validation-only import.
- Public Lean4 port: <https://github.com/rahul3613/ProofNet-lean4>.
- Inspected port revision: **`6deae98b38954dadf732746d023e8be65c56f246`**.
- Port license: **MIT**, [pinned LICENSE](https://github.com/rahul3613/ProofNet-lean4/blob/6deae98b38954dadf732746d023e8be65c56f246/LICENSE).
- Port toolchain: **Lean/Mathlib `v4.20.0`**, [lean-toolchain](https://github.com/rahul3613/ProofNet-lean4/blob/6deae98b38954dadf732746d023e8be65c56f246/lean-toolchain), [lakefile.lean](https://github.com/rahul3613/ProofNet-lean4/blob/6deae98b38954dadf732746d023e8be65c56f246/lakefile.lean).
- Pinned data: [proofnet_lean4.jsonl](https://github.com/rahul3613/ProofNet-lean4/blob/6deae98b38954dadf732746d023e8be65c56f246/proofnet_lean4.jsonl), **374 records**, fields `name`, `source`, `header`, `formal_statement`, `formal_proof`, `informal_stmt`, `informal_proof`.
- **All 374 records have `formal_proof: null`; all 374 formal statements contain `sorry`.** A source-file example is [formal/Artin.lean](https://github.com/rahul3613/ProofNet-lean4/blob/6deae98b38954dadf732746d023e8be65c56f246/formal/Artin.lean).

### Recovering the requested validation subset

Normalize canonical `id` and port `name` by lowercasing and replacing each maximal non-ASCII-alphanumeric run with `_`, stripping surrounding `_`. This joins **185/185 canonical validation records** and **186/186 canonical test records** to the port. Keep only the 185 validation IDs for this source. The port's three additional Cambridge Tripos records are outside that mapping and should remain excluded:

- `Cambridge_Tripos_exercise_2022_IA_4_I_1E_a`
- `Cambridge_Tripos_exercise_2022_IA_4_I_2D_a`
- `Cambridge_Tripos_exercise_2022_IB_3_II_13G_a_i`

The port's `informal_stmt` can already contain an English proof, and some `informal_proof` fields repeat unrelated text. Prefer canonical English fields linked by source ID, retaining provenance. Do not treat all English proof text as a checked or necessarily correct proof.

**Blocker:** complete Lean4 proof targets must be sourced or generated and verified. Normalization cannot turn null formal proofs or `sorry` placeholders into supervised proof answers. Lean4 `v4.20.0` source compatibility with target `v4.22.0` remains unverified.

## Admission policy

These sources are not banned by name in `CLAUDE.md` or `docs/DATASETS.md`. Public availability is not admission. Before training, retain licenses and provenance, run the repo's exact and word-5-gram screens against protected panels, exclude flagged examples according to the locked experiment protocol, and record verified answer counts separately from acquired prompt counts. No validation/test task content or derived debugging material may be supplied to annotation or proof-generation workers.
