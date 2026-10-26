# Public synthetic proof source audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v8/source_audit_synthetic.md>

**TLDR:** Both DeepSeek-Prover-V1 and Lean Workbook are public downloads with proof material. DeepSeek's public artifact has 27,503 rows and an unresolved dataset license. Workbook has 140,214 statements, of which 12,823 have candidate whole proofs. These counts come from parsing the pinned source artifacts on 10-19-2026; no model calls, compilation, held-out local reads, or corpus writes were performed for this audit.

## DeepSeek-Prover-V1

| Item | Observed value |
|---|---|
| Official dataset | <https://huggingface.co/datasets/deepseek-ai/DeepSeek-Prover-V1> |
| Pinned revision | `1ee889f608fb12ba3596757ee91a60acd663ea81` |
| Immutable artifact | <https://huggingface.co/datasets/deepseek-ai/DeepSeek-Prover-V1/resolve/1ee889f608fb12ba3596757ee91a60acd663ea81/dataset.jsonl> |
| Format / bytes | JSONL / 19,588,269 |
| SHA256 | `a2cdac64d011eee00836ce1a2c5511dfa5567346afabe897c3309ac17771b92b` |
| Actual rows | 27,503; all `split=train` |
| Fields | `name`, `split`, `formal_statement`, `goal`, `header`, `formal_proof` |
| Proof presence | All 27,503 have nonempty string `formal_proof`; zero literal `sorry` substrings there |

Construct a candidate complete file as `header + formal_statement + formal_proof`; the statement already ends in `:= by`. Keep `goal` as optional provenance, not an extra target that changes the task. The absence of a literal placeholder is not a current-toolchain or axiom-check certificate.

The [original paper](https://arxiv.org/html/2405.14333) names Lean `v4.7.0-rc2` and Mathlib commit `64528268b3c2cf578639bc479828882a9ecd3a82`. Its reported eight-million training pairs are not the size of this public artifact.

### License evidence and admission recommendation

- [Pinned dataset card](https://huggingface.co/datasets/deepseek-ai/DeepSeek-Prover-V1/resolve/1ee889f608fb12ba3596757ee91a60acd663ea81/README.md): metadata says `license: other`, `license_name: deepseek-license`, `license_link: LICENSE`.
- [Pinned linked LICENSE](https://huggingface.co/datasets/deepseek-ai/DeepSeek-Prover-V1/resolve/1ee889f608fb12ba3596757ee91a60acd663ea81/LICENSE): zero bytes. The dataset's six publicly listed commits were inspected through the [official history API](https://huggingface.co/api/datasets/deepseek-ai/DeepSeek-Prover-V1/commits/main); every tree has the same empty license. No historical complete dataset license was found.
- [Upstream model license](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V1/resolve/304287b0ec4bacee1a6c57fa1a7cb6c83282e6fb/LICENSE-MODEL): custom DeepSeek License Agreement v1.0. Its definitions explicitly exclude Data from its license grant; its model-derivative definition includes some distillation from outputs. The [separate MIT code license](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V1/resolve/304287b0ec4bacee1a6c57fa1a7cb6c83282e6fb/LICENSE-CODE) does not establish a dataset grant.

**Recommendation:** source can be downloaded, normalized and screened with status `license_unresolved`, but do not call it license-cleared training data. Public availability and the model card's support for commercial model use do not resolve the dataset-specific gap.

## Lean Workbook

| Item | Observed value |
|---|---|
| Official dataset | <https://huggingface.co/datasets/internlm/Lean-Workbook> |
| Pinned revision | `2e066e310b2c6d2c27616927ae131f82901c8f1c` |
| Immutable primary artifact | <https://huggingface.co/datasets/internlm/Lean-Workbook/resolve/2e066e310b2c6d2c27616927ae131f82901c8f1c/lean_workbook.json> |
| Format / bytes | JSON array / 94,484,955 |
| SHA256 | `577430f83caf094f1d9b99c9a3d18d92130fa21e74939d1b528b39c1927a7b0c` |
| Actual rows | 140,214 = 57,321 `lean_workbook` + 82,893 `lean_workbook_plus` |
| Fields | `natural_language_statement`, `answer`, `tags`, `formal_statement`, `split`, `proof` |
| Nonempty proof lists | 12,823 = 4,914 base + 7,909 plus |
| Total proof strings | 223,156; zero literal `sorry` substrings in these strings |

The source card says 57,231 base rows, differing from the actual 57,321 parsed rows. Each `proof` is a list of alternative proof scripts for one statement, **not consecutive steps to concatenate**. Statements include a placeholder `:= by sorry`; replace the final placeholder with one selected proof script, preserving indentation. Empty-proof rows have no supervised complete-proof answer and must not become assistant answers ending in `sorry`.

The same release includes [wkbk_1009.parquet](https://huggingface.co/datasets/internlm/Lean-Workbook/resolve/2e066e310b2c6d2c27616927ae131f82901c8f1c/wkbk_1009.parquet), 4,600,174 bytes, SHA256 `80275c48d2ec0f989aadb248380f37b9da5131c48a17a7a92898f760c2c663f2`. The official viewer exposes approximately 25.2k tactic-transition rows with fields `id`, `status`, `tactic`, `state_before`, `state_after`, `natural_language_statement`, `answer`, `formal_statement`. It includes `disproved` cases; these cannot be attached as proofs of the original positive statement. Prefer the whole-proof JSON for the current file-answer normalization.

### Toolchain and license evidence

- [Pinned dataset card](https://huggingface.co/datasets/internlm/Lean-Workbook/resolve/2e066e310b2c6d2c27616927ae131f82901c8f1c/README.md): Apache-2.0 metadata, Lean `v4.8.0-rc1`, Mathlib corresponding tag `v4.8.0-rc1`.
- [Official code README](https://raw.githubusercontent.com/InternLM/InternLM-Math/eaead17b7b95670f0592f5b818080fb6762f3fdf/leanworkbook/readme.md): instead says Lean `v4.7.0`; record this upstream discrepancy.
- [Official import header](https://raw.githubusercontent.com/InternLM/InternLM-Math/eaead17b7b95670f0592f5b818080fb6762f3fdf/leanworkbook/header.lean) supplies the historical imports and `open BigOperators Nat Real Rat`.
- [Official code license](https://raw.githubusercontent.com/InternLM/InternLM-Math/eaead17b7b95670f0592f5b818080fb6762f3fdf/LICENCE) contains Apache-2.0 text. The dataset repository has no separate `LICENSE` file; its license evidence is the explicit dataset-card metadata.

**Recommendation:** normalize proof-bearing rows as auxiliary theorem-to-complete-Lean-file chat examples, retaining source IDs and alternative indices. Do not invent Python wrappers. Preserve license/provenance and group alternatives by original statement before any training/dev split. Check contamination, current Lean 4.22 compatibility, allowed axioms and any applicable quality gates before admission; old source-version claims do not certify current compatibility. No proof generation is needed for the already supplied candidate scripts.
