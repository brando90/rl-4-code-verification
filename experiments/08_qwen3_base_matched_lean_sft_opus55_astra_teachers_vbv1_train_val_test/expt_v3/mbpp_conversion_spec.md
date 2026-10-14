# MBPP conversion specification (frozen encoding, version 1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/mbpp_conversion_spec.md>

**TLDR:** The 587 Mostly Basic Python Problems (MBPP) `system/user/lean` rows from experiment 02A version 3 become experiment 08 `messages` examples by keeping their system and user texts byte for byte (they already use experiment 103's frozen system prompt and VBV1 addendum) and wrapping the kept Lean bytes, unchanged, in the one assistant envelope that experiment 103's extractor decodes back to the same bytes. Any row whose round trip fails is rejected, never repaired. Prepared for Lethan (owner of the MBPP conversion) and Rakshit; frozen on 10-14-2026 by `admit_corpus_v3.py`.

## Source

- File: `/lfs/skampere1/0/brando9/rl4cv_e02a_v3/sft/lean_warmstart_v3.jsonl` (host only), SHA-256 `2a3380227dedcb53aa449d50e2823e4a34bfb25ecdcf5b0c1c618b280d6b3c8a`, 587 rows over 455 distinct `mbpp__task_N` identifiers; row keys `lean`, `lean_sha256`, `model`, `prompt_sha256`, `system`, `task_id`, `teacher`, `user`.
- Each row's `lean` is the extracted file that passed 02A v3's keep rule (`kernel_binary = 1` under the frozen scorer and screen-clean against all 896 VeriBench V1 tasks, its historical rule). Version 3 re-screens it against the D-013 validation and test splits anyway.

## Encoding (exact)

For a row with required output path `P` (the single path that `vb103_single_call.required_paths(instruction, "vbv1")` returns for the row's instruction, for example `/home/user/lean_project/Veribench/task_1.lean`) and kept Lean text `L`:

```text
messages = [
  {"role": "system",    "content": row.system},   # must hash to dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd
  {"role": "user",      "content": row.user},     # instruction.rstrip() + "\n\n---\n\n" + addendum (addendum SHA-256 a7a0fc1b…)
  {"role": "assistant", "content": "FILE: " + P + "\n```lean\n" + L + ("" if L.endswith("\n") else "\n") + "```\n"}
]
```

- The instruction is `row.user` with the frozen `"\n\n---\n\n" + addendum` suffix removed; the system prompt and addendum are verified by hash against the version-1 corpus before any row is converted.
- `L` is never edited, trimmed, re-indented or re-wrapped. The only byte added inside the fence is a single trailing newline when `L` lacks one, so that the closing fence starts a line; the extractor's output must still equal `L` byte for byte or the row is rejected (`envelope_round_trip_mismatch`).
- No hidden reasoning is invented: the template's empty `<think>\n\n</think>\n\n` block is inserted by the Qwen3 chat template at render time exactly as for the version-1 teacher responses, so the loss span is `<think>\n\n</think>\n\n` + assistant + `<|im_end|>\n`.
- Provenance kept on every converted example: `source = mbpp_lean_warmstart_v3`, `task_id`, `teacher` (vendor), `model` (exact generator id), `lean_sha256`, `response_sha256` (hash of the envelope), `lean_norm_hash`.

## Checks every converted row must pass (in `admit_corpus_v3.py`)

1. `sha256(lean) == lean_sha256` and the file hash of the source JSONL equals the value above.
2. System prompt hash and addendum suffix match the frozen version-1 prompt format.
3. Exactly one required path; `rl4cv.veribench.exp103.extract_lean(envelope, (P,))` returns `L` exactly.
4. Joint deduplication against the 1,315 originals and earlier-admitted candidates: exact normalized Lean hash, then word-5-gram Jaccard >= 0.70 (`docs/DATASETS.md` threshold).
5. Held-out screen of the Lean file, the whole assistant text and each fenced block against the 714 validation/test Python and gold Lean texts at the VeriBench pin `c11b99ba`.
6. Tokenizer rendering with the pinned Qwen3 Base tokenizer: byte and token-id prefix, expected loss span, total <= 16,384 tokens.

Rejected rows stay in `results/admitted_corpus_manifest.csv` with their reason. Changing any byte of this encoding is a new specification version and a new candidate corpus file.

**TLDR-end:** [rl4cv: 08 expt_v3 › MBPP conversion] Keep the frozen prompts, wrap the kept Lean unchanged in experiment 103's FILE-plus-fence envelope, and admit a row only when extraction, deduplication, held-out screening and rendering all pass.
