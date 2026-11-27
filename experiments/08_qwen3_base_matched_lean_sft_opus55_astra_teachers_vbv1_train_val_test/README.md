# Experiment 08 — Matched Lean SFT warm start for Qwen3 Base 1.7B–14B from Valkyrie teachers (Claude Opus 5.5, GPT-6 Astra) on the VeriBench V1 train split, evaluated on its validation and test splits

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/README.md>

**TLDR:** Qwen3 Base gives essentially zero reinforcement-learning (RL) signal on VeriBench V1 at the three measured sizes (experiment 05), so it needs a supervised fine-tuning (SFT) warm start. This experiment splits VeriBench V1 into train / validation / test (539 / 135 / 222 tasks; decision D-013). It asks two frontier teachers through Vals Valkyrie (Claude Opus 5.5 and GPT-6 Astra) for four single-call Lean files per train task, and keeps only files the Lean kernel fully verifies. It then fine-tunes Qwen3 Base 1.7B, 4B, 8B and 14B with one identical recipe (same data, order, token budget and hyperparameters at every size, as Varun requires). The validation split measures how many SFT tokens it takes before every size gives usable RL signal; each selected trained checkpoint is evaluated on the test split once after selection (historical Base/teacher test results were already inspected).

**Owner:** Rakshit Kaushik (@rakshit-kaushik), tracking issue [#7](https://github.com/brando90/rl-4-code-verification/issues/7). **Set up by:** Claude Code master session for Brando, 10-07-2026. **Status:** Version 1 DONE / frozen verdict PARTIAL (10-11-2026); see [results.md](results.md). **Version 2 PARTIAL / route blocked (10-13-2026):** matched step-658 test evaluation stopped under the runbook controls gate; Vals managed AWS access is unavailable, 0/5,328 new cells persisted, and all unknowns are listed. Reused results remain complete; see [expt_v2/PROTOCOL_v2.md](expt_v2/PROTOCOL_v2.md) and [expt_v2/results.md](expt_v2/results.md).

**Matched continuation (10-16-2026):** [expt_v3](expt_v3/README.md) is locked and running under one execution owner. Both replay and expansion at 1.7B/4B are complete (8,640/17,280 validation cells, eight namespace diagnostics); expansion 8B training and both exports are verified, validation and replay are underway, and 14B waits for eight eligible devices. [Live results](expt_v3/results.md).

## Origin

- **Brando, 10-07-2026:** "maybe we can use VeriBench as a validation set … we can split VeriBench into train val test in a reasonable way, and then create a plan so that we use Valkyrie to create a bunch of synthetic data from Claude Opus 5.5 and Astra. Guess how many tokens we might need for SFT so that these Qwen models are all trained in a consistent way … start doing an SFT and then do the training … execute it and do a light QA with Codex … create a Git issue assigned to Rakshit."
- **Experiment 05** ([results](../05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md)): Qwen3 Base 1.7B / 4B / 8B, all 896 VeriBench V1 tasks × 8 samples: `kernel_binary` mixed-group share 0.000 / 0.006 / 0.000. Experiment 01 found the same for post-trained Qwen3. Verdict at every size: SFT warm start needed.
- **Varun, 10-05-2026 meeting** ([transcript](../meetings/oct_5_2026/transcription.md), 18:23–21:47): the paper used "all of the Qwen3 sizes, and it was the same fine tuning warmup … just to keep it controlled", from the Base models, because "different sizes are post-trained in different ways in Qwen". Instruct checkpoints are not used.
- **Varun's matched warm-start contract** (`rl-env-scaling` @ `7118b86`, `docs/research/PAPER1_PHASE1_MATCHED_SFT_EXECUTION_PLAN_V1_20260829.md` and `data/manifests/paper1_phase1c_sft_v1/matched_sft_recipe.json`): every scale gets the same examples, order, template, loss and selected fraction of one SFT token budget. The checkpoint chosen is the earliest common token fraction that passes behaviour gates, never the best SFT score. His production run (`/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/`) is NeMo RL 0.4.0 SFT on 2,048 math and code rows: global batch 2, one epoch, checkpoints every 25%.
- **Experiment 02A v3** ([README](../02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/README.md), owner Ethan Li): the same teacher route on MBPP-derived tasks, with VeriBench fully held out. Its verified files are a complementary, non-VeriBench Lean source; this experiment reuses its route, scorer adapter and keep rule.

## Goal, hypothesis and decision criterion

- **Uncertainty.** Does a matched Lean SFT warm start, built only from kernel-verified teacher files on VeriBench train tasks, give Qwen3 Base usable group-relative RL signal on held-out VeriBench tasks at every size? How many SFT tokens does that take?
- **Hypothesis.** At or before the 100% checkpoint (about 4.5–6.5M assistant tokens, estimate below), every size reaches a validation `kernel_binary` mixed-group share ≥ 0.05 at G = 8 (experiment 08's readiness gate at experiment 01 G1's failure boundary; G1's strong-pass threshold is 0.20), with format reliability above the gates in [PROTOCOL.md](PROTOCOL.md) § 9. The 4B–14B models pass earlier than 1.7B.
- **Decision** (applied on the validation split only; PROTOCOL § 9):

  | Outcome | Verdict | Next |
  |---|---|---|
  | One token fraction passes at all four sizes | **RL-READY**: the earliest such fraction gives π₀(N) at every size and answers "how many tokens" | Test evaluation of π₀(N) once, then the RL phase (version 2) |
  | Some sizes pass at some fraction, but no common one | **PARTIAL** | Report each size's earliest passing fraction; version 2 enlarges the SFT data (more teacher samples, 02A v3's MBPP Lean) for all sizes alike |
  | No size passes any rung | **NOT READY** | Failure taxonomy (extraction, compile, unproved theorem, truncation); version 2 as above |

## How many SFT tokens? (estimate before any call)

Measured, zero calls (`expt_v1/results/token_budget_*.json`, Qwen3 tokenizer):

| Quantity | Value | Source |
|---|---:|---|
| Gold Lean reference, train split | mean 2,312 tokens (median 1,657, p90 3,621) | `estimate_token_budget.py gold` |
| Experiment 103 single call, Claude Opus 5 max: train tasks passing the kernel proxy | 251 / 539 (46.6%) | `estimate_token_budget.py e103` |
| … its verified files | mean 5,104 tokens (median 4,993, p90 6,425) | same |
| Experiment 103 single call, GPT-6 Astra high: train tasks passing | 261 / 539 (48.4%) | same |
| … its verified files | mean 2,731 tokens (median 2,511, p90 3,822) | same |
| Train tasks with a verified file from either teacher (one sample each) | 362 / 539 (67.2%); both 150 | same |

The kernel proxy is IC_tests = IC_proofs = 1 with at least one theorem and one `example`; it skips the vacuity check.

Estimate for this experiment: 4 samples per (task, teacher) and at most 2 kept files per (task, teacher). Assume each teacher keeps **at least one** file on 65% of train tasks and a **second** file on 45% (the latter is a subset of the former). Then 539 × 2 × (0.65 + 0.45) ≈ 1,186 examples, with a planning range of 1,100–1,300. Using 3.9K file tokens as a proxy for assistant length gives 4.62M tokens centrally, or **about 4–5M assistant tokens per model per epoch**. Full response/template overhead is not yet measured. Assuming another 3.0–3.7K prompt tokens per example gives 8.2–9.0M processed tokens centrally; this prompt allowance is an assumption, not a tokenizer measurement. An upper scenario treats a teacher's 4 samples as closer to independent draws at experiment 103's per-sample yield (about 0.47–0.48). That gives at least one kept file on up to about 85% of train tasks and a second on up to about 65%. Then 539 × 2 × (0.85 + 0.65) ≈ 1,617 examples, 6.31M assistant tokens and about 11.7M processed tokens (3.35K prompt tokens each). The planning range is therefore **about 1,200–1,600 examples and 4.5–6.5M assistant tokens per model per epoch**. Every size sees exactly the same tokens.

These are planning assumptions, not an independent-sample extrapolation or a confidence interval: samples and task difficulty are correlated, Opus 5 is not Opus 5.5, and the new efforts, deduplication, screening and length cap can change yield. The committed `median` token fields use the upper middle observation for even counts (not the average of the two middle observations).

My guess at what is needed: the 25% rung (~1M tokens) teaches the file format; nonzero verified signal needs about 2–5M tokens at 4B–14B. 1.7B is the uncertain size. For scale, Varun's math and code warm start is 2,048 long chain-of-thought rows, roughly 10M tokens (unverified estimate). The checkpoint ladder (12.5 / 25 / 50 / 75 / 100% of assistant tokens) measures the answer instead of guessing it.

## Structure

```
08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/
├── README.md        ← this design doc
├── PROTOCOL.md      ← lock 1 before the first teacher call, lock 2 before the first SFT step
├── results.md       ← live record
└── expt_v1/
    ├── cc.md                       ← SNAP worker runbook
    ├── CKPT_e08.md                 ← worker checkpoint
    ├── base_tables_from_e05.py     ← base models on the D-013 splits (zero calls)
    ├── estimate_token_budget.py    ← token-budget inputs (zero calls)
    ├── scripts/                    ← pack, scorer adapter, SFT assembly, configs, eval, analysis (worker)
    └── results/
        ├── split/                  ← D-013 manifest, id lists, links, leakage report
        ├── base_qwen3_e05_on_d013_splits.json
        └── token_budget_*.json
```

## Method (summary; exact settings in PROTOCOL.md)

1. **Split (done, D-013).** `rl4cv.splits` on VeriBench V1 at the `veribench` pin. Near-duplicates (exact normalized hash, or word-5-gram Jaccard ≥ 0.70 on the Python program or the gold Lean) and security safe/vulnerable pairs stay in one split. Groups are assigned per family in salted-hash order, toward 60 / 15 / 25%. The result is 664 groups → 539 / 135 / 222 tasks (core 369 / 93 / 152; IndustrySet 170 / 42 / 70). The largest cross-split Jaccard is 0.640 (Python) and 0.610 (gold Lean).
2. **Teacher data (Valkyrie, D-015).** The prompt is experiment 103's frozen single-call prompt for the 539 train tasks, the same bytes the Qwen policy sees in experiments 01 and 05 and at evaluation. The route is `vb103_single_call` through a collect-only benchmark service on `skampere1`. Teachers are `anthropic/claude-opus-5-5-no-fallback` at `xhigh` compute effort (the recorded lock-1 amendment A1) and GPT-6 Astra at the highest reasoning effort the registry serves. Each teacher runs 4 times over the manifest, so there are 4,312 declared cells.
3. **Keep rule.** The frozen scorer (`--skip-tc`) and `rl4cv.rewards.reward_kernel_binary == 1`. Every kept file then passes the generated-Lean screen against the validation and test splits. Apply every eligibility filter before taking at most 2 distinct files per (task, teacher), in sample order, with `opus55` before `astra` for cross-teacher deduplication. Screen full assistant text as well as extracted Lean.
4. **Matched SFT.** Qwen3-{1.7B, 4B, 8B, 14B}-Base, full-parameter, Varun's recipe: NeMo RL 0.4.0 SFT, AdamW 2×10⁻⁵, betas (0.9, 0.98), weight decay 0.1, clip 1.0, 3% warmup then cosine, global batch 2, maximum sequence length 16,384, assistant-only loss, one epoch in one fixed order. Checkpoints at 12.5 / 25 / 50 / 75 / 100% of assistant tokens. Only the GPU layout differs by size.
5. **Validation.** Experiment 05's exact sampling (G = 8, T = 0.6, 12,288-token cap, thinking template on) on the 135 validation tasks for every checkpoint. Base 1.7B / 4B / 8B come from experiment 05's receipts; Base 14B is generated here. Gates are format, truncation and `kernel_binary` mixed-group share ≥ 0.05.
6. **Test (once).** The selected π₀(N) and Base on the 222 test tasks, G = 8. Factors are IC_tests and IC_proofs from the kernel, and compile-gated formal specification coverage (FSC) from the validated `vb103_judge` (D-102). The official SCSC aggregate is the geometric mean of the three factor means on one common known cohort, with compile-gated FSC, always with its factors and denominator. Core and IndustrySet are reported separately.
7. **RL (version 2, after RL-READY).** Group-relative RL (GRPO) from π₀(N) on train-split prompts, `kernel_binary` reward first, validation monitoring, one test evaluation. It gets its own locked protocol.

## Compute and calls (estimate)

- **Teacher calls:** 4,312 single calls through Valkyrie, funded by Vals and recorded rather than capped (D-108). Budget assumption (raw charge receipts are not in the committed inputs): Opus 5 max ≈ $2.2 per call and Astra high ≈ $0.61 imply 2,156 × ($2.2 + $0.61) = $6,058.36, within a rough $5–8K range. Add 8 preflight cells; allowed retries are extra requests. The actual Opus 5.5/Astra settings may cost differently and are recorded per receipt.
- **SFT:** 6·N·D for N = (1.7 + 4 + 8 + 14)B and D = 9M processed tokens gives 1.496×10¹⁸ floating-point operations (D = 12M, the upper scenario: 1.99×10¹⁸). At an assumed sustained 100 trillion operations/s per A100, this is 4.16 GPU-hours before overhead (upper scenario 5.5); throughput and wall time are unmeasured and must be estimated on the host before launch.
- **Validation generation:** 5 rungs × 4 sizes × 1,080 samples, plus Base 14B, 22,680 samples: a provisional 8–15 GPU-hours (throughput unmeasured). Kernel scoring is provisionally budgeted at 1–2 h with 32 CPU scorers; this throughput is unmeasured.
- **Test:** at RL-READY, 5 newly generated systems × 1,776 = 8,880 cells plus 3 reused Base systems × 1,776 = 5,328, for 14,208 declared cells. Judge all IC_tests = 1 cells plus the 60-file audit per system; PARTIAL has fewer newly generated systems.
- **Host:** `skampere1` (8× A100-80GB; GPUs 1–7 free at 16:00 PDT 10-07-2026; Qwen3 1.7B / 4B / 8B Base cached at experiment 05's revisions; experiment 01/05 scorer and grading project). `skampere3` B200s if free.

## Dependencies

- D-013 (the split) and D-015 (the teacher route; D-014 is the same exception for experiment 02A v3) in [`docs/DECISIONS.md`](../../docs/DECISIONS.md); D-102 (judge route); D-108 (Valkyrie for Brando's runs).
- `rl4cv.splits`, `rl4cv.screens`, `rl4cv.rewards`, `rl4cv.veribench.{exp103,generate,jobs,collect}`, and the frozen scorer (`external/deps.lock.json`: `veribench_scorer`).
- VeriBench experiment 103: the `vb103_single_call` agent, its VBV1 pack and its service code. Experiment 01's service-deploy pattern.
- NeMo RL 0.4.0 (commit `c751f811`), built in the worker's own environment; Varun's production SFT config is copied with provenance.
- **Varun (D-105):** the math/code rows and his warm-start checkpoints would allow a math + code + Lean arm. Those data/checkpoints are not needed for version 1 and need his authorization before use; the recipe/config copy specified above is a separate, read-only dependency.

## Status

| Step | Status |
|---|---|
| Split (D-013) | DONE (10-07-2026), committed with tests |
| Base models on the splits (experiment 05 receipts) | DONE (10-07-2026), zero calls |
| Token-budget inputs | DONE (10-07-2026), zero calls |
| Protocol lock 1 (teacher data) | DONE, including recorded A1 teacher-effort amendment |
| Teacher runs, scoring, SFT set | DONE: 4,312 terminal cells; 1,315 training examples |
| Protocol lock 2, matched SFT | DONE: 658 updates/5,752,936 loss tokens at every size; all 20 exports complete |
| Validation ladder, selection | DONE: all 20 trained rungs and 25,920 validation cells; frozen PARTIAL selection |
| Test evaluation | DONE: all 10,656 test factor cells and 4,302 judge ratings known; all 60 fixed audit files per system; final analysis reproduced |
| Execution cleanup | DONE: judge services/tunnels stopped, port claim archived, pipeline watchdog retired, monitor STOP recorded |
| Version 2: matched step-658 test (1.7B, 4B, 14B; Brando, 10-13-2026) | PARTIAL: Vals managed AWS route blocked; 0/5,328 new cells persisted; owned jobs/services stopped; [expt_v2/results.md](expt_v2/results.md) |
| RL | Not started; no common passing fraction and no follow-on RL study authorized |

Version 1 is complete with PARTIAL selection: 8B step 658 and 14B step 334 are unmatched diagnostics; neither 1.7B nor 4B passes a rung. The final test table, intervals, audit, charges and preserved limitations are in [results.md](results.md); [all joined test factors](expt_v1/results/test_factor_cells.csv) are available without raw model text.

**Live dependency retaining this canonical home:** the frozen D-013 split is consumed by `tests/test_splits.py` and `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/phase0_prepare.py`; that study also references these retained checkpoint/manifests. Moving this completed folder would break those active consumers, so it remains at this path. This does not reopen training or authorize a follow-on study.

## Concise curriculum and additional 1.7B / 4B training (10-19-2026)

[Version 5](expt_v5/results.md) contains 500 compiled tiny Python-to-Lean training examples. [Version 6](expt_v6/README.md) tests the user-requested parallel 1.7B replay control, 1.7B augmented condition and 4B augmented condition, with full validation and the test split unopened. Before training, version 6 adds the required anonymous executable example declaration to each tiny answer and repeats compilation, kernel, differential, formatting and overlap checks; the original version 5 remains pristine. See the [training results](expt_v6/results.md). The 10-19-2026 RUNNING label is the last measurement: 4B is 526/904 with 0/1,080 validation cells, and no later committed file finishes it (refreshed 11-27-2026).

## Seen-versus-fresh 1.7B diagnostic (10-19-2026)

[Version 7](expt_v7/README.md) runs the user-authorized 50 seen / 50 fresh tiny-function diagnostic on the completed augmented 1.7B checkpoint, with independent Python differential tests and kernel proof checks. This inference-only diagnostic is separate from version 6’s frozen benchmark validation. All 100 checks are complete: 29/50 seen and 9/50 fresh pass. See [diagnostic results](expt_v7/results.md).

## Current 1.7B corpus and adaptive continuation campaign

- [Version12](expt_v12/results.md): the10,940-example first continuation completed all1,080validation cells with120successes (11.11%); the prepared partial-cleanup branch received zero optimizer updates and its dispatcher was fenced.
- [Version13](expt_v13/results.md): immutable partial cleanup:818verified replacements,227unchanged originals and1,540flagged fallbacks; original implementation/specification/test statements preserved.
- [Version14](expt_v14/results.md): GX10 user environment and678admitted Mathlib/DeepSeek examples from729formal candidates; source validation and training admission have separate receipts.
- [Version15](expt_v15/results.md): outcome-triggered adaptation toward25%complete validation binary success; maximum$900additional API authorization. Terra/high teachers; one user-authorized Astra/high code-porting worker only. The test split stays sealed.
- [Version18](expt_v18/README.md): complete remaining original-pool cleanup, with explicit accepted/excluded rows and no automated-proof fallback in the retained original cohort. Deployment awaits cluster reauthentication.
- [Version19](expt_v19/README.md): final second1.7B condition through full validation; prefer a truly free suitable A100, with the user-authorized GX10 prepared as fallback. The earlier partial dataset is a discarded hardware control only.
