# Experiment 01 results — small open-weight Qwen models on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md>

**TLDR:** The GPU run on `skampere1` (GPUs 2–7) is **complete**: full G=1 eval (9 models × 896 tasks) and G=8 probe (8 models × 128 tasks × 8 samples) jobs, launched 09-30-2026 12:31, all generated, kernel-scored and FSC-judged as of 10-01-2026 12:35 — every declared cell has a terminal receipt (reopened 12:16 to fix one omission: Qwen3.5-0.8B's row and FSC audit, below). D-101 (self-hosted inference) and D-102 (FSC judge route: `vb103_judge` Valkyrie, payer: Vals gateway) are both accepted; the judge's own controls passed on a new, isolated Valkyrie benchmark service. Near-zero IC_tests/IC_proofs throughout, as hypothesized, with one exception: **Qwen3-14B produced the experiment's first (and only) fully-compiling, fully-proving cell** (1/896, SCSC≈0.888 under the locked median-of-3 judge; 0.928 under the single-repeat judge that was first reported). **Gate G1 resolves to PASS**: two models (Qwen3-14B, 6 splits, max 0.333; Qwen3.5-9B, 4 splits, max 0.25) clear the locked kernel_binary mixed-group-share ≥ 0.20 threshold; the other 6 of 8 probe-scored models show exactly 0.0 overall mixed-group share — the signal is thin and concentrated in the two largest probed models. Interesting secondary observation (diagnostic only, not SCSC-relevant since still 0 positive cells): **Qwen3.6-27B's ungated audit FSC (0.775) is far higher than every smaller model's (0.01–0.46 range)** — a more capable model produces more plausible-looking Lean even when it still doesn't compile/prove. Total judge spend: **$289.78 of $400** (after the FSC repeat correction below; $106.37 before it). **Update 10-07-2026:** a recompile diagnostic (no model calls) confirms the zeros under the frozen scorer. Most files fail on Lean 4 well-formedness before any test runs. VeriBench's own `namespace {file stem}` hint, which is invalid on 533/896 tasks, is one contributor: the legacy namespace rewrite moves Qwen3-14B from 1 to 25 tasks with IC_tests·IC_proofs > 0. See "Zero-score diagnostic" below. **FSC repeat correction (10-07-2026):** PROTOCOL.md locks the judge as the median of 3 repeats per member, but only repeat 1 had been run; repeats 2 and 3 were judged on 10-07-2026 and every FSC in this file is now the median of 3. No model's FSC moved by more than 0.009, the FSC ordering of the 9 models is unchanged, Gate G1 is unaffected (it never used FSC), and no conclusion changes. See "FSC repeat correction". **Probe proving cells judged (10-07-2026):** the 11 proving G = 8 probe cells (4 Qwen3.5-9B, 7 Qwen3-14B) were judged with the same locked design (66/66 cells measured, $7.06; judge total $296.84 of $400), giving the probe its `scsc` channel for all 8 models and a partial `fsc_compiled` channel: FSC 0.2–1.0 (mean 0.536, n = 11), so the proving cells pay 0.58–1.0 under `scsc` instead of 1.0; the mixed-group shares, Gate G1 (PASS) and the 8 seed splits for experiment 02 are unchanged. See "Probe proving cells judged".

## Probe proving cells judged (10-07-2026)

**Setup and status.** The G = 8 probe's 11 proving cells (IC_tests · IC_proofs > 0: 4 for Qwen3.5-9B, 7 for Qwen3-14B, 0 for the other 6 probe models; `expt_v1/results/judge/probe_proving_cells.json`, every solution file hash-checked against its generation receipt) were judged on 10-07-2026 with the locked FSC design (GPT-6 Sol high and Claude Opus 5.5 max, 3 repeats each with byte-identical prompts, median of 3 per member, mean of the 2, divided by 5) on the same `vb103_judge` Valkyrie route (D-102, payer Vals gateway), from their own collect-only benchmark instances (ports 9710–9711, torn down afterwards). **66 of 66 judge cells measured**, no recovery pass needed. Finished 10-07-2026 20:20 PDT. Spend **$7.06**; the experiment's judge total is now **$296.84 of the $400 cap**. Checkpoint: [`expt_v1/CKPT_e01_probe_judge.md`](expt_v1/CKPT_e01_probe_judge.md); per-item FSC: `expt_v1/results/fsc_probe_<label>.json`; channel summaries: `expt_v1/results/probe_channels_summary.json` (script `expt_v1/probe_channels_report.py`, zero model calls).

**Why it was open.** PROTOCOL.md puts every cell with IC_tests · IC_proofs > 0 in the judge's scope and lists the probe's reward channels as `kernel_binary`, `proof_fraction` "plus `scsc` and `fsc_compiled` once judged"; the first judge passes covered only the G = 1 cells, so the probe table (section "Signal probe, G = 8" below) carried only the two kernel channels (REPORT.md 17, found by the Gemini 4 Argon QA test).

**Per cell** (judge scores on the 0–5 rubric scale, repeats in order; FSC = mean of the two member medians / 5; SCSC = (IC_tests · IC_proofs · FSC)^(1/3) with both IC factors 1.0 on every cell):

| Model | Task | Sample | GPT-6 Sol high, repeats → median | Claude Opus 5.5 max, repeats → median | FSC | SCSC |
|---|---|---:|---|---|---:|---:|
| Qwen3.5-9B | `compilers_set_synthetic__my_strength_reduce_mul2` | 5 | [5, 5, 5] → 5 | [4, 4, 3] → 4 | 0.9 | 0.965 |
| Qwen3.5-9B | `concurrent_set_real__my_raft_term_tick` | 4 | [2, 2, 2] → 2 | [1, 1, 1] → 1 | 0.3 | 0.669 |
| Qwen3.5-9B | `medical_oss_set_real__my_temp_target_active` | 0 | [5, 5, 5] → 5 | [5, 5, 5] → 5 | 1.0 | 1.000 |
| Qwen3.5-9B | `os_embedded_set_synthetic__my_mmu_can_write` | 7 | [2, 2, 2] → 2 | [1, 2, 2] → 2 | 0.4 | 0.737 |
| Qwen3-14B | `aerospace_set_real__my_fprime_crc_match` | 2 | [2, 2, 2] → 2 | [1, 1, 1] → 1 | 0.3 | 0.669 |
| Qwen3-14B | `concurrent_set_real__my_raft_term_tick` | 5 | [2, 1, 1] → 1 | [1, 1, 1] → 1 | 0.2 | 0.585 |
| Qwen3-14B | `concurrent_set_real__my_raft_term_tick` | 6 | [1, 2, 2] → 2 | [1, 1, 1] → 1 | 0.3 | 0.669 |
| Qwen3-14B | `finance_set_synthetic__my_utxo_double_spend_reject` | 3 | [5, 5, 2] → 5 | [1, 0, 1] → 1 | 0.6 | 0.843 |
| Qwen3-14B | `gov_cert_set_synthetic__my_election_tally_add` | 2 | [4, 2, 4] → 4 | [4, 4, 4] → 4 | 0.8 | 0.928 |
| Qwen3-14B | `hardware_set_real__my_spike_funct3_field` | 0 | [2, 2, 2] → 2 | [1, 1, 1] → 1 | 0.3 | 0.669 |
| Qwen3-14B | `medical_oss_set_real__my_expected_delta_forecast` | 3 | [4, 4, 4] → 4 | [4, 4, 3] → 4 | 0.8 | 0.928 |

- **Over the 11 cells:** mean FSC 0.536 (n = 11; Qwen3.5-9B 0.650 over 4, Qwen3-14B 0.471 over 7; range 0.2–1.0); mean cell SCSC 0.788 (range 0.585–1.000). Member bias on these cells, Sol median − Opus median: mean +0.82 rubric points (Sol higher on 6/11, equal on 5/11, Opus higher on 0/11). Within-member repeat spread was 0 on 14 of the 22 (cell, member) pairs; the widest is `finance_set_synthetic__my_utxo_double_spend_reject` sample 3 (Sol 5, 5, 2; Opus 1, 0, 1), where the median-of-3 rule matters. Every proving cell proves all of its stated theorems with a compiling file, yet the judge finds the stated theorems cover only part of the reference specification on 7 of 11 (FSC ≤ 0.6): the kernel channels pay these cells 1.0, `scsc` pays 0.58–1.0.
- **What changes in the probe table.** The `scsc` channel is fully measured for all 8 models (128/128 groups; exactly 0 wherever IC_tests · IC_proofs = 0, so the 6 models without proving cells are unchanged at 0). For the two models with proving cells, the set of mixed groups is identical to `kernel_binary` (a judged cell's SCSC is in [0.58, 1.0], still above its 0-reward siblings), so the mixed-group share, H and the per-split maximum are unchanged; the mean reward and ρ fall because the per-cell reward is now below 1: Qwen3-14B ρ 5.98 → 4.46, Qwen3.5-9B 2.06 → 1.72 (group-weighted overall; pooled single-environment ρ 4.86 → 3.72 and 1.58 → 1.33).
- **Gate G1 and experiment 02's seed splits do not change.** G1 is locked on `kernel_binary` and stays **PASS**. Under `scsc` the splits at or above 0.20 are the same 6 for Qwen3-14B (max 0.333, `aerospace_set_real`) and the same 4 for Qwen3.5-9B (max 0.25), so the union that seeds experiment 02's pools is the same 8 splits (`probe_channels_summary.json` → `gate_g1.seed_splits_unchanged_under_scsc: true`).
- **`fsc_compiled` is partial by design.** Its judge scope under D-003 is every cell with IC_tests = 1, but the locked judge scope for this experiment is IC_tests · IC_proofs > 0, so the 17 probe cells with IC_tests = 1 and IC_proofs = 0 (Qwen3.5-4B 1, Qwen3-1.7B 3, Qwen3-4B 7, Qwen3-8B 1, Qwen3-14B 5; Qwen3.5-9B 0) stay `null` and their groups are excluded from the `fsc_compiled` row, never counted as 0: measured groups 127, 126, 121, 127 and 123 of 128 respectively. Judging them would be a new admission outside the locked scope and is left for Brando to decide.
- **Files.** Pre-judging scored JSONL files on the host are untouched; the re-collected files with FSC are `out/scored/scored_<label>_g8_with_fsc.jsonl` (the 10-01-2026 G = 1 precedent), from `out/fsc/<label>_g8_s<k>.json` exported by `judge_rl4cv_e01.py fsc-probe`. Transport: `valk run results` still returns the tracker regression noted in the FSC repeat correction; the harvest read the per-task verdict bytes via `valk run task` (`results_source` recorded in each harvest).

## FSC repeat correction (10-07-2026)

**Setup and status.** Experiment 01's locked judge design (PROTOCOL.md: GPT-6 Sol high plus Claude Opus 5.5 max, **median of 3 each**, mean of the 2, divided by 5) had only been run for repeat 1: `judge_rl4cv_e01.py` built `__r1` cells only, so every FSC first reported here was a median of one call. The Gemini 4 Argon QA test found it on 10-07-2026 (`qa/argon_valkyrie_10-07-2026/results.md`); the master confirmed it. Repeats 2 and 3 of every repeat-1 main cell were judged the same day on the same route (`vb103_judge` on Valkyrie, D-102, payer Vals gateway), with byte-identical prompts (each repeat's `prompt_sha256` equals the recorded and the served repeat-1 hash), and FSC was recomputed as the median of 3. Finished 10-07-2026 18:34 PDT. Repeat-1 evidence was never edited: `expt_v1/results/fsc_<label>.json` and the repeat-1 harvests are unchanged; the new values are in `expt_v1/results/fsc_median3_<label>.json`, the summary in `expt_v1/results/fsc_median3_summary.json`, the checkpoint in [`expt_v1/CKPT_e01_fsc_median3.md`](expt_v1/CKPT_e01_fsc_median3.md).

**Cells.** 996 repeat-1 member-cells (498 items × 2 members) × repeats 2–3 = 1,992 judge cells (QA 11-25-2026 corrected the product: 996 already includes both members); 1,982 measured. 114 cells first failed at sandbox provisioning before the agent ran (no receipt, no model request) and were re-sent once, as identical cells, in the single declared recovery pass; all 114 measured. The remaining 10 (H2_opus55_max only) were served and returned `model_error` with no verdict on every repeat, exactly as the same 5 items did for that member in repeat 1; they are model observations, never re-sent, and stay listed as unmeasured: `cs_set__dfs` (qwen3.5-4b), `cs_set__heapsort_build_heap` (qwen3.5-4b), `security_set__security_6858__safe__135_unsaferaceconditiontoctou_safe` (qwen3.5-4b), `realcode_set__26_secrets_token` (qwen3.5-9b), `humaneval_set__humaneval_2_truncate_number` (qwen3.6-27b-local). Controls are repeat-1 only by design (experiment 100's `judge_run.build_cells` builds every control cell as `__r1`), so they are unchanged.

**Per model, single repeat vs median of 3** (paired on the items complete under both; Δ is new − old with a 95% task-bootstrap interval, 10,000 draws, seed 20261007; p-val from a two-sided paired sign-flip permutation test, 10,000 draws, null: paired differences symmetric about 0; "complete" = both members measured at least once, experiment 103's rule):

| Model | n (paired items) | FSC, 1 repeat | FSC, median of 3 | Δ (new − old) [95% task bootstrap] | mean abs change | items changed | **new FSC, all complete items (n/judged)** | complete items on < 3 repeats (any member) | repeats 2–3 spend incl. recovery (USD) |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | 37 | 0.011 | 0.014 | +0.003 [-0.008, +0.016] p-val=1.000 | 0.008 | 2/37 | 0.014 (37/37) | 0 | 6.15 |
| Qwen3.5-2B | 51 | 0.073 | 0.073 | -0.000 [-0.010, +0.012] p-val=1.000 | 0.012 | 5/51 | 0.073 (51/51) | 0 | 14.35 |
| Qwen3.5-4B | 57 | 0.328 | 0.332 | +0.004 [-0.014, +0.021] p-val=0.856 | 0.032 | 15/57 | 0.332 (57/60) | 0 | 25.33 |
| Qwen3.5-9B | 58 | 0.414 | 0.412 | -0.002 [-0.016, +0.012] p-val=1.000 | 0.026 | 15/58 | 0.419 (59/60) | 1 | 29.01 |
| Qwen3-1.7B | 57 | 0.096 | 0.105 | +0.009 [-0.002, +0.021] p-val=0.234 | 0.016 | 8/57 | 0.105 (57/57) | 0 | 15.24 |
| Qwen3-4B | 60 | 0.365 | 0.362 | -0.003 [-0.015, +0.008] p-val=0.791 | 0.020 | 11/60 | 0.362 (60/60) | 0 | 23.95 |
| Qwen3-8B | 60 | 0.372 | 0.375 | +0.003 [-0.013, +0.017] p-val=0.838 | 0.023 | 12/60 | 0.375 (60/60) | 0 | 23.27 |
| Qwen3-14B | 60 | 0.462 | 0.457 | -0.004 [-0.017, +0.009] p-val=0.629 | 0.024 | 14/60 | 0.455 (61/61) | 2 | 26.22 |
| Qwen3.6-27B (local route control) | 51 | 0.771 | 0.776 | +0.006 [-0.004, +0.018] p-val=0.530 | 0.014 | 6/51 | 0.775 (52/52) | 1 | 19.89 |

- **Pooled over all 491 paired items:** Δ = +0.0015 [-0.0030, +0.0059] p-val=0.53 (sign-flip permutation); mean absolute per-item change 0.020 on the 0–1 FSC scale, i.e. about 0.1 of one rubric point. Within-member repeat SD on the 0–5 scale (over complete items): qwen3.5-0.8b 0.04, qwen3.5-2b 0.08, qwen3.5-4b 0.17, qwen3.5-9b 0.19, qwen3-1.7b 0.09, qwen3-4b 0.17, qwen3-8b 0.13, qwen3-14b 0.15, qwen3.6-27b-local 0.10.
- **Items newly complete** because a member that was `unmeasured_infra` in repeat 1 measured in repeats 2–3: qwen3.5-9b: `easy_set__19_mypower`; qwen3-14b: `easy_set__38_reverse_words`; qwen3.6-27b-local: `humaneval_set__humaneval_2_truncate_number`. Their FSC rests on 2 repeats for that member and is counted in the "all complete items" column.
- **Qwen3-14B's one proving cell** `hardware_set_real__my_interrupt_preempt`: Sol repeats [4, 3, 3] → median 3, Opus [4, 4, 4] → median 4; FSC 0.8 → **0.7**; cell SCSC = (1 · 1 · 0.7)^(1/3) = 0.888 (was 0.928); mean SCSC over 896 = 0.00099 (was 0.00104).
- **Does any conclusion change? No.** Every per-model Δ interval covers 0; the FSC ordering of the 9 models is identical under both judges (`fsc_order_unchanged: true`), so the TLDR's ordering claim (Qwen3.6-27B's audit FSC far above every smaller model's) stands at 0.775 vs 0.01–0.46; SCSC stays exactly 0.0 for 8 models and 0.00099 for Qwen3-14B; Gate G1 never used FSC. What the correction adds is the locked design's noise reduction: a single call had set the per-item FSC off its median-of-3 value for 88 of 491 items (mean |Δ| 0.020), with no net bias.
- **Spend.** Repeats 2–3 plus recovery cost $183.41; the experiment's judge total is now **$289.78 of the $400 cap** ($106.37 before this correction).
- **Transport deviation (recorded, no scientific setting changed).** `valk run results <run_id>` returned "tracker returned a malformed response" for every run, including the repeat-1 runs harvested on 10-01-2026 (a Valkyrie tracker-side regression). The harvest therefore reads each task's `evaluation_result` (the same `solution_b64` verdict bytes) with `valk run task`, and records `results_source` in every harvest file; receipts come from `valk run output` as before.

## Zero-score diagnostic (10-07-2026): are the zeros real?

**Setup and status.** This used no model calls and finished 10-07-2026 16:41.

- **What ran.** On skampere1 I recompiled every available G = 1 file from all 9 models (7,264 files across 8,064 declared cells; 800 cells have no file) with the frozen scorer's command and logged every error with the declaration it sits in. Then I ran two cumulative edit variants and one proof ablation, each rescored with the frozen scorer's own functions.
- **Integrity.**
  - Every rows file has one row per task.
  - There were 0 diagnostic errors.
  - **The recompile agreed with the recorded `compiles` field on all 7,264 available files; the other 800/8,064 declared cells have no file and remain in the denominator.**
  - The "model's own file" rows below reproduce experiment 01's recorded compile counts and IC factors for all 9 models.
- **Where things are.**
  - Code: [`expt_v1/diagnostics/diagnose_zero_scores.py`](expt_v1/diagnostics/diagnose_zero_scores.py).
  - Summaries: [`expt_v1/results/diagnostics_10-07-2026/`](expt_v1/results/diagnostics_10-07-2026/README.md).
  - Per-cell rows and edited files stay on the host (`/lfs/skampere1/0/brando9/rl4cv_e01_diag_10-07-2026/`), because they contain model output on VeriBench tasks.

**Why this was run.** Brando asked whether SCSC is really 0, and whether these models fail even IC_tests, i.e. their own `example` tests. The frozen scorer gives IC_tests = 1 only if the **whole file** compiles and contains at least one `example`. So one bad line anywhere zeroes IC_tests, IC_proofs and SCSC together. The scorer kept no compile logs, so the reasons were unknown.

**What each variant changes.** These are diagnostics, never VeriBench scores. Each row replaces the previous row's cell only where the variant edits the file.

1. **Model's own file.** The file is unchanged; only the recompile is new.
2. **+ namespace escaped.** The legacy regex wraps digit-leading namespace text and matching `end`, `open` and qualified uses in `«»`; see the rewrite limitation below.
   - VeriBench's task instruction gives ``Namespace (e.g., `namespace {file stem}`)``. This is in `vb_harbor/adapter/adapter.py:134`, at the pinned commit `c11b99b` and at VeriBench HEAD `9e312c9052`.
   - For **533 of 896 tasks** (all of easy_set, realcode_set and security_set) the stem starts with a digit, e.g. `namespace 1_MyAdd`. That is not a Lean identifier.
   - The gold files use `namespace MyAdd`.
3. **+ comment syntax repaired.** On top of variant 2:
   - a stand-alone `-!` line becomes the comment closer `-/`;
   - a `/--` declaration doc comment that is followed by a non-declaration becomes the module doc `/-!`.

   These variants edit namespace declarations/references and comment delimiters; they do not replace proof bodies. They are edited-file diagnostics, not unchanged model output.

**The proof ablation (historical run).** "Failing proofs → `sorry`" replaces only the theorem or lemma proofs that hold an error with `by sorry`, for up to 4 recompiles. Its intended boundary is to preserve definitions, statements and `example` tests, because IC_tests does not inspect examples for `sorry`. The original segmenter was heuristic; the review found edge cases involving indented declarations and statement-local `:=`, and the checked-in script now refuses ambiguous boundaries and preserves line positions. A read-only audit of 488 stored ablated files found no missing active definition or example declaration lines; this is not a full Lean syntax-tree equivalence check. Historical rows were not rerun or silently replaced. Factors come from the frozen scorer's `analyze_lean_file` and `ic_pp_for_compiled` (the kernel axiom check), so a `sorry` proof counts 0. FSC was not judged for any variant, so no SCSC is given for them.

**Historical rewrite limitation.** A read-only audit found 13 of 3,653 namespace variants differ from the guarded rewrite outside comments (literal/prose text or names discovered only in comments). All 13 namespace rows and their comment-repair counterparts failed compilation before and after proof ablation; none contributes a positive-factor cell. These are legacy edited-file measurements, not a guaranteed pure identifier intervention. The guarded counterfactual has not been recompiled; affected task IDs are recorded in the combined JSON artifacts. The positive recoveries quoted below do not come from these 13 rows.

### Frozen-scorer factors over all 896 cells (95% intervals; unit = task)

| Model | Files as scored | Compile, as written [95% CI] | IC_tests [95% CI] | IC_proofs [95% CI] | Cells with IC_tests·IC_proofs > 0 | Compile after failing proofs → `sorry` | IC_tests [95% CI] | IC_proofs [95% CI] | Cells with IC_tests·IC_proofs > 0 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5-0.8b | model's own file | 4/896 (0.4%) [0.2, 1.1] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 4/896 (0.4%) [0.2, 1.1] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-0.8b | + namespace escaped | 4/896 (0.4%) [0.2, 1.1] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 4/896 (0.4%) [0.2, 1.1] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-0.8b | + comment syntax repaired | 4/896 (0.4%) [0.2, 1.1] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 4/896 (0.4%) [0.2, 1.1] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-2b | model's own file | 3/896 (0.3%) [0.1, 1.0] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 3/896 (0.3%) [0.1, 1.0] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-2b | + namespace escaped | 5/896 (0.6%) [0.2, 1.3] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 5/896 (0.6%) [0.2, 1.3] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-2b | + comment syntax repaired | 6/896 (0.7%) [0.3, 1.5] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 6/896 (0.7%) [0.3, 1.5] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3-1.7b | model's own file | 0/896 (0.0%) [0.0, 0.4] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 1/896 (0.1%) [0.0, 0.6] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3-1.7b | + namespace escaped | 2/896 (0.2%) [0.1, 0.8] | 0.002 [0.001, 0.008] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 9/896 (1.0%) [0.5, 1.9] | 0.010 [0.005, 0.019] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3-1.7b | + comment syntax repaired | 2/896 (0.2%) [0.1, 0.8] | 0.002 [0.001, 0.008] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 9/896 (1.0%) [0.5, 1.9] | 0.010 [0.005, 0.019] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-4b | model's own file | 4/896 (0.4%) [0.2, 1.1] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 4/896 (0.4%) [0.2, 1.1] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] |
| qwen3.5-4b | + namespace escaped | 6/896 (0.7%) [0.3, 1.5] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 8/896 (0.9%) [0.4, 1.8] | 0.002 [0.001, 0.008] | 0.001 [0.000, 0.002] | 1/896 (0.1%) [0.0, 0.6] |
| qwen3.5-4b | + comment syntax repaired | 15/896 (1.7%) [1.0, 2.7] | 0.002 [0.001, 0.008] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 18/896 (2.0%) [1.3, 3.1] | 0.003 [0.001, 0.010] | 0.001 [0.000, 0.002] | 1/896 (0.1%) [0.0, 0.6] |
| qwen3-4b | model's own file | 0/896 (0.0%) [0.0, 0.4] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 11/896 (1.2%) [0.7, 2.2] | 0.012 [0.007, 0.022] | 0.002 [0.000, 0.004] | 3/896 (0.3%) [0.1, 1.0] |
| qwen3-4b | + namespace escaped | 2/896 (0.2%) [0.1, 0.8] | 0.002 [0.001, 0.008] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 36/896 (4.0%) [2.9, 5.5] | 0.040 [0.029, 0.055] | 0.005 [0.002, 0.008] | 10/896 (1.1%) [0.6, 2.0] |
| qwen3-4b | + comment syntax repaired | 2/896 (0.2%) [0.1, 0.8] | 0.002 [0.001, 0.008] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 38/896 (4.2%) [3.1, 5.8] | 0.042 [0.031, 0.058] | 0.005 [0.002, 0.009] | 11/896 (1.2%) [0.7, 2.2] |
| qwen3-8b | model's own file | 2/896 (0.2%) [0.1, 0.8] | 0.002 [0.001, 0.008] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 15/896 (1.7%) [1.0, 2.7] | 0.017 [0.010, 0.027] | 0.002 [0.000, 0.005] | 5/896 (0.6%) [0.2, 1.3] |
| qwen3-8b | + namespace escaped | 13/896 (1.5%) [0.9, 2.5] | 0.015 [0.008, 0.025] | 0.011 [0.005, 0.019] | 11/896 (1.2%) [0.7, 2.2] | 73/896 (8.1%) [6.5, 10.1] | 0.082 [0.065, 0.101] | 0.022 [0.014, 0.031] | 35/896 (3.9%) [2.8, 5.4] |
| qwen3-8b | + comment syntax repaired | 13/896 (1.5%) [0.9, 2.5] | 0.015 [0.008, 0.025] | 0.011 [0.005, 0.019] | 11/896 (1.2%) [0.7, 2.2] | 74/896 (8.3%) [6.6, 10.2] | 0.083 [0.066, 0.102] | 0.022 [0.014, 0.031] | 35/896 (3.9%) [2.8, 5.4] |
| qwen3.5-9b | model's own file | 5/896 (0.6%) [0.2, 1.3] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 8/896 (0.9%) [0.4, 1.8] | 0.003 [0.001, 0.010] | 0.001 [0.000, 0.003] | 2/896 (0.2%) [0.1, 0.8] |
| qwen3.5-9b | + namespace escaped | 10/896 (1.1%) [0.6, 2.0] | 0.001 [0.000, 0.006] | 0.002 [0.000, 0.006] | 1/896 (0.1%) [0.0, 0.6] | 23/896 (2.6%) [1.7, 3.8] | 0.012 [0.007, 0.022] | 0.007 [0.003, 0.012] | 10/896 (1.1%) [0.6, 2.0] |
| qwen3.5-9b | + comment syntax repaired | 15/896 (1.7%) [1.0, 2.7] | 0.002 [0.001, 0.008] | 0.004 [0.001, 0.009] | 2/896 (0.2%) [0.1, 0.8] | 38/896 (4.2%) [3.1, 5.8] | 0.023 [0.015, 0.036] | 0.014 [0.008, 0.021] | 20/896 (2.2%) [1.5, 3.4] |
| qwen3-14b | model's own file | 5/896 (0.6%) [0.2, 1.3] | 0.006 [0.002, 0.013] | 0.001 [0.000, 0.003] | 1/896 (0.1%) [0.0, 0.6] | 37/896 (4.1%) [3.0, 5.6] | 0.041 [0.030, 0.056] | 0.009 [0.005, 0.013] | 17/896 (1.9%) [1.2, 3.0] |
| qwen3-14b | + namespace escaped | 30/896 (3.3%) [2.4, 4.7] | 0.034 [0.024, 0.047] | 0.027 [0.017, 0.038] | 25/896 (2.8%) [1.9, 4.1] | 130/896 (14.5%) [12.3, 17.0] | 0.145 [0.124, 0.170] | 0.065 [0.051, 0.080] | 90/896 (10.0%) [8.2, 12.2] |
| qwen3-14b | + comment syntax repaired | 33/896 (3.7%) [2.6, 5.1] | 0.037 [0.026, 0.051] | 0.030 [0.020, 0.042] | 28/896 (3.1%) [2.2, 4.5] | 140/896 (15.6%) [13.4, 18.1] | 0.156 [0.134, 0.181] | 0.071 [0.057, 0.086] | 98/896 (10.9%) [9.1, 13.2] |
| qwen3.6-27b-local | model's own file | 2/896 (0.2%) [0.1, 0.8] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 0/896 (0.0%) [0.0, 0.4] | 15/896 (1.7%) [1.0, 2.7] | 0.016 [0.009, 0.026] | 0.005 [0.002, 0.009] | 9/896 (1.0%) [0.5, 1.9] |
| qwen3.6-27b-local | + namespace escaped | 8/896 (0.9%) [0.4, 1.8] | 0.008 [0.004, 0.016] | 0.007 [0.002, 0.012] | 6/896 (0.7%) [0.3, 1.5] | 26/896 (2.9%) [2.0, 4.2] | 0.028 [0.019, 0.041] | 0.015 [0.008, 0.022] | 19/896 (2.1%) [1.4, 3.3] |
| qwen3.6-27b-local | + comment syntax repaired | 22/896 (2.5%) [1.6, 3.7] | 0.023 [0.015, 0.036] | 0.022 [0.013, 0.032] | 20/896 (2.2%) [1.5, 3.4] | 111/896 (12.4%) [10.4, 14.7] | 0.123 [0.103, 0.146] | 0.060 [0.047, 0.074] | 91/896 (10.2%) [8.3, 12.3] |

Compile proportions and IC_tests use Wilson intervals. IC_proofs means use 10,000 task-bootstrap resamples (NumPy default_rng seed 0); intervals describe this single run; an all-zero bootstrap interval does not bound the probability of an unseen success. All have p-val=n/a (estimation only). The JSON artifacts record both methods.

### Why the model's own files fail

| Model | Cells with a file | Recompile disagrees with recorded result | No file (cut off or no Lean) | Definitions fail | Tests or statements fail | Compiles after proof→`sorry` | Compiles as is |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5-0.8b | 800/896 | 0 | 96 | 766 | 30 | 0 | 4 |
| qwen3.5-2b | 585/896 | 0 | 311 | 578 | 4 | 0 | 3 |
| qwen3-1.7b | 606/896 | 0 | 290 | 598 | 7 | 1 | 0 |
| qwen3.5-4b | 893/896 | 0 | 3 | 874 | 15 | 0 | 4 |
| qwen3-4b | 859/896 | 0 | 37 | 820 | 28 | 11 | 0 |
| qwen3-8b | 855/896 | 0 | 41 | 810 | 30 | 13 | 2 |
| qwen3.5-9b | 895/896 | 0 | 1 | 860 | 27 | 3 | 5 |
| qwen3-14b | 875/896 | 0 | 21 | 801 | 37 | 32 | 5 |
| qwen3.6-27b-local | 896/896 | 0 | 0 | 858 | 23 | 13 | 2 |

| Model | Compiles after proof→`sorry` (incl. as is), 95% Wilson CI | Cells with IC_tests·IC_proofs > 0 after ablation | Ablation IC_tests (mean over 896, 95% CI) | Ablation IC_proofs (mean over 896, 95% CI) | Definitions compile, among non-compiling files | Empty reasoning block |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.5-0.8b | 4/896 (0.4%) [0.2, 1.1] | 0/896 (0.0%) [0.0, 0.4] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 30/796 (3.8%) | 0/753 |
| qwen3.5-2b | 3/896 (0.3%) [0.1, 1.0] | 0/896 (0.0%) [0.0, 0.4] | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 4/582 (0.7%) | 0/569 |
| qwen3-1.7b | 1/896 (0.1%) [0.0, 0.6] | 0/896 (0.0%) [0.0, 0.4] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 8/606 (1.3%) | 501/606 |
| qwen3.5-4b | 4/896 (0.4%) [0.2, 1.1] | 0/896 (0.0%) [0.0, 0.4] | 0.001 [0.000, 0.006] | 0.000 [0.000, 0.000] | 15/889 (1.7%) | 0/887 |
| qwen3-4b | 11/896 (1.2%) [0.7, 2.2] | 3/896 (0.3%) [0.1, 1.0] | 0.012 [0.007, 0.022] | 0.002 [0.000, 0.004] | 39/859 (4.5%) | 0/859 |
| qwen3-8b | 15/896 (1.7%) [1.0, 2.7] | 5/896 (0.6%) [0.2, 1.3] | 0.017 [0.010, 0.027] | 0.002 [0.000, 0.005] | 43/853 (5.0%) | 0/855 |
| qwen3.5-9b | 8/896 (0.9%) [0.4, 1.8] | 2/896 (0.2%) [0.1, 0.8] | 0.003 [0.001, 0.010] | 0.001 [0.000, 0.003] | 30/890 (3.4%) | 0/893 |
| qwen3-14b | 37/896 (4.1%) [3.0, 5.6] | 17/896 (1.9%) [1.2, 3.0] | 0.041 [0.030, 0.056] | 0.009 [0.005, 0.013] | 69/870 (7.9%) | 574/875 |
| qwen3.6-27b-local | 15/896 (1.7%) [1.0, 2.7] | 9/896 (1.0%) [0.5, 1.9] | 0.016 [0.009, 0.026] | 0.005 [0.002, 0.009] | 36/894 (4.0%) | 0/688 |

Historical share of non-compiling files with at least one error in each legacy message-regex category (categories overlap and do not isolate root causes):

| Model | Non-compiling files | parse | unknown_name | type_error | tactic_failed | termination | index_bounds_proof | timeout | other | in theorem_proof | in theorem_statement | in definition | in example_test | in other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5-0.8b | 796 | 59% | 38% | 7% | 12% | 0% | 1% | 0% | 44% | 8% | 12% | 24% | 8% | 83% |
| qwen3.5-2b | 582 | 93% | 52% | 38% | 54% | 1% | 2% | 0% | 57% | 42% | 39% | 62% | 47% | 91% |
| qwen3-1.7b | 606 | 96% | 63% | 31% | 57% | 0% | 1% | 0% | 55% | 52% | 60% | 83% | 72% | 69% |
| qwen3.5-4b | 889 | 96% | 53% | 51% | 76% | 0% | 2% | 2% | 43% | 67% | 38% | 69% | 72% | 88% |
| qwen3-4b | 859 | 92% | 59% | 49% | 68% | 0% | 1% | 0% | 53% | 62% | 35% | 63% | 67% | 81% |
| qwen3-8b | 853 | 94% | 66% | 49% | 83% | 1% | 3% | 0% | 29% | 89% | 28% | 73% | 85% | 71% |
| qwen3.5-9b | 890 | 94% | 45% | 50% | 79% | 2% | 3% | 1% | 42% | 72% | 28% | 64% | 68% | 86% |
| qwen3-14b | 870 | 88% | 51% | 48% | 70% | 0% | 4% | 0% | 30% | 68% | 24% | 49% | 59% | 81% |
| qwen3.6-27b-local | 894 | 91% | 48% | 39% | 86% | 2% | 1% | 1% | 39% | 83% | 19% | 44% | 72% | 94% |

**Failure classes (heuristic).** These are assigned to the model's own non-compiling files, in this order:

1. *definitions fail*: the file still fails with every `theorem`, `lemma` and `example` removed;
2. *tests or statements fail*: definitions compile, but an `example` or a theorem statement errors;
3. *compiles after proof → `sorry`*.

The definitions-only probe removes theorem declarations as well as proofs, so remaining definitions can fail if they depended on a removed theorem. It is not an isolated measurement of implementation correctness. The digit-namespace and `/--` cells fall in class 1, because the bad line is kept. Error kinds are the original coarse message-regex categories: `function expected` was classified as parse and `failed to synthesize` as tactic failure. The script now prioritizes these type errors correctly; historical counts above have not been recomputed. "in other" covers module-level lines such as `namespace`, `end`, `open` and imports. The summaries' `files_with_lean3_markers` came from a regex that also matched valid Lean 4 `cases … with`, so it is not reported.

### What this shows

- **The near-zero results reproduce under the frozen scorer.** The same compiler reproduces every recorded result. The baseline compile counts are reproduced. In the heuristic deletion probe, 0.7–7.9% of each model's non-compiling files compile after theorem and example blocks are removed; removing dependencies can itself cause failures.
- **VeriBench's invalid namespace hint contributes to the zeros, but most remain after repair.** The legacy regex matches digit-leading namespace text in 516 Qwen3-14B files, 526 Qwen3.5-9B files and 511 Qwen3-8B files, each out of 896 declared cells. The legacy namespace rewrite changes cells with IC_tests·IC_proofs > 0 as follows:
  - **Qwen3-14B: 1 → 25** (2.8% [1.9, 4.1]); IC_tests 0.006 → 0.034, IC_proofs 0.001 → 0.027;
  - Qwen3-8B: 0 → 11;
  - Qwen3.6-27B: 0 → 6.

  Definitions, tests and proofs originate from the model; the historical rewrite limitation above applies. Frontier single-call models in experiment 103 have higher compile-with-example rates on these task families, e.g. `gpt-6-astra-high` 346/514 = 0.673 [0.631, 0.712] vs 102/341 = 0.299 [0.253, 0.350] elsewhere (95% Wilson intervals, unit = task; 855/896 measured, 41 unmeasured). Task-family difficulty confounds that comparison; it does not identify the namespace hint's causal effect.
- **Comment syntax is the next shallow error.** Qwen3.6-27B has 659 first errors in the generic "unexpected token …; expected …" category; 655 specifically report `namespace` where a declaration is expected. The generic count alone does not isolate a doc-comment cause. Repairing comments takes it from 6 to 20 positive cells, and from 26 to 111 files compiling after failing proofs → `sorry`.
- **Conditional proof fractions describe a selected subset.** After both repairs and proof ablation, the mean per-file IC_proofs among compiling files is 0.457 [0.395, 0.520] for Qwen3-14B (140 files), 0.486 [0.420, 0.554] for Qwen3.6-27B (111), 0.330 [0.224, 0.438] for Qwen3.5-9B (38), and 0.269 [0.191, 0.353] for Qwen3-8B (74). These are 95% task-bootstrap intervals (10,000 draws, seed 0), p-val=n/a. They are means of per-file fractions, not pooled theorem pass rates, and do not establish that proof skill is adequate on the full task set.
- **The smallest models need more than syntax.** Qwen3.5-0.8B, Qwen3.5-2B and Qwen3-1.7B stay at ≤ 1.0% compiling and 0 positive cells even with every repair and the ablation. They yield no Lean file at all in 96–311 of 896 cells (cut off at the token cap or no extractable block), and they cite modules that do not exist: "unknown module prefix" is Qwen3.5-0.8B's most common first error, at 183.
- **This comparison does not establish a benefit from non-empty reasoning.** Qwen3-14B leaves its `<think>` block empty in 574 of 875 files, and Qwen3-1.7B in 501 of 606. For Qwen3-14B, files with an empty block compile after the ablation at 24/574 (4.2% [2.8%, 6.2%]); files with reasoning do so at 13/301 (4.3% [2.5%, 7.2%]). These are Wilson 95% intervals over tasks; this observational comparison establishes neither equivalence nor the causal effect of forcing reasoning.
- **What this means for the follow-up** (experiment 08, `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`).
  - An SFT warm start can test whether verified complete Lean 4 files improve generation under the pinned toolchain: valid names, comment syntax, real Mathlib modules and lemmas, instances, and proofs. This diagnostic does not isolate syntax skill from proof skill.
  - Its data should include digit-leading file stems with valid namespaces. Experiment 08 plans to generate teacher files on digit-stem VeriBench train tasks and requires kept files to compile; whether each such task yields a kept file is not yet measured. Experiment 02A v3 uses Mostly Basic Python Problems (MBPP) stems `task_<id>` instead.
  - Fixing the namespace hint is a VeriBench decision (agents-config Trigger Rule 43). A rerun on a fixed instruction would be a new `expt_v2` condition.

## Judge spend (running total against the $400 cap) — final, all runs harvested

| Suite | Members | Cells | Status | Charges (USD) |
|---|---|---:|---|---:|
| `rl4cv-e01-controls` | H2_sol_high + H2_opus55_max | 60 × 2 | measured, verdict PASS | 4.57 |
| `rl4cv-e01:qwen3.5-4b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 117/120 measured (3 `unmeasured_infra` on H2_opus55_max) | 13.49 |
| `rl4cv-e01:qwen3-8b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 120/120 measured | 13.17 |
| `rl4cv-e01:qwen3-14b` (1 main cell + audit) | H2_sol_high + H2_opus55_max | 61 × 2 | 121/122 measured (1 `unmeasured_infra` on H2_opus55_max) | 14.67 |
| `rl4cv-e01:qwen3-4b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 120/120 measured | 12.90 |
| `rl4cv-e01:qwen3.5-9b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 118/120 measured (2 `unmeasured_infra` on H2_opus55_max) | 15.14 |
| `rl4cv-e01:qwen3.5-2b` (audit only, 0 main cells; only 51 audit cells — see note) | H2_sol_high + H2_opus55_max | 51 × 2 | 102/102 measured | 8.30 |
| `rl4cv-e01:qwen3-1.7b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 57 × 2 | 114/114 measured | 9.14 |
| `rl4cv-e01:qwen3.6-27b-local` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 52 × 2 | 103/104 measured (1 `unmeasured_infra` on H2_opus55_max) | 11.17 |
| `rl4cv-e01:qwen3.5-0.8b` (audit only, 0 main cells; only 37 audit cells — see note; added 10-01-2026 12:16, the omission this reopen fixed) | H2_sol_high + H2_opus55_max | 37 × 2 | 74/74 measured | 3.82 |

| `rl4cv-e01:qwen3.5-0.8b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 37 × 2 × 2 | 148/148 measured | 6.15 |
| `rl4cv-e01:qwen3.5-2b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 51 × 2 × 2 | 204/204 measured | 14.35 |
| `rl4cv-e01:qwen3.5-4b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 60 × 2 × 2 | 234/240 measured | 25.33 |
| `rl4cv-e01:qwen3.5-9b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 60 × 2 × 2 | 238/240 measured | 29.01 |
| `rl4cv-e01:qwen3-1.7b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 57 × 2 × 2 | 228/228 measured | 15.24 |
| `rl4cv-e01:qwen3-4b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 60 × 2 × 2 | 240/240 measured | 23.95 |
| `rl4cv-e01:qwen3-8b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 60 × 2 × 2 | 240/240 measured | 23.27 |
| `rl4cv-e01:qwen3-14b` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 61 × 2 × 2 | 243/244 measured | 26.22 |
| `rl4cv-e01:qwen3.6-27b-local` repeats 2–3 (+ recovery) | H2_sol_high + H2_opus55_max | 52 × 2 × 2 | 207/208 measured | 19.89 |

| `rl4cv-e01-probe:qwen3.5-9b` (4 proving G = 8 cells × 3 repeats; added 10-07-2026) | H2_sol_high + H2_opus55_max | 4 × 3 × 2 | 24/24 measured | 3.04 |
| `rl4cv-e01-probe:qwen3-14b` (7 proving G = 8 cells × 3 repeats; added 10-07-2026) | H2_sol_high + H2_opus55_max | 7 × 3 × 2 | 42/42 measured | 4.02 |

**Final total: $296.84 (QA 11-25-2026: summing every harvest cell's reported charge gives $296.83; $296.84 adds the rounded subtotals $106.37 + $183.41 + $7.06; the $400 budget verdict is unaffected) of $400** ($106.37 for controls and repeat 1 through 10-01-2026; $183.41 for repeats 2–3 and the recovery pass on 10-07-2026; $7.06 for the 11 proving G = 8 probe cells on 10-07-2026). Every admitted FSC run is harvested; no further Valkyrie spend is expected for this experiment unless Brando admits the 17 IC_tests = 1, IC_proofs = 0 probe cells that sit outside the locked judge scope.

Last updated: 10-07-2026 20:20 PDT.

## Pipeline validation on CPU (09-30-2026, not the locked preflight)

Run in a 4-CPU cloud container with no GPU, using the transformers backend, the current v7 pack, thinking off and 3 tasks. Every stage ran: prompt construction from experiment 103's pinned code, generation, extraction, scorer jobs, the frozen scorer (`59059a20d`, Lean v4.22.0, Mathlib v4.22.0 from `lake exe cache get`), collection and summary. Evidence: [`expt_v1/results/pipeline_validation_cpu_09-30-2026.json`](expt_v1/results/pipeline_validation_cpu_09-30-2026.json).

| Cell | IC_tests | IC_proofs | Theorems proved | Verdict |
|---|---:|---:|---|---|
| Gold `easy_set__1_myadd` | 1.0 | 1.0 | 6 / 6 | control passes |
| Gold `cs_set__binary_search` | 1.0 | 1.0 | 13 / 13 | control passes |
| Empty file | 0.0 | 0.0 | — | control passes |
| Gold with one proof replaced by `sorry` | 1.0 | 0.667 | 4 / 6 (the `sorry` also reaches a `@[simp]` user) | control passes |
| Qwen3-0.6B on `easy_set__1_myadd`, `easy_set__10_myevensumparity`, `cs_set__binary_search` | 0.0 | 0.0 | 0 compile of 3 | measured on 3 cells only |

Qwen3-0.6B's answers (305, 1,047 and 754 generated tokens, all finished cleanly and extracted) are Lean-3-like pseudo-code (`module`, `definition … where`, `is_int(a)`, `<name>_prop`), matching the failure pattern experiment 103 found for Qwen3.6-27B. Generation ran at about 3 tokens per second on CPU, so the declared 896-task run needs the GPU hosts in [`scripts/cc_prompt_run_experiment_on_snap.md`](../../scripts/cc_prompt_run_experiment_on_snap.md).

## VeriBench V1, G = 1, experiment 103 single-call protocol

The denominator is always 896 declared cells per model. Unmeasured cells are listed, never counted as 0. FSC values are the locked median of 3 judge repeats per member (corrected 10-07-2026; see "FSC repeat correction").

| Model | Revision | Measured / 896 | Cut off | No Lean | Compile rate | IC_tests | IC_proofs | FSC (ungated audit diagnostic) | Historical mean per-file SCSC |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | `2fc06364` | 896/896 | 661 | 95 | 0.45% | 0.0 | 0.0 | 0.014* | 0.0 (exact) |
| Qwen3.5-2B | `15852e8c` | 896/896 | 475 | 310 | 0.33% | 0.0 | 0.0 | 0.073* | 0.0 (exact) |
| Qwen3.5-4B | `851bf6e8` | 896/896 | 12 | 3 | 0.45% | 0.0011 | 0.0 | 0.332* | 0.0 (exact) |
| Qwen3.5-9B | `c2022362` | 896/896 | 5 | 1 | 0.56% | 0.0 | 0.0 | 0.419*† | 0.0 (exact) |
| Qwen3-1.7B | `70d244cc` | 896/896 | 252 | 290 | 0.0% | 0.0 | 0.0 | 0.105* | 0.0 (exact) |
| Qwen3-4B | `1cfa9a72` | 896/896 | 37 | 37 | 0.0% | 0.0 | 0.0 | 0.362* | 0.0 (exact) |
| Qwen3-8B | `b968826d` | 896/896 | 41 | 41 | 0.22% | 0.0022 | 0.0 | 0.375* | 0.0 (exact) |
| Qwen3-14B | `40c06982` | 896/896 | 21 | 21 | 0.56% | 0.0056 | 0.0011 | 0.455** | 0.00099 (exact) |
| Qwen3.6-27B (local route control) | `6a9e13bd` | 896/896 | 236 | 0 | 0.22% | 0.0011 | 0.0 | 0.775§ | 0.0 (exact) |
| *Reference: Qwen3.6-27B via Valkyrie (experiment 103)* | | *604* | *245 at cap* | | | *0.002* | *0.002* | *0.900* | *0.002* |

\* FSC for Qwen3.5-0.8B, Qwen3.5-2B, Qwen3.5-4B, Qwen3.5-9B, Qwen3-1.7B, Qwen3-4B and Qwen3-8B is the **ungated diagnostic mean over the core-split audit only** (0 cells reach the gated `fsc_compiled` scope per D-003, since all seven have 0 cells with IC_tests · IC_proofs > 0). SCSC is exact at 0.0 for all seven. Per-task FSC (median of 3): `expt_v1/results/fsc_median3_<label>.json`; the superseded single-repeat values stay in `fsc_<label>.json`. Qwen3.5-4B's 3 items whose Opus member returned `model_error` on every repeat remain incomplete (57/60), listed, never counted as zero. Qwen3.5-0.8B's audit pack has only **37** cells and Qwen3.5-2B's only **51**, not 60 — one or more core splits had fewer than 12 tasks eligible for the audit at these models' scored output; `build-model`'s round-trip still returned `verdict: PASS` for both. Qwen3.5-0.8B's FSC audit was omitted from the first completion pass and added in the 10-01-2026 12:16 reopen (master-caught); see `REPORT.md` for the writeup.

† Qwen3.5-9B's `H2_opus55_max` member measured 59 of 60 items (`easy_set__19_mypower` measured in repeats 2–3 after an infrastructure miss in repeat 1; `realcode_set__26_secrets_token` returned `model_error` on every repeat); its FSC mean (0.419) is over the 59 complete items, with the incomplete item listed, not dropped or counted as zero (`expt_v1/results/fsc_median3_qwen3.5-9b.json` → `items_with_missing_repeats`).

§ Qwen3.6-27B's judge run (52 audit cells × 2 members, port 9708) harvested 10-01-2026 09:08 — the last FSC measurement the experiment needed. Its own IC_tests (0.0011, i.e. 1/896) is nonzero like Qwen3-14B's, but that cell's IC_proofs is 0.0, so it still has **0** cells with IC_tests · IC_proofs > 0; SCSC stays exact at 0.0. Its ungated audit FSC mean (0.775, median of 3, over 52/52 items; `humaneval_set__humaneval_2_truncate_number`'s Opus member rests on 2 repeats) is notably higher than every smaller model's (0.07-0.46): a qualitative sign that a more capable model produces more plausible/well-formed Lean even when it still doesn't compile or prove, consistent with — but not proof of — a capability gradient this project does not otherwise measure. Per-task FSC: `expt_v1/results/fsc_median3_qwen3.6-27b-local.json`.

\*\* Qwen3-14B has **one** cell with IC_tests · IC_proofs > 0 — `hardware_set_real__my_interrupt_preempt` (IC_tests 1.0, IC_proofs 1.0, FSC 0.7 as the median of 3: Sol 4, 3, 3 and Opus 4, 4, 4; 0.8 under the single repeat first reported) — the experiment's first fully-compiling, fully-proving, judge-scored cell among the ≤14B models. Its SCSC = (1.0 · 1.0 · 0.7)^(1/3) ≈ 0.888 (0.928 under the single repeat), which is why the model's overall `SCSC_exact_where_available` (0.00099, exact over all 896 cells; 0.00104 before the correction) is nonzero while every other model's stays exactly 0.0. The 0.455 FSC column value is still the ungated mean over the 60-item audit plus this one positive cell (61 items, all complete after repeats 2–3; `easy_set__38_reverse_words`'s Opus member rests on 2 repeats); see `expt_v1/results/fsc_median3_qwen3-14b.json`.

## Compute estimate (09-30-2026, skampere1, before launch)

- **Host/GPUs.** `skampere1`, 8× A100-SXM4-80GB. GPUs 0–2 belong to user `truongvo` (busy) and are never touched; GPUs 3–7 idle (0 MiB, 0%) at baseline. GPU rule (B200 → H200 first) not met: `skampere3` `/lfs` 100% full (21 GB free) and 7/8 GPUs busy; `skampere2` `/lfs` 100% full (99 GB free) and GPUs shared with 4 other users. Using `skampere1` instead.
- **G = 1 generation (9 models × 896 tasks).** From `PROTOCOL.md`: 1–3 GPU-hours/model up to 9B (7 models: Qwen3.5-0.8B/2B/4B/9B, Qwen3-1.7B/4B/8B → 7–21 GPU-hours), 3–8 GPU-hours for 14B and 27B (Qwen3-14B, Qwen3.6-27B-local → 6–16 GPU-hours). **Subtotal: 13–37 GPU-hours.**
- **G = 8 probe (8 models × 132 tasks × 8 samples, control excluded).** 1,056 generations/model at a 12,288-token cap (0.19× the eval cap) vs. 896 at 65,536. Estimated at ≈0.2–0.7 GPU-hours/model for the ≤9B/8B models and ≈0.7–1.8 GPU-hours for the 14B model. **Subtotal: ≈2–7 GPU-hours.**
- **Total generation: ≈15–44 GPU-hours.** Scoring: 1–5 CPU-hours per 896-file job × 9 eval jobs (9–45 CPU-hours) plus 64 probe scoring jobs (8 models × 8 samples) of 132 files each (≈10–50 CPU-hours combined), parallelizable across the host's 128 cores and independent of the GPU critical path.
- **Wall-clock.** One model per free GPU, in parallel across GPUs 3–7 (5 devices), smallest→largest: **≈4–12 hours** for all 9 eval + 8 probe jobs, dominated by the 14B/27B cells and by any cells that hit the token cap (experiment 103 saw 245/896 cells hit the 65,536 cap for Qwen3.6-27B).
- **Go.** Brando's "run my experiments on snap!" (09-30-2026) plus his earlier "just do the experiment ... Go" cover this GPU run (cc.md §5 "Ask"); posted to issue #3 before launch, launching without further wait per `DISPATCH_e01.md`.

## Signal probe, G = 8, 128 tasks (128 tasks over 33 splits: 31 splits × 4 tasks, `aerospace_set_real` 3, `rfc_set_synthetic` 1; QA 11-25-2026 corrected "4/split × 32")

**Gate G1 verdict (PROTOCOL.md § Locked parameters), final over all 8 probe-scored models: PASS.** The locked criterion ("any model, any split reaches a mixed-group share ≥ 0.20") is monotonic and was already decisive early from Qwen3-14B alone; with all 8 models now scored, **two** models clear it, and the signal is otherwise thin:
- **Qwen3-14B**: `kernel_binary` mixed-group share (the fraction of its 8-sample groups with non-uniform kernel-binary reward — `rl4cv.experience.q_mixed_empirical`) reaches **≥ 0.20 on 6 splits** (max 0.333): `aerospace_set_real` 0.333, `concurrent_set_real` 0.25, `finance_set_synthetic` 0.25, `gov_cert_set_synthetic` 0.25, `hardware_set_real` 0.25, `medical_oss_set_real` 0.25.
- **Qwen3.5-9B**: reaches **≥ 0.20 on 4 splits** (max 0.25): `compilers_set_synthetic` 0.25, `concurrent_set_real` 0.25, `medical_oss_set_real` 0.25, `os_embedded_set_synthetic` 0.25 (overlapping `concurrent_set_real`/`medical_oss_set_real` with Qwen3-14B).
- Both channels (`kernel_binary`/`proof_fraction`) are identical for every model, since the only measured reward difference between the two channels anywhere in the probe is the same handful of proving cells.
- **The other 6 of 8 probe-scored models (Qwen3.5-0.8B, Qwen3.5-2B, Qwen3.5-4B, Qwen3-1.7B, Qwen3-4B, Qwen3-8B) show exactly 0.0 overall mixed-group share on every split** (0/128 groups mixed each) — consistent with their 0% proof rate on the full 896-task eval. The signal is thin: only the two largest probed models (9B, 14B) produce any mixed groups at all, and even for them the overall mixed-group share is small (3.1-4.7%) — it is the **per-split max**, not the overall rate, that clears the locked 0.20 threshold.

Per README §Decision criterion, the union of Qwen3-14B's 6 splits and Qwen3.5-9B's 4 splits (8 distinct: `aerospace_set_real`, `compilers_set_synthetic`, `concurrent_set_real`, `finance_set_synthetic`, `gov_cert_set_synthetic`, `hardware_set_real`, `medical_oss_set_real`, `os_embedded_set_synthetic`) seed experiment 02's pools.

| Model | Channel | Mean reward | Mixed-group share (overall) | ρ (overall) | H (overall) | Max per-split mixed-group share | Groups measured / 128 |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | kernel_binary | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-0.8B | proof_fraction | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-0.8B | scsc | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-0.8B | fsc_compiled | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-2B | kernel_binary | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-2B | proof_fraction | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-2B | scsc | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-2B | fsc_compiled | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-4B | kernel_binary | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-4B | proof_fraction | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-4B | scsc | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3.5-4B | fsc_compiled (partial: 1 groups unmeasured) | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 127/128 |
| Qwen3.5-9B | kernel_binary | 0.0039 | 0.0312 | 2.06 | 0.0312 | **0.25** (`compilers_set_synthetic`, 3 others ≥0.20) | 128/128 |
| Qwen3.5-9B | proof_fraction | 0.0039 | 0.0312 | 2.06 | 0.0312 | **0.25** (`compilers_set_synthetic`, 3 others ≥0.20) | 128/128 |
| Qwen3.5-9B | scsc | 0.0033 | 0.0312 | 1.72 | 0.0312 | **0.25** (`compilers_set_synthetic`, 3 others ≥0.20) | 128/128 |
| Qwen3.5-9B | fsc_compiled | 0.0025 | 0.0312 | 1.30 | 0.0312 | **0.25** (`compilers_set_synthetic`, 3 others ≥0.20) | 128/128 |
| Qwen3-1.7B | kernel_binary | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-1.7B | proof_fraction | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-1.7B | scsc | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-1.7B | fsc_compiled (partial: 2 groups unmeasured) | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 126/128 |
| Qwen3-4B | kernel_binary | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-4B | proof_fraction | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-4B | scsc | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-4B | fsc_compiled (partial: 7 groups unmeasured) | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 121/128 |
| Qwen3-8B | kernel_binary | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-8B | proof_fraction | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-8B | scsc | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 128/128 |
| Qwen3-8B | fsc_compiled (partial: 1 groups unmeasured) | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 127/128 |
| Qwen3-14B | kernel_binary | 0.0068 | 0.0469 | 5.98 | 0.0469 | **0.3333** (`aerospace_set_real`, 5 others ≥0.20) | 128/128 |
| Qwen3-14B | proof_fraction | 0.0068 | 0.0469 | 5.98 | 0.0469 | **0.3333** (`aerospace_set_real`, 5 others ≥0.20) | 128/128 |
| Qwen3-14B | scsc | 0.0052 | 0.0469 | 4.46 | 0.0469 | **0.3333** (`aerospace_set_real`, 5 others ≥0.20) | 128/128 |
| Qwen3-14B | fsc_compiled (partial: 5 groups unmeasured) | 0.0034 | 0.0488 | 2.72 | 0.0488 | **0.3333** (`aerospace_set_real`, 5 others ≥0.20) | 123/128 |

"Overall" columns are group-weighted means of the per-split values over the fully measured groups (33 splits, 31 × 4 + 3 + 1 = 128 groups; QA 11-25-2026 corrected "32 splits × 4"; a group is unmeasured when any of its 8 samples has a `null` reward, and it is excluded, never counted as 0); per-split values are in `expt_v1/results/summaries/rho_h_<label>_g8_<channel>.{json,md}` (all four channels committed 10-07-2026; the pooled single-environment ρ and H are in `expt_v1/results/probe_channels_summary.json` → `pooled_single_environment`). `scsc` and `fsc_compiled` rows were added on 10-07-2026 after the 11 proving probe cells were judged (see "Probe proving cells judged"). `fsc_compiled` is **partial**: the locked judge scope (PROTOCOL.md) covers only cells with IC_tests · IC_proofs > 0, so the 17 probe cells with IC_tests = 1 and IC_proofs = 0 (Qwen3.5-4B 1, Qwen3-1.7B 3, Qwen3-4B 7, Qwen3-8B 1, Qwen3-14B 5) keep `fsc_compiled = null` and their groups are excluded from that row; Qwen3-14B's `fsc_compiled` mixed-group share (0.0488) is 6 mixed of 123 measured groups, against 6 of 128 for `scsc`.
