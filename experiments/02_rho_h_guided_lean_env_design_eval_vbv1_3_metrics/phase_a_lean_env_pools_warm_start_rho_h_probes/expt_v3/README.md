# Experiment 02A v3 — Lean warm-start data: frontier teachers on screened non-VeriBench Python, kept only when the Lean kernel verifies them

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/README.md>

**TLDR:** Every phase of experiment 02 needs a Lean supervised fine-tuning (SFT) warm start, because Qwen3 Base gives essentially no RL signal on VeriBench (experiment 05), and Varun's math/code warm-start weights are not available yet (D-105). This version builds the Lean part of that warm start without waiting: frontier teacher models, run through Vals Valkyrie (D-108), translate contamination-screened, non-VeriBench Python programs into VeriBench-format Lean 4 files, and only files the Lean kernel fully verifies are kept. It measures how many verified files each teacher yields and decides whether a paper-sized Lean set (1,024 verified examples) is reachable by this route. Nothing is trained here, and VeriBench is never used.

**Owner:** Ethan Li (@lethan3), experiment 02's owner from 10-07-2026. **Set up by:** Claude Code master session for Brando, 10-07-2026. **Status:** see [results.md](results.md).

## Origin

- **Experiment 05** ([`05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk`](../../../05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md)): Qwen3 Base 1.7B / 4B / 8B, 896 VeriBench V1 tasks × 8 samples. Mixed-group share 0.000 / 0.006 / 0.000; even the looser "compiles with tests" channel is 0.002 / 0.011 / 0.000. Verdict at all three sizes: SFT warm start needed.
- **10-05-2026 meeting** ([transcript](../../../meetings/oct_5_2026/transcription.md), 19:00–21:47): Varun offers his SFT warm-start weights; Brando: "I don't know if we need to warm up to Lean, because Lean is different from natural language math." The weights have not arrived (D-105), and they were trained on math and code, not Lean.
- **Phase 02A method, step 4** ([README](../README.md#method)): the warm start mixes the paper's 1,024 math and 1,024 code examples with a Lean SFT set built from non-panel pool tasks, "teacher answers kept only if the kernel accepts every theorem and the non-vacuity check passes". The teacher route and budget were left open as D-104.
- **D-108** (Brando, 10-07-2026): model calls in work Brando runs go through Vals Valkyrie, funded by Vals, with effectively unlimited capacity.
- **Brando, 10-07-2026:** "do whatever reasonable experiment is next to help ethan keep moving forward."

## Goal, hypothesis and decision criterion

- **Uncertainty.** Can frontier teachers, given non-VeriBench Python programs in VeriBench's task format, produce at least 1,024 kernel-verified (prompt, Lean file) pairs covering at least 512 distinct tasks, so the Lean part of the warm start is the same size as each of the paper's 1,024-example math and code parts? MBPP has 974 tasks, so a task may contribute one verified file per teacher family.
- **Prior evidence.** Experiment 103 (VeriBench) measured single-call frontier models on VeriBench V1: IC_proofs 0.607 for `claude-opus-5-max` (n = 681), 0.524 for `gpt-6-astra-high` (n = 855) and 0.054 for Gemini 3.1 Pro (n = 889) ([FACTS §2](../../../../docs/FACTS_veribench_baselines.md); VeriBench `experiments/103_…/results/IC_VBV1_TABLE.md`). Gemini 4 Argon has not been measured on Lean. Short, self-contained MBPP programs should be at least as easy as VeriBench's.
- **Hypothesis.** The Anthropic and OpenAI teachers each keep at least 40% of the screened tasks; Gemini 4 Argon's share is an open measurement.
- **Verification rule (the SFT keep rule).** A teacher file is kept only if `kernel_binary = 1` ([`rl4cv.rewards`](../../../../src/rl4cv/rewards.py)): it typechecks under the frozen scorer, states at least one `example` and at least one theorem, every stated theorem is kernel-proved with axioms only in {`propext`, `Classical.choice`, `Quot.sound`}, and no theorem is vacuous. `sorry`, `admit`, declared axioms and `native_decide` in named theorems fail.
- **Decision criterion** (locked in [PROTOCOL.md](PROTOCOL.md) before any teacher call):

  | Kept (task, teacher) pairs | Distinct tasks kept | Verdict |
  |---|---|---|
  | 1,024 or more | 512 or more | **SUFFICIENT**: build the Lean SFT set from the kept files; next is the warm-start training run (needs D-103 GPU hours and the recipe from D-105 or the paper) |
  | 300 or more, but either threshold above missed | | **PARTIAL**: add a second source (APPS programs via FVAPPS, already screened) or a teacher agent with a Lean compiler in its sandbox, as a new version |
  | below 300 | | **INSUFFICIENT** for this route; report the failure taxonomy |

## Structure

```
expt_v3/
├── README.md     ← this design doc
├── PROTOCOL.md   ← locked before the first teacher call
├── results.md    ← live results and status
├── cc.md         ← runbook for the SNAP worker
├── CKPT_e02a_v3.md  ← worker checkpoint
├── scripts/      ← source build, screens, pack build, scoring adapter, analysis
└── results/      ← manifests and summaries (raw teacher files stay on the host)
```

## Method

Draft; the exact teacher agents, prompt bytes and scoring adapter are fixed in `PROTOCOL.md` before any call.

1. **Source.** MBPP ([`google-research-datasets/mbpp`](https://huggingface.co/datasets/google-research-datasets/mbpp), revision `4bb6404fdc6cacfda99d4ac4205087b89d32030c`, CC-BY-4.0, 974 tasks). Every task is used: MBPP is a data source here, not an evaluation, so its own splits play no role. A deterministic script rewrites each task into VeriBench's Python task layout (docstring from the task text, the reference function as `prog`, a `check(candidate)` built from MBPP's assert tests, a `__main__` runner). A rewritten task is kept only if it runs and passes its own tests under Python 3.
2. **Screens.** `rl4cv.screens` against VeriBench `py_src` and `lean_src` at the pinned commit: exact normalized-hash matches and word-5-gram Jaccard ≥ 0.70 are removed and listed. MBPP is not HumanEval-derived.
3. **Prompt.** VeriBench V1's single-call system prompt and task template (experiment 103), unchanged except for the task file, so the teacher files have exactly the format the warm-started policy must later produce. The prompt is checked to carry no VeriBench task text, because it becomes the SFT input.
4. **Teachers.** One declared call per (task, teacher) through Valkyrie, for three vendor families at their strongest settings (Anthropic, OpenAI and Google's Gemini 4 Argon), exact model identifiers and agents recorded. Several families keep the warm start from inheriting one vendor's Lean style. No vendor's own agent is runnable on Valkyrie for these teachers today, so a common single-call agent is used; that is an exception to D-108, approved by Brando on 10-07-2026 as D-014 (PROTOCOL § 4).
5. **Score and screen.** The frozen scorer (`--skip-tc`) on `skampere1`, then the keep rule above; kept Lean files are then screened against VeriBench and the other held-out panels before entering the SFT set. Only cells shown to be unserved are re-sent (PROTOCOL § 4); no cell is re-sampled because of its score.
6. **Analyze.** Per teacher: observed yield (kept / declared), measured-cell yield with a 95% Wilson interval (unit = task) and missing-outcome bounds; union coverage; failure taxonomy (no Lean block, does not typecheck, no `example`, unproved theorem, forbidden axiom, vacuous theorem); file length; overlap between teachers.
7. **Outputs.** Committed: manifests, hashes, per-cell receipts and summaries. Raw teacher files and the assembled SFT set stay on the host.

## Dependencies

- `rl4cv.screens` (exact-hash and word-5-gram screens against VeriBench `py_src` and `lean_src`), `rl4cv.rewards`, the frozen scorer (`external/deps.lock.json`: `veribench_scorer`).
- Vals Valkyrie under D-108, with the payer verified before the first call.
- `skampere1` for scoring (experiment 01/05's validated Lean v4.22.0 + Mathlib grading project).

## Status

| Step | Status |
|---|---|
| Design | Done (10-07-2026), one Codex light-QA round, 7 findings fixed |
| D-108 exception (single-call teachers) | Approved by Brando 10-07-2026 ([D-014](../../../../docs/DECISIONS.md)) |
| Protocol lock | Locked 10-08-2026 00:09 UTC at commit `879eefbb…` |
| Source build and screens | Done 10-07-2026: 970 of 974 MBPP tasks, 0 screen hits |
| Teacher runs | Done 10-08-2026: 3 × 970 cells; unmeasured 13 / 15 / 14 (anthropic / openai / google) |
| Scoring, analysis, verdict | Done 10-09-2026: **PARTIAL**, 587 kept pairs over 455 tasks (anthropic 55 / openai 382 / google 150); see [results.md](results.md) |
