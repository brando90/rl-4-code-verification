# V17 Trial Protocol

The executable source snapshot is in `sources/`; this trial preserves the prospective V17 protocol verbatim. The trial continues only after the V14 `admission_v1/completion.json` receipt is `DONE` with 678 admissions, completed protected screens, formal receipt revalidation, and comment-only source roundtrips. Those conditions were satisfied before this file was created.

The V17 data regime starts from V12-current and uses all 2,585 V12 Python-to-Lean rows once plus 678 V14 public explicit-proof rows six times in the deterministic exposure schedule. It uses a fresh optimizer with the declared `5e-6` warmup/cosine schedule and never changes benchmark generation, scoring, prompts, or task IDs.

Evaluation is all 135 frozen validation IDs × eight samples. The sealed 222-task test split and 50 protected fresh diagnostics remain excluded from training, teacher work, and evaluation.
