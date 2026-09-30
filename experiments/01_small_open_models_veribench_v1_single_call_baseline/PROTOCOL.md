# Folder 01 — PROTOCOL (LOCKED before any expensive run)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md>

**TLDR:** This locks the models, tasks, prompts, sampling, scorer, judge scope, probe subset and gate thresholds for experiment 01 before any GPU or judge spend.

This file freezes the protocol before any LLM-budget-spending run begins.
It is written PRIOR to seeing any results.
Any deviation observed during execution is documented in REPORT.md → "Open questions for Brando", not by editing this file.

## Scientific question (locked)

What IC_tests, IC_proofs, FSC and SCSC do small open-weight Qwen models reach on VeriBench V1 (896 tasks) under experiment 103's single-call protocol? And does any of them produce group-relative signal (mixed reward groups at G = 8) on VeriBench tasks?

Operational criteria:

- **Complete.** The experiment is complete when every declared cell (9 models × 896 at G = 1, and 8 models × 132 × 8 at G = 8) has a terminal receipt and a scored or explicitly unmeasured status, and both tables are published with full denominators.
- **Gate G1:**
  - **Scaling-signal fail:** the `kernel_binary` mixed-group share on the probe is < 0.05 for every model at or below 14B.
  - **Scaling-signal pass:** any model reaches ≥ 0.20 on at least one split.
  - **In between:** the gate is "marginal", and the report proposes which splits or families to try.

## Locked parameters

| Parameter | Value |
|---|---|
| Condition | `rl4cv-e01-vbv1-single-call-v1` |
| Models | `expt_v1/models.yaml`: 8 models plus the Qwen3.6-27B route control. Revisions are resolved to Hugging Face commits at preflight and written to `expt_v1/results/model_revisions.json` before generation. |
| Tasks | Experiment 103's gated v6 pack, 896 tasks, task-id list SHA-256 `5d4e64e44032631beaed1a8ce98ce8cbae401ccf69d369e22c6ee16e82e2bdc3`, 0 sorry-mandating instructions |
| User prompt | the pack's `instruction.md` + `"\n\n---\n\n"` + addendum `addendum_vbv1.md` (SHA-256 `a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5`) |
| System prompt | experiment 103's `SYSTEM_PROMPT` (SHA-256 `dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd`) |
| Extraction | experiment 103's `extract_files` + `resolve_paths`, imported from the pinned VeriBench commit. The committed `single_call.py` (SHA-256 prefix `c7cbe3e6`) differs from the bundle experiment 103 pushed (`6e1a9b0d`). Preflight diffs the two and records whether extraction logic differs. |
| Evaluation sampling | G = 1, temperature 1.0, top-p 0.95, top-k 20, max 65,536 output tokens, thinking on, seed 91 (experiment 103's served Qwen settings) |
| Probe subset | 4 tasks per VeriBench split (at most 132), first in `sha256("rl4cv-probe-v1:" + task_id)` order; written once to `probe_task_ids.txt` and hashed |
| Probe sampling | G = 8, temperature 0.6, top-p 0.95, top-k 20, max 12,288 output tokens, thinking on, per-sample seed 91·100003 + k |
| Measured cell | finish reason `stop` (clean); `length` is recorded as cut off (not admitted under overlong filtering) and still scored as it stands |
| Scorer | VeriBench commit `59059a20d40adf3289869e58302169ad78102877`, with hash prefixes `run_real_eval.py` 6e82b3d1cd6d, `kernel_axioms.py` 5dbbdcae75ba, `score_scsc.py` b3713c48e0fd; `--skip-tc`; Lean v4.22.0 with Mathlib v4.22.0 |
| FSC judge | `vb103_judge` (experiment 100 H2: GPT-6 Sol high plus Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5). Scope: every cell with IC_tests · IC_proofs > 0, plus a 60-file audit per model (12 per core split, outcome-blind hash order, compiling or not). Runs only after D-102. |
| Reward channels in the probe | `kernel_binary`, `proof_fraction` (plus `scsc` and `fsc_compiled` once judged) |
| Gate G1 thresholds | < 0.05 fail; ≥ 0.20 pass; otherwise marginal |

## Scale verification (no further normalization)

- IC_tests is in {0, 1}.
- IC_proofs, FSC and SCSC are already in [0, 1].
- FSC arrives normalized (the 0–5 integer divided by 5). No script may rescale it.

## Verified data layout

- **Generation JSONL** (`rl4cv.veribench.generate`), one row per (task_id, sample_idx), with fields:
  - identity: `model`, `revision`, `sampling`;
  - prompt hashes;
  - `generated_tokens`, `finish_reason`, `measured`, `truncated`, `admitted`;
  - `extraction`, `lean`, `completion`.
- **Scorer output:** `<scores>/<job>/<job>_per_task.csv`, keyed by `task` (the trial directory name = task_id). Columns used: `IC_tests`, `IC_proofs`, `agent_compiles`, `agent_n_ex`, `agent_n_thm`, `kernel_n_theorems`, `kernel_n_honest`, `split`.
- **Scored JSONL** (`rl4cv.veribench.collect`): the generation fields plus factors and per-channel `rewards`. A channel that needs a judge score that is absent is `null` (unmeasured), never 0.

## Pre-conditions for run

- D-101 authorizes self-hosted inference for this project.
- GPU host: an 80 GB-class GPU for models up to 14B, and for Qwen3.6-27B in bf16.
- Work root on `/lfs/<host>/0/<user>/`, never DFS.
- `make external` done; the pins verified; a vLLM environment available.
- Experiment 103's pack and grading Lean project present and hash-checked.
- Hugging Face access to the listed models.

## Estimated wall-clock

- **G = 1 generation:** 1–3 GPU-hours per model up to 9B, and 3–8 GPU-hours for 14B and 27B. This is mostly thinking tokens; experiment 103's Qwen3.6 hit the 65,536 cap on 245 cells.
- **Kernel scoring:** 1–5 CPU-hours per 896-file job at 3–14 tasks per minute (experiment 103).
- **Probe:** 1,056 generations and 8 scoring jobs of 132 files per model.
- **Total:** about 1–2 days on one GPU plus one scoring worker, or faster with several scorer workers.

## Pass/fail / abort rules

- **Smoke passes when all hold:**
  - 5 of 5 preflight cells have receipts;
  - the prompt hashes match the locked values;
  - the scorer controls behave: gold file 1/1, empty file 0/0, `sorry` proof IC_proofs 0.
- **Stop new generation and diagnose on:**
  - a systematic failure (> 20% of the first 50 cells with an extraction or transport error not explained by the model's own output);
  - any scorer control failure.

  Preserve every finished cell. An abort keeps every affected and unattempted cell in the denominator as unmeasured.
- **No retries to raise scores.** Infrastructure retries rerun the identical cell; a cell is never re-sampled because of its score.

## Identity / contact crib (verified)

- GitHub: `brando90`, owner of `brando90/rl-4-code-verification` and `brando90/veribench` (verified 09-30-2026 from the session's repository list).
