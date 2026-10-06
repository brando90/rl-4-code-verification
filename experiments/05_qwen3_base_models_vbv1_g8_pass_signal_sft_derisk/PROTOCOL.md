# Experiment 05 — PROTOCOL (LOCKED before the GPU run)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/PROTOCOL.md>

**TLDR:** This locks the models, tasks, prompt, decoding, scorer, statistics and verdict thresholds for the Qwen3 Base G=8 signal check on VeriBench V1 before any GPU spend. Any deviation found during execution goes to `results.md` → "Deviations and open questions", never into this file.

## Scientific question (locked)

On all 896 VeriBench V1 tasks, with 8 samples per task, how often does each Qwen3 Base checkpoint (1.7B, 4B, 8B) produce a fully verified Lean file, and what share of tasks yields a mixed group (some but not all of the 8 samples pass), which is the only kind of group from which group-relative RL (GRPO) can learn?

Operational criteria:

- **Complete.** Every declared cell (3 models × 896 tasks × 8 samples = 21,504) has a terminal receipt: generated and kernel-scored, or explicitly failed/unmeasured with its reason. Both tables are published with full denominators.
- **Per-model verdict** on the overall `kernel_binary` mixed-group share `s` over the 896 tasks:
  - `s < 0.05` → **SFT warm start needed**;
  - `s ≥ 0.20` → **RL from Base viable**;
  - otherwise **marginal**.

  Threshold source: experiment 01's locked gate G1 (`01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`), reused for comparability. The project-level answer is Qwen3-1.7B-Base's verdict (Varun, 10-05-2026 meeting: "if it's too hard for 1.7, then we have to reevaluate").

## Locked parameters

| Parameter | Value |
|---|---|
| Condition | `rl4cv-e05-qwen3-base-vbv1-g8-v1` |
| Models | `Qwen/Qwen3-1.7B-Base` @ `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`; `Qwen/Qwen3-4B-Base` @ `906bfd4b4dc7f14ee4320094d8b41684abff8539`; `Qwen/Qwen3-8B-Base` @ `49e3418fbbbca6ecbdf9608b4d22e5a407081db4` (resolved from the Hugging Face API 10-05-2026; the preflight re-checks them) |
| Tasks | experiment 103's gated v6 pack, all 896 tasks; id list `task_ids_vbv1.txt`, file SHA-256 `7284f61513bb7876390e9af6f205103fcd640551e357ebcd3b06966c8bff5949` (= experiment 01's `5d4e64e4…`, which hashes the content without the trailing newline) |
| User prompt | the pack's `instruction.md` + `"\n\n---\n\n"` + `addendum_vbv1.md` (SHA-256 `a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5`) |
| System prompt | experiment 103's `SYSTEM_PROMPT` (SHA-256 `dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd`) |
| Prompt rendering | each model's own chat template with `add_generation_prompt=True, enable_thinking=True` (`--thinking on`), as experiment 01. The Base and post-trained templates differ only in branches for non-string content and assistant turns; the preflight verifies that the rendered prompt is byte-identical to the post-trained Qwen3-1.7B rendering for 5 tasks |
| Stop tokens | the model's EOS (`<|endoftext|>`) plus `--stop-token '<|im_end|>'`, so a Base model's turn ends where a post-trained model's would |
| Decoding | G = 8, temperature 0.6, top-p 0.95, top-k 20, max 12,288 output tokens, per-sample seed 91·100003 + k (experiment 01's probe contract) |
| Extraction | experiment 103's `extract_files` + `resolve_paths` via `rl4cv.veribench.exp103`, VeriBench commit `c11b99badfa386fd26810b208eef1eb8dc9f6806` |
| Measured cell | finish reason `stop`; `length` is recorded as cut off and still scored as it stands |
| Scorer | VeriBench commit `59059a20d40adf3289869e58302169ad78102877`; `score_scsc.py` SHA-256 `b3713c48e0fd…`, `run_real_eval.py` `6e82b3d1cd6d…`, `kernel_axioms.py` `5dbbdcae75ba…`; `--skip-tc`; Lean v4.22.0 + Mathlib v4.22.0 (experiment 01's validated grading project) |
| FSC judge | none. SCSC is exact (0) where IC_tests · IC_proofs = 0; any cell with IC_tests · IC_proofs > 0 keeps FSC and SCSC unmeasured and is listed |
| Verdict channel | `kernel_binary` (1 only if the file typechecks, has an example, states ≥ 1 theorem, proves every stated theorem within the axiom whitelist, and none is vacuous) |
| Diagnostic channels | `ic_tests` (the extracted file typechecks and has ≥ 1 example, IC_tests = 1), `proof_fraction` (IC_tests · IC_proofs, zero if any theorem is vacuous) |
| Headline statistics | per model and channel: histogram of passes k ∈ {0..8} over the 896 tasks; mixed-group share (0 < k < 8), pass@8 share (k ≥ 1) and all-pass share (k = 8), each with a 95% Wilson interval (unit = task, n = 896); one-sided exact binomial p-value for H0: share ≥ 0.05; mean pass rate (mean k/8) with a 95% task-bootstrap interval (10,000 resamples, seed 0). Core (614) and IndustrySet (282) reported separately |
| ρ and H | `rl4cv.probe --group-by split` for `kernel_binary` and `proof_fraction`, as experiment 01 |
| Paired comparison | on experiment 01's 128-task probe subset (`probe_task_ids.txt`, SHA-256 `59b877565314ab6c906081688734e8420d0a10acc512eaab248129ab002b7810`): Base minus post-trained mixed-group share per size, 95% paired task-bootstrap interval, exact McNemar p-value |

## Scale verification (no further normalization)

- IC_tests and `kernel_binary` are in {0, 1}.
- IC_proofs and `proof_fraction` are in [0, 1].
- Pass counts k are integers in [0, 8]. No script rescales any of them.

## Verified data layout

Identical to experiment 01 (`rl4cv.veribench.generate` rows, frozen scorer `<job>_per_task.csv`, `rl4cv.veribench.collect` scored rows). The only new generation field is `sampling.stop_tokens`. Generation is sharded by task (`line_index mod n_shards`) into `gen_<label>_g8.shard<j>of<n>.jsonl`, then merged into `gen_<label>_g8.jsonl` and checked one-to-one against the 896 × 8 manifest before jobs are written.

## Pre-conditions for run

- D-101 (self-hosted inference) accepted.
- `skampere1` work root `/lfs/skampere1/0/brando9/rl4cv_e05/` (never DFS); experiment 01's environment read-only: vLLM venv, pinned VeriBench checkouts and Lean grading project under `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification/`.
- Free A100-80GB GPUs verified with `nvidia-smi` right before launch; one generation process per GPU.

## Estimated wall-clock

- **Generation.** 7,168 cells per model. Experiment 01's post-trained probe averaged 5,700–6,500 tokens per cell; the worst case is every cell at the 12,288 cap (88 M tokens per model). Plan: 1.7B on 1 GPU, 4B on 2, 8B on 3. Estimate 1–4 h wall-clock, 6–20 GPU-hours in total.
- **Kernel scoring.** 24 jobs of 896 files. Experiment 01 measured about 8 files per minute per scorer under shared load, so about 2 h per job, about 45 CPU-hours in total; with 12 concurrent scorers about 4 h, overlapping generation.
- **Total:** about 5–9 h.

## Pass/fail / abort rules

- **Preflight passes when all hold:**
  - 5 of 5 tasks × 2 samples have generation receipts with `prompt_sha256`/`addendum_sha256`/`system_prompt_sha256` matching the locked values;
  - the Base rendering of each preflight prompt equals the post-trained Qwen3-1.7B rendering byte for byte;
  - at least one preflight cell finishes with `stop` (the stop token works) or, if all 10 hit the cap, the completions are inspected and the behavior is recorded before launch;
  - the 10 cells are kernel-scored without a scorer error.
- **Stop new generation and diagnose on** a systematic failure: more than 20% of the first 500 cells of any model with an extraction or transport error not explained by the model's own output, or any scorer crash that repeats on retry.
- **Preserve every finished cell.** An abort keeps every affected and unattempted cell in the denominator as unmeasured.
- **No retries to raise scores.** Infrastructure retries rerun the identical cell (same task, sample index and seed); a cell is never re-sampled because of its score.
- **The frozen single-call prompt is not changed.** It does not contain the agents-config solver completion reminder; adding it would be a new condition (as in experiment 01).

## Identity / contact crib (verified)

- GitHub: `brando90`, owner of `brando90/rl-4-code-verification` (verified 10-05-2026 from `git remote -v`).
- Meeting participants: Brando Miranda, Varun Madan, Emily Xia, Ethan R Lee, Ethan L ([transcript](../meetings/oct_5_2026/transcription.md)).
